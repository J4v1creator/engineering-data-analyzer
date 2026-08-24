"""Interactive Command-Line Interface (CLI) components, menu navigation, and input handlers."""

from datetime import datetime
from zoneinfo import ZoneInfo

from src.utils import format_price, translate_indicator


def get_user_indicator_selection(demands_list: list[int], prices_list: list[int]) -> tuple[list[int], list[int]]:
    """Displays a unified menu for selecting both Demand and Price indicators.

    Args:
        demands_list (list[int]): Available demand indicator IDs (ordered by priority).
        prices_list (list[int]): Available price indicator IDs (ordered by priority).

    Returns:
        tuple[list[int], list[int]]: Selected demand IDs and selected price IDs.

    Raises:
        ValueError: If the user inputs invalid option numbers or formats.
    """
    num_demands = len(demands_list)
    num_prices = len(prices_list)
    total_items = num_demands + num_prices

    print("\n📊 --- INDICATOR SELECTION MENU ---")
    print("Select indicators to analyze (Demands, Prices, or Both):\n")

    # Print Demands Section
    print("--- Energy Demands (MW) ---")
    for idx, demand_id in enumerate(demands_list, start=1):
        display_name = translate_indicator(indicator_id=demand_id)
        print(f"  [{idx}] {display_name}")

    # Print Prices Section
    print("\n--- Energy Prices (€/MWh) ---")
    for idx, price_id in enumerate(prices_list, start=num_demands + 1):
        english_display = translate_indicator(indicator_id=price_id)
        print(f"  [{idx}] {english_display}")

    # Quick Actions
    all_option_idx = total_items + 1
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

            if not all(1 <= idx <= total_items for idx in selected_indices):
                print("❌ Invalid selection. Please enter valid option numbers from the menu.")
                continue

            # Separate selected indices into demands and prices
            selected_demands = [demands_list[idx - 1] for idx in selected_indices if idx <= num_demands]
            selected_prices = [prices_list[idx - num_demands - 1] for idx in selected_indices if idx > num_demands]

            if selected_demands:
                english_demands = [translate_indicator(indicator_id=d) for d in selected_demands]
                print(f"✅ Selected Demands: {', '.join(english_demands)}")
            else:
                print("⏩ No demands selected.")

            if selected_prices:
                english_prices = [translate_indicator(indicator_id=p) for p in selected_prices]
                print(f"✅ Selected Prices:  {', '.join(english_prices)}")
            else:
                print("⏩ No prices selected.")

            return selected_demands, selected_prices

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

    if len(selected_demands) == 2:
        return selected_demands[0], selected_demands[1]

    print("\n🔍 --- ADVANCED DEMAND COMPARISON SELECTION ---")
    print("You selected multiple demands. Which two would you like to cross-analyze?")

    for idx, demand_id in enumerate(selected_demands, start=1):
        english_display = translate_indicator(indicator_id=demand_id)
        print(f"  [{idx}] {english_display}")

    while True:
        try:
            user_input = input("\nSelect exactly two numbers separated by a comma (e.g., 1,2): ").strip()
            indices = [int(x.strip()) for x in user_input.split(",")]

            # Check that exactly two items were entered
            if len(indices) != 2:
                print("❌ Please enter exactly two numbers separated by a comma (e.g., 1,2).")
                continue

            # Check if user picked the exact same option twice
            if indices[0] == indices[1]:
                print("❌ You cannot compare a demand type against itself. Please pick two different options.")
                continue

            # Validate that both indices are within the valid range
            if all(1 <= idx <= len(selected_demands) for idx in indices):
                model_a_id = selected_demands[indices[0] - 1]
                model_b_id = selected_demands[indices[1] - 1]

                print(f"✅ Selected for cross-analysis: '{translate_indicator(model_a_id)}' vs '{translate_indicator(model_b_id)}'")
                return model_a_id, model_b_id

            print(f"❌ Selection out of range. Please enter valid option numbers (1 to {len(selected_demands)}).")

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

        for series_label in demand_stats.keys():
            issues = anomalies.get(series_label, [])
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