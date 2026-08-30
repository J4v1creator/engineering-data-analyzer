"""PDF report generation module using ReportLab for energy market analytics."""

from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config.settings import (
    PDF_BG_LIGHT_COLOR,
    PDF_CHART_HEIGHT,
    PDF_CHART_WIDTH,
    PDF_MARGIN,
    PDF_PRIMARY_COLOR,
    PDF_SECONDARY_COLOR,
    REPORTS_OUTPUT_DIR,
)
from src.utils import format_mw, format_price, translate_indicator

# ----------------------------------------------------------------------
# REUSABLE GLOBAL STYLES
# ----------------------------------------------------------------------

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "ReportTitle",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=18,
    leading=22,
    textColor=colors.HexColor(PDF_PRIMARY_COLOR),
    spaceAfter=4,
)

subtitle_style = ParagraphStyle(
    "ReportSubtitle",
    parent=styles["Normal"],
    fontName="Helvetica-Oblique",
    fontSize=9,
    leading=12,
    textColor=colors.HexColor(PDF_SECONDARY_COLOR),
    spaceAfter=14,
)

h2_style = ParagraphStyle(
    "SectionHeading",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=14,
    textColor=colors.HexColor(PDF_PRIMARY_COLOR),
    spaceBefore=12,
    spaceAfter=6,
)

cell_style = ParagraphStyle(
    "TableCell",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
)

cell_bold = ParagraphStyle(
    "TableCellBold",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10,
)

cell_header = ParagraphStyle(
    "TableHeader",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10,
    textColor=colors.white,
)


def _get_table_style() -> TableStyle:
    """Returns standard corporate styling for PDF data tables."""
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PDF_PRIMARY_COLOR)),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D3D3")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(PDF_BG_LIGHT_COLOR)]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])


# ----------------------------------------------------------------------
# AUXILIARY FUNCTIONS FOR EACH SECTION
# ----------------------------------------------------------------------

def _build_metadata_section(df: pd.DataFrame, analysis_period: str) -> list:
    """Formats dataset metadata into a clean table.

    Args:
        df (pd.DataFrame): Validated dataset.
        analysis_period (str): Human-readable description of the analysis period.

    Returns:
        list: ReportLab flowable elements containing the formatted metadata section.
    """
    elements = [Paragraph("1. DATASET METADATA", h2_style)]
    
    num_rows, num_cols = df.shape
    column_names = ", ".join(df.columns)

    data = [
        [Paragraph("Metric", cell_header), Paragraph("Details", cell_header)],
        [Paragraph("Total Records (Rows)", cell_bold), Paragraph(str(num_rows), cell_style)],
        [Paragraph("Total Attributes (Cols)", cell_bold), Paragraph(str(num_cols), cell_style)],
        [Paragraph("Available Columns", cell_bold), Paragraph(column_names, cell_style)],
        [Paragraph("Analysis Period", cell_bold), Paragraph(analysis_period, cell_style)],
        [Paragraph("Data Provider", cell_bold), Paragraph("Red Eléctrica de España (REE / e·sios)", cell_style)],
    ]

    # Ancho total imprimible en A4 con margen de 36pt es aprox 523pt
    table = Table(data, colWidths=[140, 383])
    table.setStyle(_get_table_style())
    elements.extend([table, Spacer(1, 10)])
    return elements


def _build_demand_section(demand_stats: dict) -> list:
    """Formats demand statistics into a structured table.

    Args:
        demand_stats (dict): Dictionary containing statistical metrics for each energy demand series or indicator.

    Returns:
        list: ReportLab flowable elements containing the formatted energy demand statistics section.
    """
    elements = [Paragraph("2. STATISTICAL SUMMARY: ENERGY DEMAND (MW)", h2_style)]
    
    if not demand_stats:
        elements.extend([
            Paragraph("No demand indicators were selected for this run.", cell_style),
            Spacer(1, 10),
        ])
        return elements

    data = [[
        Paragraph("Series / Indicator", cell_header),
        Paragraph("Max Demand", cell_header),
        Paragraph("Min Demand", cell_header),
        Paragraph("Mean", cell_header),
        Paragraph("Median", cell_header),
        Paragraph("Std Dev", cell_header),
    ]]

    for series_label, metrics in demand_stats.items():
        peak_info = f"{format_mw(metrics['max'])}<br/><font size=6 color='gray'>({metrics['peak_time']})</font>"
        data.append([
            Paragraph(str(series_label), cell_bold),
            Paragraph(peak_info, cell_style),
            Paragraph(format_mw(metrics["min"]), cell_style),
            Paragraph(format_mw(metrics["mean"]), cell_style),
            Paragraph(format_mw(metrics["median"]), cell_style),
            Paragraph(format_mw(metrics["std_dev"]), cell_style),
        ])

    table = Table(data, colWidths=[153, 110, 65, 65, 65, 65])
    table.setStyle(_get_table_style())
    elements.extend([table, Spacer(1, 10)])
    return elements


def _build_price_section(price_stats: dict) -> list:
    """Formats price statistics into a structured table.

    Args:
        price_stats (dict): Dictionary containing statistical metrics for each energy price series or indicator.

    Returns:
        list: ReportLab flowable elements containing the formatted energy price statistics section.
    """
    elements = [Paragraph("3. STATISTICAL SUMMARY: ENERGY PRICES (€/MWh)", h2_style)]
    
    if not price_stats:
        elements.extend([
            Paragraph("No price indicators were selected for this run.", cell_style),
            Spacer(1, 10),
        ])
        return elements

    data = [[
        Paragraph("Series / Indicator", cell_header),
        Paragraph("Max Price", cell_header),
        Paragraph("Min Price", cell_header),
        Paragraph("Daily Spread", cell_header),
        Paragraph("Low Hours (<=5.0)", cell_header),
    ]]

    for series_label, metrics in price_stats.items():
        max_info = f"{format_price(metrics['max'])}<br/><font size=6 color='gray'>({metrics['max_time']})</font>"
        min_info = f"{format_price(metrics['min'])}<br/><font size=6 color='gray'>({metrics['min_time']})</font>"
        
        data.append([
            Paragraph(str(series_label), cell_bold),
            Paragraph(max_info, cell_style),
            Paragraph(min_info, cell_style),
            Paragraph(format_price(metrics["spread"]), cell_style),
            Paragraph(f"{metrics['zero_low_price_hours']} h", cell_style),
        ])

    table = Table(data, colWidths=[153, 100, 100, 90, 80])
    table.setStyle(_get_table_style())
    elements.extend([table, Spacer(1, 10)])
    return elements


def _build_comparison_section(comp_stats: dict | None) -> list:
    """Formats advanced model comparison into a key-value grid.

    Args:
        comp_stats (dict | None): Dictionary containing the statistical results of the demand model comparison, or None if no comparison was performed.

    Returns:
        list: ReportLab flowable elements containing the formatted demand model comparison section.
    """
    elements = [Paragraph("4. ADVANCED MODEL COMPARISON (DEMANDS ONLY)", h2_style)]
    
    if not comp_stats:
        elements.extend([
            Paragraph("No demand indicators were selected for cross-analysis in this run.", cell_style),
            Spacer(1, 10),
        ])
        return elements

    model_a = comp_stats.get("model_a")
    model_b = comp_stats.get("model_b")
    model_a_en = translate_indicator(indicator_id=model_a) if isinstance(model_a, int) else str(model_a)
    model_b_en = translate_indicator(indicator_id=model_b) if isinstance(model_b, int) else str(model_b)

    data = [
        [Paragraph("Comparison Metric", cell_header), Paragraph("Value / Info", cell_header)],
        [Paragraph("Baseline Model (A)", cell_bold), Paragraph(model_a_en, cell_style)],
        [Paragraph("Target Model (B)", cell_bold), Paragraph(model_b_en, cell_style)],
        [Paragraph("Mean Difference (A - B)", cell_bold), Paragraph(format_mw(comp_stats["mean_difference"]), cell_style)],
        [
            Paragraph("Max Absolute Deviation", cell_bold),
            Paragraph(
                f"{format_mw(abs(comp_stats['max_difference_value']))} "
                f"<font size=6 color='gray'>(At {comp_stats['max_difference_time']})</font>",
                cell_style,
            ),
        ],
        [Paragraph("Mean Absolute Pct Error (MAPE)", cell_bold), Paragraph(f"{comp_stats['mape']:.2f}%", cell_style)],
        [Paragraph("Pearson Correlation (r)", cell_bold), Paragraph(f"{comp_stats['correlation']:.4f}", cell_style)],
    ]

    table = Table(data, colWidths=[180, 343])
    table.setStyle(_get_table_style())
    elements.extend([table, Spacer(1, 10)])
    return elements


def _build_anomalies_section(anomalies: dict | None) -> list:
    """Formats detected anomalies into a table for the PDF.

    Args:
        anomalies (dict | None): Dictionary containing detected anomaly events grouped by series label.

    Returns:
        list: Flowable elements (Paragraphs, Tables, Spacers) for the PDF story.
    """
    elements = [Paragraph("5. STATISTICAL ANOMALY DETECTION (Z-SCORE > 2.0)", h2_style)]
    
    rows = []
    if anomalies and isinstance(anomalies, dict):
        for series_label, issues in anomalies.items():
            for issue in issues:
                rows.append([
                    Paragraph(str(series_label), cell_bold),
                    Paragraph(issue["type"], cell_style),
                    Paragraph(str(issue["datetime"]), cell_style),
                    Paragraph(format_mw(issue["value"]), cell_style),
                    Paragraph(format_mw(issue["deviation"]), cell_style),
                ])

    if not rows:
        elements.extend([
            Paragraph("No statistical anomalies detected in energy demand data.", cell_style),
            Spacer(1, 10),
        ])
        return elements

    data = [[
        Paragraph("Series", cell_header),
        Paragraph("Type", cell_header),
        Paragraph("Timestamp", cell_header),
        Paragraph("Observed Value", cell_header),
        Paragraph("Deviation", cell_header),
    ]] + rows

    table = Table(data, colWidths=[133, 80, 110, 100, 100])
    table.setStyle(_get_table_style())
    elements.extend([table, Spacer(1, 10)])
    return elements


def _build_volume_section(market_volume_stats: dict | None) -> list:
    """Formats market volume and economic assessment.

    Args:
        market_volume_stats (dict | None): Dictionary containing market volume
            and economic indicators calculated from demand and SPOT price data,
            or None if the analysis could not be performed.

    Returns:
        list: ReportLab flowable elements containing the formatted market volume and economic analysis section.
    """
    elements = [Paragraph("6. MARKET ECONOMIC VOLUME ANALYSIS (DEMAND × SPOT PRICE)", h2_style)]
    
    if not market_volume_stats:
        elements.extend([
            Paragraph("Market economic volume assessment skipped (insufficient matching data).", cell_style),
            Spacer(1, 10),
        ])
        return elements

    total_m_eur = market_volume_stats["total_volume_eur"] / 1_000_000
    total_gwh = market_volume_stats["total_energy_mwh"] / 1_000
    vwap = market_volume_stats["weighted_avg_price"]
    peak_spend_eur = market_volume_stats["peak_spend_eur"] / 1_000

    data = [
        [Paragraph("Volume Metric", cell_header), Paragraph("Calculated Value", cell_header)],
        [Paragraph("Total Traded Volume", cell_bold), Paragraph(f"{total_m_eur:.2f} M€", cell_style)],
        [Paragraph("Total Energy Processed", cell_bold), Paragraph(f"{total_gwh:.2f} GWh", cell_style)],
        [Paragraph("Volume-Weighted Avg Price (VWAP)", cell_bold), Paragraph(format_price(vwap), cell_style)],
        [
            Paragraph("Peak Expenditure Hour", cell_bold),
            Paragraph(
                f"{market_volume_stats['peak_spend_hour']}<br/>"
                f"↳ Cost: <b>{peak_spend_eur:.2f} k€</b> | Demand: <b>{format_mw(market_volume_stats['peak_spend_demand_mw'])}</b> | Price: <b>{format_price(market_volume_stats['peak_spend_price_eur'])}</b>",
                cell_style,
            ),
        ],
    ]

    table = Table(data, colWidths=[180, 343])
    table.setStyle(_get_table_style())
    elements.extend([table, Spacer(1, 10)])
    return elements


# ----------------------------------------------------------------------
# MAIN EXPORT FUNCTION
# ----------------------------------------------------------------------

def generate_pdf_report(
    df: pd.DataFrame,
    demand_stats: dict,
    price_stats: dict,
    comp_stats: dict | None = None,
    anomalies: dict | None = None,
    market_volume_stats: dict | None = None,
    chart_paths: list[str | Path] | None = None,
    output_dir: str | Path = REPORTS_OUTPUT_DIR,
) -> str:
    """Generates a complete, styled PDF report including tables, statistics, and charts.

    Args:
        df (pd.DataFrame): DataFrame containing the validated energy market data.
        demand_stats (dict): Statistical indicators calculated for energy demand.
        price_stats (dict): Statistical indicators calculated for energy prices.
        comp_stats (dict | None): Demand model comparison statistics, or None if no model comparison was performed.
        anomalies (dict | None): Detected statistical anomalies and outliers, or None if no anomalies were detected.
        market_volume_stats (dict | None): Market volume and economic indicators, or None if the analysis could not be performed.
        chart_paths (list[str | Path] | None): Paths to generated chart files to include in the report, or None if no charts should be included.
        output_dir (str | Path): Directory where the generated PDF report will be saved.

    Returns:
        str: Full path to the generated PDF report.

    Raises:
        RuntimeError: If the PDF report cannot be generated successfully.
    """
    print("\n📄 Generating automated PDF report...")

    out_dir_path = Path(output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    min_dt, max_dt = df["datetime"].min(), df["datetime"].max()
    fmt = "%Y%m%d_%H%M" if min_dt.date() == max_dt.date() else "%Y%m%d"
    filename = f"report_energy_analysis_{min_dt.strftime(fmt)}_to_{max_dt.strftime(fmt)}.pdf"
    file_path = out_dir_path / filename

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=PDF_MARGIN,
        leftMargin=PDF_MARGIN,
        topMargin=PDF_MARGIN,
        bottomMargin=PDF_MARGIN,
    )

    story = []

    # 1. Main Header
    story.append(Paragraph("ENERGY MARKET & DEMAND ANALYSIS REPORT", title_style))
    analysis_period = f"{min_dt.strftime('%Y-%m-%d %H:%M')} to {max_dt.strftime('%Y-%m-%d %H:%M')}"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Analysis Period: {analysis_period} | Generated: {current_time}", subtitle_style))

    # 2. Sections with Data Tables
    story.extend(_build_metadata_section(df, analysis_period))
    story.extend(_build_demand_section(demand_stats))
    story.extend(_build_price_section(price_stats))
    story.extend(_build_comparison_section(comp_stats))
    story.extend(_build_anomalies_section(anomalies))
    story.extend(_build_volume_section(market_volume_stats))

    # 3. Integrated Charts Section
    if chart_paths:
        story.append(Paragraph("7. VISUAL ANALYTICS & CHARTS", h2_style))
        for path in chart_paths:
            chart_file = Path(path)
            if chart_file.exists():
                story.append(Image(str(chart_file), width=PDF_CHART_WIDTH, height=PDF_CHART_HEIGHT))
                story.append(Spacer(1, 10))

    try:
        doc.build(story)
        print(f"✅ PDF report successfully saved to: '{file_path}'")
        return str(file_path)
    except Exception as e:
        raise RuntimeError(f"Failed to generate PDF report: {e}") from e