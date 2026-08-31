import streamlit as st

# Page settings
st.set_page_config(
    page_title="Engineering Data Analyzer",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Engineering Data Analyzer")
st.markdown("Analytical pipeline for the ingestion, visualization, and reporting of REE data (e·sios).")

# Side menu for filters
st.sidebar.header("Selection Parameters")