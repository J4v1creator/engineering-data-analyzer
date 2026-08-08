"""Centralized indicator translation and formatting utilities."""

from config.settings import DEMAND_INDICATOR_IDS,GEOGRAPHY_TRANSLATIONS, INDICATOR_TRANSLATIONS, PRICE_INDICATOR_IDS


def translate_indicator(indicator_id: int, geo_id: int | None = None, show_geo: bool = False) -> str:
    """Translate ESIOS indicator and geographic IDs into English display names.

    Args:
        indicator_id (int): ESIOS numerical indicator ID.
        geo_id (int | None): ESIOS numerical geographic region ID.
        show_geo (bool): If True, appends the regional name in parentheses.

    Returns:
        str: English indicator name (e.g., "Spot Market Price (Spain)").
    """
    english_name = INDICATOR_TRANSLATIONS.get(indicator_id, f"Indicator {indicator_id}")

    if not show_geo or geo_id is None:
        return english_name

    english_geo = GEOGRAPHY_TRANSLATIONS.get(geo_id, f"Geo {geo_id}")
    return f"{english_name} ({english_geo})"


def sort_indicators_by_priority(indicator_ids: list[int], is_demand: bool = True) -> list[int]:
    """Sort a list of indicator IDs based on the predefined priority order in settings.

    Args:
        indicator_ids (list[int]): List of raw indicator IDs to sort.
        is_demand (bool): True if sorting demand indicators, False for prices.

    Returns:
        list[int]: Sorted list of indicator IDs.
    """
    priority_order = DEMAND_INDICATOR_IDS if is_demand else PRICE_INDICATOR_IDS
    return sorted(indicator_ids, key=lambda x: priority_order.index(x) if x in priority_order else 999)


def format_mw(value: float) -> str:
    """Format a numeric value as Megawatts (MW) string.

    Args:
        value (float): Power demand value.

    Returns:
        str: Formatted string (e.g., "30,794.00 MW").
    """
    return f"{value:,.2f} MW"


def format_price(value: float) -> str:
    """Format a numeric value as Energy Price (€/MWh) string.

    Args:
        value (float): Energy price value.

    Returns:
        str: Formatted string (e.g., "175.92 €/MWh").
    """
    return f"{value:,.2f} €/MWh"