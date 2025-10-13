"""Unit tests for chart_models.py Pydantic models.

Tests cover:
- Valid model instantiation
- Field validation rules
- Cross-field validation
- Edge cases (empty lists, None values)
- Error scenarios (invalid formats, mismatched lengths)

Target: 95%+ test coverage
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from core.models.chart_models import (
    ChartDataPoint,
    ChartMetaInfo,
    ChartsMetadata,
    ChartStats,
    DataSourceInfo,
    MultiLocationKPIs,
    ProcessedChartData,
    SummaryStatistics,
    TimeSeriesData,
)


class TestChartDataPoint:
    """Test suite for ChartDataPoint model."""

    def test_valid_data_point(self) -> None:
        """Test creating a valid chart data point."""
        point = ChartDataPoint(
            date="2025-09-15",
            timestamp="2025-09-15T10:30:00",
            value=1500.50,
            has_data=True,
        )
        assert point.date == "2025-09-15"
        assert point.timestamp == "2025-09-15T10:30:00"
        assert point.value == 1500.50
        assert point.has_data is True

    def test_data_point_with_none_value(self) -> None:
        """Test data point with None value and has_data=False."""
        point = ChartDataPoint(
            date="2025-09-15",
            timestamp="2025-09-15T10:30:00",
            value=None,
            has_data=False,
        )
        assert point.value is None
        assert point.has_data is False

    def test_invalid_date_format(self) -> None:
        """Test that invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            ChartDataPoint(
                date="09/15/2025",  # Invalid format
                timestamp="2025-09-15T10:30:00",
                value=1500.50,
            )

    def test_invalid_timestamp_format(self) -> None:
        """Test that invalid timestamp format raises ValueError."""
        with pytest.raises(ValueError, match="ISO format"):
            ChartDataPoint(
                date="2025-09-15",
                timestamp="09/15/2025 10:30",  # Invalid format
                value=1500.50,
            )

    def test_iso_timestamp_with_z_suffix(self) -> None:
        """Test ISO timestamp with Z (UTC) suffix is valid."""
        point = ChartDataPoint(
            date="2025-09-15",
            timestamp="2025-09-15T10:30:00Z",
            value=1500.50,
        )
        assert point.timestamp == "2025-09-15T10:30:00Z"

    def test_integer_value(self) -> None:
        """Test data point accepts integer values."""
        point = ChartDataPoint(
            date="2025-09-15",
            timestamp="2025-09-15T10:30:00",
            value=42,
            has_data=True,
        )
        assert point.value == 42


class TestChartStats:
    """Test suite for ChartStats model."""

    def test_valid_chart_stats(self) -> None:
        """Test creating valid chart statistics."""
        stats = ChartStats(
            total=250000.0,
            average=12500.0,
            minimum=8000.0,
            maximum=18000.0,
            data_points=20,
        )
        assert stats.total == 250000.0
        assert stats.average == 12500.0
        assert stats.data_points == 20

    def test_default_values(self) -> None:
        """Test that all fields have default values."""
        stats = ChartStats()
        assert stats.total == 0.0
        assert stats.average == 0.0
        assert stats.minimum == 0.0
        assert stats.maximum == 0.0
        assert stats.data_points == 0

    def test_negative_data_points_rejected(self) -> None:
        """Test that negative data_points count is rejected."""
        with pytest.raises(ValidationError):
            ChartStats(data_points=-1)

    def test_zero_data_points_valid(self) -> None:
        """Test that zero data_points is valid (no data scenario)."""
        stats = ChartStats(data_points=0)
        assert stats.data_points == 0


class TestChartMetaInfo:
    """Test suite for ChartMetaInfo model."""

    def test_valid_metadata(self) -> None:
        """Test creating valid chart metadata."""
        meta = ChartMetaInfo(
            date_column="Submission Date",
            date_range="2025-01-01 to 2025-01-31",
            aggregation="daily",
            business_days_only=True,
        )
        assert meta.date_column == "Submission Date"
        assert meta.aggregation == "daily"
        assert meta.business_days_only is True

    def test_optional_fields_none(self) -> None:
        """Test metadata with optional fields as None."""
        meta = ChartMetaInfo(
            date_column="Date",
            date_range="2025-01-01 to 2025-01-31",
        )
        assert meta.error is None
        assert meta.aggregation is None
        assert meta.business_days_only is None

    def test_aggregation_literal_validation(self) -> None:
        """Test that aggregation only accepts valid literals."""
        # Valid aggregation levels
        for level in ["daily", "weekly", "monthly"]:
            meta = ChartMetaInfo(
                date_column="Date",
                date_range="2025-01-01 to 2025-01-31",
                aggregation=level,
            )
            assert meta.aggregation == level

    def test_error_message_preserved(self) -> None:
        """Test that error messages are preserved."""
        meta = ChartMetaInfo(
            date_column="Date",
            date_range="2025-01-01 to 2025-01-31",
            error="Data unavailable",
        )
        assert meta.error == "Data unavailable"


class TestProcessedChartData:
    """Test suite for ProcessedChartData model."""

    def test_valid_chart_data(self) -> None:
        """Test creating valid processed chart data."""
        meta = ChartMetaInfo(date_column="Date", date_range="2025-01-01 to 2025-01-05")
        data = ProcessedChartData(
            dates=["2025-01-01", "2025-01-02", "2025-01-03"],
            values=[12500.0, 13200.0, 11800.0],
            metadata=meta,
        )
        assert len(data.dates) == 3
        assert len(data.values) == 3
        assert data.error is None

    def test_mismatched_dates_values_length(self) -> None:
        """Test that mismatched dates/values length raises ValidationError."""
        meta = ChartMetaInfo(date_column="Date", date_range="2025-01-01 to 2025-01-05")
        with pytest.raises(ValidationError, match="Mismatched list lengths"):
            ProcessedChartData(
                dates=["2025-01-01", "2025-01-02"],
                values=[12500.0, 13200.0, 11800.0],  # 3 values, 2 dates
                metadata=meta,
            )

    def test_empty_dates_values_lists(self) -> None:
        """Test that empty dates/values lists are valid (no data scenario)."""
        meta = ChartMetaInfo(date_column="Date", date_range="2025-01-01 to 2025-01-05")
        data = ProcessedChartData(dates=[], values=[], metadata=meta)
        assert data.dates == []
        assert data.values == []

    def test_default_statistics_created(self) -> None:
        """Test that statistics field defaults to ChartStats instance."""
        meta = ChartMetaInfo(date_column="Date", date_range="2025-01-01 to 2025-01-05")
        data = ProcessedChartData(dates=[], values=[], metadata=meta)
        assert isinstance(data.statistics, ChartStats)


class TestTimeSeriesData:
    """Test suite for TimeSeriesData model."""

    def test_valid_time_series(self) -> None:
        """Test creating valid time series data with multiple points."""
        point1 = ChartDataPoint(
            date="2025-01-01",
            timestamp="2025-01-01T00:00:00",
            value=12500.0,
            has_data=True,
        )
        point2 = ChartDataPoint(
            date="2025-01-02",
            timestamp="2025-01-02T00:00:00",
            value=13200.0,
            has_data=True,
        )
        ts_data = TimeSeriesData(
            metric_name="Production Total",
            chart_type="line",
            data_type="currency",
            time_series=[point1, point2],
        )
        assert ts_data.metric_name == "Production Total"
        assert len(ts_data.time_series) == 2

    def test_empty_time_series_valid(self) -> None:
        """Test that empty time_series list is valid."""
        ts_data = TimeSeriesData(
            metric_name="Collection Rate",
            chart_type="bar",
            data_type="percentage",
            time_series=[],
        )
        assert ts_data.time_series == []

    def test_chart_type_literal_validation(self) -> None:
        """Test that chart_type only accepts valid literals."""
        for chart_type in ["line", "bar", "area"]:
            ts_data = TimeSeriesData(
                metric_name="Test Metric",
                chart_type=chart_type,
                data_type="float",
            )
            assert ts_data.chart_type == chart_type

    def test_data_type_literal_validation(self) -> None:
        """Test that data_type only accepts valid literals."""
        for data_type in ["currency", "percentage", "count", "float"]:
            ts_data = TimeSeriesData(
                metric_name="Test Metric",
                chart_type="line",
                data_type=data_type,
            )
            assert ts_data.data_type == data_type

    def test_format_options_default_empty(self) -> None:
        """Test that format_options defaults to empty dict."""
        ts_data = TimeSeriesData(
            metric_name="Test",
            chart_type="line",
            data_type="currency",
        )
        assert ts_data.format_options == {}

    def test_statistics_dict_accepted(self) -> None:
        """Test that statistics accepts dict with numeric values."""
        ts_data = TimeSeriesData(
            metric_name="Test",
            chart_type="line",
            data_type="float",
            statistics={"min": 100.0, "max": 200.0, "avg": 150.0},
        )
        assert ts_data.statistics is not None
        assert ts_data.statistics["avg"] == 150.0


class TestSummaryStatistics:
    """Test suite for SummaryStatistics model."""

    def test_valid_summary_statistics(self) -> None:
        """Test creating valid summary statistics."""
        stats = SummaryStatistics(
            total_points=30,
            valid_points=28,
            missing_points=2,
            coverage_percentage=93.3,
            date_range={"start": "2025-01-01", "end": "2025-01-30"},
            min_value=8500.0,
            max_value=15200.0,
            average_value=12350.0,
        )
        assert stats.total_points == 30
        assert stats.valid_points == 28
        assert stats.coverage_percentage == 93.3

    def test_default_values(self) -> None:
        """Test summary statistics with default values."""
        stats = SummaryStatistics()
        assert stats.total_points == 0
        assert stats.valid_points == 0
        assert stats.missing_points == 0
        assert stats.coverage_percentage == 0.0
        assert stats.date_range is None

    def test_coverage_percentage_bounds(self) -> None:
        """Test that coverage_percentage must be between 0 and 100."""
        # Valid edge cases
        SummaryStatistics(coverage_percentage=0.0)
        SummaryStatistics(coverage_percentage=100.0)

        # Invalid cases
        with pytest.raises(ValidationError):
            SummaryStatistics(coverage_percentage=-1.0)
        with pytest.raises(ValidationError):
            SummaryStatistics(coverage_percentage=101.0)

    def test_negative_counts_rejected(self) -> None:
        """Test that negative point counts are rejected."""
        with pytest.raises(ValidationError):
            SummaryStatistics(total_points=-1)
        with pytest.raises(ValidationError):
            SummaryStatistics(valid_points=-5)


class TestDataSourceInfo:
    """Test suite for DataSourceInfo model."""

    def test_valid_data_source_info(self) -> None:
        """Test creating valid data source info."""
        info = DataSourceInfo(eod_available=True, front_kpi_available=True)
        assert info.eod_available is True
        assert info.front_kpi_available is True

    def test_default_values_false(self) -> None:
        """Test that availability flags default to False."""
        info = DataSourceInfo()
        assert info.eod_available is False
        assert info.front_kpi_available is False

    def test_partial_availability(self) -> None:
        """Test data source info with partial availability."""
        info = DataSourceInfo(eod_available=True, front_kpi_available=False)
        assert info.eod_available is True
        assert info.front_kpi_available is False


class TestChartsMetadata:
    """Test suite for ChartsMetadata model."""

    def test_valid_charts_metadata(self) -> None:
        """Test creating valid charts metadata."""
        data_sources = DataSourceInfo(eod_available=True, front_kpi_available=True)
        meta = ChartsMetadata(data_sources=data_sources, total_metrics=5)
        assert meta.total_metrics == 5
        assert meta.data_sources.eod_available is True

    def test_auto_generated_timestamp(self) -> None:
        """Test that generated_at timestamp is auto-generated."""
        meta = ChartsMetadata()
        # Verify timestamp is ISO format
        datetime.fromisoformat(meta.generated_at)
        assert isinstance(meta.generated_at, str)

    def test_default_data_sources_created(self) -> None:
        """Test that data_sources defaults to DataSourceInfo instance."""
        meta = ChartsMetadata()
        assert isinstance(meta.data_sources, DataSourceInfo)
        assert meta.data_sources.eod_available is False

    def test_default_total_metrics_zero(self) -> None:
        """Test that total_metrics defaults to 0."""
        meta = ChartsMetadata()
        assert meta.total_metrics == 0


class TestMultiLocationKPIs:
    """Test suite for MultiLocationKPIs model."""

    def test_valid_multi_location_kpis(self) -> None:
        """Test creating valid multi-location KPI data."""
        data = MultiLocationKPIs(
            baytown={
                "production_total": 125000.0,
                "collection_rate": 97.5,
                "new_patients": 42,
            },
            humble={
                "production_total": 98000.0,
                "collection_rate": 95.2,
                "new_patients": 35,
            },
        )
        assert data.baytown["production_total"] == 125000.0
        assert data.humble["new_patients"] == 35

    def test_auto_generated_timestamp(self) -> None:
        """Test that timestamp is auto-generated on creation."""
        data = MultiLocationKPIs()
        # Verify timestamp is ISO format
        datetime.fromisoformat(data.timestamp)
        assert isinstance(data.timestamp, str)

    def test_empty_location_dicts_valid(self) -> None:
        """Test that empty location dicts are valid."""
        data = MultiLocationKPIs(baytown={}, humble={})
        assert data.baytown == {}
        assert data.humble == {}

    def test_none_values_in_kpi_dict(self) -> None:
        """Test that None values are accepted in KPI dictionaries."""
        data = MultiLocationKPIs(
            baytown={"production_total": 125000.0, "collection_rate": None}
        )
        assert data.baytown["collection_rate"] is None

    def test_default_empty_dicts(self) -> None:
        """Test that location dicts default to empty."""
        data = MultiLocationKPIs()
        assert data.baytown == {}
        assert data.humble == {}


class TestEdgeCases:
    """Test edge cases across multiple models."""

    def test_chart_data_with_single_point(self) -> None:
        """Test ProcessedChartData with single data point."""
        meta = ChartMetaInfo(date_column="Date", date_range="2025-01-01")
        data = ProcessedChartData(dates=["2025-01-01"], values=[12500.0], metadata=meta)
        assert len(data.dates) == 1
        assert len(data.values) == 1

    def test_time_series_with_mixed_has_data_flags(self) -> None:
        """Test TimeSeriesData with mix of valid and missing data points."""
        point1 = ChartDataPoint(
            date="2025-01-01",
            timestamp="2025-01-01T00:00:00",
            value=12500.0,
            has_data=True,
        )
        point2 = ChartDataPoint(
            date="2025-01-02",
            timestamp="2025-01-02T00:00:00",
            value=None,
            has_data=False,
        )
        ts_data = TimeSeriesData(
            metric_name="Production",
            chart_type="line",
            data_type="currency",
            time_series=[point1, point2],
        )
        assert ts_data.time_series[0].has_data is True
        assert ts_data.time_series[1].has_data is False

    def test_summary_statistics_with_no_data(self) -> None:
        """Test SummaryStatistics representing no available data."""
        stats = SummaryStatistics(
            total_points=10,
            valid_points=0,
            missing_points=10,
            coverage_percentage=0.0,
        )
        assert stats.valid_points == 0
        assert stats.coverage_percentage == 0.0
