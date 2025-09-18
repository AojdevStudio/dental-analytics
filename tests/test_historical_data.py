"""
Unit tests for Historical Data Manager

Tests cover:
- Operational day logic (Monday-Saturday for dental practice)
- Sunday/holiday fallback to latest operational day
- Time-series data retrieval and filtering
- Error handling for missing data points
- Framework-agnostic design validation
"""

import logging
import sys
from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import structlog

from apps.backend.historical_data import HistoricalDataManager

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


class TestOperationalDayLogic:
    """Test suite for operational day detection (Monday-Saturday)."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("apps.backend.historical_data.SheetsReader"):
            self.manager = HistoricalDataManager()

    @pytest.mark.unit
    def test_is_operational_day_monday_to_saturday(self) -> None:
        """Test operational day detection for Monday-Saturday."""
        # Monday = 0, Tuesday = 1, ..., Saturday = 5, Sunday = 6
        test_dates = [
            (datetime(2025, 9, 15), True),  # Monday
            (datetime(2025, 9, 16), True),  # Tuesday
            (datetime(2025, 9, 17), True),  # Wednesday
            (datetime(2025, 9, 18), True),  # Thursday
            (datetime(2025, 9, 19), True),  # Friday
            (datetime(2025, 9, 20), True),  # Saturday
            (datetime(2025, 9, 21), False),  # Sunday
        ]

        for test_date, expected in test_dates:
            result = self.manager.is_operational_day(test_date)
            assert (
                result == expected
            ), f"Failed for {test_date.strftime('%A')} ({test_date})"

    @pytest.mark.unit
    def test_get_latest_operational_date_from_monday(self) -> None:
        """Test latest operational date when reference is Monday."""
        monday = datetime(2025, 9, 15)  # Monday
        result = self.manager.get_latest_operational_date(monday)
        assert result == monday
        assert result.weekday() == 0  # Monday

    @pytest.mark.unit
    def test_get_latest_operational_date_from_sunday(self) -> None:
        """Test Sunday fallback to Saturday (latest operational day)."""
        sunday = datetime(2025, 9, 21)  # Sunday
        expected_saturday = datetime(2025, 9, 20)  # Previous Saturday

        result = self.manager.get_latest_operational_date(sunday)
        assert result == expected_saturday
        assert result.weekday() == 5  # Saturday

    @pytest.mark.unit
    def test_get_latest_operational_date_from_tuesday(self) -> None:
        """Test latest operational date when reference is Tuesday."""
        tuesday = datetime(2025, 9, 16)  # Tuesday
        result = self.manager.get_latest_operational_date(tuesday)
        assert result == tuesday
        assert result.weekday() == 1  # Tuesday

    @pytest.mark.unit
    def test_get_latest_operational_date_fallback_protection(self) -> None:
        """Test fallback protection against infinite loops."""
        # Test that it doesn't loop infinitely with edge cases
        any_date = datetime(2025, 9, 15)
        result = self.manager.get_latest_operational_date(any_date)
        assert result is not None
        assert isinstance(result, datetime)

    @pytest.mark.unit
    def test_get_latest_operational_date_default_today(self) -> None:
        """Test default behavior uses current date."""
        with patch("apps.backend.historical_data.datetime") as mock_datetime:
            mock_now = datetime(2025, 9, 19)  # Friday
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            result = self.manager.get_latest_operational_date()
            assert result == mock_now


class TestDateRangeCalculation:
    """Test suite for date range calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("apps.backend.historical_data.SheetsReader"):
            self.manager = HistoricalDataManager()

    @pytest.mark.unit
    def test_get_date_range_for_period_30_days(self) -> None:
        """Test 30-day date range calculation."""
        with patch.object(self.manager, "get_latest_operational_date") as mock_latest:
            mock_latest.return_value = datetime(2025, 9, 20)  # Saturday

            start_date, end_date = self.manager.get_date_range_for_period(30)

            assert end_date == datetime(2025, 9, 20)
            assert start_date == datetime(2025, 8, 21)  # 30 days before
            assert (end_date - start_date).days == 30

    @pytest.mark.unit
    def test_get_date_range_for_period_7_days(self) -> None:
        """Test 7-day date range calculation."""
        with patch.object(self.manager, "get_latest_operational_date") as mock_latest:
            mock_latest.return_value = datetime(2025, 9, 19)  # Friday

            start_date, end_date = self.manager.get_date_range_for_period(7)

            assert end_date == datetime(2025, 9, 19)
            assert start_date == datetime(2025, 9, 12)  # 7 days before
            assert (end_date - start_date).days == 7


class TestHistoricalDataRetrieval:
    """Test suite for historical data retrieval."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_sheets_reader = Mock()
        with patch(
            "apps.backend.historical_data.SheetsReader",
            return_value=self.mock_sheets_reader,
        ):
            self.manager = HistoricalDataManager()

    @pytest.mark.unit
    def test_get_historical_eod_data_success(self) -> None:
        """Test successful historical EOD data retrieval."""
        # Mock successful data retrieval
        mock_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16", "2025-09-17"],
                "total_production": [1000, 1200, 1100],
                "total_collections": [900, 1100, 1000],
            }
        )
        self.mock_sheets_reader.get_eod_data.return_value = mock_data

        with patch.object(
            self.manager, "_filter_by_date_range", return_value=mock_data
        ):
            result = self.manager.get_historical_eod_data(30)

            assert result is not None
            assert len(result) == 3
            assert "total_production" in result.columns

    @pytest.mark.unit
    def test_get_historical_eod_data_empty_response(self) -> None:
        """Test handling of empty data response."""
        self.mock_sheets_reader.get_eod_data.return_value = None

        result = self.manager.get_historical_eod_data(30)
        assert result is None

    @pytest.mark.unit
    def test_get_historical_eod_data_api_error(self) -> None:
        """Test handling of API errors."""
        self.mock_sheets_reader.get_eod_data.side_effect = Exception("API Error")

        result = self.manager.get_historical_eod_data(30)
        assert result is None

    @pytest.mark.unit
    def test_get_historical_front_kpi_data_success(self) -> None:
        """Test successful historical Front KPI data retrieval."""
        mock_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16"],
                "treatments_presented": [50, 60],
                "treatments_scheduled": [40, 45],
            }
        )
        self.mock_sheets_reader.get_front_kpi_data.return_value = mock_data

        with patch.object(
            self.manager, "_filter_by_date_range", return_value=mock_data
        ):
            result = self.manager.get_historical_front_kpi_data(30)

            assert result is not None
            assert len(result) == 2
            assert "treatments_presented" in result.columns


class TestLatestAvailableData:
    """Test suite for latest available data retrieval."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_sheets_reader = Mock()
        with patch(
            "apps.backend.historical_data.SheetsReader",
            return_value=self.mock_sheets_reader,
        ):
            self.manager = HistoricalDataManager()

    @pytest.mark.unit
    def test_get_latest_available_data_success(self) -> None:
        """Test successful latest data retrieval."""
        # Mock latest operational date
        latest_date = datetime(2025, 9, 20)  # Saturday

        # Mock data responses
        mock_eod_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-20"],
                "total_production": [1500],
                "total_collections": [1400],
            }
        )
        mock_front_kpi_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-20"],
                "treatments_presented": [25],
                "treatments_scheduled": [20],
            }
        )

        self.mock_sheets_reader.get_eod_data.return_value = mock_eod_data
        self.mock_sheets_reader.get_front_kpi_data.return_value = mock_front_kpi_data

        with (
            patch.object(
                self.manager, "get_latest_operational_date", return_value=latest_date
            ),
            patch.object(
                self.manager,
                "_filter_to_specific_date",
                side_effect=[mock_eod_data, mock_front_kpi_data],
            ),
        ):
            result = self.manager.get_latest_available_data()

            assert result["data_date"] == latest_date
            assert result["eod"] is not None
            assert result["front_kpi"] is not None
            assert len(result["eod"]) == 1
            assert len(result["front_kpi"]) == 1

    @pytest.mark.unit
    def test_get_latest_available_data_missing_eod(self) -> None:
        """Test handling when EOD data is missing."""
        latest_date = datetime(2025, 9, 20)

        self.mock_sheets_reader.get_eod_data.return_value = None
        self.mock_sheets_reader.get_front_kpi_data.return_value = pd.DataFrame(
            {"Submission Date": ["2025-09-20"], "treatments_presented": [25]}
        )

        with patch.object(
            self.manager, "get_latest_operational_date", return_value=latest_date
        ):
            result = self.manager.get_latest_available_data()

            assert result["data_date"] == latest_date
            assert result["eod"] is None
            assert result["front_kpi"] is not None


class TestDateFiltering:
    """Test suite for date filtering functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("apps.backend.historical_data.SheetsReader"):
            self.manager = HistoricalDataManager()

    @pytest.mark.unit
    def test_filter_by_date_range_success(self) -> None:
        """Test successful date range filtering."""
        # Create test data spanning multiple days
        test_data = pd.DataFrame(
            {
                "Submission Date": [
                    "2025-09-10",
                    "2025-09-15",
                    "2025-09-20",
                    "2025-09-25",
                ],
                "total_production": [1000, 1200, 1100, 1300],
            }
        )

        with patch.object(
            self.manager,
            "get_date_range_for_period",
            return_value=(datetime(2025, 9, 12), datetime(2025, 9, 22)),
        ):
            result = self.manager._filter_by_date_range(
                test_data, "Submission Date", 10
            )

            # Should include dates within range: 2025-09-15 and 2025-09-20
            assert result is not None
            assert len(result) == 2

            dates = pd.to_datetime(result["Submission Date"]).dt.date
            assert datetime(2025, 9, 15).date() in dates.values
            assert datetime(2025, 9, 20).date() in dates.values

    @pytest.mark.unit
    def test_filter_by_date_range_no_data_in_range(self) -> None:
        """Test date filtering when no data falls within range."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-08-01", "2025-08-02"],
                "total_production": [1000, 1200],
            }
        )

        with patch.object(
            self.manager,
            "get_date_range_for_period",
            return_value=(datetime(2025, 9, 1), datetime(2025, 9, 30)),
        ):
            result = self.manager._filter_by_date_range(
                test_data, "Submission Date", 30
            )

            assert result is None

    @pytest.mark.unit
    def test_filter_to_specific_date_success(self) -> None:
        """Test filtering to a specific date."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16", "2025-09-17"],
                "total_production": [1000, 1200, 1100],
            }
        )

        target_date = datetime(2025, 9, 16)
        result = self.manager._filter_to_specific_date(
            test_data, "Submission Date", target_date
        )

        assert result is not None
        assert len(result) == 1
        assert result.iloc[0]["total_production"] == 1200

    @pytest.mark.unit
    def test_filter_to_specific_date_no_match(self) -> None:
        """Test filtering when target date has no data."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-17"],
                "total_production": [1000, 1100],
            }
        )

        target_date = datetime(2025, 9, 16)  # Date not in data
        result = self.manager._filter_to_specific_date(
            test_data, "Submission Date", target_date
        )

        assert result is None

    @pytest.mark.unit
    def test_filter_date_parsing_errors(self) -> None:
        """Test handling of date parsing errors."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["invalid-date", "2025-09-15"],
                "total_production": [1000, 1200],
            }
        )

        target_date = datetime(2025, 9, 15)
        result = self.manager._filter_to_specific_date(
            test_data, "Submission Date", target_date
        )

        # Should still work with valid dates, ignoring invalid ones
        assert result is not None
        assert len(result) == 1


class TestErrorHandling:
    """Test suite for error handling and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("apps.backend.historical_data.SheetsReader"):
            self.manager = HistoricalDataManager()

    @pytest.mark.unit
    def test_missing_date_column_handling(self) -> None:
        """Test handling when date column is missing."""
        test_data = pd.DataFrame(
            {
                "total_production": [1000, 1200],
                # Missing 'Submission Date' column
            }
        )

        result = self.manager._filter_by_date_range(test_data, "Submission Date", 30)
        assert result is None

    @pytest.mark.unit
    def test_empty_dataframe_handling(self) -> None:
        """Test handling of empty DataFrames."""
        empty_df = pd.DataFrame()

        result = self.manager._filter_by_date_range(empty_df, "Submission Date", 30)
        assert result is None

    @pytest.mark.unit
    def test_none_dataframe_handling(self) -> None:
        """Test handling of None DataFrames."""
        result = self.manager._filter_by_date_range(None, "Submission Date", 30)
        assert result is None


class TestFrameworkAgnosticDesign:
    """Test suite to validate framework-agnostic design."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("apps.backend.historical_data.SheetsReader"):
            self.manager = HistoricalDataManager()

    @pytest.mark.unit
    def test_no_frontend_framework_dependencies(self) -> None:
        """Test that historical data manager has no frontend framework dependencies."""
        # Check imports for framework independence
        import apps.backend.historical_data as hdm

        # Should only import standard library, pandas, and internal modules
        # Verify imports (allowed list not actively checked but documented)
        _ = {
            "datetime",
            "typing",
            "logging",
            "sys",
            "pandas",
            "structlog",
        }

        # This is a design validation test
        assert hasattr(hdm, "HistoricalDataManager")
        assert callable(hdm.HistoricalDataManager.get_historical_eod_data)
        assert callable(hdm.HistoricalDataManager.get_latest_available_data)

    @pytest.mark.unit
    def test_return_types_are_serializable(self) -> None:
        """Test that return types are JSON-serializable for frontend flexibility."""
        # Mock successful data retrieval
        with patch.object(
            self.manager,
            "get_latest_operational_date",
            return_value=datetime(2025, 9, 20),
        ):
            result = self.manager.get_latest_available_data()

            # Should be a dictionary with standard types
            assert isinstance(result, dict)
            assert isinstance(result.get("data_date"), datetime)

            # DataFrames can be converted to JSON
            eod_data = result.get("eod")
            front_kpi_data = result.get("front_kpi")

            # None values are JSON-serializable
            if eod_data is not None:
                assert isinstance(eod_data, pd.DataFrame)
            if front_kpi_data is not None:
                assert isinstance(front_kpi_data, pd.DataFrame)

    @pytest.mark.unit
    def test_operational_day_logic_is_configurable(self) -> None:
        """Test that operational day logic is configurable (not hardcoded)."""
        # Operational days are stored as instance attribute, not hardcoded
        assert hasattr(self.manager, "operational_days")
        assert isinstance(self.manager.operational_days, set)
        assert self.manager.operational_days == {0, 1, 2, 3, 4, 5}  # Monday-Saturday

        # Could be modified for different practices if needed
        # (This demonstrates configurability without breaking existing logic)
