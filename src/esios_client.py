"""ESIOS API HTTP gateway, regional data fetching, and intelligent caching orchestration."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from config.settings import ESIOS_API_TOKEN
from src.database import load_data_by_ids, save_dataframe
from src.utils import translate_indicator


def _is_indicator_cached(
    df_cached: pd.DataFrame, indicator_id: int, start_dt: datetime, end_dt: datetime
) -> bool:
    """Evaluates whether the local database cache covers a specific indicator for the time range.

    Args:
        df_cached (pd.DataFrame): DataFrame containing cached records.
        indicator_id (int): Indicator ID to verify.
        start_dt (datetime): Start datetime of requested range.
        end_dt (datetime): End datetime of requested range.

    Returns:
        bool: True if the indicator is present and strictly covers the time range.
    """
    if df_cached.empty or "indicator_id" not in df_cached.columns:
        return False

    df_ind = df_cached[df_cached["indicator_id"] == indicator_id]
    if df_ind.empty:
        return False

    madrid_tz = ZoneInfo("Europe/Madrid")
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=madrid_tz)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=madrid_tz)

    cached_dates = pd.to_datetime(df_ind["datetime"]).dt.tz_convert("Europe/Madrid")
    min_cached = cached_dates.min()
    max_cached = cached_dates.max()

    # Strict boundary check
    return min_cached <= start_dt and max_cached >= end_dt


def _fetch_indicator_from_api(
    indicator_id: int, start_iso: str, end_iso: str, api_token: str
) -> pd.DataFrame:
    """Issues an HTTP request to e·sios API for a single indicator and parses response records.

    Args:
        indicator_id (int): ID of the indicator to fetch.
        start_iso (str): Start datetime in ISO UTC format.
        end_iso (str): End datetime in ISO UTC format.
        api_token (str): API authentication token.

    Returns:
        pd.DataFrame: DataFrame containing fetched indicator records.
    """
    headers = {
        "Accept": "application/json; application/vnd.esios-api-v1+json",
        "Content-Type": "application/json",
        "x-api-key": api_token,
    }

    params = {"start_date": start_iso, "end_date": end_iso}
    url = f"https://api.esios.ree.es/indicators/{indicator_id}"

    translated_name = translate_indicator(indicator_id=indicator_id)
    print(f"🌐 Requesting '{translated_name}' (ID: {indicator_id}) from e·sios API...")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and len(data) > 0:
            indicator_data = data[0].get("indicator", {})
        else:
            indicator_data = data.get("indicator", {}) if isinstance(data, dict) else {}

        raw_name = indicator_data.get("name", "Desconocido")
        values = indicator_data.get("values", []) if isinstance(indicator_data, dict) else []

        records = []
        for item in values:
            raw_val = item.get("value")
            if raw_val is None:
                continue

            geo_id_val = item.get("geo_id")
            geo_name_val = item.get("geo_name")

            records.append({
                "indicator_id": int(indicator_id),
                "name": str(raw_name),
                "geo_id": int(geo_id_val) if geo_id_val is not None else 0,
                "geo_name": str(geo_name_val) if geo_name_val else "Unknown",
                "value": float(raw_val),
                "datetime": item.get("datetime"),
            })

        if not records:
            print(f"⚠️ [API WARNING] No data returned for ID {indicator_id} in this time range.")
            return pd.DataFrame()

        df_indicator = pd.DataFrame(records)
        df_indicator["datetime"] = pd.to_datetime(df_indicator["datetime"], utc=True)
        return df_indicator

    except requests.exceptions.RequestException as e:
        print(f"❌ [API ERROR] Failed to fetch indicator ID {indicator_id}: {e}")
        return pd.DataFrame()


def get_energy_data(
    selected_indicators: list[int], start_dt: datetime, end_dt: datetime
) -> pd.DataFrame:
    """Orchestrates local database retrieval and API fetching fallback per indicator.

    Args:
        selected_indicators (list[int]): List of indicator IDs to retrieve.
        start_dt (datetime): Start datetime of requested range.
        end_dt (datetime): End datetime of requested range.

    Returns:
        pd.DataFrame: DataFrame containing retrieved energy and price records.

    Raises:
        ValueError: If ESIOS_API_TOKEN is missing or no data could be loaded.
    """
    token = ESIOS_API_TOKEN
    if not token:
        raise ValueError("Critical Error: 'ESIOS_API_TOKEN' is missing in environment or settings.")

    madrid_tz = ZoneInfo("Europe/Madrid")
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=madrid_tz)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=madrid_tz)

    start_utc_iso = start_dt.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_utc_iso = end_dt.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Step 1: Pre-load existing cache for requested range
    df_cached = load_data_by_ids(selected_indicators, start_utc_iso, end_utc_iso)

    indicators_to_fetch = []
    for ind_id in selected_indicators:
        if _is_indicator_cached(df_cached, ind_id, start_dt, end_dt):
            translated = translate_indicator(ind_id)
            print(f"📦 Indicator '{translated}' (ID: {ind_id}) loaded from local cache.")
        else:
            indicators_to_fetch.append(ind_id)

    # Step 2: Fetch only missing indicators from e·sios API
    if indicators_to_fetch:
        fetched_frames = []
        for indicator_id in indicators_to_fetch:
            df_ind = _fetch_indicator_from_api(indicator_id, start_utc_iso, end_utc_iso, token)
            if not df_ind.empty:
                fetched_frames.append(df_ind)

        # Step 3: Persist newly fetched metrics to database
        if fetched_frames:
            combined_df = pd.concat(fetched_frames, ignore_index=True)
            save_dataframe(combined_df)

    # Step 4: Load complete consolidated dataset from database
    final_df = load_data_by_ids(selected_indicators, start_utc_iso, end_utc_iso)

    if final_df.empty:
        raise ValueError("No data could be retrieved for any of the selected metrics.")

    return final_df