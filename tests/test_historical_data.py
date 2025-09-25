# Unit tests for historical data functionality

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from apps.backend.historical_data import HistoricalDataManager


class TestHistoricalDataManager:
    """Test suite for HistoricalDataManager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_provider = Mock()
        self.manager = HistoricalDataManager(self.mock_provider)

    @pytest.mark.unit
    def test_initialization(self) -> None:
        """Test HistoricalDataManager initialization."""
        provider = Mock()
        manager = HistoricalDataManager(provider)
        assert manager.data_provider == provider

    @pytest.mark.unit
    def test_get_operational_date_weekday(self) -> None:
        """Test operational date calculation for weekdays."""
        # Test Monday through Saturday (operational days)
        for weekday in range(6):  # 0 = Monday, 5 = Saturday
            test_date = datetime(2025, 9, 15 + weekday)  # Starts from Monday
            result = self.manager._get_operational_date(test_date)
            assert result == test_date
            assert result.weekday() == weekday

    @pytest.mark.unit
    def test_get_operational_date_sunday(self) -> None:
        """Test Sunday falls back to Saturday."""
        sunday = datetime(2025, 9, 21)  # Sunday
        expected_saturday = datetime(2025, 9, 20)  # Previous Saturday

        result = self.manager._get_operational_date(sunday)
        assert result == expected_saturday
        assert result.weekday() == 5  # Saturday

    @pytest.mark.unit
    def test_get_operational_date_edge_cases(self) -> None:
        """Test edge cases for operational date calculation."""
        # Test first Sunday of month
        first_sunday = datetime(2025, 9, 7)  # First Sunday of September
        expected_saturday = datetime(2025, 9, 6)  # Previous Saturday

        result = self.manager._get_operational_date(first_sunday)
        assert result == expected_saturday

        # Test year boundary
        new_years_sunday = datetime(2026, 1, 4)  # Sunday
        expected_saturday = datetime(2026, 1, 3)  # Previous Saturday

        result = self.manager._get_operational_date(new_years_sunday)
        assert result == expected_saturday

    @pytest.mark.unit
    def test_get_latest_operational_date(self) -> None:
        """Test getting the latest operational date."""
        # Test with different current days
        test_cases = [
            (datetime(2025, 9, 15), datetime(2025, 9, 15)),  # Monday -> Monday
            (datetime(2025, 9, 16), datetime(2025, 9, 16)),  # Tuesday -> Tuesday
            (datetime(2025, 9, 17), datetime(2025, 9, 17)),  # Wednesday -> Wednesday
            (datetime(2025, 9, 18), datetime(2025, 9, 18)),  # Thursday -> Thursday
            (datetime(2025, 9, 19), datetime(2025, 9, 19)),  # Friday -> Friday
            (datetime(2025, 9, 20), datetime(2025, 9, 20)),  # Saturday -> Saturday
            (
                datetime(2025, 9, 21),
                datetime(2025, 9, 20),
            ),  # Sunday -> Previous Saturday
        ]

        for today, expected_date in test_cases:
            with patch("apps.backend.historical_data.datetime") as mock_datetime:
                mock_datetime.now.return_value = today
                result = self.manager.get_latest_operational_date()
            expected_date = today - timedelta(days=1)
            assert result.date() == expected_date.date()

    @pytest.mark.unit
    def test_get_latest_operational_date_from_monday(self) -> None:
        """Test latest operational date when reference is Monday."""
        monday = datetime(2025, 9, 15)  # Monday
        # Mock the current time to be Monday
        with patch("apps.backend.historical_data.datetime") as mock_datetime:
            mock_datetime.now.return_value = monday
            result = self.manager.get_latest_operational_date()
        assert result == monday
        assert result.weekday() == 0  # Monday

    @pytest.mark.unit
    def test_get_latest_operational_date_from_sunday(self) -> None:
        """Test Sunday fallback to Saturday (latest operational day)."""
        sunday = datetime(2025, 9, 21)  # Sunday
        expected_saturday = datetime(2025, 9, 20)  # Previous Saturday

        # Mock the current time to be Sunday
        with patch("apps.backend.historical_data.datetime") as mock_datetime:
            mock_datetime.now.return_value = sunday
            result = self.manager.get_latest_operational_date()
        assert result == expected_saturday
        assert result.weekday() == 5  # Saturday

    @pytest.mark.unit
    def test_get_latest_operational_date_from_tuesday(self) -> None:
        """Test latest operational date when reference is Tuesday."""
        tuesday = datetime(2025, 9, 16)  # Tuesday
        # Mock the current time to be Tuesday
        with patch("apps.backend.historical_data.datetime") as mock_datetime:
            mock_datetime.now.return_value = tuesday
            result = self.manager.get_latest_operational_date()
        assert result == tuesday
        assert result.weekday() == 1  # Tuesday

    @pytest.mark.unit
    def test_get_latest_operational_date_fallback_protection(self) -> None:
        """Test fallback protection against infinite loops."""
        # Test that it doesn't loop infinitely with edge cases
        any_date = datetime(2025, 9, 15)
        # Mock the current time
        with patch("apps.backend.historical_data.datetime") as mock_datetime:
            mock_datetime.now.return_value = any_date
            result = self.manager.get_latest_operational_date()
        assert result is not None
        assert isinstance(result, datetime)

    @pytest.mark.unit
    def test_get_latest_operational_date_default_today(self) -> None:
        """Test default behavior uses current date."""
        with patch("apps.backend.historical_data.datetime") as mock_datetime:
            mock_now = datetime(2025, 9, 15)  # Monday
            mock_datetime.now.return_value = mock_now
            result = self.manager.get_latest_operational_date()
        # Should return the same date for weekdays
        assert result == mock_now

    @pytest.mark.unit
    def test_parse_date_string_formats(self) -> None:
        """Test parsing various date string formats."""
        test_cases = [
            ("2025-09-15", datetime(2025, 9, 15)),
            ("9/15/2025", datetime(2025, 9, 15)),
            ("15-09-2025", datetime(2025, 9, 15)),
            ("2025/09/15", datetime(2025, 9, 15)),
        ]

        for date_string, expected in test_cases:
            result = self.manager._parse_date_string(date_string)
            assert result == expected, f"Failed for {date_string}"

    @pytest.mark.unit
    def test_parse_date_string_invalid(self) -> None:
        """Test parsing invalid date strings."""
        invalid_dates = [
            "invalid-date",
            "2025-13-01",  # Invalid month
            "2025-02-30",  # Invalid day
            "",
            None,
        ]

        for invalid_date in invalid_dates:
            result = self.manager._parse_date_string(invalid_date)
            assert result is None, f"Should return None for {invalid_date}"

    @pytest.mark.unit
    def test_convert_to_datetime_column_success(self) -> None:
        """Test converting date column to datetime."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-16", "2025-09-17"],
                "value": [100, 200, 300],
            }
        )

        result = self.manager._convert_to_datetime_column(test_data, "Submission Date")

        assert result is not None
        assert pd.api.types.is_datetime64_any_dtype(result["Submission Date"])
        assert len(result) == 3

    @pytest.mark.unit
    def test_convert_to_datetime_column_mixed_formats(self) -> None:
        """Test converting mixed date formats."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "9/16/2025", "2025/09/17"],
                "value": [100, 200, 300],
            }
        )

        result = self.manager._convert_to_datetime_column(test_data, "Submission Date")

        assert result is not None
        assert pd.api.types.is_datetime64_any_dtype(result["Submission Date"])
        assert len(result) == 3

    @pytest.mark.unit
    def test_convert_to_datetime_column_invalid_dates(self) -> None:
        """Test handling invalid dates in conversion."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "invalid-date", "2025-09-17"],
                "value": [100, 200, 300],
            }
        )

        result = self.manager._convert_to_datetime_column(test_data, "Submission Date")

        # Should return only valid rows
        assert result is not None
        assert len(result) == 2  # Only 2 valid dates
        assert pd.api.types.is_datetime64_any_dtype(result["Submission Date"])

    @pytest.mark.unit
    def test_convert_to_datetime_column_empty_data(self) -> None:
        """Test converting empty dataframe."""
        empty_data = pd.DataFrame()
        result = self.manager._convert_to_datetime_column(empty_data, "Submission Date")
        assert result is None

    @pytest.mark.unit
    def test_convert_to_datetime_column_missing_column(self) -> None:
        """Test converting with missing date column."""
        test_data = pd.DataFrame({"value": [100, 200, 300]})

        result = self.manager._convert_to_datetime_column(test_data, "Missing Column")
        assert result is None

    @pytest.mark.unit
    def test_filter_by_date_range_success(self) -> None:
        """Test filtering data by date range."""
        test_data = pd.DataFrame(
            {
                "Submission Date": [
                    "2025-09-10",  # Too old (>10 days)
                    "2025-09-20",  # Within range
                    "2025-09-25",  # Within range
                    "2025-09-30",  # Future date
                ],
                "total_production": [1000, 1200, 1100, 1300],
            }
        )

        # Mock current date to 2025-09-25 for consistent testing
        with patch("apps.backend.historical_data.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 9, 25)
            result = self.manager._filter_by_date_range(
                test_data, "Submission Date", 10
            )

        # Should include dates within last 10 days from 2025-09-25
        assert result is not None
        assert len(result) >= 2  # At least the recent entries

    @pytest.mark.unit
    def test_filter_by_date_range_success_specific_data(self) -> None:
        """Test filtering with specific data ranges."""
        test_data = pd.DataFrame(
            {
                "Submission Date": [
                    "2025-09-10",  # Too old (>10 days from 2025-09-25)
                    "2025-09-20",  # Within range
                    "2025-09-25",  # Within range
                    "2025-09-30",  # Future date
                ],
                "total_production": [1000, 1200, 1100, 1300],
            }
        )

        # Use _filter_by_date_range directly with days parameter
        result = self.manager._filter_by_date_range(test_data, "Submission Date", 10)

        # Should include dates within last 10 days: 2025-09-20 and 2025-09-25
        assert result is not None
        assert len(result) == 2

        dates = pd.to_datetime(result["Submission Date"]).dt.date
        assert datetime(2025, 9, 20).date() in dates.values
        assert datetime(2025, 9, 25).date() in dates.values

    @pytest.mark.unit
    def test_filter_by_date_range_no_data_in_range(self) -> None:
        """Test filtering when no data falls within range."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-08-01", "2025-08-02"],
                "total_production": [1000, 1200],
            }
        )

        # Test with date range that doesn't match the data (August vs September)
        result = self.manager._filter_by_date_range(test_data, "Submission Date", 30)

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
        assert (
            pd.to_datetime(result["Submission Date"].iloc[0]).date()
            == target_date.date()
        )

    @pytest.mark.unit
    def test_filter_to_specific_date_no_match(self) -> None:
        """Test filtering to a date that doesn't exist."""
        test_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-15", "2025-09-17"],
                "total_production": [1000, 1100],
            }
        )

        target_date = datetime(2025, 9, 16)  # Missing date
        result = self.manager._filter_to_specific_date(
            test_data, "Submission Date", target_date
        )

        assert result is None

    @pytest.mark.unit
    def test_calculate_aggregations(self) -> None:
        """Test calculating various aggregations."""
        test_data = pd.DataFrame(
            {
                "total_production": [1000, 1200, 1100, 1300],
                "total_collections": [900, 1100, 1000, 1200],
                "new_patients": [5, 3, 4, 6],
            }
        )

        aggregations = self.manager._calculate_aggregations(test_data)

        assert aggregations["total_sum"] == 4600  # Sum of production
        assert aggregations["daily_average"] == 1150.0  # Average production
        assert aggregations["latest_value"] == 1300  # Last production value
        assert aggregations["data_points"] == 4  # Number of records

    @pytest.mark.unit
    def test_calculate_aggregations_empty_data(self) -> None:
        """Test aggregations with empty data."""
        empty_data = pd.DataFrame()

        aggregations = self.manager._calculate_aggregations(empty_data)

        assert aggregations["total_sum"] is None
        assert aggregations["daily_average"] is None
        assert aggregations["latest_value"] is None
        assert aggregations["data_points"] == 0

    @pytest.mark.unit
    def test_get_historical_data_success(self) -> None:
        """Test successful historical data retrieval."""
        # Mock provider to return test data
        mock_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-20", "2025-09-21", "2025-09-22"],
                "total_production": [1000, 1200, 1100],
            }
        )
        self.mock_provider.fetch.return_value = mock_data

        # Mock current date for consistent testing
        with patch("apps.backend.historical_data.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 9, 25)
            result = self.manager.get_historical_data(
                "test_alias", "Submission Date", 5
            )

        assert result is not None
        assert "total_sum" in result
        assert "daily_average" in result
        assert "latest_value" in result
        assert "data_points" in result
        assert result["data_points"] == 3

    @pytest.mark.unit
    def test_get_historical_data_provider_error(self) -> None:
        """Test handling provider errors."""
        # Mock provider to raise an exception
        self.mock_provider.fetch.side_effect = Exception("Provider error")

        result = self.manager.get_historical_data("test_alias", "Submission Date", 5)

        assert result is None

    @pytest.mark.unit
    def test_get_historical_data_no_data_in_range(self) -> None:
        """Test when no data falls within the requested range."""
        # Mock provider to return data outside the range
        mock_data = pd.DataFrame(
            {
                "Submission Date": ["2025-08-01", "2025-08-02"],
                "total_production": [1000, 1200],
            }
        )
        self.mock_provider.fetch.return_value = mock_data

        result = self.manager.get_historical_data("test_alias", "Submission Date", 5)

        assert result is None

    @pytest.mark.unit
    def test_get_latest_data_success(self) -> None:
        """Test successful latest data retrieval."""
        # Mock provider to return test data
        mock_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-20", "2025-09-21", "2025-09-22"],
                "total_production": [1000, 1200, 1100],
            }
        )
        self.mock_provider.fetch.return_value = mock_data

        # Mock current date
        with patch("apps.backend.historical_data.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 9, 22)
            result = self.manager.get_latest_data("test_alias", "Submission Date")

        assert result is not None
        assert len(result) == 1
        assert result["total_production"].iloc[0] == 1100  # Latest value

    @pytest.mark.unit
    def test_get_latest_data_no_recent_data(self) -> None:
        """Test when no recent data is available."""
        # Mock provider to return old data
        mock_data = pd.DataFrame(
            {
                "Submission Date": ["2025-08-01"],
                "total_production": [1000],
            }
        )
        self.mock_provider.fetch.return_value = mock_data

        result = self.manager.get_latest_data("test_alias", "Submission Date")

        assert result is None

    @pytest.mark.unit
    def test_data_provider_integration(self) -> None:
        """Test integration with data provider."""
        # Test that the manager correctly uses the provided data provider
        test_alias = "test_sheets_alias"

        # Mock the provider
        mock_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-25"],
                "total_production": [1500],
            }
        )
        self.mock_provider.fetch.return_value = mock_data

        # Call get_latest_data which should use the provider
        result = self.manager.get_latest_data(test_alias, "Submission Date")

        # Verify the provider was called with correct alias
        self.mock_provider.fetch.assert_called_once_with(test_alias)
        assert result is not None

    @pytest.mark.unit
    def test_edge_case_single_data_point(self) -> None:
        """Test handling single data point."""
        mock_data = pd.DataFrame(
            {
                "Submission Date": ["2025-09-25"],
                "total_production": [1500],
            }
        )
        self.mock_provider.fetch.return_value = mock_data

        with patch("apps.backend.historical_data.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 9, 25)
            result = self.manager.get_historical_data(
                "test_alias", "Submission Date", 5
            )

        assert result is not None
        assert result["total_sum"] == 1500
        assert result["daily_average"] == 1500.0
        assert result["latest_value"] == 1500
        assert result["data_points"] == 1
