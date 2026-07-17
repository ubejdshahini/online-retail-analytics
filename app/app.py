import sys
import os
from html import escape

import pandas as pd
import streamlit as st

# Path setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



from src.about_page import render_about_page
from src.theme import css_variables
from src.visualisations import (
    plot_monthly_revenue, plot_monthly_product_revenue,
    plot_revenue_by_hour, plot_revenue_by_day_of_week,
    plot_top_products, plot_product_return_rates,
    plot_rfm_segments, plot_segment_revenue_share,
    #plot_clv_distribution,
    #plot_new_vs_returning, 
    plot_country_revenue, plot_top_countries_bar,
    format_kpi_cards,
    plot_return_rate_over_time, plot_returns_revenue_impact,
)
from src.export_utils import generate_excel_report
from src.recommendation_engine import compute_rfm, get_segment_summary, generate_recommendations
from src.analysis import (
    get_kpi_summary, get_monthly_revenue, get_monthly_product_revenue,
    get_revenue_by_hour,
    get_revenue_by_day_of_week, get_top_products, get_worst_products,
    get_product_return_rate, get_country_performance,
    #get_customer_lifetime_value, #get_new_vs_returning_customers,
    #get_churned_customers, 
    get_return_summary,
    get_return_rate_over_time, get_returns_revenue_impact,
)
from src.data_cleaning import clean_data, validate_data, add_product_flag


# Required columns for validation
REQUIRED_COLUMNS = {'Invoice', 'StockCode', 'Description',
                    'Quantity', 'InvoiceDate', 'Country'}
COLUMN_ALIASES = {
    'Price':       'UnitPrice',
    'Customer ID': 'CustomerID',
}

# Page config
st.set_page_config(
    page_title='Retail Analytics Platform',
    page_icon=':material/analytics:',
    layout='wide',
    initial_sidebar_state='expanded',
)

# Inject custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
:root {
    __THEME_CSS_VARIABLES__
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: var(--color-page-bg);
    color: var(--color-text-primary);
}
[data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: var(--color-page-bg);
    color: var(--color-text-primary);
}
ui-label, p, label, [data-testid="stCaptionContainer"] { color: var(--color-text-secondary); }

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--color-card-bg);
    border-right: 1px solid var(--color-border);
}
[data-testid="stSidebar"] .block-container { padding-top: 2rem; }

/* Metric cards */
[data-testid="metric-container"] {
    background: var(--color-card-bg);
    border: 1px solid var(--color-border);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    transition: transform 0.2s ease;
}
[data-testid="metric-container"]:hover { transform: translateY(-2px); }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] > div, [data-testid="stMetricValue"] p {
    color: var(--color-accent) !important;
    font-size: 1.8rem !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
    white-space: normal !important;
    text-overflow: unset !important;
    overflow: visible !important;
}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] > div, [data-testid="stMetricLabel"] p {
    color: var(--color-text-secondary) !important;
    font-size: 0.85rem !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
    white-space: normal !important;
    text-overflow: unset !important;
    overflow: visible !important;
}

/* Card-like borders for visualizations */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: var(--color-card-bg);
    border: 1px solid var(--color-border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

/* Section headers */
h2 { color: var(--color-accent); border-bottom: 1px solid var(--color-border); padding-bottom: 0.4rem; word-wrap: break-word; }
h3 { color: var(--color-text-primary); word-wrap: break-word; margin-top: 0px !important; margin-bottom: 8px !important; }

/* Filter Label styling */
.filter-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--color-text-secondary);
    margin-bottom: 4px;
}

/* Upload area */
[data-testid="stFileUploader"] {
    background: var(--color-card-bg);
    border: 2px dashed var(--color-accent);
    border-radius: 12px;
    padding: 1rem;
}
[data-testid="stFileUploaderDropzone"] {
    background: var(--color-card-bg);
    border-color: var(--color-border);
}
[data-testid="stFileUploaderDropzone"] button {
    background: var(--color-page-bg);
    color: var(--color-accent);
    border-color: var(--color-border);
}

/* Info / warning / success boxes */
.stAlert { border-radius: 10px; word-wrap: break-word; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: var(--color-card-bg); border-radius: 10px; flex-wrap: wrap; }
.stTabs [data-baseweb="tab"]      { color: var(--color-text-secondary); white-space: normal; text-align: center; }
.stTabs [aria-selected="true"]    { color: var(--color-accent) !important; font-weight: 600; }

.stButton > button { background: var(--color-accent); color: var(--page-bg); border-color: var(--color-accent); }
.stButton > button p { color: var(--color-page-bg); }
.stButton > button:hover { background: var(--color-text-primary); color: var(--color-page-bg); border-color: var(--color-text-primary); }
.stButton > button:hover p { color: var(--color-page-bg); }
[data-baseweb="input"], [data-baseweb="select"] > div, textarea {
    background: var(--color-card-bg) !important;
    color: var(--color-text-primary) !important;
    border-color: var(--color-border) !important;
}
[data-baseweb="radio"] div[role="radio"] { border-color: var(--color-border); }
[data-baseweb="radio"] div[role="radio"][aria-checked="true"] { border-color: var(--color-accent); background: var(--color-accent); }
hr { border-color: var(--color-border); }
code {
    background: var(--color-accent-tint);
    color: var(--color-text-primary);
}

/* Recommendation cards */
.rec-card {
    background: var(--color-card-bg);
    border-left: 4px solid var(--color-accent);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: normal;
}
.rec-card.high   { border-left-color: var(--color-error); }
.rec-card.medium { border-left-color: var(--color-warning); }
.rec-card.low    { border-left-color: var(--color-success); }
</style>
""".replace("__THEME_CSS_VARIABLES__", css_variables()), unsafe_allow_html=True)


# SESSION STATE

if "df_clean" not in st.session_state:
    st.session_state["df_clean"] = None

if "filename" not in st.session_state:
    st.session_state["filename"] = None

if "sheet_names" not in st.session_state:
    st.session_state["sheet_names"] = None

if "sheet_mode" not in st.session_state:
    st.session_state["sheet_mode"] = None

if "selected_sheet" not in st.session_state:
    st.session_state["selected_sheet"] = None

if "current_tab" not in st.session_state:
    st.session_state["current_tab"] = (
        ":material/home: Data & Upload"
    )

if "last_uploaded_file" not in st.session_state:
    st.session_state["last_uploaded_file"] = None

if "_raw_sheets" not in st.session_state:
    st.session_state["_raw_sheets"] = None

if "excel_file_bytes" not in st.session_state:
    st.session_state["excel_file_bytes"] = None

if "local_excel_path" not in st.session_state:
    st.session_state["local_excel_path"] = None

if "excel_source" not in st.session_state:
    st.session_state["excel_source"] = None


# Fix dataframe column types for Streamlit / Arrow
if st.session_state["df_clean"] is not None:
    session_df = st.session_state["df_clean"]

    text_columns = [
        "Invoice",
        "StockCode",
        "Description",
        "CustomerID",
        "Country",
        "SourceSheet",
    ]

    for col in text_columns:
        if col in session_df.columns:
            session_df[col] = (
                session_df[col]
                .fillna("")
                .astype(str)
            )

    if "CustomerID" in session_df.columns:
        session_df["CustomerID"] = (
            session_df["CustomerID"]
            .replace("", "Guest")
            .fillna("Guest")
            .astype(str)
        )

if "validation_reports" not in st.session_state:
    st.session_state["validation_reports"] = []

# SIDEBAR

with st.sidebar:
    st.markdown("## :material/analytics: Retail Analytics")

    nav_options = [":material/home: Data & Upload"]
    if st.session_state['df_clean'] is not None:
        nav_options.extend([
            ":material/analytics: Analytics Dashboard",
            ":material/insights: Insights & Actions"
        ])
    nav_options.append(":material/info: About & Methodology")

    if st.session_state['current_tab'] not in nav_options:
        st.session_state['current_tab'] = ":material/home: Data & Upload"

    page = st.radio(
        "Navigate",
        options=nav_options,
        index=nav_options.index(st.session_state['current_tab']),
        key="nav_selection",
        label_visibility='collapsed',
    )
    st.session_state['current_tab'] = page

    st.markdown("---")
    st.caption("Online Retail Analytics Platform")


# HELPER FUNCTIONS

def _show_validation_report(report: dict) -> None:
    for msg in report.get('errors', []):
        st.error(f":material/cancel: {msg}")
    for msg in report.get('warnings', []):
        st.warning(f":material/warning: {msg}")
    for msg in report.get('info', []):
        st.info(f":material/info: {msg}")


def is_already_cleaned(
    df: pd.DataFrame
) -> bool:
    required = {
        'Revenue',
        'CustomerID',
        'IsReturn',
    }

    return required.issubset(df.columns)

def _process_single_df(
    df_raw: pd.DataFrame,
    source_label: str
) -> pd.DataFrame | None:

    # Work on a copy
    df_raw = df_raw.copy()

    # Remove spaces around column names
    df_raw.columns = (
        df_raw.columns
        .astype(str)
        .str.strip()
    )

    # Columns that should always be text
    text_columns = [
        "Invoice",
        "StockCode",
        "Description",
        "CustomerID",
        "Customer ID",
        "Country",
        "SourceSheet",
    ]

    for col in text_columns:
        if col in df_raw.columns:
            df_raw[col] = (
                df_raw[col]
                .fillna("")
                .astype(str)
            )

    # Convert date column safely
    if "InvoiceDate" in df_raw.columns:
        df_raw["InvoiceDate"] = pd.to_datetime(
            df_raw["InvoiceDate"],
            errors="coerce",
        )

    # Validate data
    is_valid, report = validate_data(df_raw)

    validation_entry = {
        "source": source_label,
        "is_valid": is_valid,
        "report": report,
    }

    st.session_state["validation_reports"] = [
        validation_entry
    ]

    with st.expander(
        f":material/list_alt: Validation report — {source_label}",
        expanded=not is_valid,
    ):
        _show_validation_report(report)

    if not is_valid:
        st.error(
            ":material/cancel: **Cannot proceed** — "
            "fix the errors above before analysis can run."
        )
        return None

    # Dataset is already cleaned
    if is_already_cleaned(df_raw):
        df_raw["CustomerID"] = (
            df_raw["CustomerID"]
            .replace("", "Guest")
            .fillna("Guest")
            .astype(str)
        )

        # Add or recalculate IsProduct for older cleaned files
        df_raw = add_product_flag(df_raw)

        return df_raw

    # Rename raw Price column
    if (
        "Price" in df_raw.columns
        and "UnitPrice" not in df_raw.columns
    ):
        df_raw = df_raw.rename(
            columns={"Price": "UnitPrice"}
        )

    # Clean raw dataset
    with st.spinner(
        f":material/mop: Cleaning data ({source_label})..."
    ):
        df_clean = clean_data(df_raw)

    # Fix types again after cleaning
    final_text_columns = [
        "Invoice",
        "StockCode",
        "Description",
        "CustomerID",
        "Country",
        "SourceSheet",
    ]

    for col in final_text_columns:
        if col in df_clean.columns:
            df_clean[col] = (
                df_clean[col]
                .fillna("")
                .astype(str)
            )

    if "CustomerID" in df_clean.columns:
        df_clean["CustomerID"] = (
            df_clean["CustomerID"]
            .replace("", "Guest")
            .fillna("Guest")
            .astype(str)
        )

    return df_clean


def prepare_excel_sheets(
    uploaded_file,
    sheets: dict[str, pd.DataFrame],
) -> pd.DataFrame | None:
    """Store multiple Excel sheets or process a single sheet."""

    if not sheets:
        st.error(
            ":material/cancel: The Excel file contains no readable sheets."
        )
        return None

    sheet_names = list(sheets.keys())

    st.session_state["sheet_names"] = sheet_names
    st.session_state["_raw_sheets"] = sheets

    # Multiple sheets: wait for the user to choose
    if len(sheet_names) > 1:
        return None

    # One sheet: load it automatically
    sheet_name = sheet_names[0]
    df_raw = sheets[sheet_name].copy()

    if "InvoiceDate" in df_raw.columns:
        df_raw["InvoiceDate"] = pd.to_datetime(
            df_raw["InvoiceDate"],
            errors="coerce",
        )

    return _process_single_df(
        df_raw,
        f"{uploaded_file.name} → {sheet_name}",
    )


def load_and_clean(uploaded_file) -> pd.DataFrame | None:
    """Load CSV directly or prepare Excel sheet selection."""

    filename = uploaded_file.name.lower()
    uploaded_file.seek(0)

    # CSV
    if filename.endswith(".csv"):
        try:
            df_raw = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Could not read CSV file: {e}")
            return None

        return _process_single_df(
            df_raw,
            uploaded_file.name,
        )

    # XLSX
    if filename.endswith(".xlsx"):
        try:
            uploaded_file.seek(0)

            excel_file = pd.ExcelFile(
                uploaded_file,
                engine="openpyxl",
            )

            st.session_state["sheet_names"] = excel_file.sheet_names

            # Store file bytes so sheets can be read later
            uploaded_file.seek(0)
            st.session_state["excel_file_bytes"] = uploaded_file.getvalue()

            return None

        except Exception as e:
            st.error(f"Could not read XLSX file: {e}")
            return None

    # XLS
    if filename.endswith(".xls"):
        st.error(
            "Old `.xls` files need the `xlrd` package. "
            "Convert the file to `.xlsx` or install `xlrd`."
        )
        return None

    st.error(f"Unsupported file type: {uploaded_file.name}")
    return None
# PAGE: DATA & UPLOAD


if page == ":material/home: Data & Upload":
    st.title(":material/analytics: Online Retail Analytics Platform")
    st.markdown(
        "Upload your monthly sales data (CSV or Excel) and the platform will automatically "
        "clean, validate, analyse, and generate business recommendations."
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Upload Monthly Sales Data")

        from pathlib import Path
        from io import BytesIO

        PROJECT_ROOT = Path(__file__).resolve().parent.parent
        DATA_DIR = PROJECT_ROOT / "data" / "Testing Datasets"

        # ---------------------------------------------------------
        # 1. Browser upload
        # ---------------------------------------------------------
        uploaded = st.file_uploader(
            "Drop your CSV or Excel file here",
            type=["csv", "xlsx", "xls"],
            key="uploader",
        )

        if uploaded:
            file_identity = f"{uploaded.name}-{uploaded.size}"

            if st.session_state.get("last_uploaded_file") != file_identity:
                st.session_state["last_uploaded_file"] = file_identity
                st.session_state["validation_reports"] = []

                st.session_state["sheet_names"] = None
                st.session_state["excel_file_bytes"] = None
                st.session_state["local_excel_path"] = None
                st.session_state["excel_source"] = None
                st.session_state["sheet_mode"] = None
                st.session_state["selected_sheet"] = None

                df = load_and_clean(uploaded)

                # CSV loads directly
                if df is not None:
                    st.session_state["df_clean"] = df
                    st.session_state["filename"] = uploaded.name
                    st.session_state["current_tab"] = (
                        ":material/analytics: Analytics Dashboard"
                    )
                    st.rerun()

                # XLSX stores sheet names and bytes
                if uploaded.name.lower().endswith(".xlsx"):
                    st.session_state["excel_source"] = "uploaded"

        # ---------------------------------------------------------
        # 2. Excel sheet selector
        # Works for BOTH uploaded and local files
        # ---------------------------------------------------------
        if st.session_state.get("sheet_names"):
            sheet_names = st.session_state["sheet_names"]
            source_name = uploaded.name if uploaded else "Uploaded Excel file"

            st.markdown("---")
            st.markdown(
                f"### `{source_name}` contains "
                f"**{len(sheet_names)} sheet(s)**"
            )

            sheet_mode = st.radio(
                "Choose how to load the Excel file",
                options=[
                    "Load selected sheets",
                    "Load all sheets",
                ],
                horizontal=True,
                key="sheet_mode_radio",
            )

            if sheet_mode == "Load selected sheets":
                selected_sheets = st.multiselect(
                    "Select sheets",
                    options=sheet_names,
                    default=[sheet_names[0]],
                    key="sheet_selector",
                )
            else:
                selected_sheets = sheet_names

            if st.button(
                "Load Excel Data",
                key="btn_load_excel_data",
                type="primary",
                use_container_width=True,
                disabled=not selected_sheets,
            ):
                combined_frames = []
                all_ok = True

                st.session_state["validation_reports"] = []

                with st.spinner("Reading Excel sheets..."):
                    for sheet_name in selected_sheets:
                        try:
                            excel_bytes = st.session_state.get(
                                "excel_file_bytes"
                            )

                            if not excel_bytes:
                                st.error(
                                    "Uploaded Excel data is no longer available."
                                )
                                all_ok = False
                                break

                            sheet_df = pd.read_excel(
                                BytesIO(excel_bytes),
                                sheet_name=sheet_name,
                                engine="openpyxl",
                            )

                            sheet_df = sheet_df.copy()

                            # Remove spaces around column names
                            sheet_df.columns = (
                                sheet_df.columns
                                .astype(str)
                                .str.strip()
                            )

                            # Validate this sheet
                            is_valid, report = validate_data(sheet_df)

                            # Save the report so it remains after st.rerun()
                            st.session_state["validation_reports"].append({
                                "source": f"{source_name} → {sheet_name}",
                                "is_valid": is_valid,
                                "report": report,
                            })

                            with st.expander(
                                f"Validation report — {sheet_name}",
                                expanded=not is_valid,
                            ):
                                _show_validation_report(report)

                            if not is_valid:
                                st.error(
                                    f"Sheet **{sheet_name}** "
                                    "failed validation."
                                )
                                all_ok = False
                                break

                            if (
                                "Price" in sheet_df.columns
                                and "UnitPrice" not in sheet_df.columns
                            ):
                                sheet_df = sheet_df.rename(
                                    columns={
                                        "Price": "UnitPrice"
                                    }
                                )

                            sheet_df["SourceSheet"] = sheet_name
                            combined_frames.append(sheet_df)

                        except Exception as e:
                            st.error(
                                f"Could not read sheet "
                                f"**{sheet_name}**: {e}"
                            )
                            all_ok = False
                            break

                if all_ok and combined_frames:
                    combined_raw = pd.concat(
                        combined_frames,
                        ignore_index=True,
                    )

                    if is_already_cleaned(combined_raw):
                        result = combined_raw.copy()

                        result["CustomerID"] = (
                            result["CustomerID"]
                            .fillna("Guest")
                            .astype(str)
                        )
                        result = add_product_flag(result)
                    else:
                        with st.spinner(
                            "Cleaning Excel data..."
                        ):
                            result = clean_data(combined_raw)

                    st.session_state["df_clean"] = result

                    if len(selected_sheets) == len(sheet_names):
                        st.session_state["filename"] = (
                            f"{source_name} "
                            f"(all {len(sheet_names)} sheets)"
                        )
                        st.session_state["sheet_mode"] = "all"
                    else:
                        st.session_state["filename"] = (
                            f"{source_name} → "
                            f"{', '.join(selected_sheets)}"
                        )
                        st.session_state["sheet_mode"] = "selected"

                    st.session_state["selected_sheet"] = (
                        selected_sheets
                    )
                    st.session_state["current_tab"] = (
                        ":material/analytics: Analytics Dashboard"
                    )

                    st.rerun()

    if st.session_state["validation_reports"]:
        st.markdown("---")
        st.markdown("### :material/fact_check: Validation Report")

        for entry in st.session_state["validation_reports"]:
            source = entry["source"]
            is_valid = entry["is_valid"]
            report = entry["report"]

            status = (
                ":material/check_circle: Valid"
                if is_valid
                else ":material/cancel: Invalid"
            )

            with st.expander(
                f"{status} — {source}",
                expanded=not is_valid,
            ):
                _show_validation_report(report)

    if st.session_state['df_clean'] is not None:
        st.markdown("---")
        st.markdown(
            f"### :material/folder: Currently loaded: `{st.session_state['filename']}`")
        df = st.session_state['df_clean']
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows (after cleaning)", f"{len(df):,}")
        c2.metric("Columns", str(df.shape[1]))
        c3.metric("Date range",
                  f"{pd.to_datetime(df['InvoiceDate']).min().strftime('%b %Y')}"
                  f" → {pd.to_datetime(df['InvoiceDate']).max().strftime('%b %Y')}"
                  if 'InvoiceDate' in df.columns else 'N/A')
        c4.metric("Countries", str(
            df['Country'].nunique()) if 'Country' in df.columns else 'N/A')

        with st.expander("Preview first 50 rows"):
            st.dataframe(df.head(50), width='stretch', hide_index=True)


# PAGE: ANALYTICS DASHBOARD

elif page == ":material/analytics: Analytics Dashboard":
    st.title(":material/analytics: Analytics Dashboard")
    df = st.session_state['df_clean']

    # ── KPIs ────────────────────────────────────────────────────────
    kpis = get_kpi_summary(df)
    cards = format_kpi_cards(kpis)

    # First row: 4 KPI cards
    top_cards = cards[:4]
    top_columns = st.columns(4)

    for col, card in zip(top_columns, top_cards):
        col.metric(
            card['label'],
            card['value']
        )

    # Second row: remaining 3 KPI cards
    bottom_cards = cards[4:]
    bottom_columns = st.columns(3)

    for col, card in zip(bottom_columns, bottom_cards):
        col.metric(
            card['label'],
            card['value']
        )

    st.markdown("---")

    # ── Tabs ────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        ":material/calendar_month: Revenue Trends", ":material/inventory_2: Products", ":material/analytics: Returns", ":material/group: Customers", ":material/public: Geographic"
    ])

    with tab1:

        # SHARED FILTERS FOR TAB 1
        df_t1 = df.copy()

        df_t1["InvoiceDate"] = pd.to_datetime(
            df_t1["InvoiceDate"],
            errors="coerce"
        )

        df_t1 = df_t1.dropna(subset=["InvoiceDate"])

        min_date = df_t1["InvoiceDate"].min().date()
        max_date = df_t1["InvoiceDate"].max().date()

        with st.container(border=True):
            st.markdown("### Revenue Trend Filters")

            filter_col1, filter_col2 = st.columns(2)

            with filter_col1:
                st.markdown(
                    "<p class='filter-label'>Date Range</p>",
                    unsafe_allow_html=True
                )

                selected_range = st.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="tab1_shared_date_range",
                    label_visibility="collapsed"
                )

            with filter_col2:
                st.markdown(
                    "<p class='filter-label'>Country</p>",
                    unsafe_allow_html=True
                )

                selected_country = st.selectbox(
                    "Country",
                    options=[
                        "All Countries"
                    ] + sorted(
                        df_t1["Country"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    ),
                    key="tab1_shared_country",
                    label_visibility="collapsed"
                )

        if (
            isinstance(selected_range, (list, tuple))
            and len(selected_range) == 2
        ):
            df_t1 = df_t1[
                (
                    df_t1["InvoiceDate"].dt.date
                    >= selected_range[0]
                )
                &
                (
                    df_t1["InvoiceDate"].dt.date
                    <= selected_range[1]
                )
            ]

        if selected_country != "All Countries":
            df_t1 = df_t1[
                df_t1["Country"].astype(str)
                == selected_country
            ]

        if df_t1.empty:
            st.warning("No data is available for the selected filters.")
            st.stop()

        st.markdown("---")
        # 1. Monthly Revenue & Order Volume
        with st.container(border=True):
            st.markdown("### Monthly Revenue & Order Volume")

            monthly = get_monthly_revenue(df_t1)

            if monthly.empty:
                st.warning("No monthly revenue data is available.")
            else:
                st.plotly_chart(
                    plot_monthly_revenue(monthly),
                    use_container_width=True,
                )

        st.markdown("---")

        # 2. Monthly Revenue Patterns by Product
        with st.container(border=True):
            st.markdown("### Monthly Revenue Patterns by Product")

            available_products = sorted(
                df_t1["Description"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            top_3_products = (
                df_t1
                .dropna(subset=["Description"])
                .groupby("Description", observed=True)["Revenue"]
                .sum()
                .nlargest(3)
                .index
                .astype(str)
                .tolist()
            )

            # Streamlit multiselect is searchable by typing.
            selected_products = st.multiselect(
                "Search and select products",
                options=available_products,
                default=top_3_products,
                key="monthly_selected_products",
                placeholder="Type a product name...",
                help="The top 3 revenue-generating products are selected automatically.",
            )

            if not selected_products:
                st.info(
                    "Search for and select at least one product "
                    "to display its monthly revenue."
                )
            else:
                product_df = df_t1[
                    df_t1["Description"].astype(str).isin(
                        selected_products
                    )
                ]

                # The function now receives only the selected products,
                # so it no longer chooses an automatic Top N range.
                monthly_products = get_monthly_product_revenue(
                    product_df,
                    n=len(selected_products),
                )

                if monthly_products.empty:
                    st.warning(
                        "No product data is available for this selection."
                    )
                else:
                    st.plotly_chart(
                        plot_monthly_product_revenue(monthly_products),
                        use_container_width=True,
                    )

        st.markdown("---")

        c1, c2 = st.columns(2)

        # Prepare reusable dates and weeks from the globally filtered data.
        period_df = df_t1.copy()
        period_df["_Date"] = period_df["InvoiceDate"].dt.date
        period_df["_WeekStart"] = (
            period_df["InvoiceDate"]
            - pd.to_timedelta(
                period_df["InvoiceDate"].dt.weekday,
                unit="D"
            )
        ).dt.date

        week_starts = sorted(period_df["_WeekStart"].unique())
        week_labels = {
            f"Week of {week_start:%d %b %Y}": week_start
            for week_start in week_starts
        }

        with c1:
            with st.container(border=True):
                st.markdown("### Revenue by Day of Week")

                selected_week_label = st.selectbox(
                    "Week",
                    options=["Average across selected range"]
                    + list(week_labels.keys()),
                    key="revenue_week_selection",
                )

                if selected_week_label == "Average across selected range":
                    # First calculate each weekday's revenue inside each week,
                    # then average that weekday across all selected weeks.
                    weekly_day_revenue = (
                        period_df.assign(
                            DayOfWeek=period_df[
                                "InvoiceDate"
                            ].dt.day_name()
                        )
                        .groupby(
                            ["_WeekStart", "DayOfWeek"],
                            observed=True,
                        )["Revenue"]
                        .sum()
                        .reset_index()
                    )

                    dow = (
                        weekly_day_revenue
                        .groupby("DayOfWeek", observed=True)["Revenue"]
                        .mean()
                        .reset_index()
                    )

                    day_order = [
                        "Monday", "Tuesday", "Wednesday",
                        "Thursday", "Friday", "Saturday", "Sunday",
                    ]
                    dow["DayOfWeek"] = pd.Categorical(
                        dow["DayOfWeek"],
                        categories=day_order,
                        ordered=True,
                    )
                    dow = dow.sort_values("DayOfWeek")
                else:
                    selected_week = week_labels[selected_week_label]
                    week_df = period_df[
                        period_df["_WeekStart"] == selected_week
                    ]
                    dow = get_revenue_by_day_of_week(week_df)

                if dow.empty:
                    st.warning("No weekday revenue data is available.")
                else:

                    st.plotly_chart(
                        plot_revenue_by_day_of_week(dow),
                        use_container_width=True,
                    )

        with c2:
            with st.container(border=True):
                st.markdown("### Sales Activity by Hour of Day")

                available_days = sorted(period_df["_Date"].unique())
                day_labels = {
                    pd.Timestamp(day).strftime("%d %b %Y"): day
                    for day in available_days
                }

                selected_day_label = st.selectbox(
                    "Day",
                    options=["Average across selected range"]
                    + list(day_labels.keys()),
                    key="hour_day_selection",
                )

                if selected_day_label == "Average across selected range":
                    # Calculate revenue per hour for every date, then average
                    # the same hour across all dates in the selected range.
                    daily_hour_data = (
                        period_df.assign(
                            Hour=period_df["InvoiceDate"].dt.hour
                        )
                        .groupby(
                            ["_Date", "Hour"],
                            observed=True
                        )
                        .agg(
                            Revenue=("Revenue", "sum"),
                            Transactions=("Invoice", "nunique")
                        )
                        .reset_index()
                    )

                    hourly = (
                        daily_hour_data
                        .groupby(
                            "Hour",
                            observed=True
                        )
                        .agg(
                            Revenue=("Revenue", "mean"),
                            Transactions=("Transactions", "mean")
                        )
                        .reset_index()
                    )
                else:
                    selected_day = day_labels[selected_day_label]
                    day_df = period_df[
                        period_df["_Date"] == selected_day
                    ]
                    hourly = get_revenue_by_hour(day_df)

                if hourly.empty:
                    st.warning("No hourly sales data is available.")
                else:
                    st.plotly_chart(
                        plot_revenue_by_hour(hourly),
                        use_container_width=True,
                    )



    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown("### Top Products")
                df_t2_top = df.copy()

                filt_col1, filt_col2 = st.columns([1, 1])
                with filt_col1:
                    if 'Country' in df.columns:
                        st.markdown(
                            "<p class='filter-label'>Country</p>", unsafe_allow_html=True)
                        t2_top_country = st.selectbox(
                            "Country",
                            options=["All Countries"] +
                                sorted(
                                    df['Country'].dropna().unique().tolist()),
                            key="v_t2_top_country",
                            label_visibility="collapsed"
                        )
                        if t2_top_country != "All Countries":
                            df_t2_top = df_t2_top[df_t2_top['Country']
                                == t2_top_country]
                with filt_col2:
                    st.markdown(
                        "<p class='filter-label'>Limit Count</p>", unsafe_allow_html=True)
                    top_n = st.slider("Select Top N Count", 5, 20,
                                      10, key="top_n", label_visibility="collapsed")

                if df_t2_top.empty:
                    st.warning("No product sales data found.")
                else:
                    top = get_top_products(df_t2_top, n=top_n)
                    st.plotly_chart(plot_top_products(top, n=top_n), use_container_width=True, key="chart_top_products")

        with c2:
            with st.container(border=True):
                st.markdown("### Worst Products")
                df_t2_worst = df.copy()

                filt_col1, filt_col2 = st.columns([1.5, 2])
                with filt_col1:
                    if 'Country' in df.columns:
                        st.markdown(
                            "<p class='filter-label'>Country</p>", unsafe_allow_html=True)
                        t2_worst_country = st.selectbox(
                            "Country",
                            options=["All Countries"] +
                                sorted(
                                    df['Country'].dropna().unique().tolist()),
                            key="v_t2_worst_country",
                            label_visibility="collapsed"
                        )
                        if t2_worst_country != "All Countries":
                            df_t2_worst = df_t2_worst[df_t2_worst['Country']
                                == t2_worst_country]

                if df_t2_worst.empty:
                    st.warning("No product sales data found.")
                else:
                    worst = get_worst_products(df_t2_worst, n=10)
                    st.plotly_chart(plot_top_products(worst, n=10), use_container_width=True, key="chart_worst_products")
                    st.caption("Worst-selling products — consider repricing or discontinuation")

    with tab3:
        ret_summary = get_return_summary(df)
        if ret_summary:
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric("Return Transactions",
                       f"{ret_summary.get('return_transactions', 0):,}")
            rc2.metric("Return Rate",
                       f"{ret_summary.get('return_rate_%', 0):.1f}%")
            rc3.metric("Revenue Lost to Returns",
                       f"£{ret_summary.get('revenue_lost_from_returns', 0):,.0f}")

        st.markdown("---")

        with st.container(border=True):
            st.markdown("### Return Trends & Impact Analysis")

            df_t3_filtered = df.copy()
            if 'InvoiceDate' in df.columns:
                filt_col1, filt_col2 = st.columns([1, 3])
                with filt_col1:
                    st.markdown(
                        "<p class='filter-label'>Date Range</p>", unsafe_allow_html=True)
                    t3_dates = pd.to_datetime(df['InvoiceDate'])
                    t3_min, t3_max = t3_dates.min().date(), t3_dates.max().date()
                    t3_range = st.date_input(
                        "Date Range",
                        value=(t3_min, t3_max),
                        min_value=t3_min, max_value=t3_max,
                        key="v_t3_dates",
                        label_visibility="collapsed"
                    )
                if isinstance(t3_range, (list, tuple)) and len(t3_range) == 2:
                    df_t3_filtered = df_t3_filtered[(t3_dates.dt.date >= t3_range[0]) & (
                        t3_dates.dt.date <= t3_range[1])]

            if df_t3_filtered.empty:
                st.warning("No return data found for the selected range.")
            else:
                st.plotly_chart(plot_return_rate_over_time(
                    get_return_rate_over_time(df_t3_filtered)), use_container_width=True)
                st.plotly_chart(plot_returns_revenue_impact(
                    get_returns_revenue_impact(df_t3_filtered)), use_container_width=True)

        st.markdown("---")

        with st.container(border=True):
            st.markdown("### Products with Highest Return Rates")
            df_t3_ret_rate = df.copy()
            if 'Country' in df.columns:
                filt_col1, filt_col2 = st.columns([1.5, 2])
                with filt_col1:
                    st.markdown("<p class='filter-label'>Country</p>",
                                unsafe_allow_html=True)
                    t3_ret_rate_country = st.selectbox(
                        "Country",
                        options=["All Countries"] +
                            sorted(df['Country'].dropna().unique().tolist()),
                        key="v_t3_ret_rate_country",
                        label_visibility="collapsed"
                    )
                if t3_ret_rate_country != "All Countries":
                    df_t3_ret_rate = df_t3_ret_rate[df_t3_ret_rate['Country']
                        == t3_ret_rate_country]

            ret_rate = get_product_return_rate(df_t3_ret_rate)
            if ret_rate.empty:
                st.info(
                    "No products have enough matched sales and return history "
                    "for this filter. At least 3 sales transactions are required."
                )
            else:
                st.caption(
                    "Return rate = units returned ÷ units sold. Products with "
                    "unmatched returns or fewer than 3 sales transactions are excluded."
                )
                st.plotly_chart(plot_product_return_rates(
                    ret_rate, n=15), use_container_width=True)

    with tab4:
        with st.spinner("Computing RFM scores..."):
            rfm = compute_rfm(df)
            seg_summary = get_segment_summary(rfm)

        with st.container(border=True):
            st.markdown("### Customer Segments")
            filtered_seg_summary = seg_summary
            if not rfm.empty:
                filt_col1, filt_col2 = st.columns([2, 1])
                with filt_col1:
                    st.markdown(
                        "<p class='filter-label'>Select Segments</p>", unsafe_allow_html=True)
                    selected_segs = st.multiselect(
                        "Segments",
                        options=sorted(rfm['Segment'].unique().tolist()),
                        default=sorted(rfm['Segment'].unique().tolist()),
                        key="v_t4_segments",
                        label_visibility="collapsed"
                    )
                filtered_seg_summary = seg_summary[seg_summary['Segment'].isin(
                    selected_segs)]

            if filtered_seg_summary.empty:
                st.warning("Please select at least one customer segment.")
            else:
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(plot_rfm_segments(
                        filtered_seg_summary), use_container_width=True)
                with c2:
                    st.plotly_chart(plot_segment_revenue_share(
                        filtered_seg_summary), use_container_width=True)

                st.dataframe(filtered_seg_summary.style.format({
                    'Avg_Recency_Days': '{:.0f}',
                    'Avg_Frequency':    '{:.1f}',
                    'Avg_Revenue':      '£{:,.0f}',
                    'Total_Revenue':    '£{:,.0f}',
                }), hide_index=True, width='stretch')

        # st.markdown("---")
        # sub_tab1, sub_tab2, sub_tab3 = st.tabs(
        #     [":material/attach_money: CLV", ":material/autorenew: New vs Returning", ":material/warning: Churn Risk"])

        # with sub_tab1:
        #     with st.container(border=True):
        #         st.markdown("#### CLV Distribution")
        #         clv = get_customer_lifetime_value(df)
        #         if not clv.empty:
        #             filt_col1, filt_col2 = st.columns([1, 2])
        #             with filt_col1:
        #                 st.markdown(
        #                     "<p class='filter-label'>Outliers Percentile Cap</p>", unsafe_allow_html=True)
        #                 clv_threshold = st.slider(
        #                     "Capping Percentile",
        #                     min_value=80, max_value=100, value=99, step=1,
        #                     key="v_clv_percentile",
        #                     label_visibility="collapsed"
        #                 )
        #             cap = clv['TotalRevenue'].quantile(clv_threshold / 100)
        #             filtered_clv = clv[clv['TotalRevenue'] <= cap]
        #             st.plotly_chart(plot_clv_distribution(
        #                 filtered_clv), use_container_width=True)

        #             top10_pct = clv.head(max(1, int(len(clv) * 0.1)))
        #             rev_share = top10_pct['TotalRevenue'].sum(
        #             ) / clv['TotalRevenue'].sum() * 100
        #             st.info(
        #                 f"Top 10% of customers generate **{rev_share:.1f}%** of total revenue")
        #         else:
        #             st.plotly_chart(plot_clv_distribution(clv),
        #                             use_container_width=True)
        #         with st.expander("Full CLV table"):
        #             st.dataframe(clv.head(100), width='stretch')

        # with sub_tab2:
        #     with st.container(border=True):
        #         new_ret = get_new_vs_returning_customers(df)
        #         st.plotly_chart(plot_new_vs_returning(
        #             new_ret), use_container_width=True)

        # with sub_tab3:
        #     days = st.slider("Inactive for more than (days)",
        #                      30, 180, 90, step=15)
        #     churned = get_churned_customers(df, days_threshold=days)
        #     st.metric(f"Customers inactive {days}+ days", f"{len(churned):,}")
        #     if not churned.empty:
        #         st.dataframe(churned.head(50), width='stretch')
        #         csv_export = churned.to_csv(index=False).encode()
        #         st.download_button(
        #             ":material/download: Download churn list (CSV)",
        #             data=csv_export,
        #             file_name=f"churn_risk_{days}days.csv",
        #             mime="text/csv",
        #         )

    with tab5:
        geo_full = get_country_performance(df)

        with st.container(border=True):
            st.markdown("### Geographic Distribution")

            if geo_full.empty:
                st.warning("No geographic data found.")
            else:
                top_country = str(geo_full.iloc[0]['Country'])

                filt_col1, filt_col2 = st.columns([1, 3])
                with filt_col1:
                    st.markdown(
                        f"<p class='filter-label'>Exclude {escape(top_country)} for Scale</p>",
                        unsafe_allow_html=True,
                    )
                    exclude_top_country = st.toggle(
                        f"Exclude {top_country}",
                        value=True,
                        key="geo_excl_top_country",
                        label_visibility="collapsed",
                    )

                excluded_country = top_country if exclude_top_country else None
                geo_map_data = geo_full[
                    geo_full['Country'] != excluded_country
                ] if excluded_country else geo_full

                if geo_map_data.empty:
                    st.warning(
                        f"No geographic data remains after excluding {top_country}.")

                st.plotly_chart(plot_country_revenue(
                    geo_full, excluded_country=excluded_country), use_container_width=True)

                c1, c2 = st.columns([2, 1])
                with c1:
                    n = st.slider("Top N countries", 5, 20, 10, key="geo_n")
                    st.plotly_chart(plot_top_countries_bar(
                        geo_full, n=n, excluded_country=excluded_country), use_container_width=True)
                with c2:
                    st.markdown("### Country Table")
                    st.dataframe(
                        geo_map_data.head(20).style.format(
                            {'Revenue': '£{:,.0f}'}),
                        width='stretch',
                        hide_index=True
                    )


# PAGE: INSIGHTS & ACTIONS

elif page == ":material/insights: Insights & Actions":
    st.title(":material/insights: Insights & Actions")
    df = st.session_state['df_clean']
    action_tab1, action_tab2 = st.tabs(
        [":material/lightbulb: Recommendations", ":material/psychology: What-If Simulator"])

    with action_tab1:
        with st.spinner("Generating recommendations..."):
            recs = generate_recommendations(df)

        if not recs:
            st.warning("Not enough data to generate recommendations.")
        else:
            high = [r for r in recs if r['priority'] == 'High']
            medium = [r for r in recs if r['priority'] == 'Medium']
            low = [r for r in recs if r['priority'] == 'Low']

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Recommendations", str(len(recs)))
            c2.metric(":material/error: High Priority", str(len(high)))
            c3.metric(":material/warning: Medium Priority", str(len(medium)))
            c4.metric(":material/check_circle: Low Priority", str(len(low)))

            st.markdown("---")
            priority_filter = st.multiselect(
                "Filter by priority", ["High", "Medium", "Low"],
                default=["High", "Medium", "Low"],
            )

            for rec in recs:
                if rec['priority'] not in priority_filter:
                    continue

                css_class = rec['priority'].lower()
                svgs = {
                    "High": '<svg style="vertical-align: middle; margin-right: 4px; color: var(--color-error);" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
                    "Medium": '<svg style="vertical-align: middle; margin-right: 4px; color: var(--color-warning);" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
                    "Low": '<svg style="vertical-align: middle; margin-right: 4px; color: var(--color-success);" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
                }
                priority_svg = svgs.get(rec['priority'], '')
                trending_up_svg = '<svg style="vertical-align: middle; margin-right: 4px; color: var(--color-accent);" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'

                st.markdown(f'''
                    <div class="rec-card {css_class}">
                    <strong>
                        {priority_svg} {rec['title']}
                    </strong>

                    &nbsp;&nbsp;

                    <span style="
                        color:var(--color-text-secondary);
                        font-size:0.85rem;
                    ">
                        {rec['type']} &middot; {rec['segment']}
                    </span>

                    <br><br>

                    {rec['message']}

                    <br><br>

                    <span style="
                        color:var(--color-accent);
                        font-weight:600;
                    ">
                        {trending_up_svg}
                        Estimated potential impact:
                        ~{rec['impact_pct']}%
                    </span>

                    <br>

                    <span style="
                        color:var(--color-text-secondary);
                        font-size:0.75rem;
                    ">
                        Heuristic estimate based on dataset patterns and
                        business assumptions. Actual results may vary.
                    </span>
                    </div>
                    ''', unsafe_allow_html=True)
            st.markdown("---")
            rec_df = pd.DataFrame(recs)
            st.download_button(
                ":material/download: Export Recommendations (CSV)",
                data=rec_df.to_csv(index=False).encode(),
                file_name="recommendations.csv",
                mime="text/csv",
            )

    with action_tab2:
        kpis = get_kpi_summary(df)
        base_revenue = kpis.get('total_revenue', 0)

        st.markdown(
            "Adjust the sliders below to simulate the revenue impact of business actions.")
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### :material/analytics: Your Assumptions")
            vip_retention = st.slider(
                "Improve VIP customer retention by", 0, 30, 10, step=1,
                format="%d%%", help="% increase in repeat purchases from Champion segment"
            )
            winback_rate = st.slider(
                "Win back At-Risk customers", 0, 50, 20, step=5,
                format="%d%%", help="% of at-risk customers you re-engage"
            )
            return_reduction = st.slider(
                "Reduce product returns by", 0, 50, 15, step=5,
                format="%d%%", help="% reduction in return transaction losses"
            )
            new_customer_growth = st.slider(
                "Increase new customer acquisition", 0, 30, 5, step=1,
                format="%d%%", help="% more new customers per month"
            )

        with col2:
            st.markdown("#### :material/lightbulb: Projected Impact")
            rfm = compute_rfm(df)

            champions_revenue = rfm[rfm['Segment'] == 'Champions']['Monetary'].sum(
            ) if not rfm.empty else 0
            loyal_revenue = rfm[rfm['Segment'] == 'Loyal Customers']['Monetary'].sum(
            ) if not rfm.empty else 0
            vip_revenue = champions_revenue + loyal_revenue

            at_risk_revenue = rfm[rfm['Segment'] == 'At Risk']['Monetary'].sum(
            ) if not rfm.empty else 0
            new_customer_segments = [
                "Recent Customers",
                "New One-Time Buyers",
            ]

            recent_revenue = rfm[
                rfm["Segment"].isin(new_customer_segments)
                ]["Monetary"].sum() if not rfm.empty else 0

            if vip_revenue == 0 and base_revenue > 0:
                vip_revenue = base_revenue * 0.30
            if at_risk_revenue == 0 and base_revenue > 0:
                at_risk_revenue = base_revenue * 0.10
            if recent_revenue == 0 and base_revenue > 0:
                recent_revenue = base_revenue * 0.05

            ret_summary = get_return_summary(df)
            revenue_lost_returns = ret_summary.get(
                'revenue_lost_from_returns', 0)

            revenue_from_vip = vip_revenue * (vip_retention / 100)
            revenue_from_winback = at_risk_revenue * (winback_rate / 100)
            revenue_from_returns = revenue_lost_returns * \
                (return_reduction / 100)
            revenue_from_new = recent_revenue * (new_customer_growth / 100)
            total_uplift = revenue_from_vip + revenue_from_winback + \
                revenue_from_returns + revenue_from_new

            st.metric("Base Revenue", f"£{base_revenue:,.0f}")
            st.metric("VIP Retention Uplift", f"+£{revenue_from_vip:,.0f}")
            st.metric("Win-Back Revenue", f"+£{revenue_from_winback:,.0f}")
            st.metric("Returns Savings", f"+£{revenue_from_returns:,.0f}")
            st.metric("New Customer Revenue", f"+£{revenue_from_new:,.0f}")
            st.markdown("---")
            st.metric("Projected Total Revenue",
                      f"£{base_revenue + total_uplift:,.0f}",
                      delta=f"+£{total_uplift:,.0f} (+{total_uplift/base_revenue*100:.1f}%)"
                      if base_revenue > 0 else None)

        st.caption(":material/check_circle: These projections are dynamically calculated using the RFM segment distributions.")

        st.markdown("---")
        st.markdown("### :material/download: Export Full Report")
        st.markdown("Download a comprehensive Excel report including KPIs, customer segments, and recommendations.")

        kpis_export = get_kpi_summary(df)
        recs_export = generate_recommendations(df)
        projections_export = {
            "vip_retention_pct": vip_retention,
            "winback_rate_pct": winback_rate,
            "return_reduction_pct": return_reduction,
            "new_customer_growth_pct": new_customer_growth,
            "base_revenue": base_revenue,
            "revenue_from_vip": revenue_from_vip,
            "revenue_from_winback": revenue_from_winback,
            "revenue_from_returns": revenue_from_returns,
            "revenue_from_new": revenue_from_new,
            "total_uplift": total_uplift,
            "projected_revenue": base_revenue + total_uplift,
        }

        excel_bytes = generate_excel_report(df, kpis_export, recs_export, projections_export)
        st.download_button(
            ":material/download: Download Excel Report",
            data=excel_bytes,
            file_name="retail_analytics_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# PAGE: ABOUT & METHODOLOGY

elif page == ":material/info: About & Methodology":
    render_about_page(
        st.session_state['df_clean'],
        st.session_state['filename'],
    )
