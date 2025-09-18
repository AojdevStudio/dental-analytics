"""Tests for chart data processor module.

Tests frontend-agnostic data formatting, time-series processing,
and chart data structure validation for dental analytics.
"""

from datetime import datetime

import numpy as np
import pandas as pd

from apps.backend.chart_data import (
    calculate_chart_statistics,
    create_time_series_point,
    format_all_chart_data,
    format_collection_rate_chart_data,
    format_hygiene_reappointment_chart_data,
    format_new_patients_chart_data,
    format_production_chart_data,
    format_treatment_acceptance_chart_data,
    parse_datetime_string,
    process_time_series_data,
    safe_float_conversion,
    safe_int_conversion,
    validate_chart_data,
)


class TestSafeConversions:
    """Test safe value conversion functions."""

    def test_safe_float_conversion_valid_numbers(self) -> None:
        """Test safe float conversion with valid numbers."""
        assert safe_float_conversion(123.45) == 123.45
        assert safe_float_conversion("123.45") == 123.45
        assert safe_float_conversion("1,234.56") == 1234.56
        assert safe_float_conversion("$1,234.56") == 1234.56
        assert safe_float_conversion(0) == 0.0
        assert safe_float_conversion("0") == 0.0

    def test_safe_float_conversion_invalid_values(self) -> None:
        """Test safe float conversion with invalid values."""
        assert safe_float_conversion(None) is None
        assert safe_float_conversion(np.nan) is None
        assert safe_float_conversion("invalid") is None
        assert safe_float_conversion("") == 0.0  # Empty string returns 0.0
        assert safe_float_conversion("$") == 0.0  # Just $ returns 0.0

    def test_safe_int_conversion_valid_numbers(self) -> None:
        """Test safe int conversion with valid numbers."""
        assert safe_int_conversion(123) == 123
        assert safe_int_conversion(123.0) == 123
        assert safe_int_conversion("123") == 123
        assert safe_int_conversion("123.0") == 123
        assert safe_int_conversion("1,234") == 1234

    def test_safe_int_conversion_invalid_values(self) -> None:
        """Test safe int conversion with invalid values."""
        assert safe_int_conversion(None) is None
        assert safe_int_conversion(np.nan) is None
        assert safe_int_conversion("invalid") is None
        assert safe_int_conversion("") is None
        assert safe_int_conversion(123.7) == 123  # Truncates


class TestDateTimeParsing:
    """Test datetime string parsing functions."""

    def test_parse_datetime_with_time(self) -> None:
        """Test parsing datetime string with time component."""
        result = parse_datetime_string("2025-09-15 14:30:45")

        assert result is not None
        assert result.year == 2025
        assert result.month == 9
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 45

    def test_parse_date_only(self) -> None:
        """Test parsing date string without time component."""
        result = parse_datetime_string("2025-09-15")

        assert result is not None
        assert result.year == 2025
        assert result.month == 9
        assert result.day == 15
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_parse_invalid_datetime(self) -> None:
        """Test parsing invalid datetime strings."""
        assert parse_datetime_string("") is None
        assert parse_datetime_string(None) is None
        assert parse_datetime_string("invalid-date") is None
        assert parse_datetime_string("2025-13-45") is None  # Invalid month/day
        assert parse_datetime_string(np.nan) is None

    def test_parse_datetime_with_whitespace(self) -> None:
        """Test parsing datetime string with surrounding whitespace."""
        result = parse_datetime_string("  2025-09-15 14:30:45  ")

        assert result is not None
        assert result.year == 2025
        assert result.month == 9
        assert result.day == 15


class TestTimeSeriesPoint:
    """Test time-series data point creation."""

    def test_create_valid_time_series_point(self) -> None:
        """Test creating valid time-series data point."""
        date = datetime(2025, 9, 15, 14, 30)
        value = 123.45

        point = create_time_series_point(date, value)

        assert point is not None
        assert point["date"] == "2025-09-15"
        assert point["timestamp"] == "2025-09-15T14:30:00"
        assert point["value"] == 123.45
        assert point["has_data"] is True

    def test_create_time_series_point_with_none_value(self) -> None:
        """Test creating time-series point with None value."""
        date = datetime(2025, 9, 15)

        point = create_time_series_point(date, None)

        assert point is not None
        assert point["date"] == "2025-09-15"
        assert point["value"] is None
        assert point["has_data"] is False

    def test_create_time_series_point_invalid_date(self) -> None:
        """Test creating time-series point with invalid date."""
        point = create_time_series_point(None, 123.45)
        assert point is None


class TestTimeSeriesProcessing:
    """Test time-series data processing."""

    def test_process_valid_time_series_data(self) -> None:
        """Test processing valid time-series data."""
        df = pd.DataFrame(
            {
                "date": [
                    "2025-09-15 10:00:00",
                    "2025-09-16 11:00:00",
                    "2025-09-17 12:00:00",
                ],
                "value": [100.0, 200.0, 300.0],
            }
        )

        result = process_time_series_data(df, "date", "value", "float")

        assert len(result) == 3
        assert result[0]["date"] == "2025-09-15"
        assert result[0]["value"] == 100.0
        assert result[0]["has_data"] is True
        assert result[-1]["date"] == "2025-09-17"
        assert result[-1]["value"] == 300.0

    def test_process_time_series_with_missing_data(self) -> None:
        """Test processing time-series with missing values."""
        df = pd.DataFrame(
            {
                "date": ["2025-09-15", "2025-09-16", "2025-09-17"],
                "value": [100.0, None, 300.0],
            }
        )

        result = process_time_series_data(df, "date", "value", "float")

        assert len(result) == 3
        assert result[0]["has_data"] is True
        assert result[1]["has_data"] is False
        assert result[1]["value"] is None
        assert result[2]["has_data"] is True

    def test_process_empty_dataframe(self) -> None:
        """Test processing empty DataFrame."""
        df = pd.DataFrame()
        result = process_time_series_data(df, "date", "value")
        assert result == []

    def test_process_none_dataframe(self) -> None:
        """Test processing None DataFrame."""
        result = process_time_series_data(None, "date", "value")
        assert result == []

    def test_process_missing_columns(self) -> None:
        """Test processing DataFrame with missing columns."""
        df = pd.DataFrame({"other_column": [1, 2, 3]})
        result = process_time_series_data(df, "date", "value")
        assert result == []

    def test_process_integer_data_type(self) -> None:
        """Test processing with integer data type conversion."""
        df = pd.DataFrame(
            {"date": ["2025-09-15", "2025-09-16"], "count": ["5", "10.0"]}
        )

        result = process_time_series_data(df, "date", "count", "int")

        assert len(result) == 2
        assert result[0]["value"] == 5
        assert result[1]["value"] == 10
        assert all(isinstance(point["value"], int) for point in result)


class TestChartStatistics:
    """Test chart statistics calculation."""

    def test_calculate_statistics_with_data(self) -> None:
        """Test statistics calculation with valid data."""
        time_series = [
            {"date": "2025-09-15", "value": 100.0, "has_data": True},
            {"date": "2025-09-16", "value": None, "has_data": False},
            {"date": "2025-09-17", "value": 300.0, "has_data": True},
        ]

        stats = calculate_chart_statistics(time_series)

        assert stats["total_points"] == 3
        assert stats["valid_points"] == 2
        assert stats["missing_points"] == 1
        assert abs(stats["coverage_percentage"] - (200.0 / 3)) < 0.01  # ~66.67%
        assert stats["min_value"] == 100.0
        assert stats["max_value"] == 300.0
        assert stats["average_value"] == 200.0
        assert stats["date_range"]["start"] == "2025-09-15"
        assert stats["date_range"]["end"] == "2025-09-17"

    def test_calculate_statistics_empty_data(self) -> None:
        """Test statistics calculation with empty data."""
        stats = calculate_chart_statistics([])

        assert stats["total_points"] == 0
        assert stats["valid_points"] == 0
        assert stats["missing_points"] == 0
        assert stats["coverage_percentage"] == 0.0
        assert stats["date_range"] is None

    def test_calculate_statistics_all_missing(self) -> None:
        """Test statistics with all missing values."""
        time_series = [
            {"date": "2025-09-15", "value": None, "has_data": False},
            {"date": "2025-09-16", "value": None, "has_data": False},
        ]

        stats = calculate_chart_statistics(time_series)

        assert stats["total_points"] == 2
        assert stats["valid_points"] == 0
        assert stats["missing_points"] == 2
        assert stats["coverage_percentage"] == 0.0
        assert "min_value" not in stats
        assert "max_value" not in stats
        assert "average_value" not in stats


class TestProductionChartFormatting:
    """Test production chart data formatting."""

    def test_format_production_chart_data(self, sample_eod_data: pd.DataFrame) -> None:
        """Test formatting production chart data."""
        chart_data = format_production_chart_data(sample_eod_data)

        assert chart_data["metric_name"] == "Production Total"
        assert chart_data["chart_type"] == "line"
        assert chart_data["data_type"] == "currency"
        assert len(chart_data["time_series"]) == 3
        assert chart_data["format_options"]["currency_symbol"] == "$"
        assert chart_data["format_options"]["line_color"] == "#007E9E"  # Teal

    def test_format_production_empty_data(self) -> None:
        """Test formatting production chart with empty data."""
        empty_df = pd.DataFrame()
        chart_data = format_production_chart_data(empty_df)

        assert chart_data["metric_name"] == "Production Total"
        assert len(chart_data["time_series"]) == 0
        assert chart_data["statistics"]["total_points"] == 0

    def test_format_production_alternative_column_names(self) -> None:
        """Test production formatting with alternative column names."""
        df = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15"],
                "Production": [1000.0],  # Alternative column name
            }
        )

        chart_data = format_production_chart_data(df)

        assert len(chart_data["time_series"]) == 1
        assert chart_data["time_series"][0]["value"] == 1000.0


class TestCollectionRateChartFormatting:
    """Test collection rate chart data formatting."""

    def test_format_collection_rate_chart_data(
        self, sample_eod_data: pd.DataFrame
    ) -> None:
        """Test formatting collection rate chart data."""
        chart_data = format_collection_rate_chart_data(sample_eod_data)

        assert chart_data["metric_name"] == "Collection Rate"
        assert chart_data["chart_type"] == "line"
        assert chart_data["data_type"] == "percentage"
        assert chart_data["format_options"]["percentage_symbol"] == "%"
        assert chart_data["format_options"]["line_color"] == "#142D54"  # Navy
        assert "target_range" in chart_data["format_options"]

    def test_format_collection_rate_with_zero_production(self) -> None:
        """Test collection rate formatting with zero production values."""
        df = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16"],
                "Total Production Today": [0.0, 1000.0],
                "Patient Income Today": [0.0, 400.0],
                "Unearned Income Today": [0.0, 200.0],
                "Insurance Income Today": [0.0, 200.0],
            }
        )

        chart_data = format_collection_rate_chart_data(df)

        # First point should have no data due to zero production
        assert chart_data["time_series"][0]["has_data"] is False
        assert chart_data["time_series"][1]["has_data"] is True
        assert chart_data["time_series"][1]["value"] == 80.0  # 800/1000 * 100

    def test_format_collection_rate_missing_columns(self) -> None:
        """Test collection rate formatting with missing required columns."""
        df = pd.DataFrame({"Submission Date": ["2025-09-15"], "other_column": [100.0]})

        chart_data = format_collection_rate_chart_data(df)

        assert "error" in chart_data
        assert len(chart_data["time_series"]) == 0


class TestNewPatientsChartFormatting:
    """Test new patients chart data formatting."""

    def test_format_new_patients_chart_data(
        self, sample_eod_data: pd.DataFrame
    ) -> None:
        """Test formatting new patients chart data."""
        chart_data = format_new_patients_chart_data(sample_eod_data)

        assert chart_data["metric_name"] == "New Patients"
        assert chart_data["chart_type"] == "bar"
        assert chart_data["data_type"] == "count"
        assert chart_data["format_options"]["bar_color"] == "#007E9E"  # Teal
        assert len(chart_data["time_series"]) == 3

        # Check that values are integers
        for point in chart_data["time_series"]:
            if point["has_data"]:
                assert isinstance(point["value"], int)


class TestTreatmentAcceptanceChartFormatting:
    """Test treatment acceptance chart data formatting."""

    def test_format_treatment_acceptance_chart_data(
        self, sample_front_kpi_data: pd.DataFrame
    ) -> None:
        """Test formatting treatment acceptance chart data."""
        chart_data = format_treatment_acceptance_chart_data(sample_front_kpi_data)

        assert chart_data["metric_name"] == "Treatment Acceptance"
        assert chart_data["chart_type"] == "line"
        assert chart_data["data_type"] == "percentage"
        assert chart_data["format_options"]["line_color"] == "#142D54"  # Navy
        assert "target_range" in chart_data["format_options"]
        assert len(chart_data["time_series"]) == 3
        # Values are sorted by date ascending
        # 2025-09-02: ((26739 + 2606) / 40141) * 100 = 73.1048...
        assert abs(chart_data["time_series"][0]["value"] - 73.1048) < 0.01
        # 2025-09-03: (3019 / 35822) * 100 = 8.427...
        assert abs(chart_data["time_series"][1]["value"] - 8.427) < 0.01
        # 2025-09-04: ((2715 + 1907) / 52085) * 100 = 8.875...
        assert abs(chart_data["time_series"][2]["value"] - 8.875) < 0.01

    def test_format_treatment_acceptance_empty_data(self) -> None:
        """Test formatting treatment acceptance with empty data."""
        chart_data = format_treatment_acceptance_chart_data(None)

        assert "error" in chart_data
        assert chart_data["error"] == "No data available"
        assert len(chart_data["time_series"]) == 0

    def test_format_treatment_acceptance_zero_presented(self) -> None:
        """Test treatment acceptance with zero treatments presented."""
        df = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16"],
                "treatments_presented": [0, 1000],
                "treatments_scheduled": [100, 800],
                "$ Same Day Treatment": [50, 50],
            }
        )

        chart_data = format_treatment_acceptance_chart_data(df)

        # First point should have no data due to zero presented
        assert chart_data["time_series"][0]["has_data"] is False
        assert chart_data["time_series"][1]["has_data"] is True
        assert chart_data["time_series"][1]["value"] == 85.0  # (800+50)/1000 * 100


class TestHygieneReappointmentChartFormatting:
    """Test hygiene reappointment chart data formatting."""

    def test_format_hygiene_reappointment_chart_data(
        self, sample_front_kpi_data: pd.DataFrame
    ) -> None:
        """Test formatting hygiene reappointment chart data."""
        chart_data = format_hygiene_reappointment_chart_data(sample_front_kpi_data)

        assert chart_data["metric_name"] == "Hygiene Reappointment"
        assert chart_data["chart_type"] == "line"
        assert chart_data["data_type"] == "percentage"
        assert chart_data["format_options"]["line_color"] == "#007E9E"  # Teal
        assert "target_range" in chart_data["format_options"]
        assert len(chart_data["time_series"]) == 3

    def test_format_hygiene_reappointment_zero_total(self) -> None:
        """Test hygiene reappointment with zero total appointments."""
        df = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16"],
                "Total hygiene Appointments": [0, 10],
                "Number of patients NOT reappointed?": [5, 2],
            }
        )

        chart_data = format_hygiene_reappointment_chart_data(df)

        # First point should have no data due to zero total
        assert chart_data["time_series"][0]["has_data"] is False
        assert chart_data["time_series"][1]["has_data"] is True
        assert chart_data["time_series"][1]["value"] == 80.0  # (10-2)/10 * 100


class TestAllChartDataFormatting:
    """Test comprehensive chart data formatting."""

    def test_format_all_chart_data_complete(
        self, sample_eod_data: pd.DataFrame, sample_front_kpi_data: pd.DataFrame
    ) -> None:
        """Test formatting all chart data with complete datasets."""
        chart_data = format_all_chart_data(sample_eod_data, sample_front_kpi_data)

        # Check all expected metrics are present
        expected_metrics = [
            "production_total",
            "collection_rate",
            "new_patients",
            "treatment_acceptance",
            "hygiene_reappointment",
        ]

        for metric in expected_metrics:
            assert metric in chart_data
            assert "metric_name" in chart_data[metric]
            assert "time_series" in chart_data[metric]

        # Check metadata
        assert "metadata" in chart_data
        assert chart_data["metadata"]["total_metrics"] == 5
        assert chart_data["metadata"]["data_sources"]["eod_available"] is True
        assert chart_data["metadata"]["data_sources"]["front_kpi_available"] is True

    def test_format_all_chart_data_partial_data(
        self, sample_eod_data: pd.DataFrame
    ) -> None:
        """Test formatting all chart data with partial datasets."""
        chart_data = format_all_chart_data(sample_eod_data, None)

        # EOD metrics should have data
        assert len(chart_data["production_total"]["time_series"]) > 0
        assert len(chart_data["collection_rate"]["time_series"]) > 0
        assert len(chart_data["new_patients"]["time_series"]) > 0

        # Front KPI metrics should show errors
        assert "error" in chart_data["treatment_acceptance"]
        assert "error" in chart_data["hygiene_reappointment"]

        # Metadata should reflect partial availability
        assert chart_data["metadata"]["data_sources"]["eod_available"] is True
        assert chart_data["metadata"]["data_sources"]["front_kpi_available"] is False

    def test_format_all_chart_data_no_data(self) -> None:
        """Test formatting all chart data with no datasets."""
        chart_data = format_all_chart_data(None, None)

        # All metrics should show errors or empty data
        for metric in [
            "production_total",
            "collection_rate",
            "new_patients",
            "treatment_acceptance",
            "hygiene_reappointment",
        ]:
            assert metric in chart_data
            # Should either have error or empty time series
            assert (
                "error" in chart_data[metric]
                or len(chart_data[metric]["time_series"]) == 0
            )

        # Metadata should reflect no data
        assert chart_data["metadata"]["data_sources"]["eod_available"] is False
        assert chart_data["metadata"]["data_sources"]["front_kpi_available"] is False


class TestChartDataValidation:
    """Test chart data validation functions."""

    def test_validate_valid_chart_data(self) -> None:
        """Test validation of valid chart data structure."""
        valid_data = {
            "metric_name": "Test Metric",
            "chart_type": "line",
            "data_type": "currency",
            "time_series": [{"date": "2025-09-15", "value": 100.0, "has_data": True}],
            "statistics": {},
            "format_options": {},
        }

        assert validate_chart_data(valid_data) is True

    def test_validate_missing_required_fields(self) -> None:
        """Test validation with missing required fields."""
        invalid_data = {
            "metric_name": "Test Metric",
            # Missing chart_type, data_type, time_series
        }

        assert validate_chart_data(invalid_data) is False

    def test_validate_invalid_time_series(self) -> None:
        """Test validation with invalid time series structure."""
        invalid_data = {
            "metric_name": "Test Metric",
            "chart_type": "line",
            "data_type": "currency",
            "time_series": [
                {"value": 100.0},  # Missing date field
                "invalid_point",  # Not a dictionary
            ],
        }

        assert validate_chart_data(invalid_data) is False

    def test_validate_empty_time_series(self) -> None:
        """Test validation with empty but valid time series."""
        valid_data = {
            "metric_name": "Test Metric",
            "chart_type": "line",
            "data_type": "currency",
            "time_series": [],  # Empty but valid
        }

        assert validate_chart_data(valid_data) is True


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""

    def test_malformed_currency_strings(self) -> None:
        """Test handling of malformed currency strings."""
        df = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16", "2025-09-17"],
                "total_production": ["$1,234.56", "invalid$amount", "$-789.12"],
            }
        )

        chart_data = format_production_chart_data(df)

        # Should handle valid currency, skip invalid, handle negative
        time_series = chart_data["time_series"]
        assert time_series[0]["value"] == 1234.56
        assert time_series[1]["has_data"] is False  # Invalid amount
        assert time_series[2]["value"] == -789.12  # Negative amount

    def test_large_numerical_values(self) -> None:
        """Test handling of very large numerical values."""
        df = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15"],
                "total_production": [1e12],  # 1 trillion
            }
        )

        chart_data = format_production_chart_data(df)

        assert chart_data["time_series"][0]["value"] == 1e12
        assert chart_data["time_series"][0]["has_data"] is True

    def test_mixed_data_types_in_columns(self) -> None:
        """Test handling of mixed data types within columns."""
        df = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16", "2025-09-17"],
                "new_patients": ["5", 10.0, None],  # String, float, None
            }
        )

        chart_data = format_new_patients_chart_data(df)

        time_series = chart_data["time_series"]
        assert time_series[0]["value"] == 5
        assert time_series[1]["value"] == 10
        assert time_series[2]["has_data"] is False

    def test_datetime_timezone_handling(self) -> None:
        """Test handling of datetime strings with timezone info."""
        # Current implementation doesn't handle timezones
        # This test documents the expected behavior
        df = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15 14:30:00"],  # No timezone
                "total_production": [1000.0],
            }
        )

        chart_data = format_production_chart_data(df)

        # Should work with standard format
        assert len(chart_data["time_series"]) == 1
        assert chart_data["time_series"][0]["date"] == "2025-09-15"


class TestIntegrationWithExistingFixtures:
    """Test integration with existing test fixtures."""

    def test_chart_formatting_with_sample_fixtures(
        self, sample_eod_data: pd.DataFrame, sample_front_kpi_data: pd.DataFrame
    ) -> None:
        """Test chart formatting using sample fixtures from conftest.py."""
        # This test ensures our chart formatter works with the existing
        # test data structures used throughout the test suite

        all_charts = format_all_chart_data(sample_eod_data, sample_front_kpi_data)

        # Verify each chart has valid structure
        for metric_name, chart_data in all_charts.items():
            if metric_name == "metadata":
                continue

            assert validate_chart_data(chart_data)
            assert chart_data["metric_name"] is not None
            assert isinstance(chart_data["time_series"], list)

        # Verify specific data from fixtures is processed correctly
        production_chart = all_charts["production_total"]
        assert len(production_chart["time_series"]) == 3  # Should match fixture

        # Check that the production values are present
        # (from sample_eod_data fixture)
        actual_values = [
            point["value"]
            for point in production_chart["time_series"]
            if point["has_data"]
        ]

        # Values should be present (exact values depend on processing)
        assert len(actual_values) > 0
