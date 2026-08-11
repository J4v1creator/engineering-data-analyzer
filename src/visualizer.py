"""Time-series visualization module for energy demand and market price indicators using Matplotlib."""

from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from config.settings import DEFAULT_OUTPUT_DIR, DEMAND_COLOR_PALETTE, DEMAND_INDICATOR_IDS, GEO_COLOR_PALETTE, PRICE_INDICATOR_IDS
from src.utils import translate_indicator


def _plot_time_series(
    df: pd.DataFrame,
    title: str,
    y_label: str,
    filename_prefix: str,
    color_palette: dict[int | str, str],
    priority_order: list[int] | None = None,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> str:
    """Internal helper function to generate and save standardized time-series plots.

    Args:
        df (pd.DataFrame): Validated dataset with datetime, value, indicator_id/id, and geo_id.
        title (str): Chart title.
        y_label (str): Label for the Y-axis including units.
        filename_prefix (str): Prefix for the saved PNG file (e.g., 'demand' or 'price').
        color_palette (dict): Palette containing hex color mappings for each indicator.
        priority_order (list[int] | None): Order of indicators to display.
        output_dir (str | Path): Destination directory for the plot.

    Returns:
        str: Absolute file path where the plot was saved.
    """
    if df.empty:
        print(f"⚠️ [Visualizer] Skipping plot creation for '{filename_prefix}': Dataset is empty.")
        return ""

    out_dir_path = Path(output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    df_copy = df.copy()

    # Apply priority ordering using Categorical sorting if provided
    if priority_order:
        df_copy["indicator_id"] = pd.Categorical(df_copy["indicator_id"], categories=priority_order, ordered=True)
        df_copy = df_copy.sort_values("indicator_id")

    min_dt = df_copy["datetime"].min()
    max_dt = df_copy["datetime"].max()

    if min_dt.date() == max_dt.date():
        start_str = min_dt.strftime("%Y%m%d_%H%M")
        end_str = max_dt.strftime("%Y%m%d_%H%M")
    else:
        start_str = min_dt.strftime("%Y%m%d")
        end_str = max_dt.strftime("%Y%m%d")

    filename = f"{filename_prefix}_{start_str}_to_{end_str}.png"
    output_path = out_dir_path / filename

    plt.figure(figsize=(14, 7))
    plt.style.use("seaborn-v0_8-whitegrid")

    has_multiple_geos = df_copy["geo_id"].nunique() > 1

    for (ind_id, geo_id), group_df in df_copy.groupby(["indicator_id", "geo_id"], sort=False):
        group_sorted = group_df.sort_values("datetime")

        legend_label = translate_indicator(indicator_id=ind_id, geo_id=geo_id, show_geo=has_multiple_geos)

        name_spanish = group_df["name"].iloc[0] if "name" in group_df.columns else ""
        geo_name = group_df["geo_name"].iloc[0] if "geo_name" in group_df.columns else ""

        if has_multiple_geos:
            color_hex = GEO_COLOR_PALETTE.get(
                geo_id,
                GEO_COLOR_PALETTE.get(
                    geo_name,
                    color_palette.get(ind_id, color_palette.get(name_spanish, "#7f7f7f"))
                )
            )
        else:
            color_hex = color_palette.get(
                ind_id,
                color_palette.get(name_spanish, color_palette.get("default", "#7f7f7f"))
            )

        plt.plot(
            group_sorted["datetime"],
            group_sorted["value"],
            color=color_hex,
            linewidth=2,
            label=legend_label,
        )

    plt.title(title, fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Time (HH:MM / Date)", fontsize=11, labelpad=10)
    plt.ylabel(y_label, fontsize=11, labelpad=10)

    ax = plt.gca()
    spain_tz = ZoneInfo("Europe/Madrid")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M\n%Y-%m-%d", tz=spain_tz))

    plt.gcf().autofmt_xdate()

    plt.legend(loc="upper right", frameon=True, shadow=True, facecolor="white")
    plt.tight_layout()

    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"✅ Visualization successfully saved to: '{output_path}'")
    return str(output_path)


def plot_energy_demand(df: pd.DataFrame, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> str:
    """Generates a multi-line plot of energy demand (MW) over time.

    Args:
        df (pd.DataFrame): Validated dataset with datetime, value, name, and geo_name.
        output_dir (str | Path): Directory where the plot will be saved.

    Returns:
        str: Absolute file path where the plot was saved.
    """
    print("\n📉 Generating energy demand visualization...")
    return _plot_time_series(
        df=df,
        title="Spanish Peninsula Energy Demand Comparison",
        y_label="Energy Demand (MW)",
        filename_prefix="plot_energy_demand",
        color_palette=DEMAND_COLOR_PALETTE,
        priority_order=DEMAND_INDICATOR_IDS,
        output_dir=output_dir,
    )


def plot_energy_price(df: pd.DataFrame, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> str:
    """Generates a multi-line plot of energy prices (€/MWh) over time.

    Args:
        df (pd.DataFrame): Validated dataset with datetime, value, name, and geo_name.
        output_dir (str | Path): Directory where the plot will be saved.

    Returns:
        str: Absolute file path where the plot was saved.
    """
    print("\n💶 Generating energy market price visualization...")
    return _plot_time_series(
        df=df,
        title="Spanish & Regional Energy Market Price Comparison",
        y_label="Energy Price (€/MWh)",
        filename_prefix="plot_energy_prices",
        color_palette=GEO_COLOR_PALETTE,
        priority_order=PRICE_INDICATOR_IDS,
        output_dir=output_dir,
    )