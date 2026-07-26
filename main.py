import sqlite3
import sys
from src.analyzer import calculate_energy_statistics, compare_demand_models, detect_demand_anomalies
from src.cleaner import clean_expired_cache
from config.settings import DEMAND_TRANSLATIONS, PRICE_TRANSLATIONS
from src.database import init_db
from src.cli import ask_comparison_targets, display_anomalies_summary, get_user_datetime_filter, get_user_indicator_selection
from src.esios_client import get_energy_data
from src.report import generate_text_report
from src.validator import validate_dataset
from src.visualizer import plot_energy_demand, plot_energy_price

def main() -> None:
    """Main orchestrator for the energy demand data analysis pipeline.

    Handles user configuration, interactive CLI choices, data fetching (API/Cache),
    quality validation, metric generation, anomaly detection, and artifact exports.
    """
    print("==================================================")
    print("🚀 STARTING ENERGY DEMAND ANALYSIS PIPELINE")
    print("==================================================")

    try:
        # Database setup: Ensure tables and indexes are initialized
        init_db()

        # Maintenance: Clean up expired cache files before processing
        clean_expired_cache()

        # Input: Prompt user for time filters and period constraints
        start_dt, end_dt = get_user_datetime_filter()

        # Input: Retrieve available demand and price keys directly from translation settings
        available_demands = list(DEMAND_TRANSLATIONS.keys())
        available_prices = list(PRICE_TRANSLATIONS.keys())

        # Input: Prompt user for demand and price selections
        selected_demands, selected_prices = get_user_indicator_selection(available_demands, available_prices)

        # Consolidate all user selection choices for data retrieval
        selected_indicators = selected_demands + selected_prices

        if not selected_indicators:
            print("\n⚠️ No indicators were selected for analysis. Exiting pipeline.")
            sys.exit(0)

        # Process: Retrieve, extract, and unify datasets from the cache layer or remote API
        df_filtered = get_energy_data(selected_indicators, start_dt, end_dt)

        # Validate: Enforce structural constraints and structural quality checks
        validate_dataset(df_filtered)

        # Process: Establish target baselines and pairwise comparison groups
        all_available_indicators = available_demands + available_prices
        comparison_targets = None

        if len(selected_demands) == 2:
            comparison_targets = (selected_demands[0], selected_demands[1])
        elif len(selected_demands) > 2:
            comparison_targets = ask_comparison_targets(available_demands, selected_demands)

        # Analyze: Execute mathematical metrics, model evaluations, and standard deviation anomalies
        stats = calculate_energy_statistics(df_filtered)
        comp_stats = compare_demand_models(df_filtered, comparison_targets)
        anomalies = detect_demand_anomalies(df_filtered)

        # Output: Render descriptive warning logs and runtime evaluation summaries to the CLI
        display_anomalies_summary(anomalies)

        # Output: Generate independent visualization charts for Demands and Prices
        saved_plots = []

        # 1. Plot Electricity Demands (if any were selected)
        df_demands = df_filtered[df_filtered["name"].isin(selected_demands)]
        if not df_demands.empty:
            demand_plot_path = plot_energy_demand(df_demands)
            saved_plots.append(f"📊 Demand Plot: {demand_plot_path}")

        # 2. Plot Electricity Prices (if any were selected)
        df_prices = df_filtered[df_filtered["name"].isin(selected_prices)]
        if not df_prices.empty:
            price_plot_path = plot_energy_price(df_prices)
            saved_plots.append(f"💶 Price Plot:  {price_plot_path}")

        # Output: Generate text files detailing consolidated metrics and performance history
        report_path = generate_text_report(df_filtered, stats, comp_stats, anomalies, start_dt, end_dt)

        print("\n==================================================")
        print("🎉 [SUCCESS] Pipeline executed perfectly!")
        for plot_path in saved_plots:
            print(plot_path)
        print(f"📄 Report saved to: {report_path}")
        print("==================================================")

    except sqlite3.Error as e:
        print(f"\n❌ Database Error: An issue occurred with SQLite storage.\n{e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"\n❌ API Connection Error: Could not retrieve data.\n{e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\n❌ Critical Error: Local file or directory missing.\n{e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ Data Quality Error: Validation failed.\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected System Error:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()