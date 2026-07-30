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
    "geo_id": "int64",
    "geo_name": "object",
    "value": "float64",
    "datetime": "datetime64[ns, Europe/Madrid]",
}

# E·sios API Indicators Mapping
ESIOS_INDICATORS = {
    "Demanda real": 1293,
    "Demanda prevista": 544,
    "Demanda programada": 545,
    "Demanda Programada Total Peninsular": 1941,
    "Término de facturación de energía activa del PVPC 2.0TD": 1001,
    "Precio mercado SPOT Diario": 600,
}

# Recognized geographic region identifiers for ESIOS API datasets
GEOGRAPHY_MAPPINGS = {
    1: "Portugal",
    2: "Francia",
    3: "España",
    8741: "Península",
    8742: "Canarias",
    8743: "Baleares",
    8744: "Ceuta",
    8745: "Melilla",
    8826: "Alemania",
    8827: "Bélgica",
    8828: "Países Bajos",
}

# Translation mapping for Red Eléctrica de España (REE) demand names
DEMAND_TRANSLATIONS = {
    "Demanda real": "Real Demand",
    "Demanda prevista": "Expected Demand",
    "Demanda programada": "Scheduled Demand",
    "Demanda Programada Total Peninsular": "Total Scheduled Demand",
}

# Translation mapping for Red Eléctrica de España (REE) price names
PRICE_TRANSLATIONS = {
    "Término de facturación de energía activa del PVPC 2.0TD": "PVPC Retail Energy Price",
    "Precio mercado SPOT Diario": "Spot Market Price",
}

# Translation mapping for geographic region names
GEOGRAPHY_TRANSLATIONS = {
    "Portugal": "Portugal",
    "Francia": "France",
    "España": "Spain",
    "Península": "Peninsula",
    "Canarias": "Canary Islands",
    "Baleares": "Balearic Islands",
    "Ceuta": "Ceuta",
    "Melilla": "Melilla",
    "Alemania": "Germany",
    "Bélgica": "Belgium",
    "Países Bajos": "Netherlands",
}

# UI/UX Plotting configurations
DEMAND_COLOR_PALETTE = {
    "Demanda real": "#1f77b4",
    "Demanda prevista": "#ff7f0e",
    "Demanda programada": "#2ca02c",
    "Demanda Programada Total Peninsular": "#d62728",
    "default": "#7f7f7f",
}

# Geographic region color palette for multi-region plots (e.g., Spot Market Prices)
GEO_COLOR_PALETTE = {
    # --- Spot Market Price ---
    "Portugal": "#1f77b4",
    "Francia": "#ff7f0e",
    "España": "#2ca02c",
    "Alemania": "#d62728",
    "Bélgica": "#9467bd",
    "Países Bajos": "#17becf",

    # --- PVPC Retail Energy Price ---
    "Península": "#0e4d64",
    "Canarias": "#e377c2",
    "Baleares": "#bcbd22",
    "Ceuta": "#8c564b",
    "Melilla": "#ffbb78",

    # --- Fallback ---
    "default": "#7f7f7f",
}