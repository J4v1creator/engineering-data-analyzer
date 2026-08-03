from datetime import datetime
from pathlib import Path

import pandas as pd

from config.settings import DEFAULT_OUTPUT_DIR
from src.utils import translate_indicator


def generate_text_report(
    df: pd.DataFrame,
    demand_stats: dict,
    price_stats: dict,
    comp_stats: dict | None = None,
    anomalies: dict | None = None,
    start_dt: datetime | None = None,
    end_dt: datetime | None = None,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> str:
    """Generates a structured, professional text report summarizing statistical insights
    for both energy demand (MW) and energy prices (€/MWh).

    Args:
        df (pd.DataFrame): The validated dataset.
        demand_stats (dict): Dictionary of demand statistics calculated by the analyzer.
        price_stats (dict): Dictionary of price statistics calculated by the analyzer.
        comp_stats (dict | None): Advanced comparison statistics for demands.
        anomalies (dict | None): Dictionary of detected anomalies.
        start_dt (datetime | None): Start datetime of analyzed range.
        end_dt (datetime | None): End datetime of analyzed range.
        output_dir (str | Path): Directory where the report will be saved.

    Returns:
        str: File path of the generated report.

    Raises:
        RuntimeError: If the system fails to write the report file.
    """
    print("\n📄 Generating automated text report...")

    # Ensure output directory exists
    out_dir_path = Path(output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    # Determine resolution range either from passed arguments or directly from DataFrame
    effective_start = start_dt if start_dt else df["datetime"].min()
    effective_end = end_dt if end_dt else df["datetime"].max()

    # Dynamic filename formatting: check if intraday (same day) or multi-day
    if effective_start.date() == effective_end.date():
        start_str = effective_start.strftime("%Y%m%d_%H%M")
        end_str = effective_end.strftime("%Y%m%d_%H%M")
    else:
        start_str = effective_start.strftime("%Y%m%d")
        end_str = effective_end.strftime("%Y%m%d")

    filename = f"report_energy_demand_{start_str}_to_{end_str}.txt"
    output_path = out_dir_path / filename

    # Get the current timestamp for the analysis metadata
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format the analysis period label for reporting and visualization purposes
    if start_dt and end_dt:
        analysis_period = f"{start_dt.strftime('%Y-%m-%d %H:%M')} to {end_dt.strftime('%Y-%m-%d %H:%M')}"
    else:
        analysis_period = "Full Dataset Range (Unfiltered)"

    # Gather dimensions
    num_rows, num_cols = df.shape
    column_names = ", ".join(df.columns)

    # Report Header and Metadata
    report_content = f"""==================================================
ENERGY MARKET & DEMAND ANALYSIS REPORT (AUTOMATED)
==================================================
Date of Analysis:  {current_time}
Analysis Period (Data): {analysis_period}
Data Source:       Red Eléctrica de España (REE / e·sios)

--------------------------------------------------
1. DATASET METADATA
--------------------------------------------------
- Total Rows:       {num_rows}
- Total Columns:    {num_cols}
- Column Names:     {column_names}
- Selected Range:   [{analysis_period}]

--------------------------------------------------
2. STATISTICAL SUMMARY (DEMAND IN MW)
--------------------------------------------------"""

    if demand_stats:
        has_multiple_geos = len(df["geo_name"].unique()) > 1
        for series_label, metrics in demand_stats.items():
            base_name = series_label.split(" (")[0]
            geo_name = metrics.get("geo_name", "")
            title = translate_indicator(base_name, geo_name=geo_name, show_geo=has_multiple_geos).upper()

            report_content += f"""
--- {title} ---
- Maximum Demand:  {metrics['max']:.2f} MW (At: {metrics['peak_time']})
- Minimum Demand:  {metrics['min']:.2f} MW
- Mean (Average):  {metrics['mean']:.2f} MW
- Median:          {metrics['median']:.2f} MW
- Std. Deviation:  {metrics['std_dev']:.2f} MW
"""
    else:
        report_content += "\n- No demand indicators were selected for this run.\n"

    report_content += """
--------------------------------------------------
3. STATISTICAL SUMMARY: ENERGY PRICES (€/MWh)
--------------------------------------------------"""

    if price_stats:
        has_multiple_geos = len(df["geo_name"].unique()) > 1
        for series_label, metrics in price_stats.items():
            base_name = series_label.split(" (")[0]
            geo_name = metrics.get("geo_name", "")
            title = translate_indicator(base_name, geo_name=geo_name, show_geo=has_multiple_geos).upper()

            report_content += f"""
--- {title} ---
- Maximum Price:    {metrics['max']:.2f} €/MWh (At: {metrics['max_time']})
- Minimum Price:    {metrics['min']:.2f} €/MWh (At: {metrics['min_time']})
- Daily Spread:     {metrics['spread']:.2f} €/MWh (Max - Min Swing)
- Zero/Low Hours:   {metrics['zero_low_price_hours']} hour(s) (<= 5.0 €/MWh)
"""
    else:
        report_content += "\n- No price indicators were selected for this run.\n"

    # Advanced Model Comparison Section
    if comp_stats:
        model_a_en = translate_indicator(comp_stats["model_a"])
        model_b_en = translate_indicator(comp_stats["model_b"])

        report_content += f"""
--------------------------------------------------
4. ADVANCED MODEL COMPARISON (DEMANDS ONLY)
--------------------------------------------------
Comparison Baseline (Model A): {model_a_en}
Compared Target     (Model B): {model_b_en}

- Mean Difference (A - B):      {comp_stats['mean_difference']:.2f} MW
- Maximum Absolute Deviation:   {abs(comp_stats['max_difference_value']):.2f} MW
    ↳ Occurred At:                {comp_stats['max_difference_time']}
    ↳ Directional Error (A - B):   {comp_stats['max_difference_value']:.2f} MW
- Mean Absolute Pct. Error:     {comp_stats['mape']:.2f}%
- Pearson Correlation (r):      {comp_stats['correlation']:.4f}
"""

    # Statistical Anomaly Detection Section
    report_content += f"""
--------------------------------------------------
5. STATISTICAL ANOMALY DETECTION (Z-SCORE > 2.0)
--------------------------------------------------"""
    has_printed_anomalies = False
    if anomalies and demand_stats:
        has_multiple_geos = len(df["geo_name"].unique()) > 1

        for demand_key in demand_stats.keys():
            base_demand_name = demand_key.split(" (")[0]

            for series_label, issues in anomalies.items():
                if series_label.startswith(base_demand_name) and issues:
                    has_printed_anomalies = True

                    base_name = series_label.split(" (")[0]
                    raw_geo = ""
                    if "(" in series_label and ")" in series_label:
                        raw_geo = series_label.split("(")[1].split(")")[0]

                    title = translate_indicator(base_name, geo_name=raw_geo, show_geo=has_multiple_geos).upper()

                    report_content += f"\n• {title}:"
                    for issue in issues:
                        report_content += f"\n  ↳ [{issue['type']}] At {issue['datetime']} -> {issue['value']:.2f} MW (Deviation: {issue['deviation']:.2f} MW)"
                    report_content += "\n"

    if not has_printed_anomalies:
        report_content += "\n- No statistical anomalies detected in energy demand data.\n"

    # Report Footer
    report_content += """
==================================================
Report successfully generated by Data Pipeline.
==================================================
"""

    # Save the report to a file
    try:
        output_path.write_text(report_content, encoding="utf-8")
        print(f"✅ Report successfully saved to: '{output_path}'")
        return str(output_path)
    except OSError as e:
        raise RuntimeError(f"Failed to write the report file: {e}")