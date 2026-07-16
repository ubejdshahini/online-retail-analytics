"""
Functions for cleaning and standardizing the retail dataset.
"""


import pandas as pd


# Required columns for a valid raw upload (accepted in both raw and cleaned form)
_REQUIRED_COLUMNS = ['Invoice', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'Country']
_PRICE_ALIASES    = ['Price', 'UnitPrice']
_CUSTOMER_ALIASES = ['Customer ID', 'CustomerID']


def validate_data(df: pd.DataFrame) -> tuple[bool, dict]:
    """
    Validate a raw (or partially-cleaned) retail DataFrame before cleaning.

    Checks performed
    ----------------
    - Required columns present (accepts both raw and cleaned column names)
    - InvoiceDate parseable as datetime
    - Quantity column is numeric
    - Price / UnitPrice column is numeric
    - Missing-value counts per column
    - Duplicate row count
    - Invalid rows: non-positive UnitPrice, zero Quantity

    Returns
    -------
    (is_valid, report) where:
        is_valid : bool  — False if any *blocking* issue is found
        report   : dict  — keys: 'errors' (list[str]), 'warnings' (list[str]),
                                 'info'   (list[str])
    """
    errors   = []
    warnings = []
    info     = []

    cols = set(df.columns)

    # ── 1. Required columns ────────────────────────────────────────────────
    for req in _REQUIRED_COLUMNS:
        if req not in cols:
            errors.append(f"Missing required column: **`{req}`**")

    has_price    = any(c in cols for c in _PRICE_ALIASES)
    has_customer = any(c in cols for c in _CUSTOMER_ALIASES)
    if not has_price:
        errors.append("Missing price column: expected **`Price`** or **`UnitPrice`**")
    if not has_customer:
        errors.append("Missing customer column: expected **`Customer ID`** or **`CustomerID`**")

    # If fundamental columns are missing we can't do further checks reliably
    if errors:
        return False, {'errors': errors, 'warnings': warnings, 'info': info}

    # ── 2. InvoiceDate parseable ───────────────────────────────────────────
    try:
        pd.to_datetime(df['InvoiceDate'], errors='raise')
    except Exception:
        errors.append("Column **`InvoiceDate`** cannot be parsed as a date.")

    # ── 3. Numeric types ──────────────────────────────────────────────────
    if 'Quantity' in cols and not pd.api.types.is_numeric_dtype(df['Quantity']):
        errors.append("Column **`Quantity`** must be numeric.")

    price_col = 'UnitPrice' if 'UnitPrice' in cols else 'Price'
    if price_col in cols and not pd.api.types.is_numeric_dtype(df[price_col]):
        errors.append(f"Column **`{price_col}`** must be numeric.")

    # ── 4. Missing values ─────────────────────────────────────────────────
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    for col, n in missing.items():
        pct = n / len(df) * 100
        if col in ('CustomerID', 'Customer ID'):
            info.append(f"`{col}`: {n:,} missing ({pct:.1f}%) — will be filled as **Guest**")
        elif pct > 20:
            warnings.append(f"`{col}`: {n:,} missing values ({pct:.1f}%) — high proportion")
        else:
            info.append(f"`{col}`: {n:,} missing values ({pct:.1f}%)")

    # ── 5. Duplicates ─────────────────────────────────────────────────────
    n_dupes = df.duplicated().sum()
    if n_dupes > 0:
        warnings.append(f"**{n_dupes:,}** duplicate rows detected — will be removed during cleaning")

    # ── 6. Invalid rows ──────────────────────────────────────────────────
    if price_col in cols and pd.api.types.is_numeric_dtype(df[price_col]):
        n_bad_price = (df[price_col] <= 0).sum()
        if n_bad_price > 0:
            warnings.append(f"**{n_bad_price:,}** rows have `{price_col}` ≤ 0 — will be excluded")

    if 'Quantity' in cols and pd.api.types.is_numeric_dtype(df['Quantity']):
        n_returns = (df['Quantity'] < 0).sum()
        if n_returns > 0:
            info.append(f"**{n_returns:,}** rows have negative Quantity — classified as returns (`IsReturn=True`)")

    # ── 7. Row / column counts ────────────────────────────────────────────
    info.append(f"Dataset shape: **{len(df):,} rows × {df.shape[1]} columns**")

    is_valid = len(errors) == 0
    return is_valid, {'errors': errors, 'warnings': warnings, 'info': info}


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

    return df_clean
