"""
Automated unit tests for the core retail analytics pipeline.
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_cleaning import clean_data
from src.about_page import get_dataset_profile
from src.analysis import (
    get_kpi_summary, get_return_summary, get_monthly_revenue,
    get_monthly_product_revenue, get_revenue_by_hour,
)
from src.recommendation_engine import compute_rfm, get_segment_summary, generate_recommendations
from src.visualisations import (
    plot_monthly_revenue, plot_monthly_product_revenue,
    plot_revenue_by_hour, plot_rfm_segments, plot_segment_revenue_share,
)


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def raw_df():
    """Simulates a small raw 'Online Retail II' dataset."""
    data = {
        'Invoice': ['INV001', 'INV001', 'INV002', 'INV003', 'C-INV004', 'INV005',
                     'INV006', 'INV007', 'INV008', 'INV009'],
        'StockCode': ['S01', 'S02', 'S01', 'S03', 'S01', 'S04',
                       'S01', 'S02', 'S05', 'S01'],
        'Description': ['Widget A', 'Widget B', 'Widget A', 'Widget C',
                         'Widget A', 'Widget D', 'Widget A', 'Widget B',
                         'Widget E', 'Widget A'],
        'Quantity': [10, 5, 3, 7, -2, 12, 8, 4, 6, 15],
        'InvoiceDate': pd.to_datetime([
            '2024-01-05', '2024-01-05', '2024-01-10', '2024-01-15',
            '2024-01-20', '2024-02-01', '2024-02-05', '2024-02-10',
            '2024-03-01', '2024-03-15',
        ]),
        'UnitPrice': [2.50, 3.00, 2.50, 5.00, 2.50, 4.00, 2.50, 3.00, 1.50, 2.50],
        'Customer ID': [101.0, 101.0, 102.0, 103.0, 101.0, 104.0,
                         np.nan, 102.0, 105.0, 101.0],
        'Country': ['UK', 'UK', 'France', 'UK', 'UK', 'Germany',
                     'UK', 'France', 'UK', 'UK'],
    }
    return pd.DataFrame(data)


@pytest.fixture
def cleaned_df(raw_df):
    """Returns the cleaned version of the raw fixture."""
    return clean_data(raw_df)


# TESTS: data_cleaning.clean_data()

class TestCleanData:
    def test_customer_id_renamed(self, cleaned_df):
        """'Customer ID' should be renamed to 'CustomerID'."""
        assert 'CustomerID' in cleaned_df.columns
        assert 'Customer ID' not in cleaned_df.columns

    def test_missing_customer_id_filled_as_guest(self, cleaned_df):
        """NaN CustomerID should become 'Guest'."""
        assert 'Guest' in cleaned_df['CustomerID'].values

    def test_is_return_column_created(self, cleaned_df):
        """An 'IsReturn' boolean column should be created."""
        assert 'IsReturn' in cleaned_df.columns
        assert cleaned_df['IsReturn'].dtype == bool

    def test_negative_quantity_marked_as_return(self, cleaned_df):
        """Rows with Quantity < 0 should have IsReturn == True."""
        returns = cleaned_df[cleaned_df['IsReturn']]
        assert len(returns) > 0
        assert (returns['Quantity'] < 0).all()

    def test_unit_price_positive(self, cleaned_df):
        """All rows should have UnitPrice > 0 after cleaning."""
        assert (cleaned_df['UnitPrice'] > 0).all()

    def test_revenue_column_created(self, cleaned_df):
        """Revenue = Quantity * UnitPrice should be created."""
        assert 'Revenue' in cleaned_df.columns
        expected = cleaned_df['Quantity'] * cleaned_df['UnitPrice']
        pd.testing.assert_series_equal(cleaned_df['Revenue'], expected, check_names=False)

    def test_invoice_date_is_datetime(self, cleaned_df):
        """InvoiceDate should be a datetime column after cleaning."""
        assert pd.api.types.is_datetime64_any_dtype(cleaned_df['InvoiceDate'])

    def test_no_duplicates_remain(self, raw_df):
        """Duplicate rows should be removed during cleaning."""
        # Add a duplicate row
        raw_with_dup = pd.concat([raw_df, raw_df.iloc[[0]]], ignore_index=True)
        cleaned = clean_data(raw_with_dup)
        # Should have the same number of rows as cleaning original (duplicate is removed)
        assert len(cleaned) == len(clean_data(raw_df))


# TESTS: analysis.get_kpi_summary()

class TestKPISummary:
    def test_returns_dict(self, cleaned_df):
        """get_kpi_summary should return a dict."""
        kpis = get_kpi_summary(cleaned_df)
        assert isinstance(kpis, dict)

    def test_total_revenue_key(self, cleaned_df):
        """KPI dict should contain 'total_revenue'."""
        kpis = get_kpi_summary(cleaned_df)
        assert 'total_revenue' in kpis
        assert isinstance(kpis['total_revenue'], (int, float))

    def test_total_orders_key(self, cleaned_df):
        """KPI dict should contain 'total_orders'."""
        kpis = get_kpi_summary(cleaned_df)
        assert 'total_orders' in kpis
        assert kpis['total_orders'] > 0

    def test_unique_customers_excludes_guest(self, cleaned_df):
        """unique_customers should exclude 'Guest'."""
        kpis = get_kpi_summary(cleaned_df)
        assert 'unique_customers' in kpis
        # Should not count 'Guest' customer
        guest_excluded = cleaned_df[cleaned_df['CustomerID'] != 'Guest']['CustomerID'].nunique()
        assert kpis['unique_customers'] == guest_excluded

    def test_top_country(self, cleaned_df):
        """Should identify the country with the highest revenue."""
        kpis = get_kpi_summary(cleaned_df)
        assert 'top_country' in kpis
        assert isinstance(kpis['top_country'], str)

    def test_return_rate_present(self, cleaned_df):
        """Should calculate return_rate_%."""
        kpis = get_kpi_summary(cleaned_df)
        assert 'return_rate_%' in kpis
        assert 0 <= kpis['return_rate_%'] <= 100


# TESTS: analysis.get_return_summary()

class TestReturnSummary:
    def test_returns_dict(self, cleaned_df):
        result = get_return_summary(cleaned_df)
        assert isinstance(result, dict)

    def test_has_expected_keys(self, cleaned_df):
        result = get_return_summary(cleaned_df)
        expected_keys = {'total_transactions', 'return_transactions', 'return_rate_%',
                         'revenue_lost_from_returns', 'net_revenue'}
        assert expected_keys.issubset(result.keys())

    def test_revenue_lost_is_positive(self, cleaned_df):
        """Revenue lost should be reported as a positive number."""
        result = get_return_summary(cleaned_df)
        assert result['revenue_lost_from_returns'] >= 0


# TESTS: recommendation_engine.compute_rfm()

class TestRFM:
    def test_rfm_returns_dataframe(self, cleaned_df):
        rfm = compute_rfm(cleaned_df)
        assert isinstance(rfm, pd.DataFrame)

    def test_rfm_has_required_columns(self, cleaned_df):
        rfm = compute_rfm(cleaned_df)
        if not rfm.empty:
            for col in ['CustomerID', 'Recency', 'Frequency', 'Monetary', 'Segment']:
                assert col in rfm.columns, f"Missing column: {col}"

    def test_rfm_excludes_guests(self, cleaned_df):
        """RFM should not include 'Guest' customers."""
        rfm = compute_rfm(cleaned_df)
        if not rfm.empty:
            assert 'Guest' not in rfm['CustomerID'].values

    def test_segment_summary(self, cleaned_df):
        rfm = compute_rfm(cleaned_df)
        summary = get_segment_summary(rfm)
        if not rfm.empty:
            assert isinstance(summary, pd.DataFrame)
            assert 'Segment' in summary.columns
            assert 'Customers' in summary.columns


# TESTS: recommendation_engine.generate_recommendations()

class TestRecommendations:
    def test_returns_list(self, cleaned_df):
        recs = generate_recommendations(cleaned_df)
        assert isinstance(recs, list)

    def test_recommendation_structure(self, cleaned_df):
        """Each recommendation should have the required keys."""
        recs = generate_recommendations(cleaned_df)
        required_keys = {'type', 'segment', 'title', 'message', 'impact_pct', 'priority'}
        for rec in recs:
            assert required_keys.issubset(rec.keys()), f"Missing keys in rec: {rec.get('title', '?')}"

    def test_priority_values_valid(self, cleaned_df):
        """Priority should only be 'High', 'Medium', or 'Low'."""
        recs = generate_recommendations(cleaned_df)
        valid = {'High', 'Medium', 'Low'}
        for rec in recs:
            assert rec['priority'] in valid

    def test_impact_pct_is_number(self, cleaned_df):
        recs = generate_recommendations(cleaned_df)
        for rec in recs:
            assert isinstance(rec['impact_pct'], (int, float))

    def test_sorted_by_impact_descending(self, cleaned_df):
        """Recommendations should be sorted by impact_pct descending."""
        recs = generate_recommendations(cleaned_df)
        if len(recs) > 1:
            impacts = [r['impact_pct'] for r in recs]
            assert impacts == sorted(impacts, reverse=True)


# TESTS: analysis.get_monthly_revenue()

class TestMonthlyRevenue:
    def test_returns_dataframe(self, cleaned_df):
        result = get_monthly_revenue(cleaned_df)
        assert isinstance(result, pd.DataFrame)

    def test_has_revenue_column(self, cleaned_df):
        result = get_monthly_revenue(cleaned_df)
        assert 'Revenue' in result.columns

    def test_multiple_months(self, cleaned_df):
        """Fixture data spans 3 months so we should get multiple rows."""
        result = get_monthly_revenue(cleaned_df)
        assert len(result) >= 2


class TestMonthlyRevenueVisualisation:
    def test_compares_revenue_with_order_volume(self, cleaned_df):
        monthly = get_monthly_revenue(cleaned_df)
        fig = plot_monthly_revenue(monthly)

        trace_names = [trace.name for trace in fig.data]
        assert 'Orders' in trace_names
        assert 'MoM Growth %' not in trace_names
        assert fig.layout.title.text == 'Monthly Revenue & Order Volume'
        assert fig.layout.yaxis2.title.text == 'Orders'


class TestMonthlyProductRevenue:
    def test_limits_results_to_requested_top_products(self, cleaned_df):
        result = get_monthly_product_revenue(cleaned_df, n=2)

        assert not result.empty
        assert result['Description'].nunique() == 2
        assert {'YearMonth', 'Description', 'Revenue'} == set(result.columns)

    def test_visualisation_uses_one_small_multiple_per_product(self, cleaned_df):
        monthly_products = get_monthly_product_revenue(cleaned_df, n=3)
        fig = plot_monthly_product_revenue(monthly_products)

        product_count = monthly_products['Description'].nunique()
        assert len(fig.data) == product_count
        assert all(trace.type == 'scatter' for trace in fig.data)
        assert all(trace.mode == 'lines+markers' for trace in fig.data)
        assert all(trace.fill in (None, 'none') for trace in fig.data)
        assert len(fig.layout.annotations) == product_count
        assert fig.layout.title.text == 'Monthly Revenue Patterns by Product'


class TestHourlyRevenueVisualisation:
    def test_uses_two_lines_without_area_fill(self, cleaned_df):
        hourly = get_revenue_by_hour(cleaned_df)
        fig = plot_revenue_by_hour(hourly)

        assert len(fig.data) == 2
        assert all(trace.fill in (None, 'none') for trace in fig.data)
        assert all(trace.mode == 'lines+markers' for trace in fig.data)


class TestCustomerSegmentVisualisations:
    def test_bubble_labels_use_distinct_positions_and_are_not_clipped(self):
        summary = pd.DataFrame({
            'Segment': ['Champions', 'High Spenders', 'Recent Customers', 'Loyal Customers'],
            'Customers': [100, 60, 40, 35],
            'Avg_Recency_Days': [30, 45, 20, 22],
            'Avg_Frequency': [12, 5, 2, 8],
            'Avg_Revenue': [500, 420, 80, 90],
            'Total_Revenue': [50000, 25200, 3200, 3150],
        })

        fig = plot_rfm_segments(summary)

        positions = {trace.name: trace.textposition for trace in fig.data}
        assert positions['Recent Customers'] != positions['Loyal Customers']
        assert all(trace.cliponaxis is False for trace in fig.data)
        assert all(16 <= trace.marker.size <= 60 for trace in fig.data)
        assert fig.layout.margin.r >= 60

    def test_donut_uses_inside_labels_and_complete_legend(self):
        summary = pd.DataFrame({
            'Segment': ['Champions', 'At Risk', 'Lost'],
            'Total_Revenue': [80000, 19000, 1000],
        })

        fig = plot_segment_revenue_share(summary)
        pie = fig.data[0]

        assert pie.textposition == 'inside'
        assert pie.text[-1] == ''
        assert len(pie.marker.colors) == len(summary)
        assert fig.layout.showlegend is True
        assert fig.layout.legend.orientation == 'v'


class TestAboutPageDatasetProfile:
    def test_profile_reflects_loaded_dataset(self, cleaned_df):
        profile = get_dataset_profile(cleaned_df, 'monthly_sales.csv')

        assert profile['loaded'] is True
        assert profile['filename'] == 'monthly_sales.csv'
        assert profile['rows'] == len(cleaned_df)
        assert profile['customers'] == cleaned_df.loc[
            cleaned_df['CustomerID'] != 'Guest', 'CustomerID'
        ].nunique()
        assert profile['countries'] == cleaned_df['Country'].nunique()
        assert profile['net_revenue'] == pytest.approx(cleaned_df['Revenue'].sum())

    def test_profile_handles_no_loaded_dataset(self):
        profile = get_dataset_profile(None)

        assert profile == {'loaded': False, 'filename': 'No dataset loaded'}
