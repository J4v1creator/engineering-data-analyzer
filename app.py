"""Streamlit web interface for the energy demand and market price analysis pipeline."""

from datetime import date, datetime, timedelta
import os

import pandas as pd
import streamlit as st

# Local Module Imports
from config.settings import DEMAND_INDICATOR_IDS, PRICE_INDICATOR_IDS
from src.analyzer import (
    calculate_demand_statistics,
    calculate_market_economic_volume,
    calculate_price_statistics,
    compare_demand_models,
    detect_demand_anomalies,
)
from src.cleaner import clean_expired_cache
from src.database import init_db
from src.esios_client import get_energy_data
from src.exporter import export_to_excel
from src.pdf_reporter import generate_pdf_report
from src.text_reporter import generate_text_report
from src.utils import sort_indicators_by_priority, translate_indicator
from src.validator import validate_dataset
from src.visualizer import plot_energy_demand, plot_energy_price

# ------------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & SYSTEM INITIALIZATION
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Engineering Data Analyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def setup_system() -> None:
    """Initialize database schemas and perform cache cleanup at startup."""
    init_db()
    clean_expired_cache()


# Run once per session startup
setup_system()


# ------------------------------------------------------------------------------
# 2. HELPER FUNCTIONS FOR COMPONENT RENDERING
# ------------------------------------------------------------------------------
def render_html_chart(html_path: str | None, height: int = 500) -> None:
    """Safely reads and renders an HTML chart artifact inside a Streamlit component.

    Args:
        html_path (str | None): Path to the HTML file to render.
        height (int): Height of the rendered component in pixels.
    """
    if html_path and os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            st.components.v1.html(f.read(), height=height, scrolling=True)
    else:
        st.warning("⚠️ Interactive visualization artifact is missing or unavailable.")


def render_demand_tab(data: dict) -> None:
    """Renders the Demand Analytics tab content.

    Args:
        data (dict): Dictionary containing the data for demand analytics.
    """
    df_demands: pd.DataFrame = data["df_demands"]
    demand_stats: dict = data["demand_stats"]
    comparison_results: dict | None = data.get("comp_stats")

    if df_demands.empty:
        st.info("No demand indicators were selected or available for this period.")
        return

    st.subheader("Key Demand Metrics")
    cols = st.columns(len(demand_stats)) if demand_stats else []

    for idx, (ind_key, stats) in enumerate(demand_stats.items()):
        with cols[idx]:
            raw_name = stats.get("name", str(ind_key))
            st.metric(
                label=raw_name,
                value=f"{stats.get('mean', 0):,.2f} MW",
                delta=f"Peak: {stats.get('max', 0):,.2f} MW",
                help="Main value displays Average Demand (Mean)",
            )

    # Progressive Disclosure: Complete Statistical Breakdown
    with st.expander("📋 View Complete Demand Statistics Table"):
        stats_demand_df = pd.DataFrame(demand_stats).T
        st.dataframe(stats_demand_df, use_container_width=True)

    st.divider()

    # Model Comparison Sub-section
    if comparison_results:
        st.subheader("📐 Model Comparison Analytics")

        baseline_id = comparison_results.get("baseline_id", "Baseline")
        target_id = comparison_results.get("target_id", "Model")

        baseline_name = translate_indicator(indicator_id=baseline_id)
        target_name = translate_indicator(indicator_id=target_id)

        st.caption(f"Comparing candidate model **{target_name}** against reference target **{baseline_name}**.")

        comp_col1, comp_col2, comp_col3, comp_col4 = st.columns(4)

        with comp_col1:
            st.metric(
                label="MAPE (Mean Abs. % Error)",
                value=f"{comparison_results.get('mape', 0.0):.2f} %",
                help="Lower is better. Measures average forecasting percentage error.",
            )
        with comp_col2:
            st.metric(
                label="Pearson Correlation (r)",
                value=f"{comparison_results.get('correlation', 0.0):.4f}",
                help="Closer to 1.0 indicates stronger linear alignment.",
            )
        with comp_col3:
            st.metric(
                label="Mean Difference",
                value=f"{comparison_results.get('mean_difference', 0.0):,.2f} MW",
                help="Main value displays average bias (Baseline - Target).",
            )
        with comp_col4:
            st.metric(
                label="Max Deviation",
                value=f"{comparison_results.get('max_difference_value', 0.0):,.2f} MW",
                delta=f"At: {comparison_results.get('max_difference_time', 'N/A')}",
                delta_color="off",
                help="Largest single-hour deviation between baseline and model.",
            )

        st.divider()

    st.subheader("Interactive Demand Time-Series")
    demand_paths = plot_energy_demand(df_demands)
    render_html_chart(demand_paths.get("html"))


def render_price_tab(data: dict) -> None:
    """Renders the Price Analytics tab content.

    Args:
        data (dict): Dictionary containing the data for price analytics.
    """
    df_prices: pd.DataFrame = data["df_prices"]
    price_stats: dict = data["price_stats"]

    if df_prices.empty:
        st.info("No price indicators were selected or available for this period.")
        return

    st.subheader("Key Price Metrics")
    cols = st.columns(len(price_stats)) if price_stats else []

    for idx, (ind_key, stats) in enumerate(price_stats.items()):
        with cols[idx]:
            raw_name = stats.get("name", str(ind_key))
            st.metric(
                label=raw_name,
                value=f"{stats.get('max', 0):,.2f} €/MWh",
                delta=f"Low Price: {stats.get('zero_low_price_hours', 0)} hrs",
                help="Main value displays Peak Price (Maximum)",
            )

    # Progressive Disclosure: Complete Statistical Breakdown
    with st.expander("📋 View Complete Price Statistics Table"):
        stats_price_df = pd.DataFrame(price_stats).T
        st.dataframe(stats_price_df, use_container_width=True)

    st.divider()

    st.subheader("Interactive Price Time-Series")
    price_paths = plot_energy_price(df_prices)
    render_html_chart(price_paths.get("html"))


def render_volume_and_anomalies_tab(data: dict) -> None:
    """Renders the Market Volume & Anomaly Detection tab content.

    Args:
        data (dict): Dictionary containing the data for market volume and anomalies.
    """
    vol_stats: dict = data.get("market_volume_stats", {})
    anomalies: list[dict] = data.get("anomalies", [])

    col_v1, col_v2 = st.columns(2)

    with col_v1:
        st.subheader("💰 Wholesale Market Economic Volume")
        if vol_stats:
            st.metric("Total Market Value", f"{vol_stats.get('total_volume_eur', 0):,.2f} M€")
            st.metric("Volume-Weighted Average Price (VWAP)", f"{vol_stats.get('weighted_avg_price', 0):,.2f} €/MWh")
            st.metric("Total Traded Energy", f"{vol_stats.get('total_energy_mwh', 0):,.2f} GWh")
        else:
            st.info("Market volume requires both Real Demand and Spot Market Price to be selected.")

    with col_v2:
        st.subheader("⚠️ Detected Demand Anomalies (Z-Score > 2.0)")
        if anomalies:
            df_anomalies = pd.DataFrame(anomalies)
            st.dataframe(df_anomalies, use_container_width=True, hide_index=True)
        else:
            st.success("No statistical demand anomalies detected in this timeframe.")


def render_reports_tab(data: dict) -> None:
    """Renders the Export & Download Artifacts tab content.

    Args:
        data (dict): Dictionary containing the paths to generated report artifacts.
    """
    st.subheader("📦 Download Generated Artifacts")
    st.write("Export production-grade reports and datasets directly from the interface:")

    col_d1, col_d2, col_d3 = st.columns(3)

    artifacts = [
        (col_d1, "excel_path", "📊 Download Excel Workbook", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        (col_d2, "pdf_path", "📕 Download Executive PDF Report", "application/pdf"),
        (col_d3, "report_path", "📄 Download Plain Text Summary", "text/plain"),
    ]

    for col, key, label, mime_type in artifacts:
        file_path = data.get(key)
        if file_path and os.path.exists(file_path):
            with col:
                with open(file_path, "rb") as f:
                    st.download_button(
                        label=label,
                        data=f.read(),
                        file_name=os.path.basename(file_path),
                        mime=mime_type,
                        use_container_width=True,
                    )


# ------------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS & CONTROLLER LOGIC
# ------------------------------------------------------------------------------
st.title("⚡ Engineering Data Analyzer")
st.caption("Interactive web interface for Red Eléctrica de España (e·sios) energy analytics")

st.sidebar.header("⚙️ Analysis Parameters")

# Date & Time Pickers
today = date.today()
default_start = today - timedelta(days=7)

col_date1, col_date2 = st.sidebar.columns(2)
with col_date1:
    start_date = st.date_input("Start Date", value=default_start)
    start_time = st.time_input("Start Time", value=datetime.min.time())
with col_date2:
    end_date = st.date_input("End Date", value=today)
    end_time = st.time_input("End Time", value=datetime.max.time().replace(microsecond=0))

start_dt = datetime.combine(start_date, start_time)
end_dt = datetime.combine(end_date, end_time)

st.sidebar.divider()

# Indicator Selection
st.sidebar.subheader("📊 Select Indicators")

demand_options = {translate_indicator(ind_id): ind_id for ind_id in DEMAND_INDICATOR_IDS}
price_options = {translate_indicator(ind_id): ind_id for ind_id in PRICE_INDICATOR_IDS}

selected_demand_names = st.sidebar.multiselect("Energy Demand Indicators", options=list(demand_options.keys()))
selected_price_names = st.sidebar.multiselect("Energy Price Indicators", options=list(price_options.keys()))

selected_demands = [demand_options[name] for name in selected_demand_names]
selected_prices = [price_options[name] for name in selected_price_names]

# Maintain priority ordering
selected_demands = sort_indicators_by_priority(selected_demands, DEMAND_INDICATOR_IDS)
selected_prices = sort_indicators_by_priority(selected_prices, PRICE_INDICATOR_IDS)

# Model Comparison Config
comparison_targets: tuple[int, int] | None = None

if len(selected_demands) >= 2:
    st.sidebar.divider()
    st.sidebar.subheader("📐 Model Comparison Settings")

    ordered_demand_ids = sort_indicators_by_priority(selected_demands, DEMAND_INDICATOR_IDS)
    ordered_demand_names = [translate_indicator(ind_id) for ind_id in ordered_demand_ids]

    blank_option = "-- Select Demand --"
    options_with_blank = [blank_option] + ordered_demand_names

    baseline_name = st.sidebar.selectbox("Baseline Target", options=options_with_blank, index=0)
    remaining_options = [name for name in ordered_demand_names if name != baseline_name]
    comparison_options = [blank_option] + remaining_options

    model_name = st.sidebar.selectbox("Comparison Model", options=comparison_options, index=0)

    if baseline_name != blank_option and model_name != blank_option:
        comparison_targets = (demand_options[baseline_name], demand_options[model_name])
    elif baseline_name != blank_option or model_name != blank_option:
        st.sidebar.warning("⚠️ Select both Baseline and Comparison Model for pairwise analytics.")

st.sidebar.divider()
run_analysis = st.sidebar.button("🚀 Run Analysis", type="primary", use_container_width=True)

# ------------------------------------------------------------------------------
# 4. PIPELINE EXECUTION
# ------------------------------------------------------------------------------
if run_analysis:
    selected_indicators = selected_demands + selected_prices

    if not selected_indicators:
        st.error("Please select at least one Demand or Price indicator to execute the pipeline.")
    else:
        with st.spinner("Fetching, validating, and calculating metrics..."):
            try:
                # 1. Ingest & Validate
                df_filtered = get_energy_data(selected_indicators, start_dt, end_dt)
                validate_dataset(df_filtered)

                # 2. Split Data
                df_demands = df_filtered[df_filtered["indicator_id"].isin(selected_demands)]
                df_prices = df_filtered[df_filtered["indicator_id"].isin(selected_prices)]

                # 3. Calculate Analytics
                demand_stats = calculate_demand_statistics(df_demands, selected_demands)
                price_stats = calculate_price_statistics(df_prices, selected_prices)
                comp_stats = compare_demand_models(df_demands, comparison_targets) if comparison_targets else None
                anomalies = detect_demand_anomalies(df_demands)
                market_volume_stats = calculate_market_economic_volume(df_filtered)

                # 4. Chart File Paths
                chart_paths = []
                if not df_demands.empty:
                    d_paths = plot_energy_demand(df_demands)
                    if d_paths.get("png"):
                        chart_paths.append(d_paths["png"])

                if not df_prices.empty:
                    p_paths = plot_energy_price(df_prices)
                    if p_paths.get("png"):
                        chart_paths.append(p_paths["png"])

                # 5. Generate Reports
                report_path = generate_text_report(df_filtered, start_dt, end_dt, demand_stats, price_stats, comp_stats, anomalies, market_volume_stats)
                excel_path = export_to_excel(df_filtered, demand_stats, price_stats, comp_stats, anomalies, market_volume_stats)
                pdf_path = generate_pdf_report(df_filtered, demand_stats, price_stats, comp_stats, anomalies, market_volume_stats, chart_paths)

                # 6. Save State
                st.session_state["data"] = {
                    "df_demands": df_demands,
                    "df_prices": df_prices,
                    "demand_stats": demand_stats,
                    "price_stats": price_stats,
                    "comp_stats": comp_stats,
                    "anomalies": anomalies,
                    "market_volume_stats": market_volume_stats,
                    "report_path": report_path,
                    "excel_path": excel_path,
                    "pdf_path": pdf_path,
                }
                st.success("Analysis executed successfully!")

            except Exception as e:
                st.error(f"Error during analysis execution: {e}")

# ------------------------------------------------------------------------------
# 5. MAIN DASHBOARD DISPLAY
# ------------------------------------------------------------------------------
if "data" in st.session_state:
    data = st.session_state["data"]

    tab_demand, tab_price, tab_volume, tab_reports = st.tabs(
        ["📈 Demand Analytics", "💶 Price Analytics", "💰 Market Volume & Anomalies", "📄 Reports & Exports"]
    )

    with tab_demand:
        render_demand_tab(data)

    with tab_price:
        render_price_tab(data)

    with tab_volume:
        render_volume_and_anomalies_tab(data)

    with tab_reports:
        render_reports_tab(data)

else:
    st.info("👈 Select your date range and indicators in the sidebar, then click **Run Analysis** to begin.")