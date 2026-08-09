"""Interactive Command-Line Interface (CLI) components, menu navigation, and input handlers."""

from datetime import datetime
from zoneinfo import ZoneInfo

from src.utils import format_price, translate_indicator


def get_user_indicator_selection(demands_list: list[int], prices_list: list[int]) -> tuple[list[int], list[int]]:
    """Displays a unified menu for selecting both Demand and Price indicators.

    Args:
        demands_list (list[int]): Available demand indicator IDs.
        prices_list (list[int]): Available price indicator IDs.

    Returns:
        tuple[list[int], list[int]]: Selected demand IDs and selected price IDs.

    Raises:
        ValueError: If the user inputs invalid option numbers or formats.
    """
    print("\n📊 --- INDICATOR SELECTION MENU ---")
    print("Select indicators to analyze (Demands, Prices, or Both):\n")

    menu_map = {}
    current_idx = 1

    # Print Demands Section
    print("--- Energy Demands (MW) ---")
    for item in demands_list:
        menu_map[current_idx] = ("demand", item)
        english_display = translate_indicator(indicator_id=item)
        print(f"  [{current_idx}] {english_display}")
        current_idx += 1

    # Print Prices Section
    print("\n--- Energy Prices (€/MWh) ---")
    for item in prices_list:
        menu_map[current_idx] = ("price", item)
        english_display = translate_indicator(indicator_id=item)
        print(f"  [{current_idx}] {english_display}")
        current_idx += 1

    # Quick Actions
    all_option_idx = current_idx
    print("\n--- Quick Actions ---")
    print(f"  [{all_option_idx}] ANALYZE ALL (Demands & Prices)")
    print("  [0] NONE / EXIT")

    while True:
        try:
            user_input = input("\nEnter numbers separated by commas (e.g., '1,2' for demands, '5,6' for prices, or '0' for none): ").strip()

            if user_input == "0":
                print("⏩ No indicators selected.")
                return [], []

            if user_input == "" or user_input == str(all_option_idx):
                print("🔄 Selecting all available demands and prices...")
                return demands_list, prices_list

            selected_indices = [int(x.strip()) for x in user_input.split(",")]

            if all(idx in menu_map for idx in selected_indices):
                selected_demands = []
                selected_prices = []

                for idx in selected_indices:
                    category, indicator_id = menu_map[idx]
                    if category == "demand":
                        selected_demands.append(indicator_id)
                    else:
                        selected_prices.append(indicator_id)

                if selected_demands:
                    english_demands = [
                        translate_indicator(indicator_id=demand_id) 
                        for demand_id in selected_demands
                    ]
                    print(f"✅ Selected Demands: {', '.join(english_demands)}")

                if selected_prices:
                    english_prices = [
                        translate_indicator(indicator_id=price_id) 
                        for price_id in selected_prices
                    ]
                    print(f"✅ Selected Prices:  {', '.join(english_prices)}")

                return selected_demands, selected_prices
            else:
                print("❌ Invalid selection. Please enter valid option numbers from the menu.")

        except ValueError:
            print("❌ Input format error. Please use numbers separated by commas (e.g., 1,5).")


def ask_comparison_targets(selected_demands: list[int]) -> tuple[int, int] | None:
    """Prompts the user to select exactly two distinct demand types for cross-analysis.

    Args:
        selected_demands (list[int]): List of demand IDs selected by the user.

    Returns:
        tuple[int, int] | None: IDs of the two distinct demand types selected or None if insufficient.

    Raises:
        ValueError: If the user inputs invalid option numbers or formats.
    """
    if len(selected_demands) < 2:
        return None

    print("\n🔍 --- ADVANCED DEMAND COMPARISON SELECTION ---")
    print("You selected multiple demands. Which two would you like to cross-analyze?")

    indexed_selection = {i + 1: demand_id for i, demand_id in enumerate(selected_demands)}
    for idx, demand_id in indexed_selection.items():
        english_display = translate_indicator(indicator_id=demand_id)
        print(f"  [{idx}] {english_display}")

    while True:
        try:
            user_input = input("\nSelect exactly two numbers separated by a comma (e.g., 1,2): ").strip()
            indices = [int(x.strip()) for x in user_input.split(",")]

            if len(indices) == 2 and all(idx in indexed_selection for idx in indices):
                if indices[0] == indices[1]:
                    print("❌ You cannot compare a demand type against itself. Please pick two different ones.")
                    continue

                model_a_id = indexed_selection[indices[0]]
                model_b_id = indexed_selection[indices[1]]
                return model_a_id, model_b_id

            valid_options = ", ".join(map(str, indexed_selection.keys()))
            print(f"❌ Invalid choice. Please enter exactly two numbers from your active options: [{valid_options}].")

        except ValueError:
            print("❌ Input format error. Please use numbers separated by commas only (e.g., 1,2).")


def display_anomalies_summary(anomalies: dict[str, list], demand_stats: dict) -> None:
    """Prints a clean, formatted summary of detected anomalies in console.

    Args:
        anomalies (dict[str, list]): Mapping of indicator/region names of detected issues.
        demand_stats (dict): Statistics for selected demand indicators.
    """
    if anomalies and demand_stats:
        print("\n⚠️ --- ANOMALY DETECTION SUMMARY ---")
        has_printed = False

        for series_label, issues in anomalies.items():
            if issues:
                has_printed = True
                print(f"⚠️ {series_label}: Found {len(issues)} statistical anomalies.")

        if not has_printed:
            print("✅ No anomalies detected in selected series.")
    else:
        print("✅ No anomalies detected in selected series.")


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
            start_date = input("Start Date: ").strip()
            start_time = input("Start Time: ").strip()
            start_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M").replace(tzinfo=madrid_tz)

            print("\n--- Enter End Period ---")
            end_date = input("End Date: ").strip()
            end_time = input("End Time: ").strip()
            end_dt = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M").replace(tzinfo=madrid_tz)

            if start_dt >= end_dt:
                print("❌ Error: Start period must be earlier than End period. Try again.\n")
                continue

            return start_dt, end_dt

        except ValueError:
            print("❌ Invalid format. Please check your dates (YYYY-MM-DD) and times (HH:MM).\n")


def display_market_volume_summary(volume_stats: dict) -> None:
    """Prints a concise summary of the market economic volume calculation in console.

    Args:
        volume_stats (dict): Dictionary containing calculated market volume metrics.
    """
    if not volume_stats:
        print("⚠️ Market volume calculation skipped (missing required demand or SPOT price series).")
        return

    total_million_eur = volume_stats.get("total_volume_eur", 0.0) / 1_000_000
    weighted_price = volume_stats.get("weighted_avg_price", 0.0)

    print("\n💶 --- MARKET ECONOMIC VOLUME ANALYSIS ---")
    print("✅ Market demand and SPOT prices successfully aligned (1-hour resolution).")
    print(f"📊 Total Market Volume: {total_million_eur:.2f} M€")
    print(f"📈 Volume-Weighted Average Price (VWAP): {format_price(weighted_price)}")