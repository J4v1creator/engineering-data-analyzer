"""ESIOS API HTTP gateway, regional data fetching, and intelligent caching orchestration."""

from datetime import datetime
import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
import pandas as pd
import requests

from src.database import load_data_by_ids, save_dataframe
from src.utils import translate_indicator

# Load environment variables from .env file
load_dotenv()


def _is_cache_complete(df_cached: pd.DataFrame, selected_indicators: list[int], start_dt: datetime, end_dt: datetime) -> bool:
    """Evaluates whether the local database cache fully covers requested metrics and temporal range.

    Args:
        df_cached (pd.DataFrame): DataFrame containing cached records.
        selected_indicators (list[int]): List of indicator IDs to verify.
        start_dt (datetime): Start datetime of requested range.
        end_dt (datetime): End datetime of requested range.

    Returns:
        bool: True if all selected indicators are present and fully cover the time range.
    """
    if df_cached.empty:
        return False

    if "indicator_id" not in df_cached.columns:
        return False

    cached_ids = set(df_cached["indicator_id"].unique())
    if not set(selected_indicators).issubset(cached_ids):
        return False

    # Verify temporal coverage for each individual indicator
    for indicator_id in selected_indicators:
        df_ind = df_cached[df_cached["indicator_id"] == indicator_id]
        if df_ind.empty:
            return False

        min_cached = df_ind["datetime"].min()
        max_cached = df_ind["datetime"].max()

        if min_cached > start_dt or max_cached < end_dt:
            return False

    return True


def _fetch_indicator_from_api(indicator_id: int, start_iso: str, end_iso: str, api_token: str) -> pd.DataFrame:
    """Issues an HTTP request to e·sios API for a single indicator and parses response records.

    Args:
        indicator_id (int): ID of the indicator to fetch.
        start_iso (str): Start datetime in ISO string format.
        end_iso (str): End datetime in ISO string format.
        api_token (str): API authentication token.

    Returns:
        pd.DataFrame: DataFrame containing fetched indicator records.

    Raises:
        RuntimeError: If the API HTTP request fails.
    """
    headers = {
        "Accept": "application/json; application/vnd.esios-api-v1+json",
        "Content-Type": "application/json",
        "x-api-key": api_token,
    }

    params = {"start_date": start_iso, "end_date": end_iso}
    url = f"https://api.esios.ree.es/indicators/{indicator_id}"

    translated_name = translate_indicator(indicator_id=indicator_id)
    print(f"📥 Fetching '{translated_name}' (ID: {indicator_id}) from e·sios API...")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Support dictionary structures returned by ESIOS API
        if isinstance(data, list) and len(data) > 0:
            indicator_data = data[0].get("indicator", {})
        else:
            indicator_data = data.get("indicator", {}) if isinstance(data, dict) else {}

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
                "name": translated_name,
                "geo_id": int(geo_id_val) if geo_id_val is not None else 0,
                "geo_name": str(geo_name_val) if geo_name_val else "Unknown",
                "value": float(raw_val),
                "datetime": item.get("datetime"),
            })

        if not records:
            print(f"⚠️ Warning: No data returned from API for ID {indicator_id} in this time range.")
            return pd.DataFrame()

        df_indicator = pd.DataFrame(records)

        # Standardize timezone alignment to Europe/Madrid
        df_indicator["datetime"] = pd.to_datetime(df_indicator["datetime"], utc=True)
        df_indicator["datetime"] = df_indicator["datetime"].dt.tz_convert("Europe/Madrid")

        return df_indicator

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch indicator ID {indicator_id} from e·sios API: {e}")


def get_energy_data(selected_indicators: list[int], start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    """Orchestrates local database retrieval and API fetching fallback for energy metrics.

    Args:
        selected_indicators (list[int]): List of indicator IDs to retrieve.
        start_dt (datetime): Start datetime of requested range.
        end_dt (datetime): End datetime of requested range.

    Returns:
        pd.DataFrame: DataFrame containing retrieved energy and price records.

    Raises:
        ValueError: If ESIOS_API_TOKEN is missing or no data could be loaded.
    """
    api_token = os.getenv("ESIOS_API_TOKEN")
    if not api_token:
        raise ValueError("Critical Error: 'ESIOS_API_TOKEN' is missing in environment or .env file.")

    # Assign default local timezone (Europe/Madrid)
    madrid_tz = ZoneInfo("Europe/Madrid")
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=madrid_tz)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=madrid_tz)

    start_iso = start_dt.isoformat()
    end_iso = end_dt.isoformat()

    # Step 1: Query local SQLite cache
    df_cached = load_data_by_ids(selected_indicators, start_iso, end_iso)

    if _is_cache_complete(df_cached, selected_indicators, start_dt, end_dt):
        print("📦 Data successfully loaded from local SQLite database cache.")
        return df_cached

    print("🌐 Local cache incomplete or missing hours. Requesting range from e·sios API...")

    # Step 2: Fetch missing data from API
    fetched_frames = []
    for indicator_id in selected_indicators:
        df_ind = _fetch_indicator_from_api(indicator_id, start_iso, end_iso, api_token)
        if not df_ind.empty:
            fetched_frames.append(df_ind)

    # Step 3: Persist fetched data to SQLite cache
    if fetched_frames:
        combined_fetched_df = pd.concat(fetched_frames, ignore_index=True)
        save_dataframe(combined_fetched_df)

    # Step 4: Reload consolidated dataset from DB
    final_df = load_data_by_ids(selected_indicators, start_iso, end_iso)

    if final_df.empty:
        raise ValueError("No data could be retrieved for any of the selected metrics.")

    return final_df