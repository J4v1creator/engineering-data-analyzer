"""Excel workbook export module using Pandas and OpenPyXL for multi-sheet reporting."""

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

    Raises:
        Exception: If the workbook cannot be loaded or saved.
    """
    try:
        wb = load_workbook(file_path)
    except Exception as e:
        print(f"⚠️ Could not load workbook for styling: {e}")
        return

    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style="thin", color="D3D3D3"),
        right=Side(style="thin", color="D3D3D3"),
        top=Side(style="thin", color="D3D3D3"),
        bottom=Side(style="thin", color="D3D3D3"),
    )
    align_center = Alignment(horizontal="center", vertical="center")

    header_keywords = {
        "Metric",
        "Market Indicator",
        "Indicator",
        "Indicator Name",
        "Baseline Series",
        "Timestamp",
        "Datetime",
        "indicator_id",
        "id",
    }

    for sheet in wb.worksheets:
        sheet.views.sheetView[0].showGridLines = True

        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is not None:
                    cell.border = thin_border

                    # Header Detection Logic
                    if isinstance(cell.value, str) and (cell.row == 1 or cell.value in header_keywords):
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.alignment = align_center

                    # Number Formatting for Floats
                    elif isinstance(cell.value, float):
                        cell.number_format = "#,##0.00"

        # Auto-fit Column Widths dynamically
        for col in sheet.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)

            for cell in col:
                if cell.value is not None:
                    cell_len = len(str(cell.value))
                    if cell_len > max_len:
                        max_len = cell_len

            adjusted_width = min(max(max_len + 3, 12), 50)
            sheet.column_dimensions[col_letter].width = adjusted_width

    try:
        wb.save(file_path)
    except Exception as e:
        print(f"⚠️ Could not save styled workbook: {e}")


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
        comp_stats (dict): Statistics for comparative analysis.
        anomalies (dict): Information about detected anomalies.
        market_volume_stats (dict): Statistics for market volume analysis.

    Returns:
        str: Absolute or relative file path to the generated .xlsx file.
    """
    print("\n📊 Generating Excel workbook...")
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

        # 1.1 Metadata Block
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

        # 1.2 Market Volume Block
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
                    market_volume_stats.get("total_volume_eur", 0.0) / 1_000_000,
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

        # 1.3 Quick Indicators Overview Block
        summary_rows = []

        # Demand Series
        for series_label, stats in demand_stats.items():
            summary_rows.append(
                {
                    "Indicator": series_label,
                    "Type": "Demand",
                    "Mean": stats.get("mean"),
                    "Max": stats.get("max"),
                    "Min": stats.get("min"),
                }
            )

        # Price Series
        for series_label, stats in price_stats.items():
            summary_rows.append(
                {
                    "Indicator": series_label,
                    "Type": "Price",
                    "Mean": stats.get("mean", None),
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

        # 2.1 Demand Statistics Table
        demand_cols = [
            "Indicator Name",
            "Mean (MW)",
            "Median (MW)",
            "Std Dev (MW)",
            "Max Value (MW)",
            "Max Timestamp",
            "Min Value (MW)",
        ]
        demand_rows = [
            {
                "Indicator Name": series_label,
                "Mean (MW)": stats.get("mean"),
                "Median (MW)": stats.get("median"),
                "Std Dev (MW)": stats.get("std_dev"),
                "Max Value (MW)": stats.get("max"),
                "Max Timestamp": str(stats.get("peak_time", "N/A")),
                "Min Value (MW)": stats.get("min"),
            }
            for series_label, stats in demand_stats.items()
        ]
        df_demand_sheet = pd.DataFrame(demand_rows, columns=demand_cols)
        df_demand_sheet.to_excel(writer, sheet_name="Statistical Analysis", startrow=1, index=False)

        # 2.2 Price Statistics Table (placed below Demand Table with padding)
        price_cols = [
            "Indicator Name",
            "Max (€/MWh)",
            "Max Timestamp",
            "Min (€/MWh)",
            "Min Timestamp",
            "Spread (€/MWh)",
            "Low Price Hours (<=5€)",
        ]
        price_rows = [
            {
                "Indicator Name": series_label,
                "Max (€/MWh)": stats.get("max"),
                "Max Timestamp": str(stats.get("max_time", "N/A")),
                "Min (€/MWh)": stats.get("min"),
                "Min Timestamp": str(stats.get("min_time", "N/A")),
                "Spread (€/MWh)": stats.get("spread"),
                "Low Price Hours (<=5€)": stats.get("zero_low_price_hours"),
            }
            for series_label, stats in price_stats.items()
        ]
        df_price_sheet = pd.DataFrame(price_rows, columns=price_cols)

        # Dynamic start row based on Demand Table height + padding space
        start_row_price = len(df_demand_sheet) + 4
        df_price_sheet.to_excel(writer, sheet_name="Statistical Analysis", startrow=start_row_price, index=False)

        # ==========================================
        # TAB 3: MODELS & ANOMALIES
        # ==========================================

        # 3.1 Model Comparison Metrics
        comp_cols = [
            "Baseline Series",
            "Target Series",
            "MAPE (%)",
            "Pearson Correlation (r)",
            "Mean Difference (MW)",
            "Max Difference (MW)",
            "Max Difference Timestamp",
        ]
        comp_rows = []
        if comp_stats:
            model_a_id = comp_stats.get("model_a")
            model_b_id = comp_stats.get("model_b")

            model_a_name = translate_indicator(indicator_id=model_a_id) if isinstance(model_a_id, int) else str(model_a_id)
            model_b_name = translate_indicator(indicator_id=model_b_id) if isinstance(model_b_id, int) else str(model_b_id)

            comp_rows.append(
                {
                    "Baseline Series": model_a_name,
                    "Target Series": model_b_name,
                    "MAPE (%)": comp_stats.get("mape"),
                    "Pearson Correlation (r)": comp_stats.get("correlation"),
                    "Mean Difference (MW)": comp_stats.get("mean_difference"),
                    "Max Difference (MW)": comp_stats.get("max_difference_value"),
                    "Max Difference Timestamp": str(comp_stats.get("max_difference_time", "N/A")),
                }
            )

        df_comp_sheet = pd.DataFrame(comp_rows, columns=comp_cols)
        df_comp_sheet.to_excel(writer, sheet_name="Models & Anomalies", startrow=1, index=False)

        # 3.2 Anomalies Table (placed below Model Comparison with padding)
        anomaly_cols = [
            "Timestamp",
            "Indicator",
            "Observed Value (MW)",
            "Deviation",
            "Anomaly Type",
        ]
        anomaly_rows = []
        if anomalies and isinstance(anomalies, dict):
            for series_label, rec_list in anomalies.items():
                for rec in rec_list:
                    anomaly_rows.append(
                        {
                            "Timestamp": str(rec.get("datetime")),
                            "Indicator": series_label,
                            "Observed Value (MW)": rec.get("value"),
                            "Deviation": rec.get("deviation"),
                            "Anomaly Type": rec.get("type"),
                        }
                    )

        df_anomaly_sheet = pd.DataFrame(anomaly_rows, columns=anomaly_cols)

        # Dynamic start row based on Model Comparison Table height + padding space
        start_row_anom = len(df_comp_sheet) + 4
        df_anomaly_sheet.to_excel(writer, sheet_name="Models & Anomalies", startrow=start_row_anom, index=False)

        # ==========================================
        # TAB 4: CLEAN DATA
        # ==========================================
        df_clean = df.copy()

        # 1. Format datetime to standard ISO readable string
        if "datetime" in df_clean.columns:
            df_clean["datetime"] = pd.to_datetime(df_clean["datetime"]).dt.strftime("%Y-%m-%d %H:%M:%S")

        # 2. Translate indicator name cleanly
        if "indicator_id" in df_clean.columns:
            df_clean["name"] = df_clean["indicator_id"].map(lambda x: translate_indicator(indicator_id=x))

        # 3. Select and reorder desired columns for the raw data export
        cols_to_keep = ["indicator_id", "name", "geo_id", "geo_name", "datetime", "value"]
        df_export = df_clean[[col for col in cols_to_keep if col in df_clean.columns]]

        # 4. Export to Excel sheet
        df_export.to_excel(writer, sheet_name="Clean Data", index=False)

    # Apply global openpyxl styles (headers, fonts, fills, alignments, auto-width)
    _apply_workbook_styles(file_path)

    print(f"✅ Excel report successfully exported to: '{file_path}'")
    return str(file_path)