"""
Functions for cleaning and standardizing the retail dataset.
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
        # Keep the whole column on one Arrow-compatible type. Mixing numeric
        # IDs with the string "Guest" makes Streamlit repeatedly log a
        # dataframe serialization warning.
        df_clean['CustomerID'] = df_clean['CustomerID'].fillna('Guest').astype(str)

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

    # 8. Normalise country names so they match the GeoJSON feature names used
    #    by the choropleth map.  Leading/trailing whitespace is stripped first,
    #    then known aliases (abbreviations, old names, dataset quirks) are
    #    mapped to their canonical GeoJSON form.
    if 'Country' in df_clean.columns:
        df_clean['Country'] = df_clean['Country'].astype(str).str.strip()
        _COUNTRY_ALIASES = {
            # Kosovo variants
            'Republic of Kosovo':       'Kosovo',
            'Republika e Kosovës':      'Kosovo',
            'Косово':                   'Kosovo',
            # Retail dataset abbreviations / informal names
            'EIRE':                     'Ireland',
            'USA':                      'United States of America',
            'RSA':                      'South Africa',
            'Korea':                    'South Korea',
            'Hong Kong':                'China',        # no separate polygon in GeoJSON
            'Singapore':                'Malaysia',     # island; closest land polygon
            'Bahrain':                  'Saudi Arabia', # island; closest land polygon
            'Channel Islands':          'United Kingdom',
            'European Community':       None,           # no matching polygon — drop below
            'Unspecified':              None,
        }
        df_clean['Country'] = df_clean['Country'].replace(_COUNTRY_ALIASES)
        # Drop rows whose country could not be mapped to a map polygon
        df_clean = df_clean.dropna(subset=['Country'])

    return df_clean
