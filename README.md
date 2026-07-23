# Online Retail Analytics Platform

A Streamlit application for turning transaction-level retail data into decisions. Upload a CSV or Excel workbook to explore sales performance, product returns, customer segments, and operational opportunities—then export the findings to Excel.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.34%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-48%20passed-2EA44F?logo=pytest&logoColor=white)](tests/)

## What it does

- Validates and cleans retail transaction data on upload.
- Tracks net revenue, orders, customers, return rates, and sales patterns over time.
- Identifies top and low-performing products, including product-level return rates.
- Segments known customers with RFM scoring (recency, frequency, monetary value).
- Produces rule-based, prioritised recommendations and a configurable what-if simulator.
- Exports an executive summary, customer segments, and recommendations to a formatted Excel report.

## Built for

The project is designed for analysts, retail managers, and portfolio reviewers who need a practical example of an end-to-end analytics workflow: ingestion, validation, transformation, analysis, visualisation, and reporting in one application.

It is modelled around the [UCI Online Retail II dataset](https://archive.ics.uci.edu/dataset/502/online+retail+ii), but supports retail data with the schema described below. No dataset is bundled with the repository; upload your own compatible file.

## Highlights

| Area | Included analysis |
| --- | --- |
| Sales performance | KPI summary, monthly revenue, day-of-week and hourly patterns |
| Products and returns | Top products, low-revenue candidates, product return rates, returns over time |
| Customers | RFM segments, segment revenue share, one-time buyers, churn-oriented views |
| Geography | Country-level revenue, orders, customers, and an interactive choropleth |
| Decision support | Rule-based recommendations, impact assumptions, and a what-if revenue simulator |
| Reporting | Downloadable recommendation CSV and styled multi-sheet Excel report |

## Quick start

### Prerequisites

- Python 3.11 or later
- `pip`

### Install and run

```bash
git clone https://github.com/ubejdshahini/online-retail-analytics.git
cd online-retail-analytics

python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Install dependencies and start the app:

```bash
pip install -r requirements.txt
python -m streamlit run app/app.py
```

Streamlit will open the application at `http://localhost:8501`.

## Input data contract

Upload a `.csv` or `.xlsx` file. Excel workbooks can be loaded from one or more sheets. The application accepts `Price` as an alias for `UnitPrice`, and `Customer ID` as an alias for `CustomerID`.

| Column | Required | Notes |
| --- | --- | --- |
| `Invoice` | Yes | Order or invoice identifier |
| `StockCode` | Yes | Product or stock identifier |
| `Description` | Yes | Product description |
| `Quantity` | Yes | Negative values are treated as returns |
| `InvoiceDate` | Yes | Must be parseable as a date/time |
| `UnitPrice` or `Price` | Yes | Must be numeric; non-positive values are excluded |
| `CustomerID` or `Customer ID` | Yes | Missing values are labelled `Guest` and excluded from RFM |
| `Country` | Yes | Used for geographic analysis |

### Cleaning rules

The pipeline removes duplicate rows, standardises supported column names, converts quantities and prices to numeric values, excludes invalid prices, parses dates, and derives `Revenue = Quantity × UnitPrice`. It also identifies negative-quantity rows as returns and separates selected non-product stock codes (for example postage and bank charges) from product-specific analysis.

## Methodology

### RFM segmentation

Known customers are scored from 1–4 on recency, frequency, and monetary value. Scores are assigned with quantile-based buckets and mapped to business-friendly groups such as Champions, Loyal Customers, High Spenders, Potential Loyalists, At Risk, and One-Time Buyers. Returns and guest customers are excluded from the RFM calculation.

### Recommendations and simulations

Recommendations are deterministic rules derived from the loaded data—for example, high-return products, low-revenue products, at-risk customers, and sales concentration by hour. The displayed impact values and what-if outputs are planning assumptions, not forecasts or causal estimates. Validate them with experiments and business context before acting on them.

## Architecture

```text
Upload (CSV/XLSX)
        ↓
Validation and cleaning
        ↓
KPI / product / customer / geographic analysis
        ↓
RFM segmentation and recommendation rules
        ↓
Plotly dashboard + CSV/XLSX exports
```

| Path | Responsibility |
| --- | --- |
| `app/app.py` | Streamlit UI, upload flow, session state, and page orchestration |
| `src/data_cleaning.py` | Input validation, cleaning, return and product flags |
| `src/analysis.py` | KPI, sales, product, customer, return, and country calculations |
| `src/recommendation_engine.py` | RFM scoring, segments, and rule-based recommendations |
| `src/visualisations.py` | Plotly charts and presentation helpers |
| `src/export_utils.py` | Formatted Excel report generation |
| `tests/test_analysis.py` | Unit tests for the analytics pipeline and visualisation contracts |

For a more detailed dependency map, see [architecture and workflow](docs/architecture_and_workflow.md).

## Quality checks

Run the automated tests with:

```bash
python -m pytest
```

Current repository status: **48 tests passing**.

## Limitations

- The app runs in memory and is best suited to small-to-medium files; it is not a multi-user production data platform.
- Input validation checks structure and data types, but does not replace domain-specific data quality review.
- Country mapping relies on country names and may need normalisation for organisation-specific labels.
- Recommendations and simulator results are heuristic decision-support tools, not predictive models.

## Next steps

Potential production extensions include a database-backed data layer, authentication and role-based access, scheduled refreshes, experiment tracking, and deployment with CI/CD.

## License

No license file is currently included. Add a license before reusing or distributing this project beyond the terms you intend.
