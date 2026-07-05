import sys
from src.loader import load_csv_data
from src.validator import validate_dataset
from src.analyzer import calculate_energy_statistics
from src.visualizer import plot_energy_demand
from src.report import generate_text_report

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

        # 4. Analyze: Calculate statistical metrics
        stats = calculate_energy_statistics(df)

        # 5. Visualize: Generate and save plot
        plot_path = plot_energy_demand(df)

        # 6. Report: Generate automated text summary
        report_path = generate_text_report(df, stats)

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