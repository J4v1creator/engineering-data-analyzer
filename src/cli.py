from datetime import datetime
from zoneinfo import ZoneInfo

from src.utils import translate_indicator


def get_user_indicator_selection(demands_list: list[str], prices_list: list[str]) -> tuple[list[str], list[str]]:
    """Displays a single unified menu for both Demand and Price indicators.

    Args:
        demands_list (list[str]): Available demand indicator names.
        prices_list (list[str]): Available price indicator names.

    Returns:
        tuple[list[str], list[str]]: Selected demands and selected prices.

    Raises:
        ValueError: If the user inputs invalid selections or fails to select any indicators.
    """
    print("\n📊 --- INDICATOR SELECTION MENU ---")
    print("Select indicators to analyze (Demands, Prices, or Both):\n")

    menu_map = {}
    current_idx = 1

    # Print Demands Section
    print("--- Energy Demands (MW) ---")
    for item in demands_list:
        menu_map[current_idx] = ("demand", item)
        english_display = translate_indicator(item)
        print(f"  [{current_idx}] {english_display}")
        current_idx += 1

    # Print Prices Section
    print("\n--- Energy Prices (€/MWh) ---")
    for item in prices_list:
        menu_map[current_idx] = ("price", item)
        english_display = translate_indicator(item)
        print(f"  [{current_idx}] {english_display}")
        current_idx += 1

    # Print Quick Actions
    all_option_idx = current_idx
    print("\n--- Quick Actions ---")
    print(f"  [{all_option_idx}] ANALYZE ALL (Demands & Prices)")
    print("  [0] NONE / EXIT")

    while True:
        try:
            user_input = input("\nEnter numbers separated by commas (e.g., '1,2' for demands, '5,6' for prices, or '0' for none): ").strip()

            # Option 0: User wants to exit or select nothing
            if user_input == "0":
                print("⏩ No indicators selected.")
                return [], []

            # Default / ALL option
            if user_input == "" or user_input == str(all_option_idx):
                print("🔄 Selecting all available demands and prices...")
                return demands_list, prices_list

            # Process comma-separated list
            selected_indices = [int(x.strip()) for x in user_input.split(",")]

            if all(idx in menu_map for idx in selected_indices):
                selected_demands = []
                selected_prices = []

                for idx in selected_indices:
                    category, name = menu_map[idx]
                    if category == "demand":
                        selected_demands.append(name)
                    else:
                        selected_prices.append(name)

                # Feedback logs translated to English
                if selected_demands:
                    english_demands = [translate_indicator(demand) for demand in selected_demands]
                    print(f"✅ Selected Demands: {', '.join(english_demands)}")
                if selected_prices:
                    english_prices = [translate_indicator(price) for price in selected_prices]
                    print(f"✅ Selected Prices:  {', '.join(english_prices)}")

                return selected_demands, selected_prices
            else:
                print("❌ Invalid selection. Please enter valid option numbers from the menu.")

        except ValueError:
            print("❌ Input format error. Please use numbers separated by commas (e.g., 1,5).")


def ask_comparison_targets(all_demands: list[str], selected_demands: list[str]) -> tuple[str, str] | None:
    """Prompts the user to select exactly two distinct demand types for cross-analysis.

    Args:
        all_demands (list[str]): A list of all unique demand types available.
        selected_demands (list[str]): A list of strings containing the names of the demands previously selected by the user.

    Returns:
        tuple[str, str] | None: Names of the two distinct demand types selected for comparison or None if insufficient.

    Raises:
        ValueError: If the user fails to select exactly two distinct demand types.
    """
    # Defensive check: if fewer than 2 demands were selected, cross-analysis isn't possible
    if len(selected_demands) < 2:
        return None

    print("\n🔍 --- ADVANCED DEMAND COMPARISON SELECTION ---")
    print("You selected multiple demands. Which two would you like to cross-analyze?")

    # Map global index to each active demand option
    indexed_selection = {}
    for demand in selected_demands:
        global_idx = all_demands.index(demand) + 1
        indexed_selection[global_idx] = demand
        english_display = translate_indicator(demand)
        print(f"  [{global_idx}] {english_display}")

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
        anomalies (dict[str, list]): Mapping of indicator/region names to lists of detected issues.
    """
    if anomalies:
        print("\n⚠️ --- ANOMALY DETECTION SUMMARY ---")
        for indicator_label, issues in anomalies.items():
            # If the key contains parenthesis like "Demanda real (Península)", format dynamically
            if "(" in indicator_label and ")" in indicator_label:
                raw_name, raw_geo = indicator_label.split(" (")
                raw_geo = raw_geo.rstrip(")")
                display_label = translate_indicator(raw_name, geo_name=raw_geo, show_geo=True)
            else:
                display_label = translate_indicator(indicator_label)
            print(f"⚠️ {display_label}: Found {len(issues)} statistical anomalies.")
    else:
        print("✅ No anomalies detected in the selected series.")


def get_user_datetime_filter() -> tuple[datetime, datetime]:
    """Prompts the user to enter a specific start and end datetime range.

    Returns:
        tuple[datetime, datetime]: Start and end boundaries as timezone-aware datetime objects.

    Raises:
        ValueError: If the user inputs invalid date or time formats, or if the start date is not earlier than the end date.
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