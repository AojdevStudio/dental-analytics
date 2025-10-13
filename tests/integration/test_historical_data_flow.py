"""Integration tests for historical data functionality.

Tests complete data flow from configuration through chart formatting,
validating operational day logic and error handling across modules.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pandas as pd

from apps.backend.chart_data import (
    format_all_chart_data,
    validate_chart_data,
)
from core.models.chart_models import AllChartsData
from config.data_sources import (
    get_data_source_config,
    get_historical_date_range,
    get_latest_operational_date,
    get_operational_days_in_range,
)


class TestHistoricalDataIntegrationFlow:
    """Test complete historical data processing flow."""

    def test_complete_operational_day_workflow(self) -> None:
        """Test complete workflow from Sunday to chart data generation."""
        # Scenario: It's Sunday, need to show Saturday data in charts

        # Step 1: Determine latest operational date (Sunday -> Saturday)
        sunday = datetime(2025, 9, 21)  # Known Sunday
        latest_operational = get_latest_operational_date(sunday)

        expected_saturday = datetime(2025, 9, 20)
        assert latest_operational.date() == expected_saturday.date()

        # Step 2: Get historical range from that operational date
        with patch("config.data_sources.get_latest_operational_date") as mock_latest:
            mock_latest.return_value = expected_saturday
            start_date, end_date = get_historical_date_range(days_back=7)

        assert end_date.date() == expected_saturday.date()
        assert start_date.date() == (expected_saturday - timedelta(days=7)).date()

        # Step 3: Get operational days in that range
        operational_days = get_operational_days_in_range(start_date, end_date)

        # Verify only operational days included
        for day in operational_days:
            assert day.weekday() != 6  # No Sundays

        # Step 4: Simulate data processing with mock data
        mock_eod_data = self._create_mock_eod_data(operational_days)
        mock_front_kpi_data = self._create_mock_front_kpi_data(operational_days)

        # Step 5: Generate chart data
        chart_data = format_all_chart_data(mock_eod_data, mock_front_kpi_data)
        assert isinstance(chart_data, AllChartsData)

        # Step 6: Validate complete chart structure
        for metric_model in (
            chart_data.production_total,
            chart_data.collection_rate,
            chart_data.new_patients,
            chart_data.case_acceptance,
            chart_data.hygiene_reappointment,
        ):
            assert validate_chart_data(metric_model)

        # Step 7: Verify operational day logic reflected in data
        assert chart_data.metadata.data_sources.eod_available is True
        assert chart_data.metadata.data_sources.front_kpi_available is True

    def test_missing_data_handling_workflow(self) -> None:
        """Test workflow when some data sources are unavailable."""
        # Scenario: EOD data available, Front KPI data missing

        # Create mock data with only EOD information
        operational_days = get_operational_days_in_range(
            datetime(2025, 9, 15), datetime(2025, 9, 20)
        )

        mock_eod_data = self._create_mock_eod_data(operational_days)

        # Generate chart data with missing front KPI data
        chart_data = format_all_chart_data(mock_eod_data, None)
        assert isinstance(chart_data, AllChartsData)

        # EOD-based metrics should have data
        assert len(chart_data.production_total.time_series) > 0
        assert len(chart_data.collection_rate.time_series) > 0
        assert len(chart_data.new_patients.time_series) > 0

        # Front KPI metrics should show graceful degradation
        assert chart_data.case_acceptance.error is not None
        assert chart_data.hygiene_reappointment.error is not None

        # Metadata should reflect partial availability
        metadata = chart_data.metadata
        assert metadata.data_sources.eod_available is True
        assert metadata.data_sources.front_kpi_available is False

    def test_data_source_configuration_integration(self) -> None:
        """Test integration between data source config and chart generation."""
        # Get configuration for both data sources
        eod_config = get_data_source_config("eod_billing")
        front_kpi_config = get_data_source_config("front_kpis")

        assert eod_config is not None
        assert front_kpi_config is not None

        # Verify configuration contains required fields for chart processing
        required_fields = ["date_column", "operational_days_only", "latest_fallback"]

        for field in required_fields:
            assert field in eod_config
            assert field in front_kpi_config

        # Test that date column configuration works with chart processing
        date_column = eod_config["date_column"]

        # Create test data using configured date column
        test_data = pd.DataFrame(
            {
                date_column: ["2025-09-15 10:00:00", "2025-09-16 11:00:00"],
                "total_production": [1000.0, 2000.0],
            }
        )

        # Chart formatting should work with configured column names
        chart_data = format_all_chart_data(test_data, None)
        assert isinstance(chart_data, AllChartsData)
        production_chart = chart_data.production_total

        assert len(production_chart.time_series) == 2
        assert production_chart.time_series[0].value == 1000.0

    def test_weekend_gap_handling(self) -> None:
        """Test handling of weekend gaps in time-series data."""
        # Create data spanning Friday to Monday (includes weekend)
        friday = datetime(2025, 9, 19)
        monday = datetime(2025, 9, 22)

        operational_days = get_operational_days_in_range(friday, monday)

        # Should include Friday, Saturday, Monday but not Sunday
        assert len(operational_days) == 3

        # Create mock data for operational days only
        mock_data = pd.DataFrame(
            {
                "Submission Date": [
                    "2025-09-19 17:00:00",  # Friday
                    "2025-09-20 12:00:00",  # Saturday
                    "2025-09-22 09:00:00",  # Monday
                ],
                "total_production": [1000.0, 1500.0, 2000.0],
                "total_collections": [800.0, 1200.0, 1800.0],
            }
        )

        chart_data = format_all_chart_data(mock_data, None)
        assert isinstance(chart_data, AllChartsData)

        # Chart should handle weekend gap gracefully
        production_series = chart_data.production_total.time_series
        assert len(production_series) == 3

        # Verify dates are correctly processed (no Sunday data)
        dates = [point.date for point in production_series]
        assert "2025-09-19" in dates  # Friday
        assert "2025-09-20" in dates  # Saturday
        assert "2025-09-21" not in dates  # Sunday (no data)
        assert "2025-09-22" in dates  # Monday

    def test_data_quality_validation_flow(self) -> None:
        """Test data quality validation throughout the processing flow."""
        # Create data with various quality issues
        problematic_data = pd.DataFrame(
            {
                "Submission Date": [
                    "2025-09-15 10:00:00",  # Valid
                    "invalid-date",  # Invalid date
                    "2025-09-17 12:00:00",  # Valid
                    "",  # Empty date
                ],
                "total_production": [
                    1000.0,  # Valid
                    "invalid",  # Invalid number
                    None,  # Missing value
                    2000.0,  # Valid
                ],
                "total_collections": [
                    800.0,  # Valid
                    900.0,  # Valid
                    None,  # Missing value
                    1800.0,  # Valid
                ],
            }
        )

        chart_data = format_all_chart_data(problematic_data, None)
        assert isinstance(chart_data, AllChartsData)

        # Chart should handle data quality issues gracefully
        production_series = chart_data.production_total.time_series

        # Should process only valid data points
        valid_points = [p for p in production_series if p.has_data]
        invalid_points = [p for p in production_series if not p.has_data]

        # Should have some valid and some invalid points
        assert len(valid_points) > 0
        assert len(invalid_points) > 0

        # Statistics should reflect data quality
        stats = chart_data.production_total.statistics
        if stats is None:
            valid_count = 0
            missing_count = 0
            coverage = 0.0
        elif isinstance(stats, dict):
            valid_count = stats.get("valid_points", 0)
            missing_count = stats.get("missing_points", 0)
            coverage = stats.get("coverage_percentage", 0.0)
        else:
            valid_count = getattr(stats, "valid_points", 0)
            missing_count = getattr(stats, "missing_points", 0)
            coverage = getattr(stats, "coverage_percentage", 0.0)
        assert valid_count == len(valid_points)
        assert missing_count == len(invalid_points)
        assert coverage < 100.0  # Due to missing data

    def test_performance_with_large_dataset(self) -> None:
        """Test performance and memory usage with larger datasets."""
        # Create larger dataset (90 days of data)
        start_date = datetime(2025, 6, 1)
        end_date = datetime(2025, 8, 30)
        operational_days = get_operational_days_in_range(start_date, end_date)

        # Should have approximately 60-65 operational days (90 days * 6/7)
        assert len(operational_days) >= 60
        assert len(operational_days) <= 80

        # Create large mock dataset
        large_eod_data = self._create_mock_eod_data(operational_days)
        large_front_kpi_data = self._create_mock_front_kpi_data(operational_days)

        # Process large dataset
        chart_data = format_all_chart_data(large_eod_data, large_front_kpi_data)
        assert isinstance(chart_data, AllChartsData)

        # Verify all data is processed
        for metric_model in (
            chart_data.production_total,
            chart_data.collection_rate,
            chart_data.new_patients,
            chart_data.case_acceptance,
            chart_data.hygiene_reappointment,
        ):
            assert len(metric_model.time_series) == len(operational_days)

        # Verify statistics are calculated correctly
        production_stats = chart_data.production_total.statistics
        if isinstance(production_stats, dict):
            total_points = production_stats.get("total_points", 0)
            valid_points = production_stats.get("valid_points", 0)
        else:
            total_points = getattr(production_stats, "total_points", 0)
            valid_points = getattr(production_stats, "valid_points", 0)
        assert total_points == len(operational_days)
        assert valid_points > 0

    def _create_mock_eod_data(self, operational_days: list[datetime]) -> pd.DataFrame:
        """Create mock EOD data for testing."""
        data = {
            "Submission Date": [],
            "total_production": [],
            "total_collections": [],
            "new_patients": [],
        }

        for i, day in enumerate(operational_days):
            data["Submission Date"].append(day.strftime("%Y-%m-%d %H:%M:%S"))
            data["total_production"].append(1000.0 + (i * 100))  # Increasing production
            data["total_collections"].append(
                800.0 + (i * 80)
            )  # Proportional collections
            data["new_patients"].append(2 + (i % 5))  # Varying new patients

        return pd.DataFrame(data)

    def _create_mock_front_kpi_data(
        self, operational_days: list[datetime]
    ) -> pd.DataFrame:
        """Create mock Front KPI data for testing."""
        data = {
            "Submission Date": [],
            "treatments_presented": [],
            "treatments_scheduled": [],
            "total_hygiene_appointments": [],
            "patients_not_reappointed": [],
        }

        for i, day in enumerate(operational_days):
            data["Submission Date"].append(day.strftime("%Y-%m-%d %H:%M:%S"))
            data["treatments_presented"].append(
                10000 + (i * 500)
            )  # Increasing presentations
            data["treatments_scheduled"].append(
                8000 + (i * 400)
            )  # Good acceptance rate
            data["total_hygiene_appointments"].append(10 + (i % 8))  # Varying hygiene
            data["patients_not_reappointed"].append(i % 3)  # Occasional no-shows

        return pd.DataFrame(data)


class TestErrorHandlingIntegration:
    """Test error handling across module boundaries."""

    def test_cascading_error_handling(self) -> None:
        """Test error handling cascades properly through the system."""
        # Test various error conditions that should be handled gracefully

        # 1. Invalid data source configuration
        config = get_data_source_config("nonexistent_source")
        assert config is None

        # 2. Completely empty/null data
        chart_data = format_all_chart_data(None, None)
        assert isinstance(chart_data, AllChartsData)

        # Should still return valid structure with error indicators
        assert chart_data.metadata.data_sources.eod_available is False
        assert chart_data.metadata.data_sources.front_kpi_available is False

        # 3. Malformed DataFrames
        malformed_df = pd.DataFrame({"wrong_columns": [1, 2, 3]})
        chart_data = format_all_chart_data(malformed_df, malformed_df)
        assert isinstance(chart_data, AllChartsData)

        # Should handle missing columns gracefully
        for metric_model in (
            chart_data.production_total,
            chart_data.collection_rate,
            chart_data.new_patients,
        ):
            # Should either have error or empty time series
            assert metric_model.error is not None or len(metric_model.time_series) == 0

    def test_data_validation_integration(self) -> None:
        """Test data validation integration across modules."""
        # Create data that passes initial validation but has processing issues
        edge_case_data = pd.DataFrame(
            {
                "Submission Date": [
                    "2025-09-15 10:00:00",
                    "2025-09-16 11:00:00",
                ],
                "total_production": [float("inf"), -float("inf")],  # Infinite values
                "total_collections": [1000.0, 2000.0],
            }
        )

        chart_data = format_all_chart_data(edge_case_data, None)
        assert isinstance(chart_data, AllChartsData)

        # Should handle infinite values gracefully
        collection_series = chart_data.collection_rate.time_series

        # Infinite production values should be handled
        # Collection rate calculation should handle infinite denominators
        for point in collection_series:
            if point.has_data:
                assert isinstance(point.value, (int, float))
                assert not (
                    point.value == float("inf") or point.value == -float("inf")
                )


class TestRealWorldScenarios:
    """Test realistic dental practice scenarios."""

    def test_holiday_week_scenario(self) -> None:
        """Test processing during a week with holidays (theoretical)."""
        # Scenario: Week with Memorial Day Monday (if it were a holiday)
        # This tests the framework's extensibility for holiday handling

        # Current implementation: Monday is operational
        memorial_day_week_start = datetime(2025, 5, 26)  # Monday
        memorial_day_week_end = datetime(2025, 5, 31)  # Saturday

        operational_days = get_operational_days_in_range(
            memorial_day_week_start, memorial_day_week_end
        )

        # Currently treats all Monday-Saturday as operational
        assert len(operational_days) == 6  # All weekdays

        # Future enhancement could check holiday list
        # and exclude Memorial Day Monday

    def test_month_end_reporting_scenario(self) -> None:
        """Test month-end reporting with operational day logic."""
        # Scenario: Generate month-end report on Sunday, March 30th
        month_end_sunday = datetime(2025, 3, 30)  # Sunday in March

        # Should use Saturday March 29th as latest operational day
        latest_operational = get_latest_operational_date(month_end_sunday)
        expected_saturday = datetime(2025, 3, 29)

        assert latest_operational.date() == expected_saturday.date()

        # Month-to-date range should end on Saturday
        month_start = datetime(2025, 3, 1)
        operational_days = get_operational_days_in_range(
            month_start, latest_operational
        )

        # March 2025: March 1-29, excluding Sundays (2nd, 9th, 16th, 23rd)
        # Total days 1-29: 29, Sundays: 4, Operational: 25
        assert len(operational_days) == 25

        # Verify no Sundays included
        for day in operational_days:
            assert day.weekday() != 6

    def test_new_practice_startup_scenario(self) -> None:
        """Test handling of sparse data for new practice."""
        # Scenario: New practice with only a few days of data
        sparse_data = pd.DataFrame(
            {
                "Submission Date": [
                    "2025-09-15 10:00:00",  # Monday
                    "2025-09-17 14:00:00",  # Wednesday
                ],
                "total_production": [500.0, 750.0],
                "total_collections": [400.0, 600.0],
                "new_patients": [2, 3],
            }
        )

        chart_data = format_all_chart_data(sparse_data, None)
        assert isinstance(chart_data, AllChartsData)

        # Should handle sparse data gracefully
        production_stats = chart_data.production_total.statistics
        if isinstance(production_stats, dict):
            total_points = production_stats.get("total_points")
            valid_points = production_stats.get("valid_points")
            coverage = production_stats.get("coverage_percentage")
        else:
            total_points = getattr(production_stats, "total_points", None)
            valid_points = getattr(production_stats, "valid_points", None)
            coverage = getattr(production_stats, "coverage_percentage", None)
        assert total_points == 2
        assert valid_points == 2
        assert coverage == 100.0

        # Charts should still be valid with limited data
        for metric_model in (
            chart_data.production_total,
            chart_data.collection_rate,
            chart_data.new_patients,
        ):
            assert validate_chart_data(metric_model)

    def test_high_volume_practice_scenario(self) -> None:
        """Test handling of high-volume practice data."""
        # Scenario: Large practice with high daily volumes
        high_volume_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15 18:00:00"],
                "total_production": [50000.0],  # $50k daily production
                "total_collections": [48000.0],  # 96% collection rate
                "new_patients": [25],  # High new patient volume
            }
        )

        chart_data = format_all_chart_data(high_volume_data, None)
        assert isinstance(chart_data, AllChartsData)

        # Should handle large values correctly
        production_point = chart_data.production_total.time_series[0]
        assert production_point.value == 50000.0

        collection_rate_point = chart_data.collection_rate.time_series[0]
        assert abs(collection_rate_point.value - 96.0) < 0.1  # 96% rate

        new_patients_point = chart_data.new_patients.time_series[0]
        assert new_patients_point.value == 25
