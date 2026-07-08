# Online Retail Analytics Platform

An end-to-end analytics platform for retail sales data, built on the [Online Retail II (UCI)](https://archive.ics.uci.edu/dataset/502/online+retail+ii) dataset.

---

## Project Structure

```text
online-retail-analytics/
├── data/
│   ├── raw/                          # Original CSV/Excel files (gitignored)
│   ├── processed/                    # Intermediate cleaned datasets
│   └── cleaned_retail_data.csv       # Demo dataset for Streamlit
├── notebooks/
│   ├── 01_data_exploration.ipynb     # Initial dataset exploration
│   ├── 02_eda_analysis.ipynb         # EDA & KPI insights
│   ├── 03_rfm_recommendations.ipynb  # RFM segmentation & recommendation rules
│   └── 04_visualisations.ipynb       # Plotly charting examples
├── src/
│   ├── data_cleaning.py              # clean_data() — reusable data cleaning pipeline
│   ├── analysis.py                   # EDA functions & KPI generation
│   ├── recommendation_engine.py      # RFM segmentation & rule-based recommendations
│   ├── visualisations.py             # Plotly chart generation functions
│   └── export_utils.py               # Multi-sheet Excel report generator
├── app/
│   └── app.py                        # Streamlit dashboard application
├── tests/
│   └── test_analytics.py             # Unit tests (pytest)
├── docs/
│   ├── Plani_Projektit_Online_Retail_Analytics.md   # Project plan
│   └── Plani_Hapave_Ndarja_Punes_4_Zhvillues.md     # Developer work distribution
├── requirements.txt
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data processing | Python 3.11+, pandas, numpy |
| Visualisations | Plotly |
| Web application | Streamlit |
| Reporting | openpyxl (Excel export) |
| Notebooks | Jupyter |
| Testing | pytest |

---

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/blinasopjani/online-retail-analytics.git
cd online-retail-analytics

# 2. Create and activate a virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Running the Streamlit App

```bash
streamlit run app/app.py
```

The app will open in your browser at `http://localhost:8501`.

### Running Notebooks

```bash
jupyter notebook notebooks/
```

### Running Tests

```bash
pytest tests/
```

---

## Dataset

**Online Retail II** — UCI Machine Learning Repository  
Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii

A cleaned demo version is included at `data/cleaned_retail_data.csv` for immediate use with the Streamlit app. Raw data files are gitignored and must be downloaded separately.

---

## Application Features

| Section | Description |
|---------|-------------|
| **Home & Upload** | Upload a monthly CSV file; automatic format validation |
| **Sales Dashboard** | KPIs, revenue trends, top products |
| **Customer Analysis** | RFM segments, CLV, churn risk |
| **Geographic Performance** | Country-based revenue mapping |
| **Recommendations** | Rule-based insights with estimated profit impact |
| **What-If Simulator** | Revenue projections based on RFM segment data |
| **Export** | Download a multi-sheet Excel report |

---

## Branch Strategy

```
main
 └── develop
      ├── feature/data-pipeline       # Data cleaning & pipeline (Dev A)
      ├── feature/analytics-engine    # EDA, RFM, recommendations (Dev B)
      ├── feature/streamlit-app       # Streamlit dashboard & export (Dev C)
      └── feature/testing-and-docs    # Tests, docs, deployment (Dev D)
```

See [`docs/Plani_Hapave_Ndarja_Punes_4_Zhvillues.md`](docs/Plani_Hapave_Ndarja_Punes_4_Zhvillues.md) for the full developer work distribution.

---

## Project Status

- [x] Repository structure & dependency management
- [x] **Phase 1 — Data Processing:** Dataset exploration & `clean_data()` pipeline
- [x] **Phase 2 — Analytics & Insights:** EDA functions, RFM segmentation, recommendation engine
- [x] **Phase 3 — Visualisations:** Interactive Plotly charts
- [x] **Phase 4 — Strategic Plan:** Rule-based recommendations with profit impact estimates
- [x] **Phase 5 — Streamlit Application:** Full dashboard with 6 views
- [x] **Phase 6 — What-If Simulator & Excel Export**
- [x] **Phase 7 — Automated Testing:** Unit tests covering cleaning, KPIs, RFM, recommendations
- [x] Ready for deployment on Streamlit Cloud
