"""Unit tests for chart aggregation functions (Story 3.5).

Tests the aggregate_time_series() function and its adapter helpers to ensure:
- Daily timeframe passes through unchanged
- Weekly aggregation reduces data points appropriately
- Monthly aggregation produces correct results
- Metadata.aggregation field is updated correctly
- Type contracts are preserved (TimeSeriesData → TimeSeriesData)
"""

import pandas as pd
import pytest

from apps.backend.chart_data import (
    _processed_to_time_series,
    _time_series_to_processed,
    aggregate_time_series,
    format_all_chart_data,
)
from core.models.chart_models import (
    ChartDataPoint,
    ChartMetaInfo,
    ChartStats,
    ProcessedChartData,
    TimeSeriesData,
)


class TestAggregateTimeSeries:
    """Test suite for aggregate_time_series() function."""

    @pytest.fixture
    def sample_daily_data(self) -> TimeSeriesData:
        """Create sample daily TimeSeriesData for testing.

        Generates 80 days of data points with realistic values.
        """
        # Generate 80 daily data points (roughly 3 months)
        dates = pd.date_range("2025-01-01", periods=80, freq="D")
        points = [
            ChartDataPoint(
                date=date.strftime("%Y-%m-%d"),
                timestamp=date.isoformat(),
                value=float(10000 + (i * 100)),  # Increasing values
                has_data=True,
            )
            for i, date in enumerate(dates)
        ]

        return TimeSeriesData(
            metric_name="Production Total",
            chart_type="line",
            data_type="currency",
            time_series=points,
            statistics={
                "total": sum(p.value for p in points),
                "average": sum(p.value for p in points) / len(points),
                "minimum": min(p.value for p in points),
                "maximum": max(p.value for p in points),
                "data_points": len(points),
            },
            format_options={
                "date_column": "date",
            },
            error=None,
        )

    def test_daily_passthrough(self, sample_daily_data: TimeSeriesData):
        """Daily timeframe should return data unchanged."""
        result = aggregate_time_series(sample_daily_data, "daily")

        # Should return same instance or equivalent data
        assert len(result.time_series) == len(sample_daily_data.time_series)
        assert result.metric_name == sample_daily_data.metric_name
        assert result.statistics == sample_daily_data.statistics

    def test_weekly_reduces_points(self, sample_daily_data: TimeSeriesData):
        """Weekly aggregation should reduce ~80 daily points to ~11-12 weekly points."""
        result = aggregate_time_series(sample_daily_data, "weekly")

        # 80 days ≈ 11-12 weeks
        assert (
            10 <= len(result.time_series) <= 13
        ), f"Expected 10-13 weekly points, got {len(result.time_series)}"
        assert len(result.time_series) < len(sample_daily_data.time_series)

    def test_monthly_reduces_points(self, sample_daily_data: TimeSeriesData):
        """Monthly aggregation should reduce ~80 daily points to 2-3 monthly points."""
        result = aggregate_time_series(sample_daily_data, "monthly")

        # 80 days ≈ 2-3 months
        assert (
            2 <= len(result.time_series) <= 4
        ), f"Expected 2-4 monthly points, got {len(result.time_series)}"
        assert len(result.time_series) < len(sample_daily_data.time_series)

    def test_preserves_type(self, sample_daily_data: TimeSeriesData):
        """Output must be valid TimeSeriesData (Pydantic validation)."""
        for timeframe in ["daily", "weekly", "monthly"]:
            result = aggregate_time_series(sample_daily_data, timeframe)

            # Type checking
            assert isinstance(result, TimeSeriesData)
            assert isinstance(result.time_series, list)
            assert all(isinstance(p, ChartDataPoint) for p in result.time_series)

            # Pydantic validation passes automatically during construction
            # If we got here, validation succeeded

    def test_updates_metadata_aggregation(self, sample_daily_data: TimeSeriesData):
        """Verify aggregation field is set correctly in format_options."""
        # Daily is passthrough, so aggregation field unchanged
        # Weekly should update to 'weekly'
        weekly = aggregate_time_series(sample_daily_data, "weekly")
        assert weekly.format_options["aggregation"] == "weekly"

        # Monthly should update to 'monthly'
        monthly = aggregate_time_series(sample_daily_data, "monthly")
        assert monthly.format_options["aggregation"] == "monthly"

    def test_business_days_only_flag(self, sample_daily_data: TimeSeriesData):
        """Test business_days_only flag produces different results."""
        # With business_days_only=True (default)
        result_business = aggregate_time_series(
            sample_daily_data, "weekly", business_days_only=True
        )

        # With business_days_only=False
        result_all = aggregate_time_series(
            sample_daily_data, "weekly", business_days_only=False
        )

        # Results should differ (more points when including weekends)
        # Note: This assumes sample data includes weekends
        assert len(result_business.time_series) <= len(result_all.time_series)

    def test_empty_series(self):
        """Empty time_series should return unchanged."""
        empty = TimeSeriesData(
            metric_name="Test",
            chart_type="line",
            data_type="currency",
            time_series=[],
            statistics={},
            format_options={},
            error=None,
        )

        result = aggregate_time_series(empty, "weekly")
        assert len(result.time_series) == 0
        assert result.metric_name == "Test"


class TestAdapterFunctions:
    """Test suite for internal adapter functions."""

    @pytest.fixture
    def sample_time_series(self) -> TimeSeriesData:
        """Create minimal TimeSeriesData for adapter testing."""
        points = [
            ChartDataPoint(
                date="2025-01-01",
                timestamp="2025-01-01T00:00:00",
                value=1000.0,
                has_data=True,
            ),
            ChartDataPoint(
                date="2025-01-02",
                timestamp="2025-01-02T00:00:00",
                value=2000.0,
                has_data=True,
            ),
        ]

        return TimeSeriesData(
            metric_name="Test Metric",
            chart_type="line",
            data_type="currency",
            time_series=points,
            statistics={"total": 3000.0, "average": 1500.0},
            format_options={
                "date_column": "date",
            },
            error=None,
        )

    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        """Create DataFrame for adapter testing."""
        return pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-01", "2025-01-02"]),
                "value": [1000.0, 2000.0],
            }
        )

    def test_time_series_to_processed(
        self, sample_time_series: TimeSeriesData, sample_dataframe: pd.DataFrame
    ):
        """Verify _time_series_to_processed adapter extracts data correctly."""
        result = _time_series_to_processed(sample_time_series, sample_dataframe)

        # Check type
        assert isinstance(result, ProcessedChartData)

        # Check dates and values
        assert len(result.dates) == 2
        assert result.dates == ["2025-01-01", "2025-01-02"]
        assert result.values == [1000.0, 2000.0]

        # Check statistics
        assert isinstance(result.statistics, ChartStats)
        assert result.statistics.total == 3000.0

        # Check metadata
        assert isinstance(result.metadata, ChartMetaInfo)
        assert result.metadata.date_column == "date"

    def test_processed_to_time_series(self, sample_time_series: TimeSeriesData):
        """Verify _processed_to_time_series adapter rebuilds TimeSeriesData."""
        # Create ProcessedChartData
        processed = ProcessedChartData(
            dates=["2025-01-01", "2025-01-02"],
            values=[1500.0, 2500.0],
            statistics=ChartStats(
                total=4000.0,
                average=2000.0,
                minimum=1500.0,
                maximum=2500.0,
                data_points=2,
            ),
            metadata=ChartMetaInfo(
                date_column="date",
                date_range="2025-01-01 to 2025-01-02",
            ),
            error=None,
        )

        result = _processed_to_time_series(processed, sample_time_series, "weekly")

        # Check type
        assert isinstance(result, TimeSeriesData)

        # Check preserved fields
        assert result.metric_name == sample_time_series.metric_name
        assert result.chart_type == sample_time_series.chart_type
        assert result.data_type == sample_time_series.data_type

        # Check rebuilt time_series
        assert len(result.time_series) == 2
        assert all(isinstance(p, ChartDataPoint) for p in result.time_series)
        assert result.time_series[0].date == "2025-01-01"
        assert result.time_series[0].value == 1500.0

        # Check updated statistics
        assert result.statistics["total"] == 4000.0
        assert result.statistics["average"] == 2000.0

        # Check updated aggregation field
        assert result.format_options["aggregation"] == "weekly"


class TestFormatAllChartData:
    """Test suite for format_all_chart_data with timeframe parameter."""

    @pytest.fixture
    def sample_eod_df(self) -> pd.DataFrame:
        """Create minimal EOD DataFrame for testing."""
        dates = pd.date_range("2025-01-01", periods=10, freq="D")
        return pd.DataFrame(
            {
                "Submission Date": dates,
                "Total Production Today": [10000.0] * 10,
                "Adjustments Today": [0.0] * 10,
                "Write-offs Today": [0.0] * 10,
                "Patient Income Today": [9000.0] * 10,
                "Unearned Income Today": [0.0] * 10,
                "Insurance Income Today": [1000.0] * 10,
                "New Patients - Total Month to Date": list(range(1, 11)),
            }
        )

    @pytest.fixture
    def sample_front_df(self) -> pd.DataFrame:
        """Create minimal front KPI DataFrame for testing."""
        dates = pd.date_range("2025-01-01", periods=10, freq="D")
        return pd.DataFrame(
            {
                "Submission Date": dates,
                "Total Hygiene Appointments": [20] * 10,
                "Patients Not Reappointed": [2] * 10,
                "Treatments Presented": [10] * 10,
                "Treatments Scheduled": [8] * 10,
                "Treatments Scheduled Same Day": [2] * 10,
            }
        )

    def test_applies_to_all_charts(
        self, sample_eod_df: pd.DataFrame, sample_front_df: pd.DataFrame
    ):
        """All 5 charts should have aggregation field updated."""
        result = format_all_chart_data(
            sample_eod_df, sample_front_df, timeframe="weekly"
        )

        # Check all 5 charts have aggregation field set
        assert result.production_total.format_options["aggregation"] == "weekly"
        assert result.collection_rate.format_options["aggregation"] == "weekly"
        assert result.new_patients.format_options["aggregation"] == "weekly"
        assert result.case_acceptance.format_options["aggregation"] == "weekly"
        assert result.hygiene_reappointment.format_options["aggregation"] == "weekly"

    def test_pydantic_validation_passes(
        self, sample_eod_df: pd.DataFrame, sample_front_df: pd.DataFrame
    ):
        """AllChartsData Pydantic validation must pass after aggregation."""
        for timeframe in ["daily", "weekly", "monthly"]:
            result = format_all_chart_data(
                sample_eod_df, sample_front_df, timeframe=timeframe
            )

            # If we got here, Pydantic validation succeeded
            # Verify structure
            assert isinstance(result.production_total, TimeSeriesData)
            assert isinstance(result.collection_rate, TimeSeriesData)
            assert isinstance(result.new_patients, TimeSeriesData)
            assert isinstance(result.case_acceptance, TimeSeriesData)
            assert isinstance(result.hygiene_reappointment, TimeSeriesData)

    def test_daily_no_aggregation(
        self, sample_eod_df: pd.DataFrame, sample_front_df: pd.DataFrame
    ):
        """Daily timeframe should not modify data."""
        result = format_all_chart_data(
            sample_eod_df, sample_front_df, timeframe="daily"
        )

        # Charts should have ~10 data points (daily data)
        assert len(result.production_total.time_series) == 10
        assert len(result.collection_rate.time_series) == 10
