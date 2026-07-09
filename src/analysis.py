"""
Functions for deep EDA and retail data analysis.
"""

import pandas as pd
import numpy as np


# REVENUE ANALYSIS

def get_monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Returns aggregated revenue per month with month-over-month growth %."""
    if 'InvoiceDate' not in df.columns or 'Revenue' not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['YearMonth'] = df['InvoiceDate'].dt.to_period('M')

    monthly = df.groupby('YearMonth').agg(
        Revenue=('Revenue', 'sum'),
        Orders=('Invoice', 'nunique') if 'Invoice' in df.columns else ('Revenue', 'count'),
        Customers=('CustomerID', 'nunique') if 'CustomerID' in df.columns else ('Revenue', 'count')
    ).reset_index()

    monthly['YearMonth'] = monthly['YearMonth'].astype(str)
    monthly['Revenue_Growth_%'] = monthly['Revenue'].pct_change() * 100
    return monthly


def get_daily_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Returns revenue per day — useful for spotting peak days."""
    if 'InvoiceDate' not in df.columns or 'Revenue' not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['Date'] = df['InvoiceDate'].dt.date

    daily = df.groupby('Date').agg(
        Revenue=('Revenue', 'sum'),
        Transactions=('Revenue', 'count')
    ).reset_index()
    return daily


def get_revenue_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Returns revenue and transaction count by hour of day."""
    if 'InvoiceDate' not in df.columns or 'Revenue' not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['Hour'] = df['InvoiceDate'].dt.hour

    hourly = df.groupby('Hour').agg(
        Revenue=('Revenue', 'sum'),
        Transactions=('Revenue', 'count')
    ).reset_index()
    return hourly


def get_revenue_by_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    """Returns revenue by day of week (Mon–Sun)."""
    if 'InvoiceDate' not in df.columns or 'Revenue' not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['DayOfWeek'] = df['InvoiceDate'].dt.day_name()

    order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow = df.groupby('DayOfWeek').agg(
        Revenue=('Revenue', 'sum'),
        Transactions=('Revenue', 'count')
    ).reindex(order).reset_index()
    return dow


# PRODUCT ANALYSIS

def get_top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Returns top N products by revenue and quantity sold."""
    if 'Description' not in df.columns or 'Revenue' not in df.columns:
        return pd.DataFrame()

    top = df.groupby('Description').agg(
        Revenue=('Revenue', 'sum'),
        Quantity=('Quantity', 'sum'),
        Transactions=('Revenue', 'count')
    ).reset_index()
    top = top.sort_values('Revenue', ascending=False).head(n)
    return top


def get_worst_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Returns bottom N products by revenue — candidates for discontinuation."""
    if 'Description' not in df.columns or 'Revenue' not in df.columns:
        return pd.DataFrame()

    worst = df.groupby('Description').agg(
        Revenue=('Revenue', 'sum'),
        Quantity=('Quantity', 'sum')
    ).reset_index()
    worst = worst[worst['Revenue'] > 0].sort_values('Revenue').head(n)
    return worst


def get_product_return_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Returns return rate per product — high return rate signals quality issues."""
    if 'Description' not in df.columns or 'IsReturn' not in df.columns:
        return pd.DataFrame()

    total = df.groupby('Description')['Quantity'].count().rename('Total')
    returns = df[df['IsReturn']].groupby('Description')['Quantity'].count().rename('Returns')
    result = pd.concat([total, returns], axis=1).fillna(0)
    result['ReturnRate_%'] = (result['Returns'] / result['Total'] * 100).round(2)
    result = result.sort_values('ReturnRate_%', ascending=False).reset_index()
    return result


# CUSTOMER ANALYSIS

def get_country_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Returns revenue, orders, and unique customers per country."""
    if 'Country' not in df.columns or 'Revenue' not in df.columns:
        return pd.DataFrame()

    agg = {'Revenue': 'sum'}
    if 'CustomerID' in df.columns:
        agg['CustomerID'] = 'nunique'
    if 'Invoice' in df.columns:
        agg['Invoice'] = 'nunique'

    perf = df.groupby('Country').agg(agg).reset_index()
    perf = perf.rename(columns={'CustomerID': 'UniqueCustomers', 'Invoice': 'Orders'})
    return perf.sort_values('Revenue', ascending=False)


def get_customer_lifetime_value(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns Customer Lifetime Value (CLV) per customer.
    CLV = Total Revenue | also shows avg order value and order frequency.
    Excludes 'Guest' customers (no ID).
    """
    if 'CustomerID' not in df.columns or 'Revenue' not in df.columns:
        return pd.DataFrame()

    df = df[df['CustomerID'] != 'Guest'].copy()

    invoice_col = 'Invoice' if 'Invoice' in df.columns else None

    agg = {
        'Revenue': 'sum',
    }
    if invoice_col:
        agg[invoice_col] = 'nunique'

    clv = df.groupby('CustomerID').agg(agg).reset_index()
    if invoice_col:
        clv = clv.rename(columns={invoice_col: 'Orders'})
        clv['AvgOrderValue'] = (clv['Revenue'] / clv['Orders']).round(2)

    clv = clv.rename(columns={'Revenue': 'TotalRevenue'})
    return clv.sort_values('TotalRevenue', ascending=False)


def get_churned_customers(df: pd.DataFrame, days_threshold: int = 90) -> pd.DataFrame:
    """
    Identifies customers at risk of churn:
    those who haven't purchased in the last `days_threshold` days.
    """
    if 'CustomerID' not in df.columns or 'InvoiceDate' not in df.columns:
        return pd.DataFrame()

    df = df[df['CustomerID'] != 'Guest'].copy()
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    max_date = df['InvoiceDate'].max()

    last_purchase = df.groupby('CustomerID')['InvoiceDate'].max().reset_index()
    last_purchase.columns = ['CustomerID', 'LastPurchaseDate']
    last_purchase['DaysSinceLastPurchase'] = (max_date - last_purchase['LastPurchaseDate']).dt.days
    churned = last_purchase[last_purchase['DaysSinceLastPurchase'] >= days_threshold]
    return churned.sort_values('DaysSinceLastPurchase', ascending=False)


def get_new_vs_returning_customers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per month: how many new customers vs returning customers.
    New = first purchase ever in that month.
    """
    if 'CustomerID' not in df.columns or 'InvoiceDate' not in df.columns:
        return pd.DataFrame()

    df = df[df['CustomerID'] != 'Guest'].copy()
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['YearMonth'] = df['InvoiceDate'].dt.to_period('M')

    first_purchase = df.groupby('CustomerID')['YearMonth'].min().rename('FirstMonth')
    df = df.join(first_purchase, on='CustomerID')
    df['CustomerType'] = df.apply(
        lambda r: 'New' if r['YearMonth'] == r['FirstMonth'] else 'Returning', axis=1
    )

    result = df.groupby(['YearMonth', 'CustomerType'])['CustomerID'].nunique().reset_index()
    result.columns = ['YearMonth', 'CustomerType', 'Customers']
    result['YearMonth'] = result['YearMonth'].astype(str)
    return result


# RETURNS / REFUND ANALYSIS

def get_return_summary(df: pd.DataFrame) -> dict:
    """
    Returns a high-level summary of returns/refunds:
    - Total revenue lost from returns
    - Number of return transactions
    - Return rate as % of all transactions
    """
    if 'IsReturn' not in df.columns or 'Revenue' not in df.columns:
        return {}

    returns_df = df[df['IsReturn']]
    total_transactions = len(df)
    return_transactions = len(returns_df)
    revenue_lost = abs(returns_df['Revenue'].sum())

    return {
        'total_transactions': total_transactions,
        'return_transactions': return_transactions,
        'return_rate_%': round(return_transactions / total_transactions * 100, 2),
        'revenue_lost_from_returns': round(revenue_lost, 2),
        'net_revenue': round(df['Revenue'].sum(), 2)
    }


# OVERALL KPI SUMMARY

def get_kpi_summary(df: pd.DataFrame) -> dict:
    """
    Returns top-level KPIs for the dashboard:
    - Total revenue (net)
    - Total orders
    - Unique customers
    - Average order value
    - Top country
    - Best selling product
    """
    kpis = {}

    if 'Revenue' in df.columns:
        kpis['total_revenue'] = round(df['Revenue'].sum(), 2)

    if 'Invoice' in df.columns:
        kpis['total_orders'] = df['Invoice'].nunique()
        if 'Revenue' in df.columns:
            order_revenue = df.groupby('Invoice')['Revenue'].sum()
            kpis['avg_order_value'] = round(order_revenue.mean(), 2)

    if 'CustomerID' in df.columns:
        kpis['unique_customers'] = df[df['CustomerID'] != 'Guest']['CustomerID'].nunique()

    if 'Country' in df.columns and 'Revenue' in df.columns:
        kpis['top_country'] = df.groupby('Country')['Revenue'].sum().idxmax()

    if 'Description' in df.columns and 'Revenue' in df.columns:
        kpis['best_product'] = df.groupby('Description')['Revenue'].sum().idxmax()

    if 'IsReturn' in df.columns:
        kpis['return_rate_%'] = round(df['IsReturn'].mean() * 100, 2)

    return kpis
