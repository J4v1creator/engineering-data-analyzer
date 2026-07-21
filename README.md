# Engineering Data Analyzer

## Overview
**Engineering Data Analyzer** is a production-ready, modular Python pipeline designed to automate the ingestion, validation, analytical processing, and visualization of real-world energy datasets.

Specifically tailored to interface directly with the **Red Eléctrica de España (REE) e·sios API**, the system fetches real-time and historical time-series measurements, converts raw HTTP responses into structured DataFrames, and generates high-resolution statistical reports and multi-line visualizations. The entire architecture enforces strict industry software practices, including static typing (`type hinting`), robust exception handling, local cache management, and full segregation of business logic from the user interface.

## 🛠️ Key Features
* 🌐 **Direct e·sios API Gateway (`loader.py`):** Automated REST API requests to Red Eléctrica's servers with token-based authentication (`x-api-key`), custom date range parameters, and JSON payload parsing.
* 📦 **Smart Caching & Expiration (`cleaner.py`):** Efficient local storage layer (`data/raw/`) that avoids redundant network requests, paired with an automated cache cleanup module based on configurable Time-to-Live (TTL) policies.
* 🛡️ **Data Quality Firewall (`validator.py`):** Strict pre- and post-validation system checking for expected schemas, correct technical datatypes, null value elimination, and duplicate row prevention.
* 🎛️ **Interactive Console Interface (`interface.py`):** Dynamic CLI menus allowing users to easily define temporal scope, isolate specific demand categories, or trigger comparative multi-selections via comma-separated index processing.
* 🧠 **Advanced Analytics & Cross-Modeling (`analyzer.py`):** Statistical computations (mean, median, standard deviation, peak load times) paired with dynamic cross-model analysis measuring Mean Absolute Percentage Error (MAPE) and Pearson Correlation Coefficients ($r$).
* ⚠️ **Statistical Anomaly Detection:** Automated screening for abnormal demand spikes or drops using a configurable Z-Score methodology ($> 2.0$ standard deviations).
* 📉 **High-Resolution Visualizations (`visualizer.py`):** Automated generation of publication-quality charts using centralized design templates and strict chronological data alignments.
* 📄 **Automated Reporting System (`report.py`):** Dynamic, localized file writer compiling full execution metadata, descriptive statistics, and delta error modeling into structural plain-text reports.

## 📁 Project Architecture
The codebase implements a clean, modular package hierarchy following the single-responsibility principle:

```text
engineering-data-analyzer/
│
├── data/
│   ├── processed/            # Pipeline outputs (Generated charts and reports)
│   └── raw/                  # Local cache storage for API responses (.csv)
│
├── src/                      # Package source root
│   ├── __init__.py           # Package initialization marker
│   ├── analyzer.py           # Core mathematics, temporal filtering, and Z-Score anomaly modeling
│   ├── cleaner.py            # Cache maintenance engine and expired file removal
│   ├── constants.py          # Centralized configuration, e·sios indicator IDs, and color palettes
│   ├── interface.py          # Interactive command-line menu mechanics
│   ├── loader.py             # API fetching gateway, HTTP headers, and caching logic
│   ├── report.py             # Automated text report rendering engine
│   ├── validator.py          # Structural verification and datatype firewall
│   └── visualizer.py         # Matplotlib rendering and charting engine
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
* **Metrics:** Real-time, programmed, and scheduled electricity demand measured in Megawatts ($MW$).
* **Time Resolution:** Continuous 5-minute intervals.
* **Timezone Handling:** UTC ISO 8601 network requests automatically normalized to Peninsular Spanish local time (Europe/Madrid).
* **Licensing:** Open Data (Subject to ESIOS/REE API terms of use and token registration).

## 🚀 Quick Start & Execution
### Prerequisites
* Python 3.10 or higher.
* An active e·sios API Token (requested free of charge at e·sios portal).

### Environment Setup
1. Clone the repository and install dependencies: `pip install -r requirements.txt`
2. Create a `.env` file in the root directory and insert your API Token: `ESIOS_API_TOKEN=your_personal_api_token_here`

### Execution
To initiate the pipeline, simply execute the `python main.py` command in your terminal.

### Pipeline Workflow
1. **Cache Maintenance (`cleaner.py`):** Automatically scans `data/raw/` and removes obsolete cached files exceeding the defined threshold.
2. **Temporal & Demand Filtering:** Prompts the user via CLI for a date/time window and specific energy demand categories (Real, Prevista, Programada, etc.).
3. **Extraction & Cache Check (`loader.py`):** Loads datasets from local cache if a matching file exists; otherwise, issues authenticated HTTP requests to the e·sios API and persists the response.
4. **Validation (`validator.py`):** Enforces column schema checks (`id`, `name`, `geoname`, `value`, `datetime`) and timezone consistency.
5. **Cross-Analysis & Anomalies (`analyzer.py`):** Computes statistics, pairwise models evaluation (MAPE, Pearson correlation), and Z-score calculations to detect statistical anomalies.
6. **Output Generation:** Prints an anomalies summary on the console, saving the synchronized plot (`plot_energy_demand_[TIMESTAMP].png`) and the complete analytical documentation (`report_energy_demand_[TIMESTAMP].csv`) directly inside `data/processed/`.