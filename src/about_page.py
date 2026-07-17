"""Dataset-aware About & Methodology page simplified for business managers."""

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
        "date_range": "N/A",
        "net_revenue": float(df['Revenue'].sum()) if 'Revenue' in df.columns else 0.0,
        "customers": df.loc[df['CustomerID'] != 'Guest', 'CustomerID'].nunique() if 'CustomerID' in df.columns else 0,
        "countries": df['Country'].nunique() if 'Country' in df.columns else 0,
    }

    if 'InvoiceDate' in df.columns:
        dates = pd.to_datetime(df['InvoiceDate'], errors='coerce').dropna()
        if not dates.empty:
            profile['date_range'] = (
                f"{dates.min().strftime('%b %Y')} – {dates.max().strftime('%b %Y')}"
            )

    return profile


def render_about_page(
    df: pd.DataFrame | None,
    filename: str | None = None,
) -> None:
    """Render the complete, simplified About & Methodology page for managers."""
    st.title(":material/info: About & Methodology")
    st.markdown(
        "A quick executive guide on how the platform analyses your sales data and segments customers."
    )

    # 1. Executive Summary
    with st.container(border=True):
        st.markdown("### :material/lightbulb: Business Value & Key Questions Answered")
        st.markdown(
            "This platform processes your raw sales transactions to deliver clear business insights:\n"
            "- **Revenue & Returns:** When and where is revenue generated? Which products drive the most returns?\n"
            "- **Customer Value:** Who are your top customers, and who is at risk of leaving?\n"
            "- **Actionable Marketing:** When is the best time to promote, and which customer groups should you target?"
        )

    # 2. Customer Segmentation Methodology
    st.markdown("---")
    st.markdown("### :material/groups: Customer Segmentation (RFM Methodology)")
    st.markdown(
        "We segment your customers based on three core behavioral metrics:\n"
        "- **Recency:** How recently did they purchase? (Fewer days = better)\n"
        "- **Frequency:** How many times did they buy?\n"
        "- **Monetary:** How much total revenue did they generate?"
    )

    st.markdown("#### Segment Guide & Actions")
    st.markdown("""
| Customer Segment | What it means | Recommended Business Action |
|---|---|---|
| **Champions** | Bought recently, buy frequently, and spend the most. | **Reward them:** Loyalty programs, early access, exclusive offers. |
| **Loyal Customers** | Buy regularly and recently. | **Upsell:** Cross-sell products and offer loyalty rewards. |
| **High Spenders** | Spend a lot of money but don't buy very often. | **Re-engage:** Send personalized product recommendations. |
| **Recent Customers** | Bought from you recently but only once or twice. | **Nurture:** Welcome emails and incentives for a 2nd purchase. |
| **At Risk** | Used to buy often and spend well, but haven't bought in months. | **Win-back:** Send high-value, time-limited discount offers. |
| **Needs Attention** | Drifting away; frequency and recency are dropping. | **Re-engage:** Customer surveys, custom discounts. |
| **Lost** | Haven't purchased in a long time with very low overall spend. | **Minimize spend:** Spend less marketing budget here. |
    """)

    # 4. Accepted Upload Format
    st.markdown("---")
    st.markdown("### :material/folder: Upload Requirements")
    st.markdown(
        "To ensure successful analysis, your uploaded CSV or Excel file should contain these standard columns:\n"
        "- **Order Identifiers:** `Invoice`, `StockCode`, `Description`\n"
        "- **Sales Metrics:** `Quantity` (negative represents returns), `UnitPrice` (or `Price`)\n"
        "- **Customer & Location:** `CustomerID` (or `Customer ID`), `Country`, and the transaction date `InvoiceDate`."
    )
