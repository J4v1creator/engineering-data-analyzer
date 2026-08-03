from config.settings import DEMAND_TRANSLATIONS, GEOGRAPHY_TRANSLATIONS, PRICE_TRANSLATIONS


def translate_indicator(name: str, geo_name: str = "", show_geo: bool = False) -> str:
    """Centralized helper to translate any indicator or geography to English.

    Args:
        name (str): Original indicator name in Spanish.
        geo_name (str): Original geographic region name in Spanish.
        show_geo (bool): Flag to include geographic region in the translation.

    Returns:
        str: Translated indicator name, optionally with geographic region.
    """
    english_name = DEMAND_TRANSLATIONS.get(name, PRICE_TRANSLATIONS.get(name, name))
    if not geo_name:
        return english_name

    english_geo = GEOGRAPHY_TRANSLATIONS.get(geo_name, geo_name)
    return f"{english_name} ({english_geo})" if show_geo else english_name