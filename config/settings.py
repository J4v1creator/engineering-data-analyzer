from pathlib import Path

# Base storage directory paths (resolved dynamically relative to project root)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_OUTPUT_DIR = str(BASE_DIR / "outputs")
DEFAULT_DB_PATH = str(DATA_DIR / "esios_cache.db")

# Ensure required storage directories exist at application runtime
DATA_DIR.mkdir(parents=True, exist_ok=True)
Path(DEFAULT_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# Analysis configuration
DEFAULT_ANOMALY_THRESHOLD = 2.0

# Cache expiration limit in days
CACHE_EXPIRATION_DAYS = 7

# Expected data schema for strict type validation
EXPECTED_COLUMNS = {
    "id": "int64",
    "name": "object",
    "geoname": "object",
    "value": "int64",
    "datetime": "datetime64[ns, pytz.FixedOffset(120)]"  # REE standard timezone offset (+02:00)
}

# E·sios API Indicators Mapping
ESIOS_INDICATORS = {
    "Demanda real": 1293,
    "Demanda prevista": 544,
    "Demanda programada": 545,
    "Demanda Programada Total Peninsular": 1941,
    "Término de facturación de energía activa del PVPC 2.0TD": 1001,
    "Precio mercado SPOT Diario": 600
}

# Translation mapping for Red Eléctrica de España (REE) demand names
DEMAND_TRANSLATIONS = {
    "Demanda real": "Real-Time Demand",
    "Demanda prevista": "Expected Demand",
    "Demanda programada": "Scheduled Demand",
    "Demanda Programada Total Peninsular": "Total Scheduled Demand"
}

# Translation mapping for Red Eléctrica de España (REE) price names
PRICE_TRANSLATIONS = {
    "Término de facturación de energía activa del PVPC 2.0TD": "PVPC Retail Electricity Price",
    "Precio mercado SPOT Diario": "Daily Spot Market Price"
}

# UI/UX Plotting configurations
DEMAND_COLOR_PALETTE = {
    "Demanda real": {"color": "#1f77b4"},
    "Demanda prevista": {"color": "#ff7f0e"},
    "Demanda programada": {"color": "#2ca02c"},
    "Demanda Programada Total Peninsular": {"color": "#d62728"},
    "default": {"color": "#7f7f7f"}
}

PRICE_COLOR_PALETTE = {
    "Término de facturación de energía activa del PVPC 2.0TD": {"color": "#9467bd"},
    "Precio mercado SPOT Diario": {"color": "#8c564b"},
    "default": {"color": "#7f7f7f"}
}