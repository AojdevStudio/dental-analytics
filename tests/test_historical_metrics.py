"""
Unit tests for Historical Metrics Functions

Tests cover:
- Time-series aggregation methods
- Historical KPI calculations
- Backward compatibility with existing functions
- Framework-agnostic data structures
- Error handling for missing data points
"""

import logging
import sys
from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import structlog

from apps.backend.metrics import (
    calculate_historical_collection_rate,
    calculate_historical_new_patients,
    calculate_historical_production_total,
    get_all_historical_kpis,
    safe_time_series_conversion,
)

# Configure test logging to stderr with structured output
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.dict_tracebacks,
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.PATHNAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)

log = structlog.get_logger()


class TestTimeSeriesConversion:
    """Test suite for time series data conversion."""

    @pytest.mark.unit
    def test_safe_time_series_conversion_success(self) -> None:
        """Test successful time series conversion."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16", "2025-09-17"],
                "total_production": [1000, 1200, 1100],
            }
        )

        result = safe_time_series_conversion(test_data, "total_production")

        assert len(result) == 3
        assert isinstance(result[0], tuple)
        assert isinstance(result[0][0], datetime)
        assert isinstance(result[0][1], float)

        # Check sorted by date
        dates = [date for date, _ in result]
        assert dates == sorted(dates)

        # Check values
        values = [value for _, value in result]
        assert values == [1000.0, 1200.0, 1100.0]

    @pytest.mark.unit
    def test_safe_time_series_conversion_empty_dataframe(self) -> None:
        """Test time series conversion with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = safe_time_series_conversion(empty_df, "total_production")
        assert result == []

    @pytest.mark.unit
    def test_safe_time_series_conversion_none_dataframe(self) -> None:
        """Test time series conversion with None DataFrame."""
        result = safe_time_series_conversion(None, "total_production")
        assert result == []

    @pytest.mark.unit
    def test_safe_time_series_conversion_missing_column(self) -> None:
        """Test time series conversion with missing column."""
        test_data = pd.DataFrame(
            {"Submission Date": ["2025-09-15"], "other_column": [1000]}
        )

        result = safe_time_series_conversion(test_data, "missing_column")
        assert result == []

    @pytest.mark.unit
    def test_safe_time_series_conversion_missing_date_column(self) -> None:
        """Test time series conversion with missing date column."""
        test_data = pd.DataFrame({"total_production": [1000, 1200]})

        result = safe_time_series_conversion(test_data, "total_production")
        assert result == []

    @pytest.mark.unit
    def test_safe_time_series_conversion_invalid_dates(self) -> None:
        """Test time series conversion with invalid dates."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["invalid-date", "2025-09-16", None],
                "total_production": [1000, 1200, 1100],
            }
        )

        result = safe_time_series_conversion(test_data, "total_production")

        # Should only include valid date entry
        assert len(result) == 1
        assert result[0][0] == datetime(2025, 9, 16)
        assert result[0][1] == 1200.0

    @pytest.mark.unit
    def test_safe_time_series_conversion_invalid_values(self) -> None:
        """Test time series conversion with invalid numeric values."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16", "2025-09-17"],
                "total_production": ["invalid", 1200, None],
            }
        )

        result = safe_time_series_conversion(test_data, "total_production")

        # Should only include valid numeric entry
        assert len(result) == 1
        assert result[0][0] == datetime(2025, 9, 16)
        assert result[0][1] == 1200.0


class TestHistoricalProductionTotal:
    """Test suite for historical production total calculations."""

    @pytest.mark.unit
    def test_calculate_historical_production_total_success(self) -> None:
        """Test successful historical production total calculation."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16", "2025-09-17"],
                "Total Production Today": [5000, 5200, 5100],
                "Adjustments Today": [100, 0, 50],
                "Write-offs Today": [-50, -100, -75],
            }
        )

        result = calculate_historical_production_total(test_data, 30)

        assert result["total_sum"] == 15225.0
        assert result["daily_average"] == pytest.approx(5075.0)
        assert result["latest_value"] == pytest.approx(5075.0)
        assert result["data_points"] == 3
        assert len(result["time_series"]) == 3

    @pytest.mark.unit
    def test_calculate_historical_production_total_unprefixed_columns(self) -> None:
        """Test historical production with unprefixed column names."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16"],
                "Production": [1000, 1200],  # Unprefixed column name
            }
        )

        result = calculate_historical_production_total(test_data, 30)

        assert result["total_sum"] == 2200.0
        assert result["daily_average"] == 1100.0
        assert result["data_points"] == 2

    @pytest.mark.unit
    def test_calculate_historical_production_total_empty_dataframe(self) -> None:
        """Test historical production with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = calculate_historical_production_total(empty_df, 30)

        assert result["total_sum"] == 0.0
        assert result["daily_average"] == 0.0
        assert result["latest_value"] is None
        assert result["data_points"] == 0
        assert result["time_series"] == []

    @pytest.mark.unit
    def test_calculate_historical_production_total_none_dataframe(self) -> None:
        """Test historical production with None DataFrame."""
        result = calculate_historical_production_total(None, 30)

        assert result["total_sum"] == 0.0
        assert result["daily_average"] == 0.0
        assert result["latest_value"] is None
        assert result["data_points"] == 0
        assert result["time_series"] == []

    @pytest.mark.unit
    def test_calculate_historical_production_total_missing_column(self) -> None:
        """Test historical production with missing production column."""
        test_data = pd.DataFrame(
            {"Submission Date": ["2025-09-15"], "other_column": [1000]}
        )

        result = calculate_historical_production_total(test_data, 30)

        assert result["total_sum"] == 0.0
        assert result["daily_average"] == 0.0
        assert result["latest_value"] is None
        assert result["data_points"] == 0


class TestHistoricalCollectionRate:
    """Test suite for historical collection rate calculations."""

    @pytest.mark.unit
    def test_calculate_historical_collection_rate_success(self) -> None:
        """Test successful historical collection rate calculation."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16", "2025-09-17"],
                "Total Production Today": [5000, 5000, 5000],
                "Patient Income Today": [2000, 2100, 2300],
                "Unearned Income Today": [1500, 1600, 1700],
                "Insurance Income Today": [1000, 900, 750],
            }
        )

        result = calculate_historical_collection_rate(test_data, 30)

        assert result["data_points"] == 3
        assert len(result["time_series"]) == 3

        # Check individual rates (90%, 90%, 95%)
        rates = [rate for _, rate in result["time_series"]]
        assert abs(rates[0] - 90.0) < 0.01
        assert abs(rates[1] - 92.0) < 0.01
        assert abs(rates[2] - 95.0) < 0.01

        # Check average rate
        expected_average = (90.0 + 92.0 + 95.0) / 3
        assert abs(result["average_rate"] - expected_average) < 0.01

        # Check latest value
        assert abs(result["latest_value"] - 95.0) < 0.01

    @pytest.mark.unit
    def test_calculate_historical_collection_rate_unprefixed_columns(self) -> None:
        """Test historical collection rate with unprefixed column names."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15"],
                "Production": [1000],
                "Collections": [900],
            }
        )

        result = calculate_historical_collection_rate(test_data, 30)

        assert result["data_points"] == 1
        assert abs(result["latest_value"] - 90.0) < 0.01

    @pytest.mark.unit
    def test_calculate_historical_collection_rate_zero_production(self) -> None:
        """Test historical collection rate with zero production days."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16", "2025-09-17"],
                "Total Production Today": [4000, 0, 4200],
                "Patient Income Today": [2000, 300, 2200],
                "Unearned Income Today": [1000, 200, 1100],
                "Insurance Income Today": [400, 0, 500],
            }
        )

        result = calculate_historical_collection_rate(test_data, 30)

        # Should handle zero production by excluding that day from rates
        assert result["data_points"] == 2  # Only 2 valid calculation days
        rates = [rate for _, rate in result["time_series"]]
        assert len(rates) == 2

    @pytest.mark.unit
    def test_calculate_historical_collection_rate_missing_columns(self) -> None:
        """Test historical collection rate with missing required columns."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15"],
                "Total Production Today": [5000],
                # Missing income component columns
            }
        )

        result = calculate_historical_collection_rate(test_data, 30)

        assert result["data_points"] == 0
        assert result["average_rate"] == 0.0
        assert result["latest_value"] is None

    @pytest.mark.unit
    def test_calculate_historical_collection_rate_missing_date_column(self) -> None:
        """Test historical collection rate with missing date column."""
        test_data = pd.DataFrame(
            {
                "Total Production Today": [5000],
                "Patient Income Today": [2000],
                "Unearned Income Today": [1500],
                "Insurance Income Today": [900],
                # Missing Submission Date column
            }
        )

        result = calculate_historical_collection_rate(test_data, 30)

        assert result["data_points"] == 0
        assert result["average_rate"] == 0.0


class TestHistoricalNewPatients:
    """Test suite for historical new patients calculations."""

    @pytest.mark.unit
    def test_calculate_historical_new_patients_success(self) -> None:
        """Test successful historical new patients calculation."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16", "2025-09-17"],
                "New Patients - Total Month to Date": [8, 10, 15],
            }
        )

        result = calculate_historical_new_patients(test_data, 30)

        assert result["total_count"] == 15
        assert result["daily_average"] == pytest.approx(5.0)
        assert result["latest_value"] == 5
        assert result["data_points"] == 3
        assert len(result["time_series"]) == 3

    @pytest.mark.unit
    def test_calculate_historical_new_patients_zero_values(self) -> None:
        """Test historical new patients with zero values."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16"],
                "New Patients - Total Month to Date": [5, 5],
            }
        )

        result = calculate_historical_new_patients(test_data, 30)

        assert result["total_count"] == 5
        assert result["daily_average"] == pytest.approx(2.5)
        assert result["latest_value"] == 0

    @pytest.mark.unit
    def test_calculate_historical_new_patients_missing_column(self) -> None:
        """Test historical new patients with missing column."""
        test_data = pd.DataFrame(
            {"Submission Date": ["2025-09-15"], "other_column": [3]}
        )

        result = calculate_historical_new_patients(test_data, 30)

        assert result["total_count"] == 0
        assert result["daily_average"] == 0.0
        assert result["latest_value"] is None
        assert result["data_points"] == 0


class TestGetAllHistoricalKPIs:
    """Test suite for complete historical KPI retrieval."""

    @pytest.mark.unit
    def test_get_all_historical_kpis_success(self) -> None:
        """Test successful retrieval of all historical KPIs."""
        # Mock historical data
        mock_eod_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16"],
                "Total Production Today": [5000, 5200],
                "Adjustments Today": [0, 0],
                "Write-offs Today": [0, 0],
                "Patient Income Today": [4500, 4800],
                "Unearned Income Today": [0, 0],
                "Insurance Income Today": [0, 0],
                "New Patients - Total Month to Date": [10, 12],
            }
        )

        mock_front_kpi_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16"],
                "treatments_presented": [50, 60],
                "treatments_scheduled": [40, 45],
                "Total hygiene Appointments": [30, 32],
                "Number of patients NOT reappointed?": [2, 3],
            }
        )

        mock_latest_data = {
            "eod": mock_eod_data.iloc[-1:],  # Latest day
            "front_kpi": mock_front_kpi_data.iloc[-1:],
            "data_date": datetime(2025, 9, 16),
        }

        with patch(
            "apps.backend.historical_data.HistoricalDataManager"
        ) as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            mock_manager.get_historical_eod_data.return_value = mock_eod_data
            mock_manager.get_historical_front_kpi_data.return_value = (
                mock_front_kpi_data
            )
            mock_manager.get_latest_available_data.return_value = mock_latest_data

            result = get_all_historical_kpis(30)

            # Check structure
            assert "historical" in result
            assert "current" in result
            assert "data_date" in result
            assert "period_days" in result

            # Check historical data
            historical = result["historical"]
            assert "production_total" in historical
            assert "collection_rate" in historical
            assert "new_patients" in historical

            # Check current data
            current = result["current"]
            assert "production_total" in current
            assert "collection_rate" in current
            assert "new_patients" in current
            assert "case_acceptance" in current
            assert "hygiene_reappointment" in current

            # Check metadata
            assert result["data_date"] == datetime(2025, 9, 16)
            assert result["period_days"] == 30

    @pytest.mark.unit
    def test_get_all_historical_kpis_error_handling(self) -> None:
        """Test error handling in historical KPI retrieval."""
        with patch(
            "apps.backend.historical_data.HistoricalDataManager"
        ) as mock_manager_class:
            mock_manager_class.side_effect = Exception("Manager initialization failed")

            result = get_all_historical_kpis(30)

            # Should return default structure with None values
            assert result["historical"] == {}
            assert all(v is None for v in result["current"].values())
            assert result["data_date"] is None
            assert result["period_days"] == 30

    @pytest.mark.unit
    def test_get_all_historical_kpis_partial_data_failure(self) -> None:
        """Test handling when some data sources fail."""
        with patch(
            "apps.backend.historical_data.HistoricalDataManager"
        ) as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            # Mock partial failure - EOD data fails, Front KPI succeeds
            mock_manager.get_historical_eod_data.return_value = None
            mock_manager.get_historical_front_kpi_data.return_value = pd.DataFrame(
                {
                    "Submission Date": ["2025-09-16"],
                    "treatments_presented": [60],
                    "treatments_scheduled": [48],
                    "$ Same Day Treatment": [0],
                    "Total hygiene Appointments": [10],
                    "Number of patients NOT reappointed?": [1],
                }
            )
            mock_manager.get_latest_available_data.return_value = {
                "eod": None,
                "front_kpi": pd.DataFrame(
                    {
                        "treatments_presented": [60],
                        "treatments_scheduled": [48],
                        "$ Same Day Treatment": [0],
                        "Total hygiene Appointments": [10],
                        "Number of patients NOT reappointed?": [1],
                    }
                ),
                "data_date": datetime(2025, 9, 16),
            }

            result = get_all_historical_kpis(30)

            # Should handle gracefully with None values for failed data
            assert result["current"]["production_total"] is None  # EOD data failed
            assert (
                result["current"]["case_acceptance"] is not None
            )  # Front KPI succeeded


class TestBackwardCompatibility:
    """Test suite to ensure backward compatibility with existing functions."""

    @pytest.mark.unit
    def test_existing_functions_still_work(self) -> None:
        """Test that existing single-day functions are not broken."""
        # Import existing functions to ensure they still work
        from apps.backend.metrics import (
            calculate_collection_rate,
            calculate_new_patients,
            calculate_production_total,
            get_all_kpis,
        )

        # These imports should work without errors
        assert callable(calculate_production_total)
        assert callable(calculate_collection_rate)
        assert callable(calculate_new_patients)
        assert callable(get_all_kpis)

    @pytest.mark.unit
    def test_historical_functions_are_new_additions(self) -> None:
        """Test that historical functions are properly added."""
        # Import new historical functions
        from apps.backend.metrics import (
            calculate_historical_collection_rate,
            calculate_historical_new_patients,
            calculate_historical_production_total,
            get_all_historical_kpis,
            safe_time_series_conversion,
        )

        # All new functions should be callable
        assert callable(calculate_historical_production_total)
        assert callable(calculate_historical_collection_rate)
        assert callable(calculate_historical_new_patients)
        assert callable(get_all_historical_kpis)
        assert callable(safe_time_series_conversion)

    @pytest.mark.unit
    def test_historical_vs_current_function_signatures(self) -> None:
        """Test historical functions have different signatures from current ones."""
        # Historical functions should have additional parameters
        import inspect

        from apps.backend.metrics import (
            calculate_historical_production_total,
            calculate_production_total,
        )

        # Current functions take (df) parameter
        current_sig = inspect.signature(calculate_production_total)
        assert len(current_sig.parameters) == 1

        # Historical functions take (df, days) parameters
        historical_sig = inspect.signature(calculate_historical_production_total)
        assert len(historical_sig.parameters) == 2
        assert "days" in historical_sig.parameters


class TestDataStructureCompatibility:
    """Test suite for framework-agnostic data structures."""

    @pytest.mark.unit
    def test_historical_data_structure_is_serializable(self) -> None:
        """Test that historical data structures are JSON-serializable."""
        test_data = pd.DataFrame(
            {"Submission Date": ["2025-09-15"], "total_production": [1000]}
        )

        result = calculate_historical_production_total(test_data, 30)

        # Check that all values are JSON-serializable types
        import json

        # Convert datetime objects for JSON serialization test
        serializable_result = {
            "total_sum": result["total_sum"],
            "daily_average": result["daily_average"],
            "latest_value": result["latest_value"],
            "data_points": result["data_points"],
            "time_series": [(ts[0].isoformat(), ts[1]) for ts in result["time_series"]],
        }

        # Should not raise an exception
        json_str = json.dumps(serializable_result)
        assert isinstance(json_str, str)

    @pytest.mark.unit
    def test_time_series_format_is_frontend_friendly(self) -> None:
        """Test that time series format is suitable for frontend charting libraries."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16"],
                "total_production": [1000, 1200],
            }
        )

        time_series = safe_time_series_conversion(test_data, "total_production")

        # Should be list of (datetime, value) tuples
        assert isinstance(time_series, list)
        for item in time_series:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], datetime)  # Date
            assert isinstance(item[1], int | float)  # Numeric value

        # Should be sorted by date (suitable for charting)
        dates = [item[0] for item in time_series]
        assert dates == sorted(dates)
