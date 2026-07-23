import sqlite3
import sys
from src.analyzer import calculate_energy_statistics, compare_demand_models, detect_demand_anomalies
from src.cleaner import clean_expired_cache
from src.constants import ESIOS_INDICATORS
from src.database import init_db
from src.interface import ask_comparison_targets, display_anomalies_summary, get_user_datetime_filter, get_user_demand_selection
from src.loader import fetch_and_combine_esios_data
from src.report import generate_text_report
from src.validator import validate_dataset
from src.visualizer import plot_energy_demand

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

        # Input: Retrieve full metadata parameters and fetch user choice configurations
        available_demands = list(ESIOS_INDICATORS.keys())
        selected_types, all_available_demands = get_user_demand_selection(available_demands)

        # Process: Retrieve, extract, and unify datasets from the cache layer or remote API
        df_filtered = fetch_and_combine_esios_data(selected_types, start_dt, end_dt)

        # Validate: Enforce structural constraints and structural quality checks
        validate_dataset(df_filtered)

        # Process: Establish target baselines and pairwise comparison groups based on selection limits
        comparison_targets = None
        if len(selected_types) == 2:
            comparison_targets = (selected_types[0], selected_types[1])
        elif len(selected_types) > 2:
            comparison_targets = ask_comparison_targets(all_available_demands, selected_types)

        # Analyze: Execute mathematical metrics, model evaluations, and standard deviation anomalies
        stats = calculate_energy_statistics(df_filtered)
        comp_stats = compare_demand_models(df_filtered, comparison_targets)
        anomalies = detect_demand_anomalies(df_filtered)

        # Output: Render descriptive warning logs and runtime evaluation summaries to the CLI
        display_anomalies_summary(anomalies)

        # Output: Build graphical plots and serialize analytical charts to disk storage
        plot_path = plot_energy_demand(df_filtered)

        # Output: Generate text files detailing consolidated metrics and performance history
        report_path = generate_text_report(df_filtered, stats, comp_stats, anomalies, start_dt, end_dt)

        print("\n==================================================")
        print("🎉 [SUCCESS] Pipeline executed perfectly!")
        print(f"📊 Plot saved to:   {plot_path}")
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