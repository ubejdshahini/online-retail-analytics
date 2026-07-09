# Online Retail Analytics Platform

An end-to-end business intelligence platform for retail sales data — powered by Python, Plotly, and Streamlit.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.34+-red?logo=streamlit)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-5.18+-purple?logo=plotly)](https://plotly.com)
[![Tests](https://img.shields.io/badge/Tests-29%20passed-brightgreen?logo=pytest)](tests/)


---

## Overview

Upload any retail CSV and the platform automatically cleans the data, computes KPIs, segments customers via RFM, and renders interactive charts — all in real time, with no database required.

Built on the [Online Retail II dataset (UCI)](https://archive.ics.uci.edu/dataset/502/online+retail+ii), compatible with any similarly structured retail file.

---

## Features

| Feature | Description |
|---------|-------------|
| Smart CSV Upload | Accepts raw and pre-cleaned formats; auto-validates columns |
| Automatic Data Cleaning | Normalises columns, flags returns, derives Revenue |
| Sales Dashboard | Monthly trends, peak hours, best/worst weekday |
| Product Analysis | Top products, low-revenue candidates, return rate heatmap |
| Customer Intelligence | RFM segments, CLV distribution, new vs returning, churn risk |
| Geographic Heatmap | Choropleth world map by revenue |
| Business Recommendations | 7 rule-based insights ranked by estimated profit impact |
| What-If Simulator | Adjustable sliders; projections update in real time |
| Excel Report Export | Executive Summary, Customer Segments, Recommendations sheets |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Data Processing | pandas, numpy |
| Visualisations | Plotly |
| Web Application | Streamlit |
| Excel Reporting | openpyxl |
| Testing | pytest |

---

## Project Structure

```text
online-retail-analytics/
├── app/
│   └── app.py                        # Streamlit dashboard (3 pages)
├── src/
│   ├── data_cleaning.py              # clean_data() — normalisation pipeline
│   ├── analysis.py                   # KPI & EDA functions
│   ├── recommendation_engine.py      # RFM segmentation & recommendations
│   ├── visualisations.py             # Plotly chart generators
│   └── export_utils.py               # Excel report generator
├── tests/
│   └── test_analysis.py              # 29 unit tests
├── notebooks/                        # Jupyter EDA notebooks
├── data/
│   └── cleaned_retail_data.csv       # Pre-cleaned demo dataset
├── docs/
│   └── architecture_and_workflow.md  # Module dependency & data flow
└── requirements.txt
```

---

## Getting Started

```bash
# Clone and install
git clone https://github.com/ubejdshahini/online-retail-analytics.git
cd online-retail-analytics
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Run the app
python -m streamlit run app/app.py

# Run tests
pytest tests/
```

Open **http://localhost:8501** in your browser.

---

## How It Works

```
Upload CSV
    → data_cleaning.py      Normalise columns, compute Revenue & IsReturn
    → analysis.py           KPIs, trends, product & customer statistics
    → recommendation_engine.py   RFM scoring, segments, recommendations
    → visualisations.py     Interactive Plotly charts
    → Dashboard             Rendered in real time, fully in-memory
```

See [docs/architecture_and_workflow.md](docs/architecture_and_workflow.md) for the full module dependency map.

---

## Dataset

**Online Retail II** — UCI Machine Learning Repository  
https://archive.ics.uci.edu/dataset/502/online+retail+ii

A pre-cleaned demo file is included at `data/cleaned_retail_data.csv`. Raw files must be downloaded separately (gitignored).

---

## Customer Segments (RFM)

| Segment | Description | Action |
|---------|-------------|--------|
| Champions | Recent, frequent, high spend | Reward & retain |
| Loyal Customers | Frequent and recent | Upsell & cross-sell |
| High Spenders | High spend, moderate frequency | Frequency campaigns |
| Recent Customers | New buyers, not yet habitual | Onboarding sequences |
| Potential Loyalists | Promising, need nurturing | Second-purchase incentive |
| At Risk | Were valuable, now inactive | Win-back campaign |
| Needs Attention | Drifting frequent buyers | Re-engagement offer |
| Lost | Long inactive, low value | Deep discount or sunset |

---


