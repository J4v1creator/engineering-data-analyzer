from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

def _prompt_category_selection(title: str, available_items: list[str], start_index: int = 1) -> tuple[list[str], int]:
    """Helper function to print a menu section and capture user selections.

    Args:
        title (str): The section header title (e.g., 'DEMAND SELECTION MENU').
        available_items (list[str]): List of category/indicator names.
        start_index (int): Starting index for menu options.

    Returns:
        tuple[list[str], int]: Selected items and the next available menu index.

    Raises:
        ValueError: If the user input is invalid or out of range.
    """
    print(f"\n📊 --- {title} ---")

    menu_map = {}
    current_idx = start_index

    # Print available items with sequential numbering
    for item in available_items:
        menu_map[current_idx] = item
        print(f"  [{current_idx}] {item}")
        current_idx += 1

    # Add option to analyze all items in this specific section
    all_option_idx = current_idx
    print(f"  [{all_option_idx}] ANALYZE ALL {title.split()[0]}S")
    current_idx += 1

    while True:
        try:
            user_input = input(f"\nEnter numbers separated by commas (e.g., {start_index},{start_index+1}) or press Enter for ALL: ").strip()

            # Default to ALL if user presses Enter or chooses the ALL option
            if user_input == "" or user_input == str(all_option_idx):
                print(f"🔄 Selecting all available {title.lower()}...")
                return available_items, current_idx

            selected_indices = [int(x.strip()) for x in user_input.split(",")]

            # Validate range
            if all(idx in menu_map for idx in selected_indices):
                selected_items = [menu_map[idx] for idx in selected_indices]
                print(f"✅ Selected: {', '.join(selected_items)}")
                return selected_items, current_idx
            else:
                print(f"❌ Invalid choice. Please select valid option numbers from the section.")

        except ValueError:
            print("❌ Input format error. Please use numbers separated by commas only.")

def get_user_indicator_selections(demands_list: list[str], prices_list: list[str]) -> tuple[list[str], list[str]]:
    """Displays separate selection menus for Demands and Prices.

    Args:
        demands_list (list[str]): Available demand indicator names.
        prices_list (list[str]): Available price indicator names.

    Returns:
        tuple[list[str], list[str]]: A tuple containing (selected_demands, selected_prices).
    """
    # 1. Demand Selection Menu (Indices 1 to N)
    selected_demands, next_index = _prompt_category_selection("DEMAND SELECTION MENU", demands_list, start_index=1)

    # 2. Price Selection Menu (Indices continues from N+1)
    selected_prices, _ = _prompt_category_selection("PRICE SELECTION MENU", prices_list, start_index=next_index)

    return selected_demands, selected_prices

def ask_comparison_targets(all_demands: list[str], selected_demands: list[str]) -> tuple[str, str]:
    """Prompts the user to select exactly two distinct demand types for cross-analysis.

    Args:
        all_demands (list[str]): A list of all unique demand types available.
        selected_demands (list[str]): A list of strings containing the names of the 
        demands previously selected by the user.

    Returns:
        tuple[str, str]: Names of the two distinct demand types selected for comparison.

    Raises:
        ValueError: If the user fails to select exactly two distinct demand types.
    """
    print("\n🔍 --- ADVANCED COMPARISON SELECTION ---")
    print("You selected multiple demands. Which two would you like to cross-analyze?")

    # Map global index to each active demand option
    indexed_selection = {}
    for demand in selected_demands:
        global_idx = all_demands.index(demand) + 1
        indexed_selection[global_idx] = demand
        print(f"  [{global_idx}] {demand}")

    while True:
        try:
            user_input = input("\nSelect exactly two numbers separated by a comma (e.g., 1,2): ").strip()
            indices = [int(x.strip()) for x in user_input.split(",")]

            # Validate that exactly two valid choices were made
            if len(indices) == 2 and all(idx in indexed_selection for idx in indices):
                # Ensure they didn't pick the exact same number twice (e.g., 1,1)
                if indices[0] == indices[1]:
                    print("❌ You cannot compare a demand type against itself. Please pick two different ones.")
                    continue

                model_a = indexed_selection[indices[0]]
                model_b = indexed_selection[indices[1]]
                return model_a, model_b

            valid_options = ", ".join(map(str, indexed_selection.keys()))
            print(f"❌ Invalid choice. Please enter exactly two numbers from your active options: [{valid_options}].")

        except ValueError:
            print("❌ Input format error. Please use numbers separated by commas only (e.g., 1,2).")

def display_anomalies_summary(anomalies: dict[str, list]) -> None:
    """Prints a clean, formatted summary of the detected anomalies in the console.

    Args:
        anomalies (dict[str, list]): Mapping of demand names to lists of detected issues.
    """
    if anomalies:
        for demand_name, issues in anomalies.items():
            print(f"⚠️ {demand_name}: Found {len(issues)} statistical anomalies.")
    else:
        print("✅ No anomalies detected in the selected demand types.")

def get_user_datetime_filter() -> tuple[datetime, datetime]:
    """Prompts the user to enter a specific start and end datetime range.

    Returns:
        tuple[datetime, datetime]: Start and end boundaries as timezone-aware datetime objects.

    Raises:
        ValueError: If the user inputs invalid date or time formats, or if the start date
            is not earlier than the end date.
    """
    madrid_tz = ZoneInfo("Europe/Madrid")

    print("\n📅 DATA PERIOD FILTER")
    print("Please specify the temporal range for analysis.")
    print("\nDate format: YYYY-MM-DD (e.g., 2026-07-03)")
    print("Time format: HH:MM      (e.g., 22:00)")

    while True:
        try:
            print("\n--- Enter Start Period ---")
            # Request and parse start datetime
            start_date = input("Start Date: ").strip()
            start_time = input("Start Time: ").strip()
            # Combine both strings into a single datetime
            start_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M").replace(tzinfo=madrid_tz)

            print("\n--- Enter End Period ---")
            # Request and parse end datetime
            end_date = input("End Date: ").strip()
            end_time = input("End Time: ").strip()
            end_dt = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M").replace(tzinfo=madrid_tz)

            # Ensure the range is chronologically valid
            if start_dt >= end_dt:
                print("❌ Error: Start period must be earlier than End period. Try again.\n")
                continue

            return start_dt, end_dt

        except ValueError:
            print("❌ Invalid format. Please check your dates (YYYY-MM-DD) and times (HH:MM).\n")