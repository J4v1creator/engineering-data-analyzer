# Engineering Data Analyzer

## Overview
**Engineering Data Analyzer** is a production-ready, modular Python pipeline designed to automate the ingestion, validation, analytical processing, visualization, and multi-format export of real-world energy datasets.

Specifically tailored to interface directly with the **Red Eléctrica de España (REE) e·sios API**, the system fetches real-time and historical time-series measurements for both **energy demand ($MW$)** and **energy market prices ($€/MWh$)** across various geographical regions (Peninsular Spain, Canary Islands, Balearic Islands, Ceuta, Melilla, Portugal, France, etc.). The pipeline converts raw HTTP responses into structured DataFrames, generating high-resolution statistical text summaries, interactive Plotly visualizations, publication-ready multi-page PDF executive reports, and professionally styled Excel workbooks.

The system features both an **Interactive Command-Line Interface (`main.py` / `cli.py`)** and a modern, reactive **Streamlit Web Application (`app.py`)** for visual exploration. The entire architecture enforces strict software engineering practices, including static typing (`type hinting`), robust exception handling, dynamic local SQLite database caching, unit testing coverage (`pytest`), and full segregation of business logic from user interfaces.

## 🛠️ Key Features
* 🌐 **Direct e·sios API Gateway (`esios_client.py`):** Automated REST API requests to Red Eléctrica's servers with token-based authentication (`x-api-key`), custom date range parameters, pagination for regional indicators, and JSON payload parsing.
* 🖥️ **Interactive Streamlit Web Dashboard (`app.py`):** Full-featured web interface featuring sidebar date/indicator controls, key KPI metric cards, progressive statistical tables, dynamic model comparison settings, multi-tab layout, and direct file downloads.
* 🗄️ **SQLite Persistence Layer (`database.py`):** High-performance local caching (`data/esios_cache.db`) that eliminates redundant network requests and stores time-series historical data efficiently.
* 📦 **Smart Cache Expiration (`cleaner.py`):** Maintenance engine that periodically cleans expired database entries based on configurable Time-to-Live (TTL) policies.
* 🛡️ **Data Quality Firewall (`validator.py`):** Strict pre- and post-validation system checking for expected schemas, correct technical datatypes, null value elimination, and duplicate row prevention.
* 🎛️ **Interactive Console Interface (`cli.py`):** Dynamic CLI menus allowing terminal users to easily define temporal scope, isolate specific demand and price categories (e.g., Spot Market, PVPC), or trigger comparative multi-selections via index processing.
* 🧠 **Advanced Analytics & Cross-Modeling (`analyzer.py`):** Specialized mathematical metrics separated by indicator type:
    * **Demand Analytics:** Mean, median, standard deviation, peak load times, and dynamic cross-model evaluation measuring Mean Absolute Percentage Error (MAPE) and Pearson Correlation ($r$).
    * **Market Price Analytics:** Maximum/minimum price detection, time-stamped peak/valley tracking, market price spreads ($Price_{max} - Price_{min}$), and zero/low-price hour tracking ($\le 5.0$ €/MWh).
    * **Market Economic Volume:** Temporal alignment of 5-min real demand and 15-min SPOT prices into 1-hour resolution to calculate total traded market value ($M€$), Volume-Weighted Average Price (VWAP), and peak expenditure hours.
* ⚠️ **Statistical Anomaly Detection:** Automated screening for abnormal demand spikes or drops using a configurable Z-Score methodology ($> 2.0$ standard deviations).
* 📈 **Dual Interactive & Static Visualizations (`visualizer.py`):** Automated rendering engine powered by **Plotly** and **Kaleido**. Generates fully interactive HTML charts with dynamic tooltips/zooming alongside standalone, high-DPI PNG images saved in `outputs/plots/` for both demand and price time-series.
* 📄 **Automated Text Summary System (`text_reporter.py`):** Dynamic file writer compiling full execution metadata, specialized price/demand statistics, regional breakdowns, and delta error modeling into structured plain-text summaries saved in `outputs/reports/`.
* 📕 **Multi-Page PDF Executive Report Generator (`pdf_reporter.py`):** Advanced report engine leveraging ReportLab to compile cover pages, formatted statistical tables, anomaly breakdowns, and embedded static plot images into executive-grade PDF documents saved in `outputs/reports/`.
* 📊 **Multi-Tab Excel Workbook Exporter (`exporter.py`):** Automated export engine generating multi-tab Excel files (`.xlsx`) saved in `outputs/exports/` containing executive summaries, detailed demand/price statistics, pairwise model comparison metrics, detected anomalies, and structured raw data with dynamic cell styling and merged section headers.
* 🛠️ **Developer Utilities (`scripts/`):** Command-line utility scripts for development environment management, database resetting, and testing without altering core application logic.
* 🧪 **Automated Testing Suite (`tests/`):** Robust test suite executed with `pytest` ensuring dataset schema validation integrity and core function compliance.

## 📁 Project Architecture
The codebase implements a clean, modular package hierarchy following the single-responsibility principle:

```text
engineering-data-analyzer/
│
├── config/
│   └── settings.py           # Centralized configuration, dynamic pathlib resolution, and styling constants
│
├── data/                     # Isolated database storage
│   └── esios_cache.db        # Local SQLite cache database (Untracked)
│
├── outputs/                  # Organized pipeline artifacts directory
│   ├── exports/              # Multi-tab Excel workbooks (.xlsx)
│   ├── plots/                # Interactive web charts (.html) and static images (.png)
│   └── reports/              # PDF executive reports (.pdf) and text summaries (.txt)
│
├── scripts/                  # Developer CLI utilities and administration tools
│   ├── __init__.py           # Scripts package initialization marker
│   ├── fetch_raw_sample.py   # Utility to fetch and save unparsed raw API JSON payloads for inspection
│   ├── inspect_db.py         # Diagnostic utility to inspect cached indicators, timeframe, and record counts
│   └── reset_db.py           # Utility script to safely wipe local SQLite cache records
│
├── src/                      # Package source root
│   ├── __init__.py           # Package initialization marker
│   ├── analyzer.py           # Mathematics, price spread evaluation, market volume calculation, and Z-Score modeling
│   ├── cleaner.py            # Cache maintenance engine and expired DB entry cleaner
│   ├── cli.py                # Interactive command-line interface mechanics
│   ├── database.py           # SQLite database connection managers and queries
│   ├── esios_client.py       # ESIOS API HTTP gateway regional and data loading logic
│   ├── exporter.py           # Multi-tab Excel export engine with custom formatting and merged section headers
│   ├── pdf_reporter.py       # Multi-page PDF executive report generation engine with ReportLab and embedded plots
│   ├── text_reporter.py      # Automated text summary rendering engine for demand and price metrics
│   ├── utils.py              # Centralized indicator translation and formatting utilities
│   ├── validator.py          # Structural verification and timezone-aware datatype firewall
│   └── visualizer.py         # Interactive Plotly rendering engine with HTML & PNG exports
│
├── tests/                    # Automated unit testing suite
│   ├── __init__.py           # Test package initialization marker
│   └── test_validator.py     # Test cases for data quality firewall and schema checks
│
├── .env                      # Environment variables (API Token - Untracked)
├── .env.example              # Example template for environment variables (Tracked)
├── .gitignore                # Specifies intentionally untracked files to ignore
├── app.py                    # Streamlit Web Application entry point
├── main.py                   # Central CLI execution entry point
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
* **Timezone Handling:** UTC ISO 8601 network requests automatically normalized to Peninsular Spanish local time (`Europe/Madrid`).
* **Licensing:** Open Data (Subject to ESIOS/REE API terms of use and project GNU GPLv3 license).

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

### Running the Application
**Option A: Streamlit Web Interface (Recommended)**

To launch the interactive web dashboard in your browser, run:
```bash
streamlit run app.py
```
* Use the sidebar to pick dates, select indicators, and configure pairwise model comparisons.
* Click Run Analysis to execute the pipeline.
* Browse through interactive Plotly time-series, view key metrics, inspect anomaly logs, and download generated PDF, Excel, or Text reports directly from the UI.

**Option B: Command-Line Interface (CLI)**

To initiate the terminal-based interactive pipeline, execute:
```bash
python main.py
```

### Developer Tools
To reset the local SQLite cache database during development, run:
```bash
python -m scripts.reset_db
```
To inspect the current status and metrics summary of the local cache, run:
```bash
python -m scripts.inspect_db
```
To fetch a raw JSON payload directly from the e·sios API for structural inspection (defaults to ID 600, or pass a custom ID):
```bash
python -m scripts.fetch_raw_sample
python -m scripts.fetch_raw_sample 1001
```

### Pipeline Workflow
1. **System Initialization & Cache Maintenance (`cleaner.py` / `database.py`):** Initializes SQLite schemas and automatically removes obsolete cached entries exceeding the TTL threshold upon application startup.
2. **Execution Mode & Parameter Selection:**
   * **Web Interface (`app.py`):** Parameters, date ranges, and model comparison settings are selected dynamically via Streamlit sidebar controls.
   * **CLI Interface (`cli.py`):** Interactive terminal prompts guide the user step-by-step through configuration options.
3. **Extraction & Cache Lookup (`esios_client.py`):** Checks the local SQLite database (`esios_cache.db`) for valid cached records; if missing, issues authenticated REST API requests to REE e·sios and persists the new payload.
4. **Validation (`validator.py`):** Verifies schema compliance (`id`, `name`, `geo_id`, `geo_name`, `value`, `datetime`), enforces strict datatypes, cleans nulls, and standardizes timezones to `Europe/Madrid`.
5. **Analytics & Volume Modeling (`analyzer.py`):** Calculates statistical metrics, price volatility/spreads, pairwise model evaluations (MAPE, Pearson $r$), Z-Score demand anomalies ($> 2.0$), and wholesale market economic volume ($M€$).
6. **Artifact Generation & Display:** Renders dashboard UI elements or CLI text metrics while writing production-ready artifacts into dedicated `outputs/` subdirectories:
   * 📈 **Plots (`outputs/plots/`):** Interactive HTML charts (`st.iframe` compatible) and static high-DPI PNGs.
   * 📕 **PDF Report (`outputs/reports/`):** Executive multi-page PDF generated via ReportLab.
   * 📄 **Text Summary (`outputs/reports/`):** Formatted plain-text summary report.
   * 📊 **Excel Dataset (`outputs/exports/`):** Styled multi-tab Excel workbook.

## 📜 License
This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.