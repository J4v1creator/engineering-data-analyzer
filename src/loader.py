from datetime import datetime
import os
from dotenv import load_dotenv
import pandas as pd
import requests
from src.constants import DEFAULT_RAW_DIR, RAW_FILE_PREFIX, ESIOS_INDICATORS, DEMAND_TRANSLATIONS

# Load environment variables from .env file
load_dotenv()

def generate_indicator_filepath(demand_name: str, start_dt: datetime, end_dt: datetime) -> str:
    """Generates a professional, unique filename for a specific indicator and date range.

    Args:
        demand_name (str): The name of the electricity demand type.
        start_dt (datetime): Start bound of the temporal range.
        end_dt (datetime): End bound of the temporal range.

    Returns:
        str: The full optimized destination file path for local caching.
    """
    # Translate the demand name to English using constants mapping (with fallback)
    english_name = DEMAND_TRANSLATIONS.get(demand_name, demand_name)
    safe_demand_name = english_name.lower().replace(" ", "_").replace("-", "_")

    # Format timestamps: include hours if the range is within the same day
    if start_dt.date() == end_dt.date():
        start_str = start_dt.strftime("%Y%m%d_%H%M")
        end_str = end_dt.strftime("%Y%m%d_%H%M")
    else:
        start_str = start_dt.strftime("%Y%m%d")
        end_str = end_dt.strftime("%Y%m%d")

    filename = f"{RAW_FILE_PREFIX}_{safe_demand_name}_{start_str}_to_{end_str}.csv"
    return os.path.join(DEFAULT_RAW_DIR, filename)

def fetch_and_combine_esios_data(selected_demands: list, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    """Fetches selected energy indicators from the e-sios API, handles local caching,
    and unifies them into a structural schema matching EXPECTED_COLUMNS.

    Args:
        selected_demands (list): List of demand names chosen by the user.
        start_dt (datetime): Start boundary of the analysis period.
        end_dt (datetime): End boundary of the analysis period.

    Returns:
        pd.DataFrame: A unified, timezone-aware DataFrame ready for validation.

    Raises:
        ValueError: If the 'ESIOS_API_TOKEN' is missing from the environment variables,
                    or if no data could be retrieved for any of the selected types.
        RuntimeError: If the remote HTTP request to the e-sios gateway fails or 
                    returns a bad status code.
    """
    api_token = os.getenv("ESIOS_API_TOKEN")
    if not api_token:
        raise ValueError("Critical Error: 'ESIOS_API_TOKEN' missing in .env file.")

    # The e-sios gateway enforces strict UTC ISO 8601 formatting for parameters
    start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    headers = {
        "Accept": "application/json; application/vnd.esios-api-v1+json",
        "Content-Type": "application/json",
        "x-api-key": api_token
    }
    params = {"start_date": start_iso, "end_date": end_iso}
    all_dataframes = []

    for demand_name in selected_demands:
        indicator_id = ESIOS_INDICATORS.get(demand_name)
        if not indicator_id:
            print(f"⚠️ Warning: No API indicator ID configured for '{demand_name}'. Skipping.")
            continue

        csv_path = generate_indicator_filepath(demand_name, start_dt, end_dt)

        # Hit: Load dataset from local cache storage layer if available
        if os.path.exists(csv_path):
            print(f"📦 Local cache found for '{demand_name}' at '{csv_path}'.")
            df_indicator = pd.read_csv(csv_path, sep=";")
            df_indicator["datetime"] = pd.to_datetime(df_indicator["datetime"])
            all_dataframes.append(df_indicator)
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

            # Persist response object to internal file storage to bypass API limits on future runs
            os.makedirs(DEFAULT_RAW_DIR, exist_ok=True)
            df_indicator.to_csv(csv_path, sep=";", index=False)

            all_dataframes.append(df_indicator)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch indicator {indicator_id} ({demand_name}): {e}")

    if not all_dataframes:
        raise ValueError("No data could be retrieved for any of the selected demand types.")

    # Consolidate all standalone series into a clean, unified structure
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    return combined_df