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
    

# ══════════════════════════════════════════════════════════════════════
# SESSION STATE — shared cleaned df across pages
# ══════════════════════════════════════════════════════════════════════

if 'df_clean' not in st.session_state:
    st.session_state['df_clean'] = None
if 'filename' not in st.session_state:
    st.session_state['filename'] = None


# ══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def validate_columns(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Check if uploaded file has the required columns.

    Accepts both raw format (Price, Customer ID) and pre-cleaned format
    (UnitPrice, CustomerID) so users can upload either version.
    """
    cols = set(df.columns)
    missing = []
    for req in REQUIRED_COLUMNS:
        alias = COLUMN_ALIASES.get(req)          # e.g. 'Price' → 'UnitPrice'
        rev_alias = {v: k for k, v in COLUMN_ALIASES.items()}.get(req)  # reverse
        if req not in cols and (alias not in cols) and (rev_alias not in cols):
            missing.append(req)
    # Check price column (Price OR UnitPrice)
    if 'Price' not in cols and 'UnitPrice' not in cols:
        missing.append('Price / UnitPrice')
    # Check customer column (Customer ID OR CustomerID)
    if 'Customer ID' not in cols and 'CustomerID' not in cols:
        missing.append('Customer ID / CustomerID')
    return len(missing) == 0, missing


def is_already_cleaned(df: pd.DataFrame) -> bool:
    """Return True if the CSV is already in the cleaned format (has Revenue & CustomerID)."""
    return 'Revenue' in df.columns and 'CustomerID' in df.columns and 'IsReturn' in df.columns


def load_and_clean(uploaded_file) -> pd.DataFrame | None:
    """Read CSV, rename columns if needed, then run clean_data() — or skip
    cleaning if the file is already in the cleaned format.
    """
    try:
        df_raw = pd.read_csv(uploaded_file, parse_dates=['InvoiceDate'])
    except Exception as e:
        st.error(f":material/cancel: Could not read file: {e}")
        return None

    ok, missing = validate_columns(df_raw)
    if not ok:
        st.error(
            f":material/cancel: **Invalid file format.** Missing required columns: `{', '.join(missing)}`\n\n"
            "Expected columns: `Invoice, StockCode, Description, Quantity, "
            "InvoiceDate, Price (or UnitPrice), Customer ID (or CustomerID), Country`"
        )
        return None

    # If the file is already cleaned (e.g. cleaned_retail_data.csv), skip re-cleaning
    if is_already_cleaned(df_raw):
        return df_raw

    # Raw file — rename Price → UnitPrice then run cleaner
    if 'Price' in df_raw.columns and 'UnitPrice' not in df_raw.columns:
        df_raw = df_raw.rename(columns={'Price': 'UnitPrice'})

    with st.spinner(":material/mop: Cleaning data..."):
        df_clean = clean_data(df_raw)

    return df_clean


def require_data() -> bool:
    """Show a prompt if no data is loaded yet. Returns True if data is ready."""
    if st.session_state['df_clean'] is None:
        st.info(":material/folder_open: Please upload a CSV file on the **:material/home: Data & Upload** page first.")
        return False
    return True


# ══════════════════════════════════════════════════════════════════════
# PAGE: DATA & UPLOAD
# ══════════════════════════════════════════════════════════════════════