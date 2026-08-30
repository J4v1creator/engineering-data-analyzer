"""Centralized configuration, dynamic pathlib resolution, and constants."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file at root level
load_dotenv()

# --- API & Authentication ---
ESIOS_API_TOKEN = os.getenv("ESIOS_API_TOKEN", "")

# --- Base Storage Directories ---
# Resolved dynamically relative to the project root
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
DEFAULT_DB_PATH = DATA_DIR / "esios_cache.db"

# Subdirectories for generated artifacts
EXPORTS_OUTPUT_DIR = OUTPUT_DIR / "exports"
PLOTS_OUTPUT_DIR = OUTPUT_DIR / "plots"
REPORTS_OUTPUT_DIR = OUTPUT_DIR / "reports"

# Output routes within outputs/plots
PLOTS_HTML_DIR = PLOTS_OUTPUT_DIR / "interactive"
PLOTS_STATIC_DIR = PLOTS_OUTPUT_DIR / "static"

# Ensure all required storage and output subdirectories exist on startup
ALL_DIRECTORIES = [
    DATA_DIR,
    OUTPUT_DIR,
    EXPORTS_OUTPUT_DIR,
    PLOTS_OUTPUT_DIR,
    PLOTS_HTML_DIR,
    PLOTS_STATIC_DIR,
    REPORTS_OUTPUT_DIR,
]

for directory in ALL_DIRECTORIES:
    directory.mkdir(parents=True, exist_ok=True)

# --- Analysis Parameters ---
DEFAULT_ANOMALY_THRESHOLD = 2.0  # Standard deviation threshold for Z-score
CACHE_EXPIRATION_DAYS = 7        # Cache retention period

# --- Data Validation Schema ---
EXPECTED_COLUMNS = {
    "indicator_id": "int64",
    "name": "object",
    "geo_id": "int64",
    "geo_name": "object",
    "value": "float64",
    "datetime": "datetime64[ns, Europe/Madrid]",
}

# --- Indicator Ordering & Priorities ---
# The order defined in these lists dictates display priority across UI, plots, and exports.
DEMAND_INDICATOR_IDS = [
    1293,  # Real Demand
    544,   # Expected Demand
    545,   # Scheduled Demand
    1941,  # Total Scheduled Demand
]

PRICE_INDICATOR_IDS = [
    600,   # Spot Market Price
    1001,  # PVPC Retail Energy Price
]

# --- Geographic Region Priority Ordering ---
# Controls the exact sequence of regions in plots, CLI output, and tables.

# Specific priority order for Spot Market Prices
SPOT_GEO_ORDER = [
    3,     # Spain
    1,     # Portugal
    2,     # France
    8826,  # Germany
    8827,  # Belgium
    8828,  # Netherlands
]

# Specific priority order for PVPC Retail Prices & Demands
PVPC_GEO_ORDER = [
    8741,  # Peninsula
    8743,  # Balearic Islands
    8742,  # Canary Islands
    8744,  # Ceuta
    8745,  # Melilla
]

# Global priority fallback list (unifies all regions for generic sorting)
GLOBAL_GEO_ORDER = SPOT_GEO_ORDER + PVPC_GEO_ORDER

# --- Translations (ESIOS Numerical IDs to English Standards) ---
INDICATOR_TRANSLATIONS = {
    1293: "Real Demand",
    544: "Expected Demand",
    545: "Scheduled Demand",
    1941: "Total Scheduled Demand",
    600: "Spot Market Price",
    1001: "PVPC Retail Energy Price",
}

GEOGRAPHY_TRANSLATIONS = {
    # Spot Market Regions
    1: "Portugal",
    2: "France",
    3: "Spain",
    8826: "Germany",
    8827: "Belgium",
    8828: "Netherlands",
    # PVPC Regions
    8741: "Peninsula",
    8742: "Canary Islands",
    8743: "Balearic Islands",
    8744: "Ceuta",
    8745: "Melilla",
}

# --- Visualizer / Plotting Styling Configurations ---
DEMAND_COLOR_PALETTE = {
    1293: "#1f77b4",  # Blue (Real)
    544: "#ff7f0e",   # Orange (Expected)
    545: "#2ca02c",   # Green (Scheduled)
    1941: "#d62728",  # Red (Total Scheduled)
    "default": "#7f7f7f",
}

# Line style mapping to differentiate Real Demand (solid) from Forecasts/Schedules (dashed)
DEMAND_LINE_STYLES = {
    1293: "-",   # Solid line
    544: "--",   # Dashed
    545: "--",   # Dashed
    1941: "-.",  # Dash-dot
    "default": "-",
}

GEO_COLOR_PALETTE = {
    # Spot Market
    1: "#1f77b4",     # Portugal
    2: "#ff7f0e",     # France
    3: "#2ca02c",     # Spain
    8826: "#d62728",  # Germany
    8827: "#9467bd",  # Belgium
    8828: "#17becf",  # Netherlands
    # PVPC Regions
    8741: "#0e4d64",  # Peninsula
    8742: "#e377c2",  # Canary Islands
    8743: "#bcbd22",  # Balearic Islands
    8744: "#8c564b",  # Ceuta
    8745: "#ffbb78",  # Melilla
    # Fallback
    "default": "#7f7f7f",
}

# --- Excel Export Styling Configurations ---
EXCEL_SECTION_GAP = 3

EXCEL_PRIMARY_FILL_COLOR = "1F4E78"    # Dark Blue for main section headers
EXCEL_SECONDARY_FILL_COLOR = "D9E1F2"  # Light Blue for table column headers
EXCEL_BORDER_COLOR = "D3D3D3"          # Soft light grey for cell borders

EXCEL_PRIMARY_SECTION_KEYWORDS = {
    "ANALYSIS METADATA & PERIOD",
    "MARKET ECONOMIC VOLUME SUMMARY",
    "KEY INDICATORS PERFORMANCE OVERVIEW",
    "DETAILED DEMAND STATISTICS (MW)",
    "DETAILED PRICE STATISTICS (€/MWh)",
    "PAIRWISE DEMAND MODEL COMPARISON",
    "DETECTED STATISTICAL ANOMALIES & OUTLIERS",
    "CLEAN & PROCESSED MARKET DATA",
}

# --- Pdf Export Styling Configurations ---
PDF_PAGE_SIZE = "A4"
PDF_MARGIN = 36  # Dots (approx. 0.5 inches)

# Color palette for PDF (Hexadecimal or RGB)
PDF_PRIMARY_COLOR = "#1F4E78"    # Dark blue for titles/headings
PDF_SECONDARY_COLOR = "#595959"  # Gray for subtitles and borders
PDF_BG_LIGHT_COLOR = "#F2F2F2"   # Light gray for alternating rows in tables

# Default dimensions for embedded graphics (in inches or points)
PDF_CHART_WIDTH = 500
PDF_CHART_HEIGHT = 250