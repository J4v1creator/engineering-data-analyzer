import sys
import pandas as pd
from src.analyzer import calculate_energy_statistics, compare_demand_models
from src.interface import get_user_demand_selection, ask_comparison_targets
from src.loader import load_csv_data
from src.report import generate_text_report
from src.validator import validate_dataset
from src.visualizer import plot_energy_demand

def main():
    """Entry point for the data pipeline execution."""
    print("==================================================")
    print("🚀 STARTING ENERGY PIPELINE EXECUTION (v1.0.0)")
    print("==================================================")

    # Configuration paths
    input_csv = "data/raw/energy_data.csv"

    try:
        # Extract: Load raw data from CSV
        df = load_csv_data(input_csv)

        # Validate: Structural and data quality checks
        validate_dataset(df)

        # Interactive Menu: Query user for specific demand types to filter
        selected_types, all_available_demands = get_user_demand_selection(df)
        df_filtered = df[df["name"].isin(selected_types)]

        # Determine comparison targets based on user requirements
        comparison_targets = None
        if len(selected_types) == 2:
            # Map automatically if exactly two options are selected
            comparison_targets = (selected_types[0], selected_types[1])
        elif len(selected_types) > 2:
            # Prompt submenu for explicit choice if more than two options exist
            comparison_targets = ask_comparison_targets(all_available_demands, selected_types)

        # Analyze: Calculate metrics over the filtered data subset
        stats = calculate_energy_statistics(df_filtered)

        # Analyze: Run advanced evaluation between selected models
        comp_stats = compare_demand_models(df_filtered, comparison_targets)

        # Visualize: Build and save the multi-line chart
        plot_path = plot_energy_demand(df_filtered)

        # Report: Write summary details to disk
        report_path = generate_text_report(df_filtered, stats, comp_stats)

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