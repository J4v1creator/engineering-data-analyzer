# Engineering Data Analyzer

## Overview
**Engineering Data Analyzer** is a production-ready, modular Python pipeline designed to automate the ingestion, validation, analytical processing, and visualization of real-world energy datasets.

Specifically tailored to interface with Red Eléctrica de España (REE) data structures, the system transforms raw time-series measurements into structured, high-resolution statistical reports and multi-line visualizations. The entire architecture enforces strict industry software practices, including static typing (type hinting), robust exception handling, and full segregation of business logic from the user interface.

## 🛠️ Key Features
* 🔄 **Automated Data Pipeline:** High-performance CSV parsing adapted to specialized grid data delimiters and automatic timezone-aware datetime normalization.
* 🛡️ **Data Quality Firewall (`validator.py`):** Strict pre- and post-validation system checking for expected schemas, correct technical datatypes, null value elimination, and duplicate row prevention.
* 🎛️ **Interactive Console Interface (`interface.py`):** Dynamic CLI menus allowing users to easily isolate specific demand categories or trigger comparative multi-selections via comma-separated index processing.
* 🧠 **Advanced Analytics & Cross-Modeling (`analyzer.py`):** Statistical computations (mean, median, standard deviation, peak load times) paired with dynamic cross-model analysis measuring Mean Absolute Percentage Error (MAPE) and Pearson Correlation Coefficients ($r$).
* 📉 **High-Resolution Visualizations (`visualizer.py`):** Automated generation of publication-quality charts using centralized design templates and strict chronological data alignments.
* 📄 **Automated Reporting System (`report.py`):** Dynamic, localized file writer compiling full execution metadata, descriptive statistics, and delta error modeling into structural plain-text reports.

## 📁 Project Architecture
The codebase implements a clean, modular package hierarchy following the single-responsibility principle:

```text
engineering-data-analyzer/
│
├── data/
│   ├── raw/                  # Ingestion directory (Source CSV files)
│   └── processed/            # Pipeline output (Generated charts and reports)
│
├── src/                      # Package source root
│   ├── __init__.py           # Package initialization marker
│   ├── analyzer.py           # Core mathematics and advanced statistical modeling
│   ├── constants.py          # Centralized configuration, labels, and color palettes
│   ├── interface.py          # Interactive command-line menu mechanics
│   ├── loader.py             # File system IO and raw extraction logic
│   ├── report.py             # Automated text report rendering engine
│   ├── validator.py          # Structural verification and datatype firewall
│   └── visualizer.py         # Matplotlib rendering and charting engine
│
├── main.py                   # Central execution entry point
└── README.md                 # Project documentation
```

## 📊 Dataset Specifications
* **Source:** Red Eléctrica de España (REE) - ESIOS Public Portal.
* **Dataset Name:** Generación y Consumo (Spanish Peninsula Grid).
* **Metrics:** Real-time, programmed, and scheduled electricity demand measured in Megawatts ($MW$).
* **Data Format:** Semicolon-delimited CSV ($;$) with native ISO 8601 timestamps.
* **Time Resolution:** Continuous 5-minute intervals.
* **Temporal Scope:** From 2026-07-03 21:00 CEST to 2026-07-04 19:55 CEST.
* **Licensing:** Public Domain / Open Data (Subject to ESIOS/REE terms of use).

## 🚀 Quick Start & Execution
### Prerequisites
* Python 3.10 or higher.
* Pandas, Matplotlib, and standard dependencies installed via your virtual environment.

### Execution
To initiate the pipeline, simply execute the `python main.py` command in your terminal.

### Pipeline Workflow
1. **Extraction:** Loads raw data from `data/raw/energy_data.csv`.
2. **Validation:** Verifies column schemas (`id`, `name`, `geoname`, `value`, `datetime`) and strict datatypes.
3. **Filtering:** An interactive prompt asks you to select which specific electricity demands to include.
4. **Cross-Analysis:** If multiple metrics are selected, a sub-menu prompts you to specify a baseline and a target model for detailed comparative evaluations.
5. **Output Generation:** Saves the synchronized multi-line visualization (`energy_demand_plot.png`) and the complete analytical documentation (`energy_analysis_report.txt`) directly inside `data/processed/`.