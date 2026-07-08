import sys
import os
import io
import pandas as pd
import streamlit as st

# ── Path setup ─────────────────────────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_cleaning import clean_data
from src.analysis import (
    get_kpi_summary, get_monthly_revenue, get_revenue_by_hour,
    get_revenue_by_day_of_week, get_top_products, get_worst_products,
    get_product_return_rate, get_country_performance,
    get_customer_lifetime_value, get_new_vs_returning_customers,
    get_churned_customers, get_return_summary,
)
from src.recommendation_engine import compute_rfm, get_segment_summary, generate_recommendations
from src.export_utils import generate_excel_report
from src.visualisations import (
    plot_monthly_revenue, plot_revenue_by_hour, plot_revenue_by_day_of_week,
    plot_top_products, plot_product_return_rates,
    plot_rfm_segments, plot_segment_revenue_share, plot_clv_distribution,
    plot_new_vs_returning, plot_country_revenue, plot_top_countries_bar,
    format_kpi_cards,
)

# ── Required columns for validation ───────────────────────────────────
# Raw format uses 'Price' and 'Customer ID'; cleaned export uses 'UnitPrice' and 'CustomerID'
REQUIRED_COLUMNS = {'Invoice', 'StockCode', 'Description',
                    'Quantity', 'InvoiceDate', 'Country'}
# These columns have accepted aliases (raw name → cleaned name)
COLUMN_ALIASES = {
    'Price':       'UnitPrice',
    'Customer ID': 'CustomerID',
}

# ── Page config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title='Retail Analytics Platform',
    page_icon='💼',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── Inject custom CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0F1117;
    color: #EAEAEA;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A1D2E 0%, #0F1117 100%);
    border-right: 1px solid #2A2D3E;
}
[data-testid="stSidebar"] .block-container { padding-top: 2rem; }

/* Metric cards */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1E2130 0%, #252840 100%);
    border: 1px solid #2A2D3E;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    transition: transform 0.2s ease;
}
[data-testid="metric-container"]:hover { transform: translateY(-2px); }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] > div, [data-testid="stMetricValue"] p { 
    color: #6C63FF !important; 
    font-size: 1.8rem !important; 
    word-break: break-word !important;
    overflow-wrap: break-word !important;
    white-space: normal !important;
    text-overflow: unset !important;
    overflow: visible !important;
}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] > div, [data-testid="stMetricLabel"] p { 
    color: #8D99AE !important; 
    font-size: 0.85rem !important; 
    word-break: break-word !important;
    overflow-wrap: break-word !important;
    white-space: normal !important;
    text-overflow: unset !important;
    overflow: visible !important;
}

/* Section headers */
h2 { color: #6C63FF; border-bottom: 1px solid #2A2D3E; padding-bottom: 0.4rem; word-wrap: break-word; }
h3 { color: #EAEAEA; word-wrap: break-word; }

/* Upload area */
[data-testid="stFileUploader"] {
    background: #1E2130;
    border: 2px dashed #6C63FF;
    border-radius: 12px;
    padding: 1rem;
}

/* Info / warning / success boxes */
.stAlert { border-radius: 10px; word-wrap: break-word; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: #1E2130; border-radius: 10px; flex-wrap: wrap; }
.stTabs [data-baseweb="tab"]      { color: #8D99AE; white-space: normal; text-align: center; }
.stTabs [aria-selected="true"]    { color: #6C63FF !important; font-weight: 600; }

/* Recommendation cards */
.rec-card {
    background: linear-gradient(135deg, #1E2130 0%, #252840 100%);
    border-left: 4px solid #6C63FF;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: normal;
}
.rec-card.high   { border-left-color: #E71D36; }
.rec-card.medium { border-left-color: #F7931E; }
.rec-card.low    { border-left-color: #2EC4B6; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## :material/analytics: Retail Analytics")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        [":material/home: Data & Upload", ":material/analytics: Analytics Dashboard", ":material/insights: Insights & Actions"],
        label_visibility='collapsed',
    )

    st.markdown("---")
    st.caption("Online Retail Analytics Platform")
    