import os
from datetime import datetime
import pandas as pd
import requests
from dotenv import load_dotenv
from src.constants import DEFAULT_RAW_DIR, RAW_FILE_PREFIX, ESIOS_INDICATORS

def load_csv_data(file_path: str) -> pd.DataFrame:
    """Loads an energy dataset from a CSV file into a Pandas DataFrame.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: The loaded dataset.
        
    Raises:
        FileNotFoundError: If the file does not exist at the specified path.
        ValueError: If the file is empty or has parsing issues.
        RuntimeError: If an unexpected error occurs while reading the file.
    """
    print(f"📂 Attempting to load data from: {file_path}")

    # Pre-validation: Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file does not exist at the specified path: '{file_path}'")
    
    try:
        # Read CSV tailored to REE data structure (semi-colon separated)
        df = pd.read_csv(file_path, sep=";", parse_dates=["datetime"])

        # Post-validation: Check if the DataFrame is empty
        if df.empty:
            raise ValueError(f"The file '{file_path}' is empty.")

        print(f"✅ Successfully loaded {len(df)} rows.")
        return df
    
    except pd.errors.ParserError as e:
        raise ValueError(f"Formatting error while parsing CSV. Check delimiters: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred while reading the file: {e}")

# Load environment variables from .env file
load_dotenv()

def generate_indicator_filepath(demand_name: str, start_dt: datetime, end_dt: datetime) -> str:
    """Generates a professional, unique filename for a specific indicator and date range."""
    # Create a safe filename string by replacing spaces
    safe_demand_name = demand_name.lower().replace(" ", "_")
    start_str = start_dt.strftime("%Y%m%d")
    end_str = end_dt.strftime("%Y%m%d")

    filename = f"{RAW_FILE_PREFIX}_{safe_demand_name}_{start_str}_to_{end_str}.csv"
    return os.path.join(DEFAULT_RAW_DIR, filename)

def fetch_and_combine_esios_data(selected_demands: list, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    """Fetches selected energy indicators from e-sios API, handles caching, and combines them.

    Args:
        selected_demands (list): List of demand names selected by the user.
        start_dt (datetime): Start of the analysis period.
        end_dt (datetime): End of the analysis period.

    Returns:
        pd.DataFrame: A unified DataFrame containing all requested demand data.

    Raises:
        ValueError: If the API token is missing or no data could be retrieved.
        RuntimeError: If an HTTP or connection error occurs during the API request.
    """
    # Validate API authentication credentials
    api_token = os.getenv("ESIOS_API_TOKEN")
    if not api_token:
        raise ValueError("Critical Error: 'ESIOS_API_TOKEN' missing in .env file.")

    # Convert datetime parameters to ISO 8601 strings required by e-sios
    start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Configure API request headers and parameters
    headers = {
        "Accept": "application/json; application/vnd.esios-api-v1+json",
        "Content-Type": "application/json",
        "Authorization": f'Token token="{api_token}"'
    }
    params = {"start_date": start_iso, "end_date": end_iso}
    all_dataframes = []

    # Process each requested indicator sequentially
    for demand_name in selected_demands:
        indicator_id = ESIOS_INDICATORS.get(demand_name)
        if not indicator_id:
            print(f"⚠️ Warning: No API indicator ID configured for '{demand_name}'. Skipping.")
            continue

        csv_path = generate_indicator_filepath(demand_name, start_dt, end_dt)

        # Hit: Load data from local cache if available
        if os.path.exists(csv_path):
            print(f"📦 Local cache found for '{demand_name}' at '{csv_path}'.")
            df_indicator = pd.read_csv(csv_path, sep=";")
            all_dataframes.append(df_indicator)
            continue

        # Miss: Request data from remote API
        print(f"🌐 Fetching '{demand_name}' (ID: {indicator_id}) from e·sios API...")
        url = f"https://api.esios.ree.es/indicators/{indicator_id}"

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Parse payload response values
            records = []
            values = data.get("indicator", {}).get("values", [])
            
            for item in values:
                records.append({
                    "datetime": item.get("datetime"),
                    "value": item.get("value"),
                    "name": demand_name  # Maintain consistency with the pipeline's expected text labels
                })

            if not records:
                print(f"⚠️ Warning: No data returned from API for '{demand_name}' in this range.")
                continue

            # Persist response to local cache storage
            df_indicator = pd.DataFrame(records)
            os.makedirs(DEFAULT_RAW_DIR, exist_ok=True)
            df_indicator.to_csv(csv_path, sep=";", index=False)
            
            all_dataframes.append(df_indicator)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch indicator {indicator_id} ({demand_name}): {e}")

    # Validate that at least one dataset was successfully built
    if not all_dataframes:
        raise ValueError("No data could be retrieved for any of the selected demand types.")

    # Consolidate all individual datasets into a single cohesive DataFrame
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    return combined_df