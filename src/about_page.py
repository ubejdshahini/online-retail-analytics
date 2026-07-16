"""Dataset-aware About & Methodology page for the Streamlit application."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def get_dataset_profile(
    df: pd.DataFrame | None,
    filename: str | None = None,
) -> dict:
    """Return display-ready facts about the currently loaded dataset."""
    if df is None:
        return {"loaded": False, "filename": filename or "No dataset loaded"}

    profile = {
        "loaded": True,
        "filename": filename or "Uploaded dataset",
        "rows": len(df),
        "columns": len(df.columns),
        "date_range": "N/A",
        "countries": df['Country'].nunique() if 'Country' in df.columns else 0,
        "customers": 0,
        "net_revenue": float(df['Revenue'].sum()) if 'Revenue' in df.columns else 0.0,
    }

    if 'InvoiceDate' in df.columns:
        dates = pd.to_datetime(df['InvoiceDate'], errors='coerce').dropna()
        if not dates.empty:
            profile['date_range'] = (
                f"{dates.min().strftime('%b %Y')} – {dates.max().strftime('%b %Y')}"
            )

    if 'CustomerID' in df.columns:
        identified = df.loc[df['CustomerID'].astype(str) != 'Guest', 'CustomerID']
        profile['customers'] = identified.nunique()

    return profile


def _render_dataset_status(df: pd.DataFrame | None, filename: str | None) -> None:
    profile = get_dataset_profile(df, filename)
    st.markdown("## Current dataset")

    if not profile['loaded']:
        st.info(
            ":material/folder_open: No dataset is loaded. The methodology below "
            "still applies; upload a CSV to populate this status panel."
        )
        return

    st.success(
        f":material/check_circle: Methodology is currently being applied to "
        f"**{profile['filename']}**."
    )
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Rows", f"{profile['rows']:,}")
    c2.metric("Date range", profile['date_range'])
    c3.metric("Countries", f"{profile['countries']:,}")
    c4.metric("Identified customers", f"{profile['customers']:,}")
    c5.metric("Net revenue", f"£{profile['net_revenue']:,.0f}")


def _render_pipeline() -> None:
    st.markdown("## How the platform works")
    columns = st.columns(3)
    steps = [
        (
            ":material/upload_file: 1. Upload",
            "A retail CSV is validated against the required transaction columns.",
        ),
        (
            ":material/mop: 2. Clean",
            "Column names, dates, customer IDs, returns, duplicates, and revenue are normalised.",
        ),
        (
            ":material/analytics: 3. Explore",
            "Every KPI, chart, segment, recommendation, and export recalculates from that dataset.",
        ),
    ]
    for column, (title, description) in zip(columns, steps):
        with column:
            with st.container(border=True):
                st.markdown(f"### {title}")
                st.write(description)


def _render_visual_guide() -> None:
    st.markdown(
        "Use these notes to understand what each chart measures and what business "
        "question it can answer."
    )

    with st.expander(":material/calendar_month: Revenue Trends", expanded=True):
        st.markdown("""
| Visualization | How to read it | Interpretation note |
|---|---|---|
| **Monthly Revenue & Order Volume** | Bars show monthly net revenue; the line shows distinct invoice IDs. | Reveals whether revenue movement is supported by order volume. Partial months can distort comparisons. |
| **Monthly Revenue Patterns by Product** | Each selected product has its own monthly chart; the yellow point marks its peak month. | Every panel has an independent revenue scale. Compare each product's pattern, not the apparent heights between panels. |
| **Revenue by Day of Week** | Total net revenue accumulated on Monday through Sunday. | These are totals, not averages per occurrence of each weekday. |
| **Sales Activity by Hour** | Blue shows net revenue; yellow shows transaction-line activity by hour. | “Transactions” here means CSV rows or invoice line items, not distinct orders. |
        """)

    with st.expander(":material/inventory_2: Products and Returns"):
        st.markdown("""
| Visualization | How to read it | Interpretation note |
|---|---|---|
| **Top Products** | Products ranked by total net revenue across the loaded period. | Grouping uses `Description`; inconsistent descriptions can split the same product. |
| **Lowest-Revenue Products** | The lowest positive net-revenue products. | Useful for review, but low revenue alone does not prove a product should be discontinued. |
| **Product Return Rates** | Returned line items divided by all line items for each product. | High rates with very few transactions require caution; use hover details and transaction volume together. |
| **Return Summary** | Returned rows, overall row-level return rate, and absolute revenue lost. | A return is currently identified by negative quantity. |
        """)

    with st.expander(":material/group: Customers"):
        st.markdown("""
| Visualization | How to read it | Interpretation note |
|---|---|---|
| **RFM Segment Bubble Chart** | Horizontal position is average recency, vertical position is average customer revenue, and bubble size is customer count. | Farther right means customers purchased less recently. Hover for frequency and total revenue. |
| **Revenue-Share Donut** | Each slice is a segment's share of identified-customer revenue. | Small segments remain available in the legend and hover details. |
| **CLV Distribution** | Historical net revenue generated by each identified customer. | The chart removes values above the 99th percentile visually so outliers do not flatten the distribution. |
| **New vs Returning** | New customers first purchased in that month; returning customers appeared in an earlier month. | Classification is limited to the history contained in the uploaded file. |
| **Churn Risk** | Identified customers inactive for at least the selected number of days. | Inactivity is measured from the latest date in the dataset, not today's date. |
        """)

    with st.expander(":material/public: Geographic"):
        st.markdown("""
| Visualization | How to read it | Interpretation note |
|---|---|---|
| **Revenue Map** | Every recognized country in the dataset is colored by net revenue. | Country labels must match names Plotly can resolve. The UK toggle affects the map, ranking, and table. |
| **Top Countries** | Countries ranked by net revenue; the slider controls how many are shown. | The Top-N slider limits the bar chart, not the world map. |
| **Country Table** | Net revenue, distinct customers, and distinct invoices by country. | Country spelling and whitespace should be standardized before comparison. |
        """)

    with st.expander(":material/insights: Insights, Scenarios, and Exports"):
        st.markdown("""
| Feature | What it provides | Interpretation note |
|---|---|---|
| **Recommendations** | Rule-based actions derived from RFM, product, return, and shopping-pattern signals. | They are decision support—not machine-learning predictions or guaranteed outcomes. |
| **What-If Simulator** | Applies selected rates to historical segment revenue and return losses. | Results are scenarios, not forecasts; effects are added independently and exclude costs and margins. |
| **Excel Report** | Executive KPIs, customer segments, recommendations, and selected projections. | The report reflects the dataset and slider assumptions active when it is generated. |
        """)


def _render_methodology() -> None:
    st.markdown("### Required input columns")
    st.markdown("""
| Column | Purpose | Accepted alias |
|---|---|---|
| `Invoice` | Order or cancellation identifier | — |
| `StockCode` | Product identifier | — |
| `Description` | Product name used in product charts | — |
| `Quantity` | Units sold; negative values indicate returns | — |
| `InvoiceDate` | Transaction date and time | — |
| `UnitPrice` | Price per unit | `Price` |
| `CustomerID` | Customer identifier | `Customer ID` |
| `Country` | Transaction country | — |
    """)

    st.markdown("### Cleaning rules")
    st.markdown("""
1. Accepted aliases are renamed to the internal schema.
2. Missing customer IDs become `Guest`.
3. Duplicate rows are removed.
4. Rows with `UnitPrice <= 0` are removed.
5. `InvoiceDate` is converted to a datetime value.
6. `IsReturn` is true when `Quantity < 0`.
7. `Revenue = Quantity × UnitPrice`; returns therefore reduce net revenue.
    """)

    st.markdown("### KPI glossary")
    st.markdown("""
| KPI | Calculation |
|---|---|
| **Total Revenue** | Sum of `Revenue`, including negative return revenue |
| **Total Orders** | Count of distinct `Invoice` values |
| **Average Order Value** | Mean net revenue across distinct invoices |
| **Unique Customers** | Distinct `CustomerID` values excluding `Guest` |
| **Top Country** | Country with the highest summed net revenue |
| **Best Product** | Product description with the highest summed net revenue |
| **Return Rate** | Returned transaction rows divided by all transaction rows |
    """)


def _render_segments() -> None:
    st.markdown("### How RFM works")
    st.markdown("""
RFM is calculated only for identified customers and positive-revenue purchases. Each dimension receives a score from **1 to 4**, where 4 is best.

- **Recency:** days since the customer's latest positive purchase, measured from one day after the dataset's latest transaction.
- **Frequency:** number of distinct invoices.
- **Monetary:** total positive revenue generated by the customer.
    """)

    st.markdown("### Segment reference")
    st.markdown("""
| Segment | Meaning | Typical action |
|---|---|---|
| **Champions** | Recent, frequent, and high-spending customers | Reward and retain |
| **Loyal Customers** | Frequent customers who purchased recently | Cross-sell and recognize loyalty |
| **High Spenders** | High monetary value with moderate frequency | Encourage more frequent purchases |
| **Recent Customers** | Purchased recently but have not formed a habit | Strengthen onboarding and second purchase |
| **Potential Loyalists** | Promising customers who need nurturing | Use targeted follow-up offers |
| **At Risk** | Previously valuable customers who have gone quiet | Run a focused win-back campaign |
| **Needs Attention** | Formerly frequent customers who are drifting | Re-engage before they become lost |
| **Lost** | Long-inactive, low-value customers | Use selective reactivation or sunset |
    """)


def _render_limitations() -> None:
    st.warning(
        ":material/warning: Analytics describe the uploaded history. They do not "
        "automatically account for costs, margins, inventory, campaign spend, or future events."
    )
    st.markdown("""
### Interpretation safeguards

- **Partial periods:** incomplete first or last months can look like sharp growth or decline.
- **Net revenue:** returns reduce revenue throughout the dashboard.
- **Independent product scales:** product small multiples reveal patterns but panel heights are not directly comparable.
- **Line items versus orders:** “transactions” in hourly, weekday, and product-volume calculations means dataset rows; “orders” means distinct invoices.
- **Customer history:** new/returning and churn classifications only know the dates present in the uploaded file.
- **Country matching:** inconsistent country labels can create separate groups or fail geographic matching.
- **Product matching:** product analysis groups by description rather than a canonical catalog record.
- **CLV scope:** CLV is historical net revenue, not a predictive lifetime-value model.
- **Scenario outputs:** what-if effects are additive estimates and can overlap in reality.

### Privacy and operation

- Processing occurs in memory while the Streamlit session is active.
- The application does not require a database or external analytics service.
- Uploaded data is not intentionally persisted by the application.
- Downloaded CSV and Excel reports contain information derived from the uploaded dataset.
    """)


def render_about_page(
    df: pd.DataFrame | None,
    filename: str | None = None,
) -> None:
    """Render the complete About & Methodology page."""
    st.title(":material/info: About & Methodology")
    st.markdown(
        "A practical guide to what the dashboard measures, how each visual should "
        "be interpreted, and where the analysis has limits."
    )

    with st.container(border=True):
        st.markdown("### What this platform answers")
        st.markdown(
            "**When is revenue generated? Which products and countries drive it? "
            "Who are the most valuable or at-risk customers? Where are returns "
            "creating losses? What actions are worth testing?**"
        )

    _render_dataset_status(df, filename)
    _render_pipeline()
    st.markdown("---")

    visual_tab, methodology_tab, segments_tab, limitations_tab = st.tabs([
        ":material/visibility: Visual Guide",
        ":material/calculate: Calculations",
        ":material/groups: RFM Segments",
        ":material/gpp_maybe: Limits & Privacy",
    ])

    with visual_tab:
        _render_visual_guide()
    with methodology_tab:
        _render_methodology()
    with segments_tab:
        _render_segments()
    with limitations_tab:
        _render_limitations()
