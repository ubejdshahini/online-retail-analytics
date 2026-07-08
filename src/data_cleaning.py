"""
Step 1.2 — Data Cleaning and Standardization (Dev A).

This function will be used twice:
1. By Dev B for EDA (notebook 02).
2. By Dev C within Streamlit, for every new CSV uploaded by the client.

Therefore, it must remain a pure function without side-effects (no printing,
no reading files on its own — it takes a DataFrame, returns a DataFrame).
"""

import pandas as pd


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the "Online Retail II" dataset.

    Steps applied:
    - Handle missing CustomerID (mark as "Guest").
    - Classify negative Quantity as returns/refunds (IsReturn column).
    - Filter out UnitPrice <= 0.
    - Convert InvoiceDate to datetime.
    - Create Revenue column = Quantity * UnitPrice.

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataset.

    Returns
    -------
    pd.DataFrame
        Cleaned dataset.
    """
    df_clean = df.copy()

    # 1. Handle missing CustomerID — mark as "Guest"
    if 'Customer ID' in df_clean.columns:
        df_clean.rename(columns={'Customer ID': 'CustomerID'}, inplace=True)
    if 'CustomerID' in df_clean.columns:
        df_clean['CustomerID'] = df_clean['CustomerID'].fillna('Guest')

    # 2. Normalise column name: 'Price' (UCI raw format) → 'UnitPrice'
    if 'Price' in df_clean.columns and 'UnitPrice' not in df_clean.columns:
        df_clean.rename(columns={'Price': 'UnitPrice'}, inplace=True)

    # 3. Remove duplicate rows
    df_clean = df_clean.drop_duplicates()

    # 4. Classify negative Quantity as returns (do not delete)
    if 'Quantity' in df_clean.columns:
        df_clean['IsReturn'] = df_clean['Quantity'] < 0

    # 5. Filter out UnitPrice <= 0
    if 'UnitPrice' in df_clean.columns:
        df_clean = df_clean[df_clean['UnitPrice'] > 0].copy()

    # 6. Convert InvoiceDate to datetime
    if 'InvoiceDate' in df_clean.columns:
        df_clean['InvoiceDate'] = pd.to_datetime(df_clean['InvoiceDate'])

    # 7. Create Revenue column = Quantity * UnitPrice
    if 'Quantity' in df_clean.columns and 'UnitPrice' in df_clean.columns:
        df_clean['Revenue'] = df_clean['Quantity'] * df_clean['UnitPrice']

    return df_clean
