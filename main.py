import sys
from src.loader import load_csv_data
from src.validator import validate_dataset
from src.analyzer import calculate_energy_statistics
from src.visualizer import plot_energy_demand
from src.report import generate_text_report
from src.interface import get_user_demand_selection

def main():
    print("==================================================")
    # Define the version constant within the entry point
    print("🚀 STARTING ENERGY PIPELINE EXECUTION (v1.0.0)")
    print("==================================================")

    # 1. Define paths
    input_csv = "data/raw/energy_data.csv"

    try:
        # 2. Extract: Load data
        df = load_csv_data(input_csv)

        # 3. Validate: Quality check firewall
        validate_dataset(df)

        # 4. Interactive Menu: Ask user for specific demand types to analyze
        selected_types = get_user_demand_selection(df)
        df_filtered = df[df["name"].isin(selected_types)]

        # 5. Analyze: Calculate statistical metrics on filtered data
        stats = calculate_energy_statistics(df_filtered)

        # 6. Visualize: Generate and save plot on filtered data
        plot_path = plot_energy_demand(df_filtered)

        # 7. Report: Generate automated text summary on filtered data
        report_path = generate_text_report(df_filtered, stats)

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