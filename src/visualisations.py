"""
Functions for generating Plotly visualizations.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from src.theme import CHART_COLORS, THEME


# ── Colour palette (consistent across all charts) ──────────────────────
COLORS = {
    'primary':    THEME['accent'],
    'secondary':  THEME['warning'],
    'success':    THEME['success'],
    'danger':     THEME['error'],
    'neutral':    CHART_COLORS[5],
    'background': THEME['page_bg'],
    'surface':    THEME['card_bg'],
    'text':       THEME['text_primary'],
    'border':     THEME['border'],
}

PALETTE = list(CHART_COLORS)

BASE_LAYOUT = dict(
    paper_bgcolor=COLORS['background'],
    plot_bgcolor=COLORS['surface'],
    font=dict(color=COLORS['text'], family='Inter, sans-serif', size=13),
    margin=dict(l=40, r=40, t=60, b=40),
    legend=dict(bgcolor='rgba(0,0,0,0)', borderwidth=0),
)


def _apply_base(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(title=dict(text=title, font=dict(size=18, color=COLORS['text'])),
                      **BASE_LAYOUT)
    fig.update_xaxes(showgrid=True, gridcolor=COLORS['border'], zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=COLORS['border'], zeroline=False)
    return fig


# REVENUE CHARTS

def plot_monthly_revenue(monthly_df: pd.DataFrame) -> go.Figure:
    """
    Bar + line combo: monthly revenue bars with MoM growth % line overlay.
    Input: output of get_monthly_revenue().
    """
    if monthly_df.empty:
        return go.Figure()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=monthly_df['YearMonth'],
        y=monthly_df['Revenue'],
        name='Revenue (£)',
        marker_color=COLORS['primary'],
        opacity=0.85,
    ), secondary_y=False)

    if 'Revenue_Growth_%' in monthly_df.columns:
        fig.add_trace(go.Scatter(
            x=monthly_df['YearMonth'],
            y=monthly_df['Revenue_Growth_%'],
            name='MoM Growth %',
            mode='lines+markers',
            line=dict(color=COLORS['secondary'], width=2.5),
            marker=dict(size=6),
        ), secondary_y=True)
        fig.update_yaxes(title_text='Growth %', secondary_y=True,
                         showgrid=False, color=COLORS['secondary'])

    fig.update_yaxes(title_text='Revenue (£)', secondary_y=False)
    fig.update_xaxes(tickangle=-45)
    return _apply_base(fig, 'Monthly Revenue & Month-over-Month Growth')


def plot_revenue_by_day_of_week(dow_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart: revenue by day of week."""
    if dow_df.empty:
        return go.Figure()

    fig = go.Figure(go.Bar(
        x=dow_df['Revenue'],
        y=dow_df['DayOfWeek'],
        orientation='h',
        marker_color=COLORS['primary'],
        text=dow_df['Revenue'].apply(lambda v: f'£{v:,.0f}'),
        textposition='auto',
    ))
    return _apply_base(fig, 'Revenue by Day of Week')


def plot_revenue_by_hour(hourly_df: pd.DataFrame) -> go.Figure:
    """Area chart: revenue and transaction volume by hour of day."""
    if hourly_df.empty:
        return go.Figure()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=hourly_df['Hour'], y=hourly_df['Revenue'],
        name='Revenue (£)', fill='tozeroy',
        line=dict(color=COLORS['primary'], width=2),
        fillcolor=COLORS['primary'],
        opacity=0.25,
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=hourly_df['Hour'], y=hourly_df['Transactions'],
        name='Transactions', mode='lines+markers',
        line=dict(color=COLORS['secondary'], width=2, dash='dot'),
        marker=dict(size=5),
    ), secondary_y=True)
    fig.update_xaxes(title_text='Hour of Day', dtick=1)
    fig.update_yaxes(title_text='Revenue (£)', secondary_y=False)
    fig.update_yaxes(title_text='Transactions', secondary_y=True, showgrid=False)
    return _apply_base(fig, 'Sales Activity by Hour of Day')


# PRODUCT CHARTS

def plot_top_products(top_df: pd.DataFrame, n: int = 10) -> go.Figure:
    """Horizontal bar chart: top N products by revenue."""
    if top_df.empty:
        return go.Figure()

    df = top_df.head(n).sort_values('Revenue')
    fig = go.Figure(go.Bar(
        x=df['Revenue'], y=df['Description'],
        orientation='h',
        marker=dict(color=COLORS['success']),
        text=df['Revenue'].apply(lambda v: f'£{v:,.0f}'),
        textposition='auto',
    ))
    fig.update_yaxes(tickfont=dict(size=11))
    return _apply_base(fig, f'Top {n} Products by Revenue')


def plot_product_return_rates(return_df: pd.DataFrame, n: int = 15) -> go.Figure:
    """Bar chart: products with highest return rates, grouped by risk level."""
    if return_df.empty:
        return go.Figure()

    df = return_df.head(n).sort_values('ReturnRate_%').copy()

    # A single set of risk bands is easier to interpret than bar colours that
    # conflict with a separate threshold line.
    risk_bands = [
        (35, 'Critical (35%+)', '#B91C1C'),
        (25, 'High (25–34.9%)', '#EA580C'),
        (15, 'Elevated (15–24.9%)', '#D97706'),
        (0, 'Normal (<15%)', '#64748B'),
    ]

    def classify(rate: float) -> tuple[str, str]:
        for lower_bound, label, color in risk_bands:
            if rate >= lower_bound:
                return label, color

    risk = df['ReturnRate_%'].apply(classify)
    df['Risk'] = risk.str[0]
    colors = risk.str[1]

    fig = go.Figure(go.Bar(
        x=df['ReturnRate_%'], y=df['Description'],
        orientation='h',
        marker_color=colors,
        text=df['ReturnRate_%'].apply(lambda v: f'{v:.1f}%'),
        textposition='auto',
        customdata=df[['Risk']],
        hovertemplate=(
            '<b>%{y}</b><br>Return rate: %{x:.1f}%'
            '<br>Risk level: %{customdata[0]}<extra></extra>'
        ),
        showlegend=False,
    ))

    # Invisible point traces provide a compact, explicit legend for the bar
    # colours without splitting the ordered bars into separate traces.
    for _, label, color in reversed(risk_bands):
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers', name=label,
            marker=dict(size=10, color=color, symbol='square'),
            hoverinfo='skip',
        ))

    fig = _apply_base(
        fig,
        'Product Return Rates — higher rates indicate greater risk'
    )
    fig.update_xaxes(title_text='Return rate', ticksuffix='%', rangemode='tozero')
    fig.update_yaxes(tickfont=dict(size=11), showgrid=False)
    fig.update_layout(
        legend=dict(
            title=dict(text='Risk level', font=dict(size=13)),
            orientation='v',
            yanchor='top', y=1,
            xanchor='left', x=1.01,
            font=dict(size=12),
            itemsizing='constant',
            tracegroupgap=8,
        ),
        margin=dict(l=40, r=210, t=60, b=55),
    )
    return fig


# CUSTOMER CHARTS

def plot_rfm_segments(seg_summary: pd.DataFrame) -> go.Figure:
    """
    Bubble chart: segments plotted by Avg Recency vs Avg Revenue,
    bubble size = number of customers.
    """
    if seg_summary.empty:
        return go.Figure()

    fig = go.Figure()
    for i, row in seg_summary.iterrows():
        fig.add_trace(go.Scatter(
            x=[row['Avg_Recency_Days']],
            y=[row['Avg_Revenue']],
            mode='markers+text',
            name=row['Segment'],
            text=[row['Segment']],
            textposition='top center',
            marker=dict(
                size=max(row['Customers'] / seg_summary['Customers'].max() * 80, 12),
                color=PALETTE[i % len(PALETTE)],
                opacity=0.85,
                line=dict(width=1, color=COLORS['background']),
            ),
        ))
    fig.update_xaxes(title_text='Avg Days Since Last Purchase (Recency ↑ = worse)')
    fig.update_yaxes(title_text='Avg Revenue per Customer (£)')
    fig.update_layout(showlegend=False)
    return _apply_base(fig, 'Customer Segments — Recency vs Revenue\n(bubble size = # customers)')


def plot_segment_revenue_share(seg_summary: pd.DataFrame) -> go.Figure:
    """Donut chart: each segment's share of total revenue."""
    if seg_summary.empty:
        return go.Figure()

    fig = go.Figure(go.Pie(
        labels=seg_summary['Segment'],
        values=seg_summary['Total_Revenue'],
        hole=0.55,
        marker=dict(colors=PALETTE[:len(seg_summary)],
                    line=dict(color=COLORS['background'], width=2)),
        textinfo='label+percent',
        hovertemplate='%{label}<br>Revenue: £%{value:,.0f}<extra></extra>',
    ))
    fig.update_layout(
        annotations=[dict(text='Revenue<br>Share', x=0.5, y=0.5,
                          font_size=14, showarrow=False,
                          font_color=COLORS['text'])],
        showlegend=False,
    )
    return _apply_base(fig, 'Revenue Share by Customer Segment')


def plot_clv_distribution(clv_df: pd.DataFrame) -> go.Figure:
    """Histogram: distribution of customer lifetime value."""
    if clv_df.empty or 'TotalRevenue' not in clv_df.columns:
        return go.Figure()

    # Cap at 99th percentile to avoid long tail distortion
    cap = clv_df['TotalRevenue'].quantile(0.99)
    df = clv_df[clv_df['TotalRevenue'] <= cap]

    fig = go.Figure(go.Histogram(
        x=df['TotalRevenue'],
        nbinsx=50,
        marker_color=COLORS['primary'],
        opacity=0.8,
    ))
    fig.update_xaxes(title_text='Total Revenue per Customer (£)')
    fig.update_yaxes(title_text='Number of Customers')
    return _apply_base(fig, 'Customer Lifetime Value Distribution (capped at 99th pct)')


def plot_new_vs_returning(new_ret_df: pd.DataFrame) -> go.Figure:
    """Stacked bar chart: new vs returning customers per month."""
    if new_ret_df.empty:
        return go.Figure()

    fig = go.Figure()
    for ctype, color in [('New', COLORS['success']), ('Returning', COLORS['primary'])]:
        sub = new_ret_df[new_ret_df['CustomerType'] == ctype]
        fig.add_trace(go.Bar(
            x=sub['YearMonth'], y=sub['Customers'],
            name=ctype, marker_color=color, opacity=0.85,
        ))
    fig.update_layout(barmode='stack')
    fig.update_xaxes(tickangle=-45)
    return _apply_base(fig, 'New vs Returning Customers per Month')


# GEOGRAPHIC CHART

def plot_country_revenue(geo_df: pd.DataFrame, exclude_uk: bool = True) -> go.Figure:
    """
    Choropleth world map of revenue by country.
    exclude_uk: removes United Kingdom to avoid scale distortion.
    """
    if geo_df.empty or 'Country' not in geo_df.columns:
        return go.Figure()

    df = geo_df.copy()
    if exclude_uk:
        df = df[df['Country'] != 'United Kingdom']

    fig = px.choropleth(
        df,
        locations='Country',
        locationmode='country names',
        color='Revenue',
        color_continuous_scale=[[i / (len(PALETTE) - 1), color]
                                for i, color in enumerate(PALETTE)],
        hover_data={'Revenue': ':,.0f'},
        labels={'Revenue': 'Revenue (£)'},
    )
    fig.update_layout(
        geo=dict(
            bgcolor=COLORS['background'],
            lakecolor=COLORS['background'],
            landcolor=THEME['border'],
            showframe=False,
        ),
        coloraxis_colorbar=dict(title='Revenue (£)'),
        **BASE_LAYOUT,
    )
    fig.update_layout(title=dict(
        text='Geographic Revenue Distribution' + (' (excl. UK)' if exclude_uk else ''),
        font=dict(size=18, color=COLORS['text'])
    ))
    return fig


def plot_top_countries_bar(geo_df: pd.DataFrame, n: int = 10,
                           exclude_uk: bool = True) -> go.Figure:
    """Horizontal bar chart: top N countries by revenue."""
    if geo_df.empty:
        return go.Figure()

    df = geo_df.copy()
    if exclude_uk:
        df = df[df['Country'] != 'United Kingdom']

    df = df.head(n).sort_values('Revenue')
    fig = go.Figure(go.Bar(
        x=df['Revenue'], y=df['Country'],
        orientation='h',
        marker_color=COLORS['secondary'],
        text=df['Revenue'].apply(lambda v: f'£{v:,.0f}'),
        textposition='auto',
    ))
    title = f'Top {n} Countries by Revenue' + (' (excl. UK)' if exclude_uk else '')
    return _apply_base(fig, title)


# KPI SUMMARY CARD

def format_kpi_cards(kpi_dict: dict) -> list[dict]:
    """
    Converts raw KPI dict into a list of display-ready card dicts.
    Each card: {label, value, delta (optional)}
    Streamlit: for card in cards: st.metric(card['label'], card['value'])
    """
    cards = []
    formatters = {
        'total_revenue':    ('Total Revenue',    lambda v: f'£{v:,.0f}'),
        'total_orders':     ('Total Orders',     lambda v: f'{v:,}'),
        'avg_order_value':  ('Avg Order Value',  lambda v: f'£{v:,.2f}'),
        'unique_customers': ('Unique Customers', lambda v: f'{v:,}'),
        'top_country':      ('Top Country',      lambda v: str(v)),
        'best_product':     ('Best Product',     lambda v: str(v)[:40]),
        'return_rate_%':    ('Return Rate',      lambda v: f'{v:.1f}%'),
    }
    for key, (label, fmt) in formatters.items():
        if key in kpi_dict:
            cards.append({'label': label, 'value': fmt(kpi_dict[key])})
    return cards
