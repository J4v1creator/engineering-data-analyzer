from datetime import datetime
import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import pandas as pd
import requests
from config.settings import ESIOS_INDICATORS
from src.database import load_demand_data, save_demand_dataframe

# Load environment variables from .env file
load_dotenv()

def _is_cache_complete(df_cached: pd.DataFrame, selected_indicators: list[str], start_dt: datetime, end_dt: datetime) -> bool:
    """Evaluates whether the local database cache fully covers the requested metrics and temporal range.

    Args:
        df_cached (pd.DataFrame): DataFrame containing cached records.
        selected_indicators (list[str]): List of demand names to check.
        start_dt (datetime): Start datetime of the requested range.
        end_dt (datetime): End datetime of the requested range.

    Returns:
        bool: True if the cache is complete, False otherwise.
    """
    if df_cached.empty:
        return False

    cached_indicators = set(df_cached["name"].unique())
    all_present = set(selected_indicators).issubset(cached_indicators)

    # Ensure min and max timestamps in SQLite fully cover the requested period
    min_cached = df_cached["datetime"].min()
    max_cached = df_cached["datetime"].max()

    starts_covered = min_cached <= start_dt
    ends_covered = max_cached >= end_dt

    return all_present and starts_covered and ends_covered

def _fetch_indicator_from_api(indicator_name: str, start_iso: str, end_iso: str, api_token: str) -> pd.DataFrame:
    """Issues an HTTP request to e·sios API for a single indicator and parses response records.

    Args:
        indicator_name (str): Name of the demand indicator to fetch.
        start_iso (str): Start datetime in ISO format.
        end_iso (str): End datetime in ISO format.
        api_token (str): API token for authentication.

    Returns:
        pd.DataFrame: DataFrame containing the fetched indicator data.

    Raises:
        RuntimeError: If the API request fails or returns an error.
    """
    indicator_id = ESIOS_INDICATORS.get(indicator_name)
    if not indicator_id:
        print(f"⚠️ Warning: No API indicator ID configured for '{indicator_name}'. Skipping.")
        return pd.DataFrame()

    headers = {
        "Accept": "application/json; application/vnd.esios-api-v1+json",
        "Content-Type": "application/json",
        "x-api-key": api_token,
    }

    # Miss: Request raw response from remote server gateway
    params = {"start_date": start_iso, "end_date": end_iso}
    url = f"https://api.esios.ree.es/indicators/{indicator_id}"

    print(f"📥 Fetching '{indicator_name}' (ID: {indicator_id}) from e·sios API...")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Support nested dictionary structures
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

            # Preserves decimals for prices (float) and numeric precision for demand
            records.append({
                "id": int(indicator_id),
                "name": str(indicator_name),
                "geoname": str(item.get("geo_name", "Peninsula")),
                "value": float(raw_val),
                "datetime": item.get("datetime"),
            })

        if not records:
            print(f"⚠️ Warning: No data returned from API for '{indicator_name}' in this range.")
            return pd.DataFrame()

        df_indicator = pd.DataFrame(records)

        # Standardize timezone alignment to Europe/Madrid
        df_indicator["datetime"] = pd.to_datetime(df_indicator["datetime"], utc=True)
        df_indicator["datetime"] = df_indicator["datetime"].dt.tz_convert("Europe/Madrid")

        return df_indicator

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch indicator {indicator_id} ({indicator_name}): {e}")

def get_energy_data(selected_indicators: list[str], start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    """Orchestrates local database retrieval and API fetching fallback for energy metrics.

    Args:
        selected_indicators (list[str]): List of demand names to retrieve.
        start_dt (datetime): Start datetime of the requested range.
        end_dt (datetime): End datetime of the requested range.

    Returns:
        pd.DataFrame: DataFrame containing the retrieved energy data.

    Raises:
        ValueError: If no data could be retrieved for any of the selected metrics.
    """
    api_token = os.getenv("ESIOS_API_TOKEN")
    if not api_token:
        raise ValueError("Critical Error: 'ESIOS_API_TOKEN' missing in .env file.")

    # Assign local Spanish timezone (Europe/Madrid)
    madrid_tz = ZoneInfo("Europe/Madrid")
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=madrid_tz)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=madrid_tz)

    start_iso = start_dt.isoformat()
    end_iso = end_dt.isoformat()

    # Query local SQLite database
    df_cached = load_demand_data(selected_indicators, start_iso, end_iso)

    if _is_cache_complete(df_cached, selected_indicators, start_dt, end_dt):
        print("📦 Data successfully loaded from local SQLite database cache.")
        return df_cached

    print("🌐 Local cache incomplete or missing hours. Requesting full range from e·sios API...")

    fetched_frames = []
    for indicator_name in selected_indicators:
        df_ind = _fetch_indicator_from_api(indicator_name, start_iso, end_iso, api_token)
        if not df_ind.empty:
            fetched_frames.append(df_ind)

    # Persist freshly fetched remote data into SQLite cache
    if fetched_frames:
        combined_fetched_df = pd.concat(fetched_frames, ignore_index=True)
        save_demand_dataframe(combined_fetched_df)

    # Consolidated load from DB to guarantee schema normalization
    final_df = load_demand_data(selected_indicators, start_iso, end_iso)

    if final_df.empty:
        raise ValueError("No data could be retrieved for any of the selected metrics.")

    return final_df