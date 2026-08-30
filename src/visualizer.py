"""Time-series visualization module for energy demand and market price indicators using Plotly."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from config.settings import (
    DEMAND_COLOR_PALETTE,
    DEMAND_INDICATOR_IDS,
    GEO_COLOR_PALETTE,
    GLOBAL_GEO_ORDER,
    PLOTS_HTML_DIR,
    PLOTS_STATIC_DIR,
    PRICE_INDICATOR_IDS,
)
from src.utils import translate_full_indicator


def _plot_time_series(
    df: pd.DataFrame,
    title: str,
    y_label: str,
    filename_prefix: str,
    color_palette: dict[int | str, str],
    static_output_dir: str | Path = PLOTS_STATIC_DIR,
    html_output_dir: str | Path = PLOTS_HTML_DIR,
    priority_order: list[int] | None = None,
) -> dict[str, str]:
    """Internal helper function to generate interactive HTML and static PNG time-series plots.

    Args:
        df (pd.DataFrame): Validated dataset with datetime, value, indicator_id, and geo_id.
        title (str): Chart title.
        y_label (str): Label for the Y-axis including units.
        filename_prefix (str): Prefix for saved files (e.g., 'plot_energy_demands').
        color_palette (dict): Palette containing hex color mappings.
        static_output_dir (str | Path): Directory for PNG files.
        html_output_dir (str | Path): Directory for interactive HTML files.
        priority_order (list[int] | None): Order of indicator IDs to display.

    Returns:
        dict[str, str]: Dictionary containing absolute paths for 'html' and 'png' generated files.
    """
    if df.empty:
        print(f"⚠️ [Visualizer] Skipping plot creation for '{filename_prefix}': Dataset is empty.")
        return {"html": "", "png": ""}

    static_dir_path = Path(static_output_dir)
    html_dir_path = Path(html_output_dir)
    static_dir_path.mkdir(parents=True, exist_ok=True)
    html_dir_path.mkdir(parents=True, exist_ok=True)

    df_copy = df.copy()

    # Apply indicator and geographic region sorting
    if priority_order:
        df_copy["indicator_id"] = pd.Categorical(df_copy["indicator_id"], categories=priority_order, ordered=True)

    # Apply geographic region sorting from settings
    if "geo_id" in df_copy.columns:
        df_copy["geo_id"] = pd.Categorical(df_copy["geo_id"], categories=GLOBAL_GEO_ORDER, ordered=True)

    # Sort DataFrame rows by indicator and geography priority before plotting
    sort_cols = [col for col in ["indicator_id", "geo_id"] if col in df_copy.columns]
    if sort_cols:
        df_copy = df_copy.sort_values(sort_cols)

    # Generate standardized file names
    min_dt, max_dt = df_copy["datetime"].min(), df_copy["datetime"].max()
    fmt = "%Y%m%d_%H%M" if min_dt.date() == max_dt.date() else "%Y%m%d"
    base_filename = f"{filename_prefix}_{min_dt.strftime(fmt)}_to_{max_dt.strftime(fmt)}"
    
    png_path = static_dir_path / f"{base_filename}.png"
    html_path = html_dir_path / f"{base_filename}.html"

    fig = go.Figure()
    has_multiple_geos = df_copy["geo_id"].nunique() > 1

    for (ind_id, geo_id), group_df in df_copy.groupby(["indicator_id", "geo_id"], sort=False, observed=True):
        if group_df.empty:
            continue

        group_sorted = group_df.sort_values("datetime")
        legend_label = translate_full_indicator(ind_id, geo_id, has_multiple_geos=has_multiple_geos)

        name_spanish = group_df["name"].iloc[0] if "name" in group_df.columns else ""
        geo_name = group_df["geo_name"].iloc[0] if "geo_name" in group_df.columns else ""

        # Resolve color mapping cleanly based on geography or indicator
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

        # Add line trace to Plotly figure
        fig.add_trace(
            go.Scatter(
                x=group_sorted["datetime"],
                y=group_sorted["value"],
                mode="lines",
                name=legend_label,
                line=dict(color=color_hex, width=2),
                hovertemplate=f"<b>{legend_label}</b><br>"
                            f"Date/Time: %{{x|%Y-%m-%d %H:%M}}<br>"
                            f"Value: %{{y:.2f}} {y_label.split('(')[-1].replace(')', '')}<extra></extra>"
            )
        )

    # Layout styling matching whitegrid aesthetic
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, family="Arial, sans-serif"), x=0.01),
        xaxis=dict(
            title="Time",
            showgrid=True,
            gridcolor="#E5E5E5",
            tickformat="%H:%M\n%Y-%m-%d"
        ),
        yaxis=dict(
            title=y_label,
            showgrid=True,
            gridcolor="#E5E5E5"
        ),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="#E5E5E5",
            borderwidth=1
        ),
        margin=dict(l=60, r=40, t=80, b=60),
        width=1200,
        height=600
    )

    # 1. Export interactive HTML
    fig.write_html(str(html_path), include_plotlyjs="cdn")
    print(f"✅ Interactive visualization saved to: '{html_path}'")

    # 2. Export static high-DPI PNG for PDF report
    fig.write_image(str(png_path), scale=2)
    print(f"✅ Static visualization saved to: '{png_path}'")

    return {
        "html": str(html_path),
        "png": str(png_path)
    }


def plot_energy_demand(
    df: pd.DataFrame,
    static_output_dir: str | Path = PLOTS_STATIC_DIR,
    html_output_dir: str | Path = PLOTS_HTML_DIR,
) -> dict[str, str]:
    """Generates multi-line interactive (HTML) and static (PNG) plots of energy demand (MW).

    Args:
        df (pd.DataFrame): Validated dataset with datetime, value, name, and geo_name.
        static_output_dir (str | Path): Directory for PNG files.
        html_output_dir (str | Path): Directory for interactive HTML files.

    Returns:
        dict[str, str]: Dictionary containing absolute paths for 'html' and 'png' generated files.
    """
    print("\n📉 Generating energy demand visualizations...")
    return _plot_time_series(
        df=df,
        title="Spanish Peninsula Energy Demand Comparison",
        y_label="Energy Demand (MW)",
        filename_prefix="plot_energy_demands",
        color_palette=DEMAND_COLOR_PALETTE,
        static_output_dir=static_output_dir,
        html_output_dir=html_output_dir,
        priority_order=DEMAND_INDICATOR_IDS,
    )


def plot_energy_price(
    df: pd.DataFrame,
    static_output_dir: str | Path = PLOTS_STATIC_DIR,
    html_output_dir: str | Path = PLOTS_HTML_DIR,
) -> dict[str, str]:
    """Generates multi-line interactive (HTML) and static (PNG) plots of energy prices (€/MWh)."

    Args:
        df (pd.DataFrame): Validated dataset with datetime, value, name, and geo_name.
        static_output_dir (str | Path): Directory for PNG files.
        html_output_dir (str | Path): Directory for interactive HTML files.

    Returns:
        dict[str, str]: Dictionary containing absolute paths for 'html' and 'png' generated files.
    """
    print("\n💶 Generating energy market price visualization...")
    return _plot_time_series(
        df=df,
        title="Spanish & Regional Energy Market Price Comparison",
        y_label="Energy Price (€/MWh)",
        filename_prefix="plot_energy_prices",
        color_palette=GEO_COLOR_PALETTE,
        static_output_dir=static_output_dir,
        html_output_dir=html_output_dir,
        priority_order=PRICE_INDICATOR_IDS,
    )