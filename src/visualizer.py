import os
from zoneinfo import ZoneInfo
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from config.settings import DEFAULT_OUTPUT_DIR, DEMAND_COLOR_PALETTE, DEMAND_TRANSLATIONS, GEO_COLOR_PALETTE, GEOGRAPHY_TRANSLATIONS, PRICE_TRANSLATIONS

def _plot_time_series(df: pd.DataFrame, title: str, y_label: str, filename_prefix: str, color_palette: dict[str, str], translations: dict[str, str], output_dir: str = DEFAULT_OUTPUT_DIR) -> str:
    """Internal helper function to generate and save standardized time-series plots.

    Args:
        df (pd.DataFrame): Validated dataset with 'datetime', 'value', 'name', and 'geo_name'.
        title (str): Chart title.
        y_label (str): Label for the Y-axis including units.
        filename_prefix (str): Prefix for the saved PNG file (e.g., 'demand' or 'price').
        color_palette (dict): Palette containing hex color mappings for each indicator.
        translations (dict): Dictionary mapping Spanish indicator names to English.
        output_dir (str): Destination directory for the plot.

    Returns:
        str: Absolute file path where the plot was saved.
    """
    if df.empty:
        print(f"⚠️ [Visualizer] Skipping plot creation for '{filename_prefix}': Dataset is empty.")
        return ""

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 Created output directory at: '{output_dir}'")

    # Dynamic filename generation based on dataset temporal range
    min_dt = df["datetime"].min()
    max_dt = df["datetime"].max()

    if min_dt.date() == max_dt.date():
        start_str = min_dt.strftime("%Y%m%d_%H%M")
        end_str = max_dt.strftime("%Y%m%d_%H%M")
    else:
        start_str = min_dt.strftime("%Y%m%d")
        end_str = max_dt.strftime("%Y%m%d")

    filename = f"{filename_prefix}_{start_str}_to_{end_str}.png"
    output_path = os.path.join(output_dir, filename)

    # Setup the plot figure size and style
    plt.figure(figsize=(14, 7))
    plt.style.use("seaborn-v0_8-whitegrid")

    # Determine if multiple geographic regions exist in this dataset
    unique_geos = df["geo_name"].unique()
    has_multiple_geos = len(unique_geos) > 1

    # Group by indicator name and plot each series independently
    for name_spanish, english_name in translations.items():
        if name_spanish not in df["name"].values:
            continue

        indicator_df = df[df["name"] == name_spanish]
        available_geos = indicator_df["geo_name"].unique()

        for geo_name in available_geos:
            group_df = indicator_df[indicator_df["geo_name"] == geo_name]
            group_sorted = group_df.sort_values("datetime")

            english_geo = GEOGRAPHY_TRANSLATIONS.get(geo_name, geo_name)

            # Dynamic legend label
            if has_multiple_geos:
                legend_label = f"{english_name} ({english_geo})"
                color_hex = GEO_COLOR_PALETTE.get(geo_name, color_palette.get(name_spanish, "#7f7f7f"))
            else:
                legend_label = english_name
                color_hex = color_palette.get(name_spanish, color_palette.get("default", "#7f7f7f"))

            plt.plot(
                group_sorted["datetime"],
                group_sorted["value"],
                color=color_hex,
                linewidth=2,
                label=legend_label,
            )

    # Format titles and labels
    plt.title(title, fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Time (HH:MM / Date)", fontsize=11, labelpad=10)
    plt.ylabel(y_label, fontsize=11, labelpad=10)

    # Date formatting for X-axis (Europe/Madrid timezone)
    ax = plt.gca()
    spain_tz = ZoneInfo("Europe/Madrid")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M\n%Y-%m-%d", tz=spain_tz))

    plt.gcf().autofmt_xdate()

    # Add legend and optimize layout
    plt.legend(loc="upper right", frameon=True, shadow=True, facecolor="white")
    plt.tight_layout()

    # Save and close plot
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"✅ Visualization successfully saved to: '{output_path}'")
    return output_path

def plot_energy_demand(df: pd.DataFrame, output_dir: str = DEFAULT_OUTPUT_DIR) -> str:
    """Generates a multi-line plot of energy demand (MW) over time."""
    print("\n📉 Generating energy demand visualization...")
    return _plot_time_series(
        df=df,
        title="Spanish Peninsula Energy Demand Comparison",
        y_label="Energy Demand (MW)",
        filename_prefix="plot_energy_demand",
        color_palette=DEMAND_COLOR_PALETTE,
        translations=DEMAND_TRANSLATIONS,
        output_dir=output_dir
    )

def plot_energy_price(df: pd.DataFrame, output_dir: str = DEFAULT_OUTPUT_DIR) -> str:
    """Generates a multi-line plot of energy prices (€/MWh) over time."""
    print("\n💶 Generating energy market price visualization...")
    return _plot_time_series(
        df=df,
        title="Spanish & Regional Energy Market Price Comparison",
        y_label="Energy Price (€/MWh)",
        filename_prefix="plot_energy_prices",
        color_palette=GEO_COLOR_PALETTE,
        translations=PRICE_TRANSLATIONS,
        output_dir=output_dir
    )