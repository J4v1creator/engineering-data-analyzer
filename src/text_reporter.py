"""Automated text report generation module for energy market and demand statistics."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from config.settings import REPORTS_OUTPUT_DIR
from src.utils import format_mw, format_price, translate_indicator


def _build_demand_section(demand_stats: dict) -> list[str]:
    """Helper to format the Energy Demand section lines.

    Args:
        demand_stats (dict): Dictionary of demand statistics calculated.

    Returns:
        list [str]: Formatted lines for the Energy Demand statistical summary.
    """
    lines = [
        "--------------------------------------------------",
        "2. STATISTICAL SUMMARY: ENERGY DEMAND (MW)",
        "--------------------------------------------------",
    ]
    if not demand_stats:
        lines.append("- No demand indicators were selected for this run.\n")
        return lines

    for series_label, metrics in demand_stats.items():
        lines.extend([
            f"\n--- {str(series_label).upper()} ---",
            f"- Maximum Demand:  {format_mw(metrics['max'])} (At: {metrics['peak_time']})",
            f"- Minimum Demand:  {format_mw(metrics['min'])}",
            f"- Mean (Average):  {format_mw(metrics['mean'])}",
            f"- Median:          {format_mw(metrics['median'])}",
            f"- Std. Deviation:  {format_mw(metrics['std_dev'])}",
        ])
    lines.append("")
    return lines


def _build_price_section(price_stats: dict) -> list[str]:
    """Helper to format the Energy Prices section lines.

    Args:
        price_stats (dict): Dictionary of price statistics calculated.

    Returns:
        list [str]: Formatted lines for the Energy Demand statistical summary.
    """
    lines = [
        "--------------------------------------------------",
        "3. STATISTICAL SUMMARY: ENERGY PRICES (€/MWh)",
        "--------------------------------------------------",
    ]
    if not price_stats:
        lines.append("- No price indicators were selected for this run.\n")
        return lines

    for series_label, metrics in price_stats.items():
        lines.extend([
            f"\n--- {str(series_label).upper()} ---",
            f"- Maximum Price:    {format_price(metrics['max'])} (At: {metrics['max_time']})",
            f"- Minimum Price:    {format_price(metrics['min'])} (At: {metrics['min_time']})",
            f"- Daily Spread:     {format_price(metrics['spread'])} (Max - Min Swing)",
            f"- Zero/Low Hours:   {metrics['zero_low_price_hours']} hour(s) (<= 5.0)",
        ])
    lines.append("")
    return lines


def _build_comparison_section(comp_stats: dict | None) -> list[str]:
    """Helper to format the Model Comparison section lines.

    Args:
        comp_stats (dict | None): Advanced comparison statistics.

    Returns:
        list [str]: Formatted lines for the Energy Demand statistical summary.
    """
    lines = [
        "--------------------------------------------------",
        "4. ADVANCED MODEL COMPARISON (DEMANDS ONLY)",
        "--------------------------------------------------",
    ]
    if not comp_stats:
        lines.append("- No demand indicators were selected for cross-analysis in this run.\n")
        return lines

    model_a = comp_stats.get("model_a")
    model_b = comp_stats.get("model_b")
    model_a_en = translate_indicator(indicator_id=model_a) if isinstance(model_a, int) else str(model_a)
    model_b_en = translate_indicator(indicator_id=model_b) if isinstance(model_b, int) else str(model_b)

    lines.extend([
        f"Comparison Baseline (Model A): {model_a_en}",
        f"Compared Target     (Model B): {model_b_en}",
        "",
        f"- Mean Difference (A - B):      {format_mw(comp_stats['mean_difference'])}",
        f"- Maximum Absolute Deviation:   {format_mw(abs(comp_stats['max_difference_value']))}",
        f"    ↳ Occurred At:                {comp_stats['max_difference_time']}",
        f"    ↳ Directional Error (A - B):   {format_mw(comp_stats['max_difference_value'])}",
        f"- Mean Absolute Pct. Error:     {comp_stats['mape']:.2f}%",
        f"- Pearson Correlation (r):      {comp_stats['correlation']:.4f}",
        "",
    ])
    return lines


def _build_anomalies_section(anomalies: dict | None) -> list[str]:
    """Helper to format the Statistical Anomaly Detection section lines.

    Args:
        anomalies (dict | None): Dictionary of detected anomalies.

    Returns:
        list [str]: Formatted lines for the Energy Demand statistical summary.
    """
    lines = [
        "--------------------------------------------------",
        "5. STATISTICAL ANOMALY DETECTION (Z-SCORE > 2.0)",
        "--------------------------------------------------",
    ]
    has_printed_anomalies = False

    if anomalies and isinstance(anomalies, dict):
        for series_label, issues in anomalies.items():
            if issues:
                has_printed_anomalies = True
                lines.append(f"\n• {str(series_label).upper()}:")
                for issue in issues:
                    lines.append(
                        f"    ↳ [{issue['type']}] At {issue['datetime']} -> "
                        f"{format_mw(issue['value'])} (Deviation: {format_mw(issue['deviation'])})"
                    )

    if not has_printed_anomalies:
        lines.append("- No statistical anomalies detected in energy demand data.")
    
    lines.append("")
    return lines


def _build_volume_section(market_volume_stats: dict | None) -> list[str]:
    """Helper to format the Market Volume section lines.

    Args:
        market_volume_stats (dict | None): Dictionary of market volume statistics.

    Returns:
        list [str]: Formatted lines for the Energy Demand statistical summary.
    """
    lines = [
        "--------------------------------------------------",
        "6. MARKET ECONOMIC VOLUME ANALYSIS (DEMAND × SPOT PRICE)",
        "--------------------------------------------------",
    ]
    if not market_volume_stats:
        lines.append("- Market economic volume assessment skipped (insufficient matching data).\n")
        return lines

    total_m_eur = market_volume_stats["total_volume_eur"] / 1_000_000
    total_gwh = market_volume_stats["total_energy_mwh"] / 1_000
    vwap = market_volume_stats["weighted_avg_price"]
    peak_spend_eur = market_volume_stats["peak_spend_eur"] / 1_000
    peak_time = market_volume_stats["peak_spend_hour"]
    peak_mw = market_volume_stats["peak_spend_demand_mw"]
    peak_price = market_volume_stats["peak_spend_price_eur"]

    lines.extend([
        f"• Total Electricity Traded Volume : {total_m_eur:.2f} M€",
        f"• Total Energy Demand Processed   : {total_gwh:.2f} GWh",
        f"• Volume-Weighted Avg Price (VWAP): {format_price(vwap)}",
        "",
        "• Peak Expenditure Hour:",
        f"    ↳ Timestamp : {peak_time}",
        f"    ↳ Hourly Cost: {peak_spend_eur:.2f} k€",
        f"    ↳ Demand    : {format_mw(peak_mw)}",
        f"    ↳ SPOT Price: {format_price(peak_price)}",
        "",
    ])
    return lines


def generate_text_report(
    df: pd.DataFrame,
    start_dt: datetime | None,
    end_dt: datetime | None,
    demand_stats: dict,
    price_stats: dict,
    comp_stats: dict | None = None,
    anomalies: dict | None = None,
    market_volume_stats: dict | None = None,
    output_dir: str | Path = REPORTS_OUTPUT_DIR,
) -> str:
    """"Generates a complete text report including demand, prices, models, anomalies, and market volume.

    Args:
        df (pd.DataFrame): Validated dataset.
        start_dt (datetime | None): Start datetime of analyzed range.
        end_dt (datetime | None): End datetime of analyzed range.
        demand_stats (dict): Dictionary of demand statistics calculated.
        price_stats (dict): Dictionary of price statistics calculated.
        comp_stats (dict | None): Advanced comparison statistics.
        anomalies (dict | None): Dictionary of detected anomalies.
        market_volume_stats (dict | None): Dictionary of market volume statistics.
        output_dir (str | Path): Directory where the report will be saved.

    Returns:
        str: File path of the generated report.

    Raises:
        RuntimeError: If writing the report file fails.
    """
    print("\n📄 Generating automated text report...")

    out_dir_path = Path(output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    effective_start = start_dt if start_dt else df["datetime"].min()
    effective_end = end_dt if end_dt else df["datetime"].max()

    fmt = "%Y%m%d_%H%M" if effective_start.date() == effective_end.date() else "%Y%m%d"
    filename = f"summary_energy_analysis_{effective_start.strftime(fmt)}_to_{effective_end.strftime(fmt)}.txt"
    output_path = out_dir_path / filename

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if start_dt and end_dt:
        analysis_period = f"{start_dt.strftime('%Y-%m-%d %H:%M')} to {end_dt.strftime('%Y-%m-%d %H:%M')}"
    else:
        analysis_period = "Full Dataset Range (Unfiltered)"

    num_rows, num_cols = df.shape
    column_names = ", ".join(df.columns)

    # Construct complete report section by section
    lines = [
        "==================================================",
        "ENERGY MARKET & DEMAND ANALYSIS REPORT (AUTOMATED)",
        "==================================================",
        f"Date of Analysis:       {current_time}",
        f"Analysis Period (Data): {analysis_period}",
        "Data Source:            Red Eléctrica de España (REE / e·sios)",
        "",
        "--------------------------------------------------",
        "1. DATASET METADATA",
        "--------------------------------------------------",
        f"- Total Rows:       {num_rows}",
        f"- Total Columns:    {num_cols}",
        f"- Column Names:     {column_names}",
        f"- Selected Range:   [{analysis_period}]",
        "",
    ]

    lines.extend(_build_demand_section(demand_stats))
    lines.extend(_build_price_section(price_stats))
    lines.extend(_build_comparison_section(comp_stats))
    lines.extend(_build_anomalies_section(anomalies))
    lines.extend(_build_volume_section(market_volume_stats))

    lines.extend([
        "==================================================",
        "Report successfully generated by Data Pipeline.",
        "==================================================",
    ])

    report_content = "\n".join(lines)

    try:
        output_path.write_text(report_content, encoding="utf-8")
        print(f"✅ Report successfully saved to: '{output_path}'")
        return str(output_path)
    except OSError as e:
        raise RuntimeError(f"Failed to write report file: {e}") from e