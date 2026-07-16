import sys
import os
import io
import pandas as pd
import streamlit as st

# Path setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_cleaning import clean_data
from src.analysis import (
    get_kpi_summary, get_monthly_revenue, get_monthly_product_revenue,
    get_revenue_by_hour,
    get_revenue_by_day_of_week, get_top_products, get_worst_products,
    get_product_return_rate, get_country_performance,
    get_customer_lifetime_value, get_new_vs_returning_customers,
    get_churned_customers, get_return_summary,
)
from src.recommendation_engine import compute_rfm, get_segment_summary, generate_recommendations
from src.export_utils import generate_excel_report
from src.visualisations import (
    plot_monthly_revenue, plot_monthly_product_revenue,
    plot_revenue_by_hour, plot_revenue_by_day_of_week,
    plot_top_products, plot_product_return_rates,
    plot_rfm_segments, plot_segment_revenue_share, plot_clv_distribution,
    plot_new_vs_returning, plot_country_revenue, plot_top_countries_bar,
    format_kpi_cards,
)
from src.theme import css_variables

# Required columns for validation
# Raw format uses 'Price' and 'Customer ID'; cleaned export uses 'UnitPrice' and 'CustomerID'
REQUIRED_COLUMNS = {'Invoice', 'StockCode', 'Description',
                    'Quantity', 'InvoiceDate', 'Country'}
# These columns have accepted aliases (raw name → cleaned name)
COLUMN_ALIASES = {
    'Price':       'UnitPrice',
    'Customer ID': 'CustomerID',
}

# Page config
st.set_page_config(
    page_title='Retail Analytics Platform',
    page_icon='💼',
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
p, label, [data-testid="stCaptionContainer"] { color: var(--color-text-secondary); }

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

/* Section headers */
h2 { color: var(--color-accent); border-bottom: 1px solid var(--color-border); padding-bottom: 0.4rem; word-wrap: break-word; }
h3 { color: var(--color-text-primary); word-wrap: break-word; }

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

.stButton > button { background: var(--color-accent); color: var(--color-page-bg); border-color: var(--color-accent); }
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


# SIDEBAR

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
    

# SESSION STATE

if 'df_clean' not in st.session_state:
    st.session_state['df_clean'] = None
if 'filename' not in st.session_state:
    st.session_state['filename'] = None

# Older cleaned CSVs may contain numeric customer IDs plus the text "Guest".
# Normalize existing session data as well as newly loaded files so Streamlit
# can serialize every dataframe without Arrow type-conversion warnings.
if st.session_state['df_clean'] is not None:
    session_df = st.session_state['df_clean']
    if 'CustomerID' in session_df.columns:
        session_df['CustomerID'] = session_df['CustomerID'].fillna('Guest').astype(str)


# HELPER FUNCTIONS

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
        df_raw['CustomerID'] = df_raw['CustomerID'].fillna('Guest').astype(str)
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


# PAGE: DATA & UPLOAD

if page == ":material/home: Data & Upload":
    st.title(":material/analytics: Online Retail Analytics Platform")
    st.markdown(
        "Upload your monthly sales CSV and the platform will automatically "
        "clean, analyse, and generate business recommendations."
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Upload Monthly Sales Data")
        uploaded = st.file_uploader(
            "Drop your CSV here (Online Retail II format)",
            type=["csv"],
            key="uploader",
        )
        
        #st.markdown("— **OR** —")

        #if st.button("Load local default dataset (`data/cleaned_retail_data.csv`)"):
        #    import os
        #    default_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned_retail_data.csv')
        #    if os.path.exists(default_path):
        #        with st.spinner("Loading local file..."):
        #            df = pd.read_csv(default_path, parse_dates=['InvoiceDate'])
        #            if 'CustomerID' in df.columns:
        #                df['CustomerID'] = df['CustomerID'].fillna('Guest').astype(str)
        #            st.session_state['df_clean'] = df
        #            st.session_state['filename'] = 'cleaned_retail_data.csv'
        #        st.success(":material/check_circle: Local default dataset loaded successfully!")
        #    else:
        #        st.error(":material/cancel: `cleaned_retail_data.csv` not found in `data/`. Please run `01_data_exploration.ipynb` first.")

        if uploaded:
            df = load_and_clean(uploaded)
            if df is not None:
                st.session_state['df_clean'] = df
                st.session_state['filename'] = uploaded.name
                st.success(
                    f":material/check_circle: **{uploaded.name}** loaded successfully — "
                    f"**{len(df):,}** rows after cleaning."
                )

   

    # Show currently loaded file
    if st.session_state['df_clean'] is not None:
        st.markdown("---")
        st.markdown(f"### :material/folder: Currently loaded: `{st.session_state['filename']}`")
        df = st.session_state['df_clean']
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows (after cleaning)", f"{len(df):,}")
        c2.metric("Columns", str(df.shape[1]))
        c3.metric("Date range",
                  f"{pd.to_datetime(df['InvoiceDate']).min().strftime('%b %Y')}"
                  f" → {pd.to_datetime(df['InvoiceDate']).max().strftime('%b %Y')}"
                  if 'InvoiceDate' in df.columns else 'N/A')
        c4.metric("Countries", str(df['Country'].nunique()) if 'Country' in df.columns else 'N/A')

        with st.expander("Preview first 50 rows"):
            st.dataframe(df.head(50), width='stretch')


# PAGE: ANALYTICS DASHBOARD

elif page == ":material/analytics: Analytics Dashboard":
    st.title(":material/analytics: Analytics Dashboard")
    if not require_data():
        st.stop()

    df = st.session_state['df_clean']

    # ── KPIs ────────────────────────────────────────────────────────
    kpis = get_kpi_summary(df)
    cards = format_kpi_cards(kpis)

    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        col.metric(card['label'], card['value'])

    st.markdown("---")

    # ── Tabs ────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        ":material/calendar_month: Revenue Trends", ":material/inventory_2: Products", ":material/analytics: Returns", ":material/group: Customers", ":material/public: Geographic"
    ])

    with tab1:
        monthly = get_monthly_revenue(df)
        st.plotly_chart(plot_monthly_revenue(monthly), width='stretch')

        product_count = st.slider(
            "Products to compare by month",
            min_value=3,
            max_value=10,
            value=4,
            key="monthly_product_count",
        )
        monthly_products = get_monthly_product_revenue(df, n=product_count)
        st.plotly_chart(
            plot_monthly_product_revenue(monthly_products),
            width='stretch',
        )

        c1, c2 = st.columns(2)
        with c1:
            dow = get_revenue_by_day_of_week(df)
            st.plotly_chart(plot_revenue_by_day_of_week(dow), width='stretch')
        with c2:
            hourly = get_revenue_by_hour(df)
            st.plotly_chart(plot_revenue_by_hour(hourly), width='stretch')

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            top_n = st.slider("Top N products", 5, 20, 10, key="top_n")
            top = get_top_products(df, n=top_n)
            st.plotly_chart(plot_top_products(top, n=top_n), width='stretch')
        with c2:
            worst = get_worst_products(df, n=10)
            st.plotly_chart(plot_top_products(worst, n=10), width='stretch')
            st.caption(":material/arrow_upward: Worst-selling products — consider repricing or discontinuation")

    with tab3:
        ret_summary = get_return_summary(df)
        if ret_summary:
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric("Return Transactions", f"{ret_summary.get('return_transactions', 0):,}")
            rc2.metric("Return Rate", f"{ret_summary.get('return_rate_%', 0):.1f}%")
            rc3.metric("Revenue Lost to Returns",
                       f"£{ret_summary.get('revenue_lost_from_returns', 0):,.0f}")

        ret_rate = get_product_return_rate(df)
        st.plotly_chart(plot_product_return_rates(ret_rate, n=15), width='stretch')

    with tab4:
        with st.spinner("Computing RFM scores..."):
            rfm = compute_rfm(df)
            seg_summary = get_segment_summary(rfm)

        # Segment overview
        st.markdown("### Customer Segments")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_rfm_segments(seg_summary), width='stretch')
        with c2:
            st.plotly_chart(plot_segment_revenue_share(seg_summary), width='stretch')

        st.dataframe(seg_summary.style.format({
            'Avg_Recency_Days': '{:.0f}',
            'Avg_Frequency':    '{:.1f}',
            'Avg_Revenue':      '£{:,.0f}',
            'Total_Revenue':    '£{:,.0f}',
        }), width='stretch')

        st.markdown("---")
        
        # Sub-tabs for more details
        sub_tab1, sub_tab2, sub_tab3 = st.tabs([":material/attach_money: CLV", ":material/autorenew: New vs Returning", ":material/warning: Churn Risk"])
        
        with sub_tab1:
            clv = get_customer_lifetime_value(df)
            st.plotly_chart(plot_clv_distribution(clv), width='stretch')
            if not clv.empty:
                top10_pct = clv.head(max(1, int(len(clv) * 0.1)))
                rev_share = top10_pct['TotalRevenue'].sum() / clv['TotalRevenue'].sum() * 100
                st.info(f":material/emoji_events: Top 10% of customers generate **{rev_share:.1f}%** of total revenue")
            with st.expander("Full CLV table"):
                st.dataframe(clv.head(100), width='stretch')
                
        with sub_tab2:
            new_ret = get_new_vs_returning_customers(df)
            st.plotly_chart(plot_new_vs_returning(new_ret), width='stretch')
            
        with sub_tab3:
            days = st.slider("Inactive for more than (days)", 30, 180, 90, step=15)
            churned = get_churned_customers(df, days_threshold=days)
            st.metric(f"Customers inactive {days}+ days", f"{len(churned):,}")
            if not churned.empty:
                st.dataframe(churned.head(50), width='stretch')
                csv_export = churned.to_csv(index=False).encode()
                st.download_button(
                    ":material/download: Download churn list (CSV)",
                    data=csv_export,
                    file_name=f"churn_risk_{days}days.csv",
                    mime="text/csv",
                )

    with tab5:
        geo = get_country_performance(df)
        exclude_uk = st.toggle("Exclude United Kingdom (avoids scale distortion)", value=True)
        st.plotly_chart(plot_country_revenue(geo, exclude_uk=exclude_uk), width='stretch')
        c1, c2 = st.columns([2, 1])
        with c1:
            n = st.slider("Top N countries", 5, 20, 10, key="geo_n")
            st.plotly_chart(plot_top_countries_bar(geo, n=n, exclude_uk=exclude_uk),
                            width='stretch')
        with c2:
            st.markdown("### Country Table")
            display_geo = geo[geo['Country'] != 'United Kingdom'] if exclude_uk else geo
            st.dataframe(
                display_geo.head(20).style.format({'Revenue': '£{:,.0f}'}),
                width='stretch',
            )


# PAGE: INSIGHTS & ACTIONS

elif page == ":material/insights: Insights & Actions":
    st.title(":material/insights: Insights & Actions")
    if not require_data():
        st.stop()

    df = st.session_state['df_clean']

    action_tab1, action_tab2 = st.tabs([":material/lightbulb: Recommendations", ":material/psychology: What-If Simulator"])

    with action_tab1:
        with st.spinner("Generating recommendations..."):
            recs = generate_recommendations(df)

        if not recs:
            st.warning("Not enough data to generate recommendations.")
        else:
            # Summary counts
            high   = [r for r in recs if r['priority'] == 'High']
            medium = [r for r in recs if r['priority'] == 'Medium']
            low    = [r for r in recs if r['priority'] == 'Low']

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
  <strong>{priority_svg} {rec['title']}</strong>
  &nbsp;&nbsp;<span style="color:var(--color-text-secondary); font-size:0.85rem">{rec['type']} &middot; {rec['segment']}</span><br><br>
  {rec['message']}<br><br>
  <span style="color:var(--color-accent); font-weight:600">{trending_up_svg} Estimated impact: ~+{rec['impact_pct']}% profit improvement</span>
</div>
''', unsafe_allow_html=True)

            # Export recommendations as CSV
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
            "Adjust the sliders below to simulate the revenue impact of business actions."
        )

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### :material/analytics: Your Assumptions")
            vip_retention = st.slider(
                ":material/emoji_events: Improve VIP customer retention by", 0, 30, 10, step=1,
                format="%d%%", help="% increase in repeat purchases from Champion segment"
            )
            winback_rate = st.slider(
                ":material/autorenew: Win back At-Risk customers", 0, 50, 20, step=5,
                format="%d%%", help="% of at-risk customers you re-engage"
            )
            return_reduction = st.slider(
                ":material/inventory_2: Reduce product returns by", 0, 50, 15, step=5,
                format="%d%%", help="% reduction in return transaction losses"
            )
            new_customer_growth = st.slider(
                ":material/person_add: Increase new customer acquisition", 0, 30, 5, step=1,
                format="%d%%", help="% more new customers per month"
            )

        with col2:
            st.markdown("#### :material/lightbulb: Projected Impact")

            # Advanced projection formulas (Phase 5.1 - Local RFM based)
            rfm = compute_rfm(df)
            
            # Exact segment contributions
            champions_revenue = rfm[rfm['Segment'] == 'Champions']['Monetary'].sum() if not rfm.empty else 0
            loyal_revenue = rfm[rfm['Segment'] == 'Loyal Customers']['Monetary'].sum() if not rfm.empty else 0
            vip_revenue = champions_revenue + loyal_revenue
            
            at_risk_revenue = rfm[rfm['Segment'] == 'At Risk']['Monetary'].sum() if not rfm.empty else 0
            recent_revenue = rfm[rfm['Segment'] == 'Recent Customers']['Monetary'].sum() if not rfm.empty else 0
            
            # Fallbacks in case segment is empty but overall base_revenue is positive
            if vip_revenue == 0 and base_revenue > 0:
                vip_revenue = base_revenue * 0.30
            if at_risk_revenue == 0 and base_revenue > 0:
                at_risk_revenue = base_revenue * 0.10
            if recent_revenue == 0 and base_revenue > 0:
                recent_revenue = base_revenue * 0.05

            ret_summary = get_return_summary(df)
            revenue_lost_returns = ret_summary.get('revenue_lost_from_returns', 0)
            
            # Simulated gains
            revenue_from_vip     = vip_revenue * (vip_retention / 100)
            revenue_from_winback = at_risk_revenue * (winback_rate / 100)
            revenue_from_returns = revenue_lost_returns * (return_reduction / 100)
            revenue_from_new     = recent_revenue * (new_customer_growth / 100)
            total_uplift         = revenue_from_vip + revenue_from_winback + revenue_from_returns + revenue_from_new

            st.metric("Base Revenue", f"£{base_revenue:,.0f}")
            st.metric("VIP Retention Uplift", f"+£{revenue_from_vip:,.0f}")
            st.metric("Win-Back Revenue", f"+£{revenue_from_winback:,.0f}")
            st.metric("Returns Savings", f"+£{revenue_from_returns:,.0f}")
            st.metric("New Customer Revenue", f"+£{revenue_from_new:,.0f}")
            st.markdown("---")
            st.metric(":material/track_changes: Projected Total Revenue",
                      f"£{base_revenue + total_uplift:,.0f}",
                      delta=f"+£{total_uplift:,.0f} (+{total_uplift/base_revenue*100:.1f}%)"
                      if base_revenue > 0 else None)

        st.caption(
            ":material/check_circle: These projections are dynamically calculated using the RFM segment distributions "
            "of the currently loaded retail dataset."
        )

        # ── Excel Export (Phase 5.2) ────────────────────────────────
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

