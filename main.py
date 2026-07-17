import sys
import pandas as pd
from src.analyzer import calculate_energy_statistics, compare_demand_models, detect_demand_anomalies, filter_dataframe_by_time
from src.constants import DEFAULT_RAW_DIR, DEFAULT_PROCESSED_DIR
from src.interface import get_user_demand_selection, ask_comparison_targets, display_anomalies_summary, get_user_datetime_filter
from src.loader import load_csv_data
from src.report import generate_text_report
from src.validator import validate_dataset
from src.visualizer import plot_energy_demand

def main():
    """Entry point for the data pipeline execution."""
    print("==================================================")
    print("🚀 STARTING ENERGY DEMAND ANALYSIS PIPELINE")
    print("==================================================")

    try:
        # Extract: Load raw data from CSV
        df = load_csv_data(DEFAULT_RAW_DIR)

        # Validate: Structural and data quality checks
        validate_dataset(df)

        # Interactive Menu: Prompt the user to select or define a specific analysis period
        start_dt, end_dt = get_user_datetime_filter()

        # Analyze: Apply the temporal filter to isolate the relevant data subset
        df_time_filtered = filter_dataframe_by_time(df, start_dt, end_dt)

        # Interactive Menu: Query user for specific demand types to filter
        selected_types, all_available_demands = get_user_demand_selection(df_time_filtered)
        df_filtered = df_time_filtered[df_time_filtered["name"].isin(selected_types)]

        # Determine comparison targets based on user requirements
        comparison_targets = None
        if len(selected_types) == 2:
            # Map automatically if exactly two options are selected
            comparison_targets = (selected_types[0], selected_types[1])
        elif len(selected_types) > 2:
            # Interactive Menu: Prompt submenu for explicit choice if more than two options exist
            comparison_targets = ask_comparison_targets(all_available_demands, selected_types)

        # Analyze: Calculate metrics over the filtered data subset
        stats = calculate_energy_statistics(df_filtered)

        # Analyze: Run advanced evaluation between selected models
        comp_stats = compare_demand_models(df_filtered, comparison_targets)

        # Analyze: Detect Anomalies
        anomalies = detect_demand_anomalies(df_filtered)

        # Interactive Menu: Print summary using the interface layer
        display_anomalies_summary(anomalies)

        # Visualize: Build and save the multi-line chart
        plot_path = plot_energy_demand(df_filtered)

        # Report: Write summary details to disk
        report_path = generate_text_report(df_filtered, stats, comp_stats, anomalies, start_dt, end_dt)

        print("\n==================================================")
        print("🎉 [SUCCESS] Pipeline executed perfectly!")
        print(f"📊 Plot saved to:   {plot_path}")
        print(f"📄 Report saved to: {report_path}")
        print("==================================================")

    except FileNotFoundError as e:
        print(f"\n❌ Critical Error: File not found.\n{e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ Data Quality Error: Validation failed.\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected System Error:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()