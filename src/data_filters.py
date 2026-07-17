"""
Reusable filters for retail transaction analysis.
"""

import pandas as pd


def get_product_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return rows representing actual retail products.

    If IsProduct is missing, return all rows for backward
    compatibility with older cleaned datasets.
    """
    if df.empty:
        return df.copy()

    if 'IsProduct' not in df.columns:
        return df.copy()

    return df[df['IsProduct']].copy()


def get_non_product_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return postage, fees, services, and adjustment rows.
    """
    if df.empty or 'IsProduct' not in df.columns:
        return pd.DataFrame(columns=df.columns)

    return df[~df['IsProduct']].copy()


def get_product_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return positive sales of real products only.

    Excludes:
    - non-products
    - returns
    - zero or negative revenue
    """
    result = get_product_rows(df)

    if 'IsReturn' in result.columns:
        result = result[~result['IsReturn']]

    if 'Revenue' in result.columns:
        result = result[result['Revenue'] > 0]

    return result.copy()


def get_product_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return returned product rows only.
    """
    result = get_product_rows(df)

    if 'IsReturn' not in result.columns:
        return pd.DataFrame(columns=df.columns)

    return result[result['IsReturn']].copy()
