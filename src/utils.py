"""Centralized indicator translation, formatting, and helper utilities."""

from config.settings import GEOGRAPHY_TRANSLATIONS, INDICATOR_TRANSLATIONS


def translate_indicator(indicator_id: int) -> str:
    """Translate ESIOS numerical indicator ID into English display name.

    Args:
        indicator_id (int): ESIOS numerical indicator ID.

    Returns:
        str: English indicator name (e.g., "Spot Market Price").
    """
    return INDICATOR_TRANSLATIONS.get(indicator_id, f"Indicator {indicator_id}")


def translate_geography(geo_id: int) -> str:
    """Translate ESIOS numerical geographic ID into English display name.

    Args:
        geo_id (int): ESIOS numerical geographic region ID.

    Returns:
        str: English region name (e.g., "Peninsula", "Spain").
    """
    return GEOGRAPHY_TRANSLATIONS.get(geo_id, f"Geo {geo_id}")


def translate_full_indicator(indicator_id: int, geo_id: int | None = None, has_multiple_geos: bool = True) -> str:
    """Translate ESIOS indicator and geographic IDs into a full formatted English name.

    Args:
        indicator_id (int): ESIOS numerical indicator ID.
        geo_id (int | None): ESIOS numerical geographic region ID.
        has_multiple_geos (bool): If False, ignores geography and returns only indicator name.

    Returns:
        str: Formatted English display string (e.g., "Spot Market Price (Spain)").
    """
    name = translate_indicator(indicator_id)
    if has_multiple_geos and geo_id is not None:
        geo_name = translate_geography(geo_id)
        return f"{name} ({geo_name})"
    return name


def sort_indicators_by_priority(indicator_ids: list[int], priority_order: list[int]) -> list[int]:
    """Sort a list of indicator IDs based on a provided priority order list.

    Args:
        indicator_ids (list[int]): List of raw indicator IDs to sort.
        priority_order (list[int]): Reference list indicating the priority hierarchy.

    Returns:
        list[int]: Sorted list of indicator IDs.
    """
    return sorted(indicator_ids, key=lambda x: priority_order.index(x) if x in priority_order else 999)


def format_mw(value: float) -> str:
    """Format a numeric value as Megawatts (MW) string.

    Args:
        value (float): Power demand value.

    Returns:
        str: Formatted string (e.g., "30,794.00 MW").
    """
    return f"{value:,.2f} MW" if value is not None else "N/A"


def format_price(value: float) -> str:
    """Format a numeric value as Energy Price (€/MWh) string.

    Args:
        value (float): Energy price value.

    Returns:
        str: Formatted string (e.g., "175.92 €/MWh").
    """
    return f"{value:,.2f} €/MWh" if value is not None else "N/A"


def format_datetime(dt) -> str:
    """Safely formats datetime objects or pandas Timestamps to a standard string format.

    Args:
        dt: Datetime object, Timestamp, or string.

    Returns:
        str: Formatted string ("YYYY-MM-DD HH:MM").
    """
    return dt.strftime("%Y-%m-%d %H:%M") if hasattr(dt, "strftime") else str(dt)