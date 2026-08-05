from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from config.settings import DEFAULT_OUTPUT_DIR
from src.utils import translate_indicator


def _apply_workbook_styles(file_path: Path) -> None:
    """Applies professional formatting, header colors, thin borders, and auto-adjusts
    column widths across all worksheets in the generated Excel file.

    Args:
        file_path (Path): Path to the generated Excel workbook.
    """

    wb = load_workbook(file_path)

    # Define common styles
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold = True, color="FFFFFF")
    thin_border = Border(
        left=Side(style="thin", color="D3D3D3"),
        right=Side(style="thin", color="D3D3D3"),
        top=Side(style="thin", color="D3D3D3"),
        bottom=Side(style="thin", color="D3D3D3"),
    )
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")

    for sheet in wb.worksheets:
        # Enable grid lines explicitly
        sheet.views.sheetView[0].showGridLines = True

        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is not None:
                    # Apply light borders to all populated cells
                    cell.border = thin_border

                    # Check if row is a header row (openpyxl detects headers by bold/fill logic or first row of tables)
                    # Headers in our generated sheets match specific title strings or row 1/startrows
                    if isinstance(cell.value, str) and (
                        cell.row == 1
                        or cell.value
                        in [
                            "Metric",
                            "Market Indicator",
                            "Indicator",
                            "Indicator Name",
                            "Baseline Series",
                            "Timestamp",
                            "Datetime",
                        ]
                    ):
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.alignment = align_center

        # Auto-fit Column Widths dynamically
        for col in sheet.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)

            for cell in col:
                if cell.value is not None:
                    # Limit long strings in 'Clean Data' to avoid ridiculously wide columns
                    cell_len = len(str(cell.value))
                    if cell_len > max_len:
                        max_len = cell_len

            # Set padding width (min width 12, max width 50 for readability)
            adjusted_width = min(max(max_len + 3, 12), 50)
            sheet.column_dimensions[col_letter].width = adjusted_width

    wb.save(file_path)


def export_to_excel(
    df: pd.DataFrame,
    demand_stats: dict,
    price_stats: dict,
    comp_stats: dict,
    anomalies: dict,
    market_volume_stats: dict,
) -> str:
    """Generates a styled, multi-tab Excel workbook containing energy market analytics,
    raw data, model evaluation, and anomaly breakdowns.

    Args:
        df (pd.DataFrame): Cleaned and validated energy market data.
        demand_stats (dict): Statistics for demand analysis.
        price_stats (dict): Statistics for price analysis.
        comp_stats (dict): Statistics for competitive analysis.
        anomalies (dict): Information about detected anomalies.
        market_volume_stats (dict): Statistics for market volume analysis.

    Returns:
        str: Absolute or relative file path to the generated .xlsx file.
    """
    # Ensure output directory exists
    out_dir_path = Path(DEFAULT_OUTPUT_DIR)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    # Dynamic filename generation based on dataset temporal range
    min_dt = df["datetime"].min()
    max_dt = df["datetime"].max()

    if min_dt.date() == max_dt.date():
        start_str = min_dt.strftime("%Y%m%d_%H%M")
        end_str = max_dt.strftime("%Y%m%d_%H%M")
    else:
        start_str = min_dt.strftime("%Y%m%d")
        end_str = max_dt.strftime("%Y%m%d")

    filename = f"energy_analysis_{start_str}_to_{end_str}.xlsx"
    file_path = out_dir_path / filename

    # Create Excel Writer
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        # ==========================================
        # TAB 1: EXECUTIVE SUMMARY
        # ==========================================
        # Metadata block
        meta_data = {
            "Metric": [
                "Analysis Period Start",
                "Analysis Period End",
                "Report Generation Time",
            ],
            "Value": [
                min_dt.strftime("%Y-%m-%d %H:%M:%S"),
                max_dt.strftime("%Y-%m-%d %H:%M:%S"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ],
        }
        df_meta = pd.DataFrame(meta_data)
        df_meta.to_excel(writer, sheet_name="Executive Summary", startrow=1, index=False)

        # Market Volume Block
        if market_volume_stats:
            volume_data = {
                "Market Indicator": [
                    "Total Traded Volume (M€)",
                    "Total Energy Processed (GWh)",
                    "Volume-Weighted Avg Price (VWAP)",
                    "Peak Expenditure Timestamp",
                    "Peak Hourly Cost (k€)",
                    "Peak Hour Demand (MW)",
                    "Peak Hour SPOT Price (€/MWh)",
                ],
                "Value": [
                    market_volume_stats.get("total_volume_eur", 0.0)
                    / 1_000_000,
                    market_volume_stats.get("total_energy_mwh", 0.0) / 1_000,
                    market_volume_stats.get("weighted_avg_price", 0.0),
                    str(market_volume_stats.get("peak_spend_hour", "N/A")),
                    market_volume_stats.get("peak_spend_eur", 0.0) / 1_000,
                    market_volume_stats.get("peak_spend_demand_mw", 0.0),
                    market_volume_stats.get("peak_spend_price_eur", 0.0),
                ],
            }
            df_volume = pd.DataFrame(volume_data)
            df_volume.to_excel(writer, sheet_name="Executive Summary", startrow=6, index=False)

        # Quick Indicators Overview Block
        summary_rows = []

        has_multiple_geos = False
        if "geo_name" in df.columns and not df["geo_name"].empty:
            has_multiple_geos = df["geo_name"].nunique(dropna=True) > 1

        for name, stats in demand_stats.items():
            base_name = name.split(" (")[0]
            geo_name = stats.get("geo_name", "")
            translated_name = translate_indicator(name)
            summary_rows.append(
                {
                    "Indicator": translated_name,
                    "Type": "Demand",
                    "Mean": stats.get("mean"),
                    "Max": stats.get("max"),
                    "Min": stats.get("min"),
                }
            )

        for series_label, stats in price_stats.items():
            base_name = series_label.split(" (")[0]
            geo_name = stats.get("geo_name", "")
            translated_name = translate_indicator(base_name, geo_name=geo_name, show_geo=has_multiple_geos)
            summary_rows.append(
                {
                    "Indicator": translated_name,
                    "Type": "Price",
                    "Mean": stats.get("mean"),
                    "Max": stats.get("max"),
                    "Min": stats.get("min"),
                }
            )
        if summary_rows:
            df_summary = pd.DataFrame(summary_rows)
            df_summary.to_excel(writer, sheet_name="Executive Summary", startrow=16, index=False)

        # ==========================================
        # TAB 2: STATISTICAL ANALYSIS
        # ==========================================
        # 1. Demand Statistics Table
        demand_rows = []
        for name, stats in demand_stats.items():
            translated_name = translate_indicator(name)
            demand_rows.append(
                {
                    "Indicator Name": translated_name,
                    "Mean (MW)": stats.get("mean"),
                    "Median (MW)": stats.get("median"),
                    "Std Dev (MW)": stats.get("std"),
                    "Max Value (MW)": stats.get("max"),
                    "Max Timestamp": str(stats.get("max_time", "N/A")),
                    "Min Value (MW)": stats.get("min"),
                }
            )

        df_demand_sheet = (
            pd.DataFrame(demand_rows)
            if demand_rows
            else pd.DataFrame(
                columns=[
                    "Indicator Name",
                    "Mean (MW)",
                    "Median (MW)",
                    "Std Dev (MW)",
                    "Max Value (MW)",
                    "Max Timestamp",
                    "Min Value (MW)",
                ]
            )
        )

        df_demand_sheet.to_excel(writer, sheet_name="Statistical Analysis", startrow=1, index=False)

        # 2. Price Statistics Table (placed below Demand Table)
        price_rows = []
        for series_label, stats in price_stats.items():
            base_name = series_label.split(" (")[0]
            geo_name = stats.get("geo_name", "")
            translated_name = translate_indicator(base_name, geo_name=geo_name, show_geo=has_multiple_geos)
            price_rows.append(
                {
                    "Indicator Name": translated_name,
                    "Max (€/MWh)": stats.get("max"),
                    "Max Timestamp": str(stats.get("max_time", "N/A")),
                    "Min (€/MWh)": stats.get("min"),
                    "Min Timestamp": str(stats.get("min_time", "N/A")),
                    "Spread (€/MWh)": stats.get("spread"),
                    "Low Price Hours (<=5€)": stats.get("zero_low_hours"),
                }
            )

        df_price_sheet = (
            pd.DataFrame(price_rows)
            if price_rows
            else pd.DataFrame(
                columns=[
                    "Indicator Name",
                    "Max (€/MWh)",
                    "Max Timestamp",
                    "Min (€/MWh)",
                    "Min Timestamp",
                    "Spread (€/MWh)",
                    "Low Price Hours (<=5€)",
                ]
            )
        )

        # Start row dynamically based on the length of demand table + padding
        start_row_price = len(df_demand_sheet) + 4
        df_price_sheet.to_excel(writer, sheet_name="Statistical Analysis", startrow=start_row_price, index=False)

        # ==========================================
        # TAB 3: MODELS & ANOMALIES
        # ==========================================
        # 1. Model Comparison Metrics
        comp_rows = []
        if comp_stats:
            comp_rows.append(
                {
                    "Baseline Series": translate_indicator(comp_stats.get("series_1", "")),
                    "Target Series": translate_indicator(comp_stats.get("series_2", "")),
                    "MAPE (%)": comp_stats.get("mape"),
                    "Pearson Correlation (r)": comp_stats.get(
                        "pearson_correlation"
                    ),
                    "Mean Difference (MW)": comp_stats.get("mean_difference"),
                    "Max Absolute Delta (MW)": comp_stats.get("max_delta"),
                }
            )

        df_comp_sheet = (
            pd.DataFrame(comp_rows)
            if comp_rows
            else pd.DataFrame(
                columns=[
                    "Baseline Series",
                    "Target Series",
                    "MAPE (%)",
                    "Pearson Correlation (r)",
                    "Mean Difference (MW)",
                    "Max Absolute Delta (MW)",
                ]
            )
        )

        df_comp_sheet.to_excel(writer, sheet_name="Models & Anomalies", startrow=1, index=False)

        # 2. Anomalies Table (placed below Model Comparison)
        anomaly_rows = []
        if anomalies and "anomaly_records" in anomalies:
            for rec in anomalies["anomaly_records"]:
                anomaly_rows.append(
                    {
                        "Timestamp": str(rec.get("datetime")),
                        "Indicator Name": translate_indicator(rec.get("indicator", "")),
                        "Observed Value (MW)": rec.get("value"),
                        "Series Mean (MW)": rec.get("mean"),
                        "Series Std Dev": rec.get("std"),
                        "Z-Score": rec.get("z_score"),
                        "Anomaly Type": rec.get("type"),
                    }
                )

        df_anomaly_sheet = (
            pd.DataFrame(anomaly_rows)
            if anomaly_rows
            else pd.DataFrame(
                columns=[
                    "Timestamp",
                    "Indicator Name",
                    "Observed Value (MW)",
                    "Series Mean (MW)",
                    "Series Std Dev",
                    "Z-Score",
                    "Anomaly Type",
                ]
            )
        )

        start_row_anom = len(df_comp_sheet) + 4
        df_anomaly_sheet.to_excel(writer, sheet_name="Models & Anomalies", startrow=start_row_anom, index=False)

        # ==========================================
        # TAB 4: CLEAN DATA
        # ==========================================
        df_clean = df.copy()
        df_clean["datetime"] = df_clean["datetime"].astype(str)
        df_clean.to_excel(writer, sheet_name="Clean Data", index=False)

        pass

    # Apply global styles from openpyxl (column widths, colors, formats)
    _apply_workbook_styles(file_path)

    return str(file_path)