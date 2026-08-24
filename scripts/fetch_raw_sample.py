import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import requests
from dotenv import load_dotenv

# Add project root directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.utils import translate_indicator

# Load environment variables
load_dotenv()

# Sample Indicator ID (e.g., 600 = PVPC, 1001 = Real Demand Peninsula)
DEFAULT_INDICATOR_ID = 600


def fetch_raw_sample(indicator_id: int = DEFAULT_INDICATOR_ID) -> None:
    """Fetches a raw JSON payload from the e·sios API for a specific indicator 
    and saves it to data/raw/ for API inspection.

    Args:
        indicator_id (int): ESIOS indicator ID to query. Defaults to 600 (PVPC).
    """
    api_token = os.getenv("ESIOS_API_TOKEN")
    if not api_token:
        print("❌ Critical Error: 'ESIOS_API_TOKEN' is missing in .env file.")
        return

    # Request the last 24 hours of data
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=1)

    headers = {
        "Accept": "application/json; application/vnd.esios-api-v1+json",
        "Content-Type": "application/json",
        "x-api-key": api_token,
    }

    params = {
        "start_date": start_dt.isoformat(),
        "end_date": end_dt.isoformat(),
    }
    url = f"https://api.esios.ree.es/indicators/{indicator_id}"

    translated_name = translate_indicator(indicator_id=indicator_id)
    print(f"📡 Requesting raw JSON payload for '{translated_name}' (ID: {indicator_id})...")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Define directory data/raw/
        raw_dir = PROJECT_ROOT / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = raw_dir / f"raw_sample_indicator_{indicator_id}_{timestamp_str}.json"

        # Save formatted JSON payload to disk
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"✅ Raw JSON payload successfully saved to:\n   {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch raw API sample: {e}")


if __name__ == "__main__":
    # Allow passing an optional indicator ID via CLI argument (e.g., python -m scripts.fetch_raw_sample 1001)
    target_id = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else DEFAULT_INDICATOR_ID
    fetch_raw_sample(indicator_id=target_id)