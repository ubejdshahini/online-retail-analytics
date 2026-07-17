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
SEGMENT_PALETTE = PALETTE + ['#06B6D4', '#F97316']
MAP_REVENUE_SCALE = [
    [0.00, THEME['accent_tint']],
    [0.33, '#93C5FD'],
    [0.66, '#60A5FA'],
    [1.00, THEME['accent']],
]

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
    fig.update_xaxes(showgrid=True, gridcolor=COLORS['border'], zeroline=False,
                     automargin=True)
    fig.update_yaxes(showgrid=True, gridcolor=COLORS['border'], zeroline=False,
                     automargin=True)
    return fig


# REVENUE CHARTS

def plot_monthly_revenue(monthly_df: pd.DataFrame) -> go.Figure:
    """
    Bar + line combo: monthly revenue bars with order volume line overlay.
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

    if 'Orders' in monthly_df.columns:
        fig.add_trace(go.Scatter(
            x=monthly_df['YearMonth'],
            y=monthly_df['Orders'],
            name='Orders',
            mode='lines+markers',
            line=dict(color=COLORS['secondary'], width=2.5),
            marker=dict(size=6),
        ), secondary_y=True)
        fig.update_yaxes(title_text='Orders', secondary_y=True,
                         showgrid=False, color=COLORS['secondary'])

    fig.update_yaxes(title_text='Revenue (£)', secondary_y=False)
    fig.update_xaxes(tickangle=-45, automargin=True, tickfont=dict(size=11))
    return _apply_base(fig, 'Monthly Revenue & Order Volume')


def plot_monthly_product_revenue(product_monthly_df: pd.DataFrame) -> go.Figure:
    """Small-multiple monthly revenue trends for the dataset's top products."""
    if product_monthly_df.empty:
        return go.Figure()

    products = product_monthly_df['Description'].drop_duplicates().tolist()
    column_count = 2
    row_count = int(np.ceil(len(products) / column_count))
    subplot_titles = []
    for product in products:
        product_total = product_monthly_df.loc[
            product_monthly_df['Description'] == product, 'Revenue'
        ].sum()
        display_name = product if len(product) <= 34 else f'{product[:31]}...'
        subplot_titles.append(
            f'<b>{display_name}</b>  ·  Total £{product_total:,.0f}'
        )

    fig = make_subplots(
        rows=row_count,
        cols=column_count,
        subplot_titles=subplot_titles,
        horizontal_spacing=0.10,
        vertical_spacing=min(0.14, 0.32 / row_count),
    )

    for index, product in enumerate(products):
        row = index // column_count + 1
        column = index % column_count + 1
        color = PALETTE[index % len(PALETTE)]
        product_data = product_monthly_df[
            product_monthly_df['Description'] == product
        ]
        peak_revenue = product_data['Revenue'].max()
        marker_colors = [
            COLORS['secondary'] if value == peak_revenue else color
            for value in product_data['Revenue']
        ]
        marker_sizes = [
            10 if value == peak_revenue else 4
            for value in product_data['Revenue']
        ]

        fig.add_trace(go.Scatter(
            x=product_data['YearMonth'],
            y=product_data['Revenue'],
            name=product,
            mode='lines+markers',
            line=dict(color=color, width=3, shape='spline', smoothing=0.35),
            marker=dict(
                color=marker_colors,
                size=marker_sizes,
                line=dict(color=COLORS['surface'], width=1),
            ),
            hovertemplate=(
                f'<b>{product}</b><br>'
                'Month: %{x}<br>'
                'Revenue: £%{y:,.0f}<extra></extra>'
            ),
            showlegend=False,
        ), row=row, col=column)

    fig = _apply_base(fig, 'Monthly Revenue Patterns by Product')
    fig.update_layout(
        height=max(560, row_count * 245 + 100),
        showlegend=False,
        margin=dict(l=70, r=40, t=95, b=70),
    )
    fig.update_annotations(font=dict(size=13, color=COLORS['text']))
    fig.update_xaxes(tickangle=-35, showgrid=False)
    fig.update_yaxes(
        tickprefix='£',
        tickformat='~s',
        rangemode='tozero',
        gridcolor=COLORS['border'],
    )

    # Show month labels only on the lowest populated chart in each column.
    last_row_by_column = {
        1: row_count,
        2: row_count if len(products) % 2 == 0 else max(1, row_count - 1),
    }
    for index in range(len(products)):
        row = index // column_count + 1
        column = index % column_count + 1
        fig.update_xaxes(
            showticklabels=row == last_row_by_column[column],
            row=row,
            col=column,
        )

    if len(products) % 2:
        fig.update_xaxes(visible=False, row=row_count, col=2)
        fig.update_yaxes(visible=False, row=row_count, col=2)
    return fig


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
        name='Revenue (£)', mode='lines+markers',
        line=dict(color=COLORS['primary'], width=2),
        marker=dict(size=5),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=hourly_df['Hour'], y=hourly_df['Transactions'],
        name='Transactions', mode='lines+markers',
        line=dict(color=COLORS['secondary'], width=2),
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

    hover_columns = ['Risk']
    hover_lines = ['<br>Risk level: %{customdata[0]}']
    for column, label in [
        ('SalesUnits', 'Units sold'),
        ('ReturnedUnits', 'Units returned'),
        ('SalesTransactions', 'Sales transactions'),
    ]:
        if column in df.columns:
            hover_columns.append(column)
            hover_lines.append(
                f'<br>{label}: %{{customdata[{len(hover_columns) - 1}]:,.0f}}'
            )

    fig = go.Figure(go.Bar(
        x=df['ReturnRate_%'], y=df['Description'],
        orientation='h',
        marker_color=colors,
        text=df['ReturnRate_%'].apply(lambda v: f'{v:.1f}%'),
        textposition='auto',
        customdata=df[hover_columns],
        hovertemplate=(
            '<b>%{y}</b><br>Return rate: %{x:.1f}%'
            + ''.join(hover_lines)
            + '<extra></extra>'
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


# RETURNS CHARTS

def plot_return_rate_over_time(return_trend_df: pd.DataFrame) -> go.Figure:
    """
    Dual-axis line chart: monthly return rate (%) on left axis,
    revenue lost to returns (£) on right axis.
    Input: output of get_return_rate_over_time().
    """
    if return_trend_df.empty:
        return go.Figure()

    fig = make_subplots(specs=[[{'secondary_y': True}]])

    fig.add_trace(go.Scatter(
        x=return_trend_df['YearMonth'],
        y=return_trend_df['ReturnRate_%'],
        name='Return Rate (%)',
        mode='lines+markers',
        line=dict(color=COLORS['danger'], width=2.5),
        marker=dict(size=6),
        hovertemplate='%{x}<br>Return rate: %{y:.1f}%<extra></extra>',
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=return_trend_df['YearMonth'],
        y=return_trend_df['RevenueLost'],
        name='Revenue Lost (£)',
        mode='lines+markers',
        line=dict(color=COLORS['secondary'], width=2, dash='dot'),
        marker=dict(size=5),
        hovertemplate='%{x}<br>Revenue lost: £%{y:,.0f}<extra></extra>',
    ), secondary_y=True)

    fig.update_yaxes(title_text='Return Rate (%)', secondary_y=False,
                     ticksuffix='%')
    fig.update_yaxes(title_text='Revenue Lost (£)', secondary_y=True,
                     showgrid=False, tickprefix='£')
    fig.update_xaxes(tickangle=-45, automargin=True, tickfont=dict(size=11))
    return _apply_base(fig, 'Return Rate & Revenue Lost Over Time')


def plot_top_returning_customers(customers_df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart: top customers by revenue lost from their returns.
    Input: output of get_top_returning_customers().
    """
    if customers_df.empty:
        return go.Figure()

    df = customers_df.sort_values('RevenueLost')
    fig = go.Figure(go.Bar(
        x=df['RevenueLost'],
        y=df['CustomerID'].astype(str),
        orientation='h',
        marker_color=COLORS['danger'],
        text=df['RevenueLost'].apply(lambda v: f'£{v:,.0f}'),
        textposition='auto',
        customdata=df[['ReturnTransactions']],
        hovertemplate=(
            'Customer: <b>%{y}</b><br>'
            'Revenue lost: £%{x:,.0f}<br>'
            'Return transactions: %{customdata[0]:,}<extra></extra>'
        ),
    ))
    fig.update_xaxes(title_text='Revenue Lost to Returns (£)', tickprefix='£', automargin=True)
    fig.update_yaxes(tickfont=dict(size=11), automargin=True)
    return _apply_base(fig, 'Top Customers by Revenue Lost from Returns')


def plot_returns_revenue_impact(impact_df: pd.DataFrame) -> go.Figure:
    """
    Stacked bar + line chart showing monthly Gross Revenue, Revenue Lost,
    and Net Revenue — so the impact of returns is immediately visible.
    Input: output of get_returns_revenue_impact().
    """
    if impact_df.empty:
        return go.Figure()

    fig = make_subplots(specs=[[{'secondary_y': True}]])

    fig.add_trace(go.Bar(
        x=impact_df['YearMonth'],
        y=impact_df['GrossRevenue'],
        name='Gross Revenue',
        marker_color=COLORS['primary'],
        opacity=0.7,
        hovertemplate='%{x}<br>Gross: £%{y:,.0f}<extra></extra>',
    ), secondary_y=False)

    fig.add_trace(go.Bar(
        x=impact_df['YearMonth'],
        y=impact_df['RevenueLost'],
        name='Revenue Lost to Returns',
        marker_color=COLORS['danger'],
        opacity=0.85,
        hovertemplate='%{x}<br>Lost: £%{y:,.0f}<extra></extra>',
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=impact_df['YearMonth'],
        y=impact_df['NetRevenue'],
        name='Net Revenue',
        mode='lines+markers',
        line=dict(color=COLORS['success'], width=2.5),
        marker=dict(size=6),
        hovertemplate='%{x}<br>Net: £%{y:,.0f}<extra></extra>',
    ), secondary_y=False)

    fig.update_layout(barmode='stack')
    fig.update_yaxes(title_text='Revenue (£)', tickprefix='£', secondary_y=False)
    fig.update_xaxes(tickangle=-45, automargin=True, tickfont=dict(size=11))
    return _apply_base(fig, 'Monthly Revenue Impact of Returns')

def plot_rfm_segments(seg_summary: pd.DataFrame) -> go.Figure:
    """
    Bubble chart: segments plotted by Avg Recency vs Avg Revenue,
    bubble size = number of customers.
    """
    if seg_summary.empty:
        return go.Figure()

    label_positions = {
        'Champions': 'top center',
        'High Spenders': 'bottom center',
        'At Risk': 'top center',
        'Potential Loyalists': 'top right',
        'Needs Attention': 'bottom center',
        'Lost': 'top center',
        'Recent Customers': 'middle left',
        'Loyal Customers': 'middle right',
    }
    max_customers = max(float(seg_summary['Customers'].max()), 1)

    fig = go.Figure()
    for index, (_, row) in enumerate(seg_summary.iterrows()):
        # Plotly treats scalar marker sizes as pixels, so calculate a bounded
        # diameter directly. Square-root scaling preserves area proportionality
        # without allowing a large segment to cover the chart.
        bubble_size = 16 + np.sqrt(row['Customers'] / max_customers) * 44
        fig.add_trace(go.Scatter(
            x=[row['Avg_Recency_Days']],
            y=[row['Avg_Revenue']],
            mode='markers+text',
            name=row['Segment'],
            text=[row['Segment']],
            textposition=label_positions.get(row['Segment'], 'top center'),
            textfont=dict(size=11, color=COLORS['text']),
            cliponaxis=False,
            marker=dict(
                size=bubble_size,
                color=SEGMENT_PALETTE[index % len(SEGMENT_PALETTE)],
                opacity=0.85,
                line=dict(width=1.5, color=COLORS['background']),
            ),
            customdata=[[
                row['Customers'],
                row['Avg_Frequency'],
                row['Total_Revenue'],
            ]],
            hovertemplate=(
                '<b>%{text}</b><br>'
                'Customers: %{customdata[0]:,.0f}<br>'
                'Avg recency: %{x:,.0f} days<br>'
                'Avg frequency: %{customdata[1]:,.1f} orders<br>'
                'Avg revenue: £%{y:,.0f}<br>'
                'Total revenue: £%{customdata[2]:,.0f}<extra></extra>'
            ),
        ))
    fig = _apply_base(
        fig,
        'Customer Segments: Recency vs Revenue',
    )
    fig.update_xaxes(
        title_text='Avg Days Since Last Purchase (Recency ↑ = worse)',
        automargin=True,
    )
    fig.update_yaxes(
        title_text='Avg Revenue per Customer (£)',
        automargin=True,
        rangemode='tozero',
    )
    fig.update_layout(
        showlegend=False,
        height=500,
        title_font_size=17,
        margin=dict(l=75, r=65, t=80, b=75),
    )
    return fig


def plot_segment_revenue_share(seg_summary: pd.DataFrame) -> go.Figure:
    """Donut chart: each segment's share of total revenue."""
    if seg_summary.empty:
        return go.Figure()

    total_revenue = seg_summary['Total_Revenue'].sum()
    revenue_shares = (
        seg_summary['Total_Revenue'] / total_revenue * 100
        if total_revenue else pd.Series(0, index=seg_summary.index)
    )
    inside_labels = [
        f'<b>{segment}</b><br>{share:.1f}%'
        if share >= 5 else ''
        for segment, share in zip(seg_summary['Segment'], revenue_shares)
    ]
    segment_colors = [
        SEGMENT_PALETTE[index % len(SEGMENT_PALETTE)]
        for index in range(len(seg_summary))
    ]

    fig = go.Figure(go.Pie(
        labels=seg_summary['Segment'],
        values=seg_summary['Total_Revenue'],
        hole=0.60,
        domain=dict(x=[0.00, 0.68], y=[0.04, 0.96]),
        marker=dict(colors=segment_colors,
                    line=dict(color=COLORS['background'], width=2)),
        text=inside_labels,
        textinfo='text',
        textposition='inside',
        sort=False,
        hovertemplate=(
            '<b>%{label}</b><br>'
            'Revenue: £%{value:,.0f}<br>'
            'Share: %{percent}<extra></extra>'
        ),
    ))
    fig = _apply_base(fig, 'Revenue Share by Customer Segment')
    fig.update_layout(
        annotations=[dict(text='Revenue<br>Share', x=0.34, y=0.5,
                           font_size=14, showarrow=False,
                           font_color=COLORS['text'])],
        showlegend=True,
        height=500,
        uniformtext_minsize=11,
        uniformtext_mode='hide',
        legend=dict(
            title=dict(text='Customer segments', font=dict(size=12)),
            orientation='v',
            yanchor='middle',
            y=0.5,
            xanchor='left',
            x=0.73,
            font=dict(size=11),
            itemsizing='constant',
        ),
        margin=dict(l=20, r=20, t=75, b=35),
    )
    return fig


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
    fig.update_xaxes(tickangle=-45, automargin=True, tickfont=dict(size=11))
    return _apply_base(fig, 'New vs Returning Customers per Month')


# GEOGRAPHIC CHART

def plot_country_revenue(
    geo_df: pd.DataFrame,
    excluded_country: str | None = None,
) -> go.Figure:
    """
    Choropleth world map of revenue by country.
    excluded_country: optionally removes the named country to avoid scale distortion.
    """
    if geo_df.empty or 'Country' not in geo_df.columns:
        return go.Figure()

    df = geo_df.copy()
    if excluded_country:
        df = df[df['Country'] != excluded_country]

    fig = px.choropleth(
        df,
        locations='Country',
        locationmode='country names',
        color='Revenue',
        color_continuous_scale=MAP_REVENUE_SCALE,
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
        text='Geographic Revenue Distribution' +
             (f' (excl. {excluded_country})' if excluded_country else ''),
        font=dict(size=18, color=COLORS['text'])
    ))
    return fig


def plot_top_countries_bar(geo_df: pd.DataFrame, n: int = 10,
                           excluded_country: str | None = None) -> go.Figure:
    """Horizontal bar chart: top N countries by revenue."""
    if geo_df.empty:
        return go.Figure()

    df = geo_df.copy()
    if excluded_country:
        df = df[df['Country'] != excluded_country]

    df = df.head(n).sort_values('Revenue')
    fig = go.Figure(go.Bar(
        x=df['Revenue'], y=df['Country'],
        orientation='h',
        marker_color=COLORS['secondary'],
        text=df['Revenue'].apply(lambda v: f'£{v:,.0f}'),
        textposition='auto',
    ))
    title = f'Top {n} Countries by Revenue' + (
        f' (excl. {excluded_country})' if excluded_country else ''
    )
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
