from datetime import datetime
import pandas as pd

def get_user_demand_selection(df_or_list) -> tuple:
    """Displays the available electricity demand types found in the dataset
    and prompts the user to select which ones to analyze using numbers.

    Args:
        df_or_list (pd.DataFrame or list): The validated dataset or a list of demand types.

    Returns:
        tuple: A tuple containing (selected_demands, all_available_demands).
    """
    if isinstance(df_or_list, list):
        available_demands = df_or_list
    else:
        available_demands = list(pd.unique(df_or_list["name"]))

    print("\n📊 --- DEMAND SELECTION MENU ---")
    print("Select which demand types you want to include in the report and chart:")

    # Print options dynamically with an associated index number
    for i, demand in enumerate(available_demands, start=1):
        print(f"  [{i}] {demand}")

    # The last option is always dynamically mapped to "Analyze All"
    all_options_idx = len(available_demands) + 1
    print(f"  [{all_options_idx}] ANALYZE ALL DEMANDS")

    while True:
        try:
            # Capture user input and clean trailing whitespaces
            user_input = input(f"\nEnter numbers separated by commas (e.g., 1,3) or press Enter for ALL: ").strip()

            # If the user presses Enter or selects the "All" option, return the full list
            if user_input == "" or user_input == str(all_options_idx):
                print("🔄 Analyzing all available demand types...")
                return available_demands, available_demands
            
            # Parse input string into a list of integers (e.g., "1, 3" -> [1, 3])
            selected_indices = [int(x.strip()) for x in user_input.split(",")]

            # Validate that all selected numbers fall within the valid menu range
            if all(1 <= idx <= len(available_demands) for idx in selected_indices):
                # Map integers back to the actual string names from the dataset
                selected_demands = [available_demands[idx - 1] for idx in selected_indices]
                print(f"✅ Selected categories: {', '.join(selected_demands)}")
                return selected_demands, available_demands
            else:
                print(f"❌ Invalid selection. Please enter numbers between 1 and {all_options_idx}.")

        except ValueError:
            print("❌ Input format error. Please use numbers separated by commas only (e.g., 1,2).")

def ask_comparison_targets(all_demands: list, selected_demands: list) -> tuple:
    """Prompts the user to select exactly two demand types for the advanced 
    comparison out of the previously selected options.

    Args:
        all_demands (list): A list of all unique demand types available.
        selected_demands (list): A list of strings containing the names of the 
        demands previously selected by the user.

    Returns:
        tuple: A tuple containing two strings (model_a, model_b) with the names 
        of the two distinct demand types chosen for comparison.
    """
    print("\n🔍 --- ADVANCED COMPARISON SELECTION ---")
    print("You selected multiple demands. Which two would you like to cross-analyze?")

    # Create a map to link the global index (1-based) to each selected demand
    indexed_selection = {}
    for demand in selected_demands:
        global_idx = all_demands.index(demand) + 1
        indexed_selection[global_idx] = demand
        print(f"  [{global_idx}] {demand}")

    while True:
        try:
            user_input = input("\nSelect exactly two numbers separated by a comma (e.g., 1,2): ").strip()
            indices = [int(x.strip()) for x in user_input.split(",")]

            # Validate we got exactly two numbers and both are inside our allowed selection map
            if len(indices) == 2 and all(idx in indexed_selection for idx in indices):
                # Ensure they didn't pick the exact same number twice (e.g., 1,1)
                if indices[0] == indices[1]:
                    print("❌ You cannot compare a demand type against itself. Please pick two different ones.")
                    continue

                model_a = indexed_selection[indices[0]]
                model_b = indexed_selection[indices[1]]
                return model_a, model_b
            else:
                valid_options = ", ".join(map(str, indexed_selection.keys()))
                print(f"❌ Invalid choice. Please enter exactly two numbers from your active options: [{valid_options}].")
        except ValueError:
            print("❌ Input format error. Please use numbers separated by commas only (e.g., 1,2).")

def display_anomalies_summary(anomalies: dict):
    """Prints a clean, formatted summary of the detected anomalies in the console.

    Args:
        anomalies (dict): A dictionary where keys are demand names (str)
        and values are lists of detected issues.
    """
    if anomalies:
        for demand_name, issues in anomalies.items():
            print(f"⚠️ {demand_name}: Found {len(issues)} statistical anomalies.")
    else:
        print("✅ No anomalies detected in the selected demand types.")

def get_user_datetime_filter() -> tuple:
    """Asks the user to analyze all data or a specific datetime range.

    Returns:
        tuple: (start_datetime, end_datetime) as datetime objects, or (None, None).
    """
    print("\n📅 DATA PERIOD FILTER")
    print("1. Analyze all data (Full available range)")
    print("2. Custom exact date and time range")

    while True:
        choice = input("Select an option (1-2): ").strip()

        if choice == "1":
            return None, None

        elif choice == "2":
            print("\nDate format: YYYY-MM-DD (e.g., 2026-07-03)")
            print("Time format: HH:MM      (e.g., 22:00)")

            while True:
                try:
                    print("\n--- Enter Start Period ---")
                    # Request and parse start datetime
                    start_date = input("Start Date: ").strip()
                    start_time = input("Start Time: ").strip()
                    # Combine both strings into a single datetime
                    start_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")

                    print("\n--- Enter End Period ---")
                    # Request and parse end datetime
                    end_date = input("End Date: ").strip()
                    end_time = input("End Time: ").strip()
                    end_dt = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

                    # Ensure the range is chronologically valid
                    if start_dt >= end_dt:
                        print("❌ Error: Start period must be earlier than End period. Try again.\n")
                        continue
                    return start_dt, end_dt

                except ValueError:
                    print("❌ Invalid format. Please check your dates (YYYY-MM-DD) and times (HH:MM).\n")

        else:
            print("❌ Invalid selection. Please choose 1 or 2.")