"""
Test location switching functionality for multi-location dental analytics.

Tests the ability to switch between Baytown and Humble locations
and retrieve location-specific KPI data.
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from apps.backend.metrics import (
    calculate_collection_rate,
    calculate_production_total,
    get_all_kpis,
    get_combined_kpis,
)


def get_simple_eod_data() -> pd.DataFrame:
    """Simple EOD test data with all required columns."""
    return pd.DataFrame(
        {
            "Total Production Today": [1000],
            "Adjustments Today": [50],
            "Write-offs Today": [25],
            "Patient Income Today": [800],
            "Unearned Income Today": [100],
            "Insurance Income Today": [150],
            "New Patients - Total Month to Date": [5],
        }
    )


def get_simple_front_kpi_data() -> pd.DataFrame:
    """Simple Front KPI test data with all required columns."""
    return pd.DataFrame(
        {
            "treatments_presented": [10],
            "treatments_scheduled": [8],
            "$ Same Day Treatment": [2],
            "Total hygiene Appointments": [20],
            "Number of patients NOT reappointed?": [3],
        }
    )


class TestLocationSwitching:
    """Test location switching functionality."""

    @patch("apps.backend.metrics.SheetsReader")
    def test_get_baytown_kpis(self, mock_sheets_reader: MagicMock) -> None:
        """Test retrieving KPIs for Baytown location."""
        # Setup mock
        mock_instance = mock_sheets_reader.return_value
        mock_instance.get_eod_data.return_value = get_simple_eod_data()
        mock_instance.get_front_kpi_data.return_value = get_simple_front_kpi_data()

        # Test
        kpis = get_all_kpis("baytown")

        # Verify
        mock_instance.get_eod_data.assert_called_once_with("baytown")
        mock_instance.get_front_kpi_data.assert_called_once_with("baytown")
        assert kpis["production_total"] == 1075.0  # 1000 + 50 + 25
        assert kpis["collection_rate"] == pytest.approx(
            97.67, rel=1e-2
        )  # 1050/1075*100

    @patch("apps.backend.metrics.SheetsReader")
    def test_get_humble_kpis(self, mock_sheets_reader: MagicMock) -> None:
        """Test retrieving KPIs for Humble location."""
        # Setup mock with different data for Humble
        humble_eod = pd.DataFrame(
            {
                "Total Production Today": [1500],
                "Adjustments Today": [75],
                "Write-offs Today": [40],
                "Patient Income Today": [1200],
                "Unearned Income Today": [150],
                "Insurance Income Today": [200],
                "New Patients - Total Month to Date": [8],
            }
        )

        mock_instance = mock_sheets_reader.return_value
        mock_instance.get_eod_data.return_value = humble_eod
        mock_instance.get_front_kpi_data.return_value = get_simple_front_kpi_data()

        # Test
        kpis = get_all_kpis("humble")

        # Verify
        mock_instance.get_eod_data.assert_called_once_with("humble")
        mock_instance.get_front_kpi_data.assert_called_once_with("humble")
        assert kpis["production_total"] == 1615.0  # 1500 + 75 + 40
        assert kpis["collection_rate"] == pytest.approx(96.0, rel=1e-2)  # 1550/1615*100

    @patch("apps.backend.metrics.SheetsReader")
    def test_get_combined_kpis(self, mock_sheets_reader: MagicMock) -> None:
        """Test retrieving KPIs for both locations."""
        # Setup mock with different data for each location
        baytown_eod = get_simple_eod_data()
        humble_eod = pd.DataFrame(
            {
                "Total Production Today": [1500],
                "Adjustments Today": [75],
                "Write-offs Today": [40],
                "Patient Income Today": [1200],
                "Unearned Income Today": [150],
                "Insurance Income Today": [200],
                "New Patients - Total Month to Date": [8],
            }
        )

        mock_instance = mock_sheets_reader.return_value

        # Mock the location-specific data returns
        def mock_get_eod_data(location: str) -> pd.DataFrame:
            return baytown_eod if location == "baytown" else humble_eod

        mock_instance.get_eod_data.side_effect = mock_get_eod_data
        mock_instance.get_front_kpi_data.return_value = get_simple_front_kpi_data()

        # Get KPIs for both locations
        combined_kpis = get_combined_kpis()

        # Verify structure
        assert "baytown" in combined_kpis
        assert "humble" in combined_kpis

        # Verify Baytown KPIs
        baytown_kpis = combined_kpis["baytown"]
        assert baytown_kpis["production_total"] == 1075.0
        assert baytown_kpis["collection_rate"] == pytest.approx(97.67, rel=1e-2)

        # Verify Humble KPIs
        humble_kpis = combined_kpis["humble"]
        assert humble_kpis["production_total"] == 1615.0
        assert humble_kpis["collection_rate"] == pytest.approx(96.0, rel=1e-2)

        # Verify calls were made for both locations
        assert mock_instance.get_eod_data.call_count == 2

    def test_calculate_production_with_location_data(self) -> None:
        """Test production calculation with location-specific column structure."""
        # Test with Story 2.1 validated column names
        baytown_data = pd.DataFrame(
            {
                "Total Production Today": [1000],
                "Adjustments Today": [50],
                "Write-offs Today": [25],
            }
        )

        production = calculate_production_total(baytown_data)
        assert production == 1075.0

        # Test with different values for another location
        humble_data = pd.DataFrame(
            {
                "Total Production Today": [1500],
                "Adjustments Today": [75],
                "Write-offs Today": [40],
            }
        )

        production = calculate_production_total(humble_data)
        assert production == 1615.0

    def test_calculate_collection_rate_with_location_data(self) -> None:
        """Test collection rate calculation with location-specific data."""
        # Test with complete Story 2.1 column structure
        location_data = pd.DataFrame(
            {
                "Total Production Today": [1000],
                "Adjustments Today": [50],
                "Write-offs Today": [25],
                "Patient Income Today": [800],
                "Unearned Income Today": [100],
                "Insurance Income Today": [150],
            }
        )

        rate = calculate_collection_rate(location_data)
        # Total production: 1000 + 50 + 25 = 1075
        # Total collections: 800 + 100 + 150 = 1050
        # Rate: 1050/1075 * 100 = 97.67%
        assert rate == pytest.approx(97.67, rel=1e-2)

    @patch("apps.backend.metrics.SheetsReader")
    def test_location_parameter_validation(self, mock_sheets_reader: MagicMock) -> None:
        """Test that location parameter is properly passed to sheets reader."""
        mock_instance = mock_sheets_reader.return_value
        mock_instance.get_eod_data.return_value = get_simple_eod_data()
        mock_instance.get_front_kpi_data.return_value = get_simple_front_kpi_data()

        # Test with specific location
        get_all_kpis("humble")

        # Verify the location was passed correctly
        mock_instance.get_eod_data.assert_called_once_with("humble")
        mock_instance.get_front_kpi_data.assert_called_once_with("humble")

    @patch("apps.backend.metrics.SheetsReader")
    def test_default_location_parameter(self, mock_sheets_reader: MagicMock) -> None:
        """Test that default location parameter works correctly."""
        mock_instance = mock_sheets_reader.return_value
        mock_instance.get_eod_data.return_value = get_simple_eod_data()
        mock_instance.get_front_kpi_data.return_value = get_simple_front_kpi_data()

        # Test without specifying location (should default to 'baytown')
        get_all_kpis()

        # Verify the default location was used
        mock_instance.get_eod_data.assert_called_once_with("baytown")
        mock_instance.get_front_kpi_data.assert_called_once_with("baytown")


@pytest.fixture
def baytown_sample_data() -> pd.DataFrame:
    """Sample data for Baytown location."""
    return pd.DataFrame(
        {
            "Total Production Today": [1000],
            "Adjustments Today": [50],
            "Write-offs Today": [25],
            "Patient Income Today": [800],
            "Unearned Income Today": [100],
            "Insurance Income Today": [150],
            "New Patients - Total Month to Date": [5],
        }
    )


@pytest.fixture
def humble_sample_data() -> pd.DataFrame:
    """Sample data for Humble location."""
    return pd.DataFrame(
        {
            "Total Production Today": [1500],
            "Adjustments Today": [75],
            "Write-offs Today": [40],
            "Patient Income Today": [1200],
            "Unearned Income Today": [150],
            "Insurance Income Today": [200],
            "New Patients - Total Month to Date": [8],
        }
    )
