# Shared pytest fixtures for all tests

from typing import Any

import pandas as pd
import pytest


@pytest.fixture
def sample_eod_data() -> pd.DataFrame:
    """Sample EOD billing sheet data based on real production data from August 2025."""
    # Real column names from spreadsheet verified via G-Drive MCP
    return pd.DataFrame(
        {
            "Date": ["2025-08-16", "2025-08-15", "2025-08-14"],
            "Submission Date": [
                "2025-08-16 15:58:28",
                "2025-08-15 15:47:32",
                "2025-08-14 17:44:28",
            ],
            "total_production": [3669.00, 7772.00, 13000.00],  # Column I simplified
            "total_collections": [831.60, 51721.25, 3428.61],  # Column L + N combined
            "new_patients": [3, 5, 2],  # Simulated from Column S
            "Adjustments Today": ["$0.00", "-$1,572.00", "-$1,059.00"],  # Column J
            "Write-offs Today": ["$0.00", "-$17,237.82", "-$1,396.00"],  # Column K
            "Patient Income Today": ["$831.60", "$44,482.52", "$3,428.61"],  # Column L
            "Unearned Income Today": ["$0.00", "$0.00", "$0.00"],  # Column M
            "Insurance Income Today": ["$0.00", "$7,238.73", "$0.00"],  # Column N
            "Month to Date Production": [
                "$69,770.53",
                "$62,533.53",
                "$79,397.35",
            ],  # Column O
            "Month to Date Collection": [
                "$83,154.11",
                "$82,297.51",
                "$70,610.26",
            ],  # Column P
            "Cases Presented (Dollar Amount)": [
                "$45,758.00",
                "$27,868.00",
                "$28,930.00",
            ],  # Column Q
            "Cases Accepted (Percentage)": ["22.33", "64.46", "58.88"],  # Column R
            "New Patients - Total Month to Date": ["52", "48", "45"],  # Column S
        }
    )


@pytest.fixture
def sample_front_kpi_data() -> pd.DataFrame:
    """Sample Front KPI sheet data based on real production data from September 2025."""
    # Real column names from spreadsheet verified via G-Drive MCP
    return pd.DataFrame(
        {
            "Date": ["2025-09-04", "2025-09-03", "2025-09-02"],
            "Submission Date": [
                "2025-09-04 17:27:38",
                "2025-09-03 15:20:10",
                "2025-09-02 17:21:32",
            ],
            "Name": ["Patience", "Patience", "Patience"],
            "total_hygiene_appointments": [7, 4, 6],  # Column C simplified
            "patients_not_reappointed": [0, 0, 0],  # Column D simplified
            "treatments_presented": [52085, 35822, 40141],  # Column L simplified
            "treatments_scheduled": [2715, 3019, 26739],  # Column M simplified
            "Total hygiene Appointments": ["7", "4", "6"],  # Column C original
            "Number of patients NOT reappointed?": ["0", "0", "0"],  # Column D original
            "Total Dollar amount Presented for the day": [
                "52085",
                "35822",
                "40141",
            ],  # Column L original
            "$ Total Dollar amount Scheduled": [
                "2715",
                "3019",
                "26739",
            ],  # Column M original
            "$ Same Day Treatment": ["1907", "0", "2606"],  # Column N original
        }
    )


@pytest.fixture
def empty_dataframe() -> pd.DataFrame:
    """Empty DataFrame for edge case testing."""
    return pd.DataFrame()


@pytest.fixture
def mock_sheets_service(mocker: Any) -> Any:
    """Mock Google Sheets API service."""
    mock_service = mocker.Mock()
    mock_values = mocker.Mock()
    mock_spreadsheets = mocker.Mock()

    # Set up the chain of mock returns
    mock_service.spreadsheets.return_value = mock_spreadsheets
    mock_spreadsheets.values.return_value = mock_values

    # Default successful response
    mock_values.get.return_value.execute.return_value = {
        "values": [["header1", "header2", "header3"], ["value1", "value2", "value3"]]
    }

    return mock_service


@pytest.fixture
def zero_values_data() -> pd.DataFrame:
    """Test data with zero values."""
    return pd.DataFrame(
        {
            "total_production": [0, 0, 0],
            "total_collections": [0, 0, 0],
            "new_patients": [0, 0, 0],
            "treatments_presented": [0, 0, 0],
            "treatments_scheduled": [0, 0, 0],
            "total_hygiene_appointments": [0, 0, 0],
            "patients_not_reappointed": [0, 0, 0],
        }
    )


@pytest.fixture
def negative_values_data() -> pd.DataFrame:
    """Test data with negative values."""
    return pd.DataFrame(
        {
            "total_production": [-100, 200, -50],
            "total_collections": [100, -200, 50],
            "new_patients": [-1, 2, -3],
            "treatments_presented": [-1000, 2000, -500],
            "treatments_scheduled": [500, -1000, 250],
        }
    )


@pytest.fixture
def mixed_types_data() -> pd.DataFrame:
    """Test data with mixed data types."""
    return pd.DataFrame(
        {
            "total_production": ["1000", 2000, "3000.50"],
            "total_collections": [900, "1800", "2700.25"],
            "new_patients": ["3", 4, "5"],
            "treatments_presented": ["$10,000", 20000, "30000.00"],
            "treatments_scheduled": ["$5,000", "10000", 15000.50],
        }
    )


@pytest.fixture
def nulls_data() -> pd.DataFrame:
    """Test data with null values."""
    import numpy as np

    return pd.DataFrame(
        {
            "total_production": [1000, None, 3000, np.nan],
            "total_collections": [None, 1800, np.nan, 2500],
            "new_patients": [3, np.nan, None, 2],
            "treatments_presented": [1000, np.nan, 3000, None],
            "treatments_scheduled": [None, 1000, 2000, np.nan],
            "total_hygiene_appointments": [10, None, np.nan, 5],
            "patients_not_reappointed": [np.nan, 2, None, 1],
        }
    )


@pytest.fixture
def large_values_data() -> pd.DataFrame:
    """Test data with very large values."""
    return pd.DataFrame(
        {
            "total_production": [1e10, 1e11, 1e12],
            "total_collections": [9e9, 9e10, 9e11],
            "new_patients": [1000000, 2000000, 3000000],
            "treatments_presented": [1e15, 2e15, 3e15],
            "treatments_scheduled": [5e14, 1e15, 1.5e15],
        }
    )
