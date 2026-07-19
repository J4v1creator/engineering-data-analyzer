"""Global constants and configuration mappings for the energy pipeline."""

# File system paths
DEFAULT_RAW_DIR = "data/raw"
DEFAULT_PROCESSED_DIR = "data/processed"

# Prefix to identify API files
RAW_FILE_PREFIX = "esios_demand"

# Analysis configuration
DEFAULT_ANOMALY_THRESHOLD = 2.0

# Cache expiration in days for API data
CACHE_EXPIRATION_DAYS = 7

# Expected schema for strict type checking
EXPECTED_COLUMNS = {
    "id": "int64",
    "name": "object",
    "geoname": "object",
    "value": "int64",
    "datetime": "datetime64[ns, pytz.FixedOffset(120)]"  # Matches +02:00 timezone
}

# E·sios API Indicators Mapping
ESIOS_INDICATORS = {
    "Demanda real": 1293,
    "Demanda prevista": 544,
    "Demanda programada": 545,
    "Demanda Programada Total Peninsular": 1941
}

# Translation mapping for Red Eléctrica de España (REE) demand names
DEMAND_TRANSLATIONS = {
    "Demanda real": "Real-Time Demand",
    "Demanda prevista": "Expected Demand",
    "Demanda programada": "Scheduled Demand",
    "Demanda Programada Total Peninsular": "Total Peninsular Scheduled Demand"
}

# UI/UX Plotting configurations
DEMAND_COLOR_PALETTE = {
    "Demanda real": {"color": "#1f77b4"},
    "Demanda prevista": {"color": "#ff7f0e"},
    "Demanda programada": {"color": "#2ca02c"},
    "Demanda Programada Total Peninsular": {"color": "#d62728"},
    "default": {"color": "#7f7f7f"},
}