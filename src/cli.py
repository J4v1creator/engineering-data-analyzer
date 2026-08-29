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
        display_name = translate_indicator(indicator_id=price_id)
        print(f"  [{idx}] {display_name}")

    # Quick Actions
    all_option_idx = total_items + 1
    print("\n--- Quick Actions ---")
    print(f"  [{all_option_idx}] ANALYZE ALL (Demands & Prices)")
    print("  [0] NONE / EXIT")

    while True:
        try:
            prompt = f"\nEnter options separated by commas (Press ENTER for ALL, '0' to exit): "
            user_input = input(prompt).strip()

            if user_input == "0":
                print("⏩ No indicators selected.")
                return [], []

            # Default to ALL if user presses enter or types the 'All' index
            if user_input == "" or user_input == str(all_option_idx):
                print("🔄 Selecting all available demands and prices...")
                return demands_list, prices_list

            # Parse indices and remove duplicates while preserving order
            raw_indices = [int(x.strip()) for x in user_input.split(",") if x.strip()]
            selected_indices = list(dict.fromkeys(raw_indices))

            if not all(1 <= idx <= total_items for idx in selected_indices):
                print(f"❌ Invalid selection. Please enter numbers between 1 and {total_items}.")
                continue

            # Map selection
            selected_demands = [demands_list[i - 1] for i in selected_indices if i <= num_demands]
            selected_prices = [prices_list[i - num_demands - 1] for i in selected_indices if i > num_demands]

            if selected_demands:
                demand_names = [translate_indicator(d) for d in selected_demands]
                print(f"✅ Selected Demands: {', '.join(demand_names)}")
            else:
                print("⏩ No demands selected.")

            if selected_prices:
                price_names = [translate_indicator(p) for p in selected_prices]
                print(f"✅ Selected Prices:  {', '.join(price_names)}")
            else:
                print("⏩ No prices selected.")

            return selected_demands, selected_prices

        except ValueError:
            print("❌ Input format error. Please use numbers separated by commas (e.g., 1,5).")


def ask_comparison_targets(selected_demands: list[int]) -> tuple[int, int] | None:
    """Prompts the user to select two distinct demand types for cross-analysis.

    Args:
        selected_demands (list[int]): List of demand IDs selected by the user.

    Returns:
        tuple[int, int] | None: Demand IDs to compare, or None if skipped.

    Raises:
        ValueError: If the user inputs invalid option numbers or formats.
    """
    if len(selected_demands) < 2:
        return None

    print("\n🔍 --- ADVANCED DEMAND COMPARISON SELECTION ---")
    print("Which two demand series would you like to cross-analyze?")

    for idx, demand_id in enumerate(selected_demands, start=1):
        display_name = translate_indicator(indicator_id=demand_id)
        print(f"  [{idx}] {display_name}")
    print("  [0] Skip comparison")

    while True:
        try:
            user_input = input("\nEnter two numbers (e.g., 1,2) or '0' to skip: ").strip()

            if user_input in ("", "0"):
                print("⏩ Comparison skipped.")
                return None

            indices = [int(x.strip()) for x in user_input.split(",") if x.strip()]

            # Check that exactly two items were entered
            if len(indices) != 2:
                print("❌ Please enter exactly two numbers separated by a comma (e.g., 1,2)  or '0' to skip.")
                continue

            # Check if user picked the exact same option twice
            if indices[0] == indices[1]:
                print("❌ You cannot compare a demand type against itself. Please pick two different options.")
                continue

            # Validate that both indices are within the valid range
            if all(1 <= idx <= len(selected_demands) for idx in indices):
                id_a = selected_demands[indices[0] - 1]
                id_b = selected_demands[indices[1] - 1]

                print(f"✅ Selected for cross-analysis: '{translate_indicator(id_a)}' vs '{translate_indicator(id_b)}'")
                return id_a, id_b

            print(f"❌ Selection out of range. Please enter valid option numbers (1 to {len(selected_demands)})  or '0' to skip.")

        except ValueError:
            print("❌ Input format error. Please use numbers separated by commas only (e.g., 1,2)  or '0' to skip.")


def display_anomalies_summary(anomalies: dict[str, list], demand_stats: dict) -> None:
    """Prints a clean, formatted summary of detected anomalies in console.

    Args:
        anomalies (dict[str, list]): Mapping of series names to anomaly details.
        demand_stats (dict): Statistics for selected demand indicators.
    """
    # Filtramos únicamente las series que tienen al menos una anomalía registrada
    detected = {
        label: len(issues)
        for label, issues in anomalies.items()
        if label in demand_stats and len(issues) > 0
    }

    if not detected:
        print("✅ No anomalies detected in selected series.")
        return

    print("\n⚠️ --- ANOMALY DETECTION SUMMARY ---")
    for series_label, count in detected.items():
        print(f"⚠️ {series_label}: Found {count} statistical anomalies.")


def get_user_datetime_filter() -> tuple[datetime, datetime]:
    """Prompts the user to enter a specific start and end datetime range.

    Returns:
        tuple[datetime, datetime]: Start and end boundaries with timezone set to Europe/Madrid.

    Raises:
        ValueError: If the user inputs invalid date or time formats, or if the start date is not earlier than the end date.
    """
    madrid_tz = ZoneInfo("Europe/Madrid")

    print("\n📅 DATA PERIOD FILTER")
    print("Please specify the temporal range for analysis. (Date: YYYY-MM-DD, Time: HH:MM)")

    while True:
        try:
            print("\n--- Enter Start Period ---")
            start_date = input("Start Date  (e.g. 2026-07-01): ").strip()
            start_time = input("Start Time  (e.g. 00:00): ").strip()
            start_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M").replace(tzinfo=madrid_tz)

            print("\n--- Enter End Period ---")
            end_date = input("End Date (e.g. 2026-07-03): ").strip()
            end_time = input("End Time (e.g. 23:59): ").strip()
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
    print("✅ Market demand and SPOT prices aligned successfully.")
    print(f"📊 Total Market Volume: {total_million_eur:.2f} M€")
    print(f"📈 Volume-Weighted Average Price (VWAP): {format_price(weighted_price)}")