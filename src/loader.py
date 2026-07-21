from datetime import datetime
import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import pandas as pd
import requests
from src.constants import ESIOS_INDICATORS
from src.database import load_demand_data, save_demand_dataframe

# Load environment variables from .env file
load_dotenv()

def fetch_and_combine_esios_data(selected_demands: list, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    """Fetches selected energy indicators from the e-sios API or SQLite database cache,
    and unifies them into a timezone-aware DataFrame ready for validation.

    Args:
        selected_demands (list): List of demand names chosen by the user.
        start_dt (datetime): Start boundary of the analysis period.
        end_dt (datetime): End boundary of the analysis period.

    Returns:
        pd.DataFrame: A unified, timezone-aware DataFrame ready for processing.

    Raises:
        ValueError: If the 'ESIOS_API_TOKEN' is missing from the environment variables,
                    or if no data could be retrieved for any of the selected types.
        RuntimeError: If the remote HTTP request to the e-sios gateway fails.
    """
    api_token = os.getenv("ESIOS_API_TOKEN")
    if not api_token:
        raise ValueError("Critical Error: 'ESIOS_API_TOKEN' missing in .env file.")

    # Assign Spain local timezone (Europe/Madrid) to prevent UTC offset shifts
    madrid_tz = ZoneInfo("Europe/Madrid")
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=madrid_tz)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=madrid_tz)

    # Convert datetimes to proper ISO 8601 strings carrying timezone offsets
    start_iso = start_dt.isoformat()
    end_iso = end_dt.isoformat()

    # Check if requested records already exist in SQLite
    df_cached = load_demand_data(selected_demands, start_iso, end_iso)

    # Check if all requested demand indicators are fully present in the returned cache
    cached_demands = df_cached["name"].unique() if not df_cached.empty else []
    missing_demands = [d for d in selected_demands if d not in cached_demands]

    if not df_cached.empty and not missing_demands:
        print("📦 Data successfully loaded from local SQLite database cache.")
        return df_cached

    # Retrieve missing demand series directly from e-sios
    demands_to_fetch = missing_demands if not df_cached.empty else selected_demands
    headers = {
        "Accept": "application/json; application/vnd.esios-api-v1+json",
        "Content-Type": "application/json",
        "x-api-key": api_token
    }
    params = {"start_date": start_iso, "end_date": end_iso}
    fetched_dataframes = []

    for demand_name in demands_to_fetch:
        indicator_id = ESIOS_INDICATORS.get(demand_name)
        if not indicator_id:
            print(f"⚠️ Warning: No API indicator ID configured for '{demand_name}'. Skipping.")
            continue

        # Miss: Request raw response from remote server gateway
        print(f"🌐 Fetching '{demand_name}' (ID: {indicator_id}) from e·sios API...")
        url = f"https://api.esios.ree.es/indicators/{indicator_id}"

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Defensive payload parsing supporting alternative root structures
            if isinstance(data, list) and len(data) > 0:
                indicator_data = data[0].get("indicator", {})
            else:
                indicator_data = data.get("indicator", {}) if isinstance(data, dict) else {}

            values = indicator_data.get("values", []) if isinstance(indicator_data, dict) else []

            records = []
            for item in values:
                # Direct structural alignment matching the strict pipeline firewall schema
                records.append({
                    "id": int(indicator_id),
                    "name": str(demand_name),
                    "geoname": str(item.get("geo_name", "Peninsula")),
                    "value": int(round(item.get("value", 0))),
                    "datetime": item.get("datetime")
                })

            if not records:
                print(f"⚠️ Warning: No data returned from API for '{demand_name}' in this range.")
                continue

            df_indicator = pd.DataFrame(records)

            # Normalize chronological series into dynamic Madrid mainland local time
            df_indicator["datetime"] = pd.to_datetime(df_indicator["datetime"], utc=True)
            df_indicator["datetime"] = df_indicator["datetime"].dt.tz_convert('Europe/Madrid')

            # Store freshly fetched records in SQLite
            save_demand_dataframe(df_indicator)
            fetched_dataframes.append(df_indicator)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch indicator {indicator_id} ({demand_name}): {e}")

    # Combine cached and newly fetched DataFrames if necessary
    all_dataframes = []
    if not df_cached.empty:
        all_dataframes.append(df_cached)

    if not all_dataframes:
        raise ValueError("No data could be retrieved for any of the selected demand types.")

    # Consolidate, deduplicate, and sort the final dataset
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=["name", "datetime"]).sort_values("datetime").reset_index(drop=True)

    return combined_df