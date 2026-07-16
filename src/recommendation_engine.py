"""
Functions for RFM customer segmentation and rule-based business recommendations.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from src.analysis import (
    get_product_return_rate,
    get_worst_products,
    get_revenue_by_hour,
    get_revenue_by_day_of_week
)

# RFM COMPUTATION

def _safe_qcut(series: pd.Series, q: int, labels_asc: list) -> pd.Series:
    """
    Robust quantile-based scorer that avoids two common crash cases:

    1. Non-unique bin edges — caused when many rows share the same raw value
       (very common for Recency after date/country filtering).
       Fix: rank with method='first' before cutting so every rank is unique.

    2. Fewer unique values than requested quantiles (q > n_customers).
       Fix: reduce q until it fits, then pad labels to match.
       If q reaches 1 (only one distinct group possible), assign score 1 to all.

    Parameters
    ----------
    series : pd.Series
        The raw metric column (Recency, Frequency, or Monetary).
    q : int
        Desired number of quantile buckets (typically 4).
    labels_asc : list
        Integer labels in ascending order of the metric value.
        For Recency (lower = better) pass [4, 3, 2, 1];
        for Frequency/Monetary (higher = better) pass [1, 2, 3, 4].

    Returns
    -------
    pd.Series[int]
        Integer scores aligned with the input index.
    """
    n = len(series)
    # Always rank first — eliminates non-unique bin-edge errors entirely
    ranked = series.rank(method='first')

    # Reduce q until we can actually form that many bins
    effective_q = min(q, n)
    while effective_q > 1:
        try:
            result = pd.qcut(ranked, q=effective_q,
                             labels=labels_asc[::-1][:effective_q][::-1])
            return result.astype(int)
        except ValueError:
            effective_q -= 1

    # Absolute fallback: assign score 1 to every customer
    return pd.Series(1, index=series.index, dtype=int)

def compute_rfm(df: pd.DataFrame, reference_date: datetime = None) -> pd.DataFrame:
    """
    Computes Recency, Frequency, and Monetary (RFM) scores per customer.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned dataset (output of clean_data()).
    reference_date : datetime, optional
        The date to compute recency from. Defaults to max InvoiceDate + 1 day.

    Returns
    -------
    pd.DataFrame
        One row per customer with columns:
        CustomerID, Recency, Frequency, Monetary,
        R_Score, F_Score, M_Score, RFM_Score, Segment
    """
    required = {'CustomerID', 'InvoiceDate', 'Revenue'}
    if not required.issubset(df.columns):
        return pd.DataFrame()

    # Exclude guests and returns for CLV-based RFM
    df = df[(df['CustomerID'] != 'Guest') & (df['Revenue'] > 0)].copy()
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

    if reference_date is None:
        reference_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)

    invoice_col = 'Invoice' if 'Invoice' in df.columns else None

    # Aggregate per customer
    agg = {
        'InvoiceDate': lambda x: (reference_date - x.max()).days,  # Recency
        'Revenue': 'sum',                                           # Monetary
    }
    if invoice_col:
        agg[invoice_col] = 'nunique'  # Frequency

    rfm = df.groupby('CustomerID').agg(agg).reset_index()

    # Rename columns explicitly to avoid positional ordering bugs
    rename_map = {'InvoiceDate': 'Recency', 'Revenue': 'Monetary'}
    if invoice_col:
        rename_map[invoice_col] = 'Frequency'
    rfm = rfm.rename(columns=rename_map)

    if 'Frequency' not in rfm.columns:
        # Fallback: count rows per customer — merge to preserve alignment
        freq = df.groupby('CustomerID')['Revenue'].count().rename('Frequency').reset_index()
        rfm = rfm.merge(freq, on='CustomerID', how='left')

    # Score each dimension 1–4 (4 = best).
    # _safe_qcut always ranks first (rank='first') so duplicate raw values
    # never produce non-unique bin edges, and it degrades gracefully when
    # fewer than 4 customers remain after filtering.
    rfm['R_Score'] = _safe_qcut(rfm['Recency'],   q=4, labels_asc=[4, 3, 2, 1])
    rfm['F_Score'] = _safe_qcut(rfm['Frequency'],  q=4, labels_asc=[1, 2, 3, 4])
    rfm['M_Score'] = _safe_qcut(rfm['Monetary'],   q=4, labels_asc=[1, 2, 3, 4])

    rfm['RFM_Score'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']

    rfm['Segment'] = rfm.apply(_assign_segment, axis=1)

    return rfm.sort_values('RFM_Score', ascending=False).reset_index(drop=True)


def _assign_segment(row) -> str:
    """Maps RFM scores to business-friendly segment names."""
    r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
    score = row['RFM_Score']

    if r >= 3 and f >= 3 and m >= 3:
        return 'Champions'           # Bought recently, often, and spend most
    elif r >= 3 and f >= 3:
        return 'Loyal Customers'     # Buy often and recently
    elif r >= 3 and m >= 3:
        return 'High Spenders'       # Spend a lot but moderate frequency
    elif r >= 3 and f <= 2:
        return 'Recent Customers'    # Bought recently but not often yet
    elif r <= 2 and f >= 3 and m >= 3:
        return 'At Risk'             # Were great customers, haven't returned
    elif r <= 2 and f >= 3:
        return 'Needs Attention'     # Frequent before, now drifting
    elif r == 1 and f == 1 and m == 1:
        return 'Lost'                # Haven't bought in a long time, low value
    else:
        return 'Potential Loyalists' # Promising but need nurturing


def get_segment_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a summary table of segments with customer count,
    average monetary value, and average recency.
    """
    if 'Segment' not in rfm.columns:
        return pd.DataFrame()

    summary = rfm.groupby('Segment').agg(
        Customers=('CustomerID', 'count'),
        Avg_Recency_Days=('Recency', 'mean'),
        Avg_Frequency=('Frequency', 'mean'),
        Avg_Revenue=('Monetary', 'mean'),
        Total_Revenue=('Monetary', 'sum')
    ).reset_index()

    summary = summary.round(2).sort_values('Total_Revenue', ascending=False)
    return summary


# RECOMMENDATION ENGINE

def generate_recommendations(df: pd.DataFrame) -> list[dict]:
    """
    Generates rule-based business recommendations.
    Each recommendation includes:
      - type        : category of recommendation
      - segment     : which customer group it targets (if applicable)
      - title       : short action label
      - message     : detailed explanation for the client
      - impact_pct  : estimated % improvement in profit if acted upon
      - priority    : 'High' / 'Medium' / 'Low'

    Returns
    -------
    list[dict]
        Sorted by impact_pct descending.
    """
    recommendations = []

    # --- Prerequisite: compute RFM ---
    rfm = compute_rfm(df)
    if rfm.empty:
        return []

    seg_summary = get_segment_summary(rfm)
    total_revenue = rfm['Monetary'].sum()

    # ── Rule 1: Champions — reward them ──────────────────────────
    champions = rfm[rfm['Segment'] == 'Champions']
    if len(champions) > 0:
        champ_revenue = champions['Monetary'].sum()
        champ_pct = round(champ_revenue / total_revenue * 100, 1)
        recommendations.append({
            'type': 'Retention',
            'segment': 'Champions',
            'title': 'Reward Your Top Customers',
            'message': (
                f"You have {len(champions)} Champion customers who generate "
                f"{champ_pct}% of total revenue. "
                "Launch an exclusive loyalty programme (early access, free shipping, "
                "personalised discounts) to keep them engaged and prevent churn."
            ),
            'impact_pct': round(champ_pct * 0.05, 1),  # retaining 5% extra of their spend
            'priority': 'High'
        })

    # ── Rule 2: At-Risk customers — win-back ─────────────────────
    at_risk = rfm[rfm['Segment'] == 'At Risk']
    if len(at_risk) > 0:
        at_risk_revenue = at_risk['Monetary'].sum()
        at_risk_pct = round(at_risk_revenue / total_revenue * 100, 1)
        recommendations.append({
            'type': 'Win-Back',
            'segment': 'At Risk',
            'title': 'Re-engage At-Risk Customers',
            'message': (
                f"{len(at_risk)} customers who used to be valuable are now inactive. "
                f"They previously accounted for {at_risk_pct}% of revenue. "
                "Send a personalised win-back email with a time-limited discount (e.g. 15% off) "
                "to recover a portion of that revenue."
            ),
            'impact_pct': round(at_risk_pct * 0.20, 1),  # recover 20% of lost spend
            'priority': 'High'
        })

    # ── Rule 3: Potential Loyalists — convert them ───────────────
    potentials = rfm[rfm['Segment'] == 'Potential Loyalists']
    if len(potentials) > 0:
        recommendations.append({
            'type': 'Upsell',
            'segment': 'Potential Loyalists',
            'title': 'Convert Potential Loyalists to Loyal Customers',
            'message': (
                f"{len(potentials)} customers have shown interest but haven't committed yet. "
                "Offer a 'second purchase' incentive (e.g. 10% off next order) or "
                "introduce a membership scheme to move them into the Loyal tier."
            ),
            'impact_pct': 3.5,
            'priority': 'Medium'
        })

    # Rule 4: High return rate products
    if 'IsReturn' in df.columns and 'Description' in df.columns:
        return_rate = get_product_return_rate(df)
        high_return = return_rate[return_rate['ReturnRate_%'] > 20]
        if len(high_return) > 0:
            top_return_product = high_return.iloc[0]['Description']
            top_return_rate = high_return.iloc[0]['ReturnRate_%']
            recommendations.append({
                'type': 'Quality',
                'segment': 'All',
                'title': 'Investigate High-Return Products',
                'message': (
                    f"{len(high_return)} products have a return rate above 20%. "
                    f"The worst offender is \"{top_return_product}\" at {top_return_rate}%. "
                    "Review product descriptions, packaging, and quality to reduce return costs."
                ),
                'impact_pct': 2.5,
                'priority': 'Medium'
            })

    # Rule 5: Low revenue products
    if 'Description' in df.columns and 'Revenue' in df.columns:
        worst = get_worst_products(df, n=20)
        if len(worst) > 0:
            recommendations.append({
                'type': 'Pricing / Catalogue',
                'segment': 'All',
                'title': 'Review or Discontinue Low-Revenue Products',
                'message': (
                    f"{len(worst)} products generate less than £{worst['Revenue'].max():,.0f} "
                    "total revenue. Consider discontinuing them or adjusting their price to "
                    "free up storage and reduce operational overhead."
                ),
                'impact_pct': 1.5,
                'priority': 'Low'
            })

    # Rule 6: Peak hour — only surface if top 2 hours carry a disproportionate
    # share of daily revenue (>40%), which is non-obvious from the bar chart alone.
    if 'InvoiceDate' in df.columns and 'Revenue' in df.columns:
        hourly = get_revenue_by_hour(df)
        if not hourly.empty:
            total_hourly_rev = hourly['Revenue'].sum()
            if total_hourly_rev > 0:
                top2_rev = hourly.nlargest(2, 'Revenue')['Revenue'].sum()
                top2_pct = round(top2_rev / total_hourly_rev * 100, 1)
                if top2_pct >= 40:
                    peak_hours = hourly.nlargest(2, 'Revenue')['Hour'].tolist()
                    hours_str = ' and '.join(f'{int(h)}:00' for h in sorted(peak_hours))
                    dow = get_revenue_by_day_of_week(df)
                    peak_day = dow.loc[dow['Revenue'].idxmax(), 'DayOfWeek'] if not dow.empty else None
                    day_note = f" on {peak_day}s" if peak_day else ""
                    recommendations.append({
                        'type': 'Marketing',
                        'segment': 'All',
                        'title': 'Revenue Is Dangerously Concentrated in Two Hours',
                        'message': (
                            f"**{top2_pct}%** of all daily revenue arrives between {hours_str}{day_note}. "
                            "This is a structural risk: a single disruption (outage, delayed email) "
                            "during those windows costs nearly half your daily income. "
                            "Run A/B tests to spread demand — staggered promotions or morning flash "
                            "sales can reduce this concentration while growing total volume."
                        ),
                        'impact_pct': round(top2_pct * 0.04, 1),
                        'priority': 'Medium'
                    })

    # Rule 7: Single-purchase customers
    if 'Frequency' in rfm.columns:
        one_timers = rfm[rfm['Frequency'] == 1]
        if len(one_timers) > 0:
            one_pct = round(len(one_timers) / len(rfm) * 100, 1)
            # Calculate how much revenue is locked in one-timers
            one_timer_revenue = one_timers['Monetary'].sum()
            avg_loyal_monetary = rfm[rfm['Frequency'] > 2]['Monetary'].mean() if len(rfm[rfm['Frequency'] > 2]) > 0 else 0
            uplift_potential = (avg_loyal_monetary - one_timers['Monetary'].mean()) * len(one_timers) * 0.15
            recommendations.append({
                'type': 'Cross-Sell',
                'segment': 'Recent Customers',
                'title': 'Convert One-Time Buyers to Repeat Customers',
                'message': (
                    f"**{one_pct}%** of customers ({len(one_timers):,}) have purchased exactly once, "
                    f"generating £{one_timer_revenue:,.0f} total. "
                    "If just 15% of them make a second purchase at the loyalty-customer average, "
                    f"that adds ~£{uplift_potential:,.0f} in incremental revenue. "
                    "A triggered email 7 days post-purchase with a 10% second-order incentive "
                    "is the single highest-ROI action for this segment."
                ),
                'impact_pct': round(one_pct * 0.10, 1),
                'priority': 'High'
            })

    # Rule 8: Return rate spike — flag the single worst month if its rate is
    # materially above the annual average (non-obvious without trend analysis).
    if 'IsReturn' in df.columns and 'InvoiceDate' in df.columns:
        from src.analysis import get_return_rate_over_time
        trend = get_return_rate_over_time(df)
        if not trend.empty and len(trend) >= 3:
            avg_rate = trend['ReturnRate_%'].mean()
            worst = trend.loc[trend['ReturnRate_%'].idxmax()]
            spike = worst['ReturnRate_%'] - avg_rate
            if spike >= 5:  # at least 5 pp above average
                recommendations.append({
                    'type': 'Quality / Operations',
                    'segment': 'All',
                    'title': f"Return Rate Spike in {worst['YearMonth']} Needs Investigation",
                    'message': (
                        f"The return rate in **{worst['YearMonth']}** was **{worst['ReturnRate_%']:.1f}%** — "
                        f"{spike:.1f} percentage points above your {avg_rate:.1f}% annual average. "
                        f"That month alone cost £{worst['RevenueLost']:,.0f} in lost revenue. "
                        "Isolated spikes like this typically trace to a single product batch, "
                        "a fulfilment error, or a quality issue. Audit the top-returned products "
                        "from that month before the pattern repeats."
                    ),
                    'impact_pct': round(worst['RevenueLost'] / rfm['Monetary'].sum() * 100, 1),
                    'priority': 'High'
                })

    # Sort by impact descending
    recommendations.sort(key=lambda x: x['impact_pct'], reverse=True)
    return recommendations
