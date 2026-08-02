# Engineering Data Analyzer

## Overview
**Engineering Data Analyzer** is a production-ready, modular Python pipeline designed to automate the ingestion, validation, analytical processing, and visualization of real-world energy datasets.

Specifically tailored to interface directly with the **Red Eléctrica de España (REE) e·sios API**, the system fetches real-time and historical time-series measurements for both **energy demand ($MW$)** and **energy market prices ($€/MWh$)** across various geographical regions (Peninsular Spain, Canary Islands, Balearic Islands, Ceuta, Melilla, Portugal, France, etc.). The pipeline converts raw HTTP responses into structured DataFrames, and generates high-resolution statistical reports and multi-line visualizations. The entire architecture enforces strict industry software practices, including static typing (`type hinting`), robust exception handling, dynamic local SQLite database caching, unit testing coverage (`pytest`), and full segregation of business logic from the user interface.

## 🛠️ Key Features
* 🌐 **Direct e·sios API Gateway (`esios_client.py`):** Automated REST API requests to Red Eléctrica's servers with token-based authentication (`x-api-key`), custom date range parameters, pagination for regional indicators, and JSON payload parsing.
* 🗄️ **SQLite Persistence Layer (`database.py`):** High-performance local caching (`data/esios_cache.db`) that eliminates redundant network requests and stores time-series historical data efficiently.
* 📦 **Smart Cache Expiration (`cleaner.py`):** Maintenance engine that periodically cleans expired database entries based on configurable Time-to-Live (TTL) policies.
* 🛡️ **Data Quality Firewall (`validator.py`):** Strict pre- and post-validation system checking for expected schemas, correct technical datatypes, null value elimination, and duplicate row prevention.
* 🎛️ **Interactive Console Interface (`cli.py`):** Dynamic CLI menus allowing users to easily define temporal scope,isolate specific demand and price categories (e.g., Spot Market, PVPC), or trigger comparative multi-selections via index processing.
* 🧠 **Advanced Analytics & Cross-Modeling (`analyzer.py`):** Specialized mathematical metrics separated by indicator type:
    * **Demand Analytics:** Mean, median, standard deviation, peak load times, and dynamic cross-model evaluation measuring Mean Absolute Percentage Error (MAPE) and Pearson Correlation ($r$).
    * **Market Price Analytics:** Maximum/minimum price detection, time-stamped peak/valley tracking, market price spreads ($Price_{max} - Price_{min}$), and zero/low-price hour tracking ($\le 5.0$ €/MWh).
* ⚠️ **Statistical Anomaly Detection:** Automated screening for abnormal demand spikes or drops using a configurable Z-Score methodology ($> 2.0$ standard deviations).
* 📉 **High-Resolution Visualizations (`visualizer.py`):** Automated generation of independent, publication-quality multi-line charts saved directly as high-DPI artifacts in `outputs/` for both energy demand and regional price series.
* 📄 **Automated Reporting System (`report.py`):** Dynamic file writer compiling full execution metadata, specialized price/demand statistics, regional breakdowns, and delta error modeling into structured plain-text reports in `outputs/`.
* 🧪 **Automated Testing Suite (`tests/`):** Robust test suite executed with `pytest` ensuring dataset schema validation integrity and core function compliance.

## 📁 Project Architecture
The codebase implements a clean, modular package hierarchy following the single-responsibility principle:

```text
engineering-data-analyzer/
│
├── config/
│   └── settings.py           # Centralized configuration, dynamic pathlib resolution, and constants
│
├── data/                     # Isolated database storage
│   └── esios_cache.db        # Local SQLite cache database (Untracked)
│
├── outputs/                  # Isolated pipeline exports (Generated charts and reports)
│
├── src/                      # Package source root
│   ├── __init__.py           # Package initialization marker
│   ├── analyzer.py           # Core mathematics, price spread evaluation, and Z-Score anomaly modeling
│   ├── cleaner.py            # Cache maintenance engine and expired DB entry cleaner
│   ├── cli.py                # Interactive command-line interface mechanics
│   ├── database.py           # SQLite database connection managers and queries
│   ├── esios_client.py       # ESIOS API HTTP gateway regional and data loading logic
│   ├── report.py             # Automated text report rendering engine for demand and prices
│   ├── validator.py          # Structural verification and timezone-aware datatype firewall
│   └── visualizer.py         # Matplotlib rendering and charting engine with geographic region mapping
│
├── tests/                    # Automated unit testing suite
│   ├── __init__.py           # Test package initialization marker
│   └── test_validator.py     # Test cases for data quality firewall and schema checks
│
├── .env                      # Environment variables (API Token - Untracked)
├── .env.example              # Example template for environment variables (Tracked)
├── .gitignore                # Specifies intentionally untracked files to ignore
├── main.py                   # Central execution entry point
├── README.md                 # Project documentation
└── requirements.txt          # List of external Python dependencies
```

## 📊 Dataset Specifications
* **Source:** Red Eléctrica de España (REE) - Official e·sios API.
* **Metrics:**
    * Real-time, programmed, and scheduled energy demand measured in Megawatts ($MW$).
    * **Energy Prices:** Daily Spot Market Price and PVPC Retail Rates measured in Euros per Megawatt-hour ($€/MWh$).
* **Geographic Coverage:** Peninsular Spain, Canary Islands, Balearic Islands, Ceuta, Melilla, and interconnected European markets (Portugal, France, Germany, Belgium, Netherlands).
* **Time Resolution:** Continuous 5-minute to hourly intervals.
* **Timezone Handling:** UTC ISO 8601 network requests automatically normalized to Peninsular Spanish local time (Europe/Madrid).
* **Licensing:** Open Data (Subject to ESIOS/REE API terms of use and token registration).

## 🚀 Quick Start & Execution
### Prerequisites
* Python 3.10 or higher.
* An active e·sios API Token (requested free of charge at e·sios portal).

### Environment Setup
1. Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```
2. Create a `.env` file in the root directory following `.env.example`:
```python
ESIOS_API_TOKEN=your_personal_api_token_here
```

### Running Tests
To verify that the validation pipeline passes all unit tests, run:
```bash
pytest
```

### Execution
To initiate the main pipeline, execute the orchestrator script from your terminal:
```bash
python main.py
```

### Pipeline Workflow
1. **System Initialization & Cache Maintenance (`cleaner.py` / `database.py`):** Ensures SQLite tables exist and automatically removes obsolete database entries exceeding the TTL threshold.
2. **Temporal & Demand Filtering (`cli.py`):** Prompts the user via CLI for a date/time window, energy demand categories, and market price indicators.
3. **Extraction & Cache Lookup (`esios_client.py`):** Fetches dataset from local SQLite cache if present; otherwise, issues authenticated HTTP requests to the e·sios API and stores the results.
4. **Validation (`validator.py`):** Enforces column schema checks (`id`, `name`, `geo_id`,`geo_name`, `value`, `datetime`), null checks, and timezone consistency.
5. **Cross-Analysis & Anomalies (`analyzer.py`):** Computes dedicated demand metrics, price volatility statistics (spreads and low-price hours), pairwise model evaluations (MAPE, Pearson correlation), and regional Z-score calculations.
6. **Output Generation:** Displays anomaly summaries on the terminal, exporting independent demand and price plots (`plot_energy_demand_[TIMESTAMP].png`, `plot_energy_prices_[TIMESTAMP].png`) and the analytical document (`report_energy_demand_[TIMESTAMP].txt`) directly into `outputs/`.