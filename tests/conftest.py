# Shared pytest fixtures for all tests

from typing import Any

import pandas as pd
import pytest


@pytest.fixture
def sample_eod_data() -> pd.DataFrame:
    """Sample EOD billing sheet data based on real production data from August 2025."""
    # Real column names from spreadsheet verified via G-Drive MCP
    df = pd.DataFrame(
        {
            "Date": ["2025-08-16", "2025-08-15", "2025-08-14"],
            "Submission Date": [
                "2025-08-16 15:58:28",
                "2025-08-15 15:47:32",
                "2025-08-14 17:44:28",
            ],
            "Total Production Today": [3669.00, 7772.00, 13000.00],
            "Adjustments Today": [0.0, -1572.00, -1059.00],
            "Write-offs Today": [0.0, -17237.82, -1396.00],
            "Patient Income Today": [831.60, 44482.52, 3428.61],
            "Unearned Income Today": [0.0, 0.0, 0.0],
            "Insurance Income Today": [0.0, 7238.73, 0.0],
            "New Patients - Total Month to Date": [52, 48, 45],
        }
    )

    # Backward compatibility columns for legacy tests
    df["total_production"] = df["Total Production Today"]
    df["total_collections"] = (
        df["Patient Income Today"]
        + df["Unearned Income Today"]
        + df["Insurance Income Today"]
    )
    df["new_patients"] = [3, 5, 2]

    return df


@pytest.fixture
def sample_front_kpi_data() -> pd.DataFrame:
    """Sample Front KPI sheet data based on real production data from September 2025."""
    # Real column names from spreadsheet verified via G-Drive MCP
    df = pd.DataFrame(
        {
            "Date": ["2025-09-04", "2025-09-03", "2025-09-02"],
            "Submission Date": [
                "2025-09-04 17:27:38",
                "2025-09-03 15:20:10",
                "2025-09-02 17:21:32",
            ],
            "treatments_presented": [52085, 35822, 40141],
            "treatments_scheduled": [2715, 3019, 26739],
            "Total hygiene Appointments": [7, 4, 6],
            "Number of patients NOT reappointed?": [0, 0, 0],
            "$ Same Day Treatment": [1907, 0, 2606],
        }
    )

    # Backward compatibility columns for legacy tests
    df["total_hygiene_appointments"] = df["Total hygiene Appointments"]
    df["patients_not_reappointed"] = df["Number of patients NOT reappointed?"]

    return df


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
    df = pd.DataFrame(
        {
            "Total Production Today": [0, 0, 0],
            "Adjustments Today": [0, 0, 0],
            "Write-offs Today": [0, 0, 0],
            "Patient Income Today": [0, 0, 0],
            "Unearned Income Today": [0, 0, 0],
            "Insurance Income Today": [0, 0, 0],
            "New Patients - Total Month to Date": [0, 0, 0],
            "treatments_presented": [0, 0, 0],
            "treatments_scheduled": [0, 0, 0],
            "Total hygiene Appointments": [0, 0, 0],
            "Number of patients NOT reappointed?": [0, 0, 0],
        }
    )

    df["total_production"] = df["Total Production Today"]
    df["total_collections"] = 0
    df["new_patients"] = 0
    df["total_hygiene_appointments"] = df["Total hygiene Appointments"]
    df["patients_not_reappointed"] = df["Number of patients NOT reappointed?"]

    return df


@pytest.fixture
def negative_values_data() -> pd.DataFrame:
    """Test data with negative values."""
    df = pd.DataFrame(
        {
            "Total Production Today": [-100, 200, -50],
            "Adjustments Today": [0, 0, 0],
            "Write-offs Today": [0, 0, 0],
            "Patient Income Today": [100, -200, 50],
            "Unearned Income Today": [0, 0, 0],
            "Insurance Income Today": [0, 0, 0],
            "New Patients - Total Month to Date": [-1, 2, -3],
            "treatments_presented": [-1000, 2000, -500],
            "treatments_scheduled": [500, -1000, 250],
        }
    )

    df["total_production"] = df["Total Production Today"]
    df["total_collections"] = (
        df["Patient Income Today"]
        + df["Unearned Income Today"]
        + df["Insurance Income Today"]
    )
    df["new_patients"] = df["New Patients - Total Month to Date"]

    return df


@pytest.fixture
def mixed_types_data() -> pd.DataFrame:
    """Test data with mixed data types."""
    df = pd.DataFrame(
        {
            "Total Production Today": ["1000", 2000, "3000.50"],
            "Adjustments Today": ["0", "-100", "50"],
            "Write-offs Today": ["-10", "0", "-20.5"],
            "Patient Income Today": [900, "1800", "2700.25"],
            "Unearned Income Today": ["0", "0", "0"],
            "Insurance Income Today": ["0", "0", "0"],
            "New Patients - Total Month to Date": ["3", 4, "5"],
            "treatments_presented": ["$10,000", 20000, "30000.00"],
            "treatments_scheduled": ["$5,000", "10000", 15000.50],
        }
    )

    df["total_production"] = df["Total Production Today"]
    df["total_collections"] = df["Patient Income Today"]
    df["new_patients"] = df["New Patients - Total Month to Date"]

    return df


@pytest.fixture
def nulls_data() -> pd.DataFrame:
    """Test data with null values."""
    import numpy as np

    df = pd.DataFrame(
        {
            "Total Production Today": [1000, None, 3000, np.nan],
            "Adjustments Today": [0, None, 0, np.nan],
            "Write-offs Today": [0, None, 0, np.nan],
            "Patient Income Today": [None, 1800, np.nan, 2500],
            "Unearned Income Today": [0, 0, None, 0],
            "Insurance Income Today": [0, 0, None, 0],
            "New Patients - Total Month to Date": [3, np.nan, None, 2],
            "treatments_presented": [1000, np.nan, 3000, None],
            "treatments_scheduled": [None, 1000, 2000, np.nan],
            "Total hygiene Appointments": [10, None, np.nan, 5],
            "Number of patients NOT reappointed?": [np.nan, 2, None, 1],
        }
    )

    df["total_production"] = df["Total Production Today"]
    df["total_collections"] = (
        df["Patient Income Today"]
        + df["Unearned Income Today"]
        + df["Insurance Income Today"]
    )
    df["new_patients"] = df["New Patients - Total Month to Date"]
    df["total_hygiene_appointments"] = df["Total hygiene Appointments"]
    df["patients_not_reappointed"] = df["Number of patients NOT reappointed?"]

    return df


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
