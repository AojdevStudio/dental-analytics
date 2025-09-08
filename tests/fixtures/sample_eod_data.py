# Sample EOD billing sheet test data

import pandas as pd


def get_sample_eod_data() -> pd.DataFrame:
    """Get sample EOD - Baytown Billing sheet data based on actual structure."""
    # Based on actual column mappings from spreadsheet ID:
    # 1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8
    return pd.DataFrame(
        {
            "date": ["2024-01-15", "2024-01-16", "2024-01-17"],
            "total_production": [5000, 4500, 6200],
            "total_collections": [4800, 4200, 5900],
            "adjustments": [100, 50, 150],
            "writeoffs": [200, 100, 250],
            "new_patients": [3, 2, 5],
        }
    )


def get_simple_eod_data() -> pd.DataFrame:
    """Get simplified EOD data for unit testing with expected column names."""
    return pd.DataFrame(
        {
            "Date": ["2025-09-04", "2025-09-03", "2025-09-02"],
            "total_production": [5000, 4500, 6200],
            "total_collections": [4800, 4200, 5900],
            "adjustments": [100, 50, 150],
            "writeoffs": [200, 100, 250],
            "new_patients": [3, 2, 5],
        }
    )


def get_empty_eod_data() -> pd.DataFrame:
    """Get empty EOD data for testing edge cases."""
    return pd.DataFrame()


def get_invalid_eod_data() -> pd.DataFrame:
    """Get EOD data with invalid values for testing."""
    return pd.DataFrame(
        {
            "date": ["2024-01-15", "2024-01-16"],
            "total_production": ["invalid", None],
            "total_collections": [None, "invalid"],
            "adjustments": ["", 0],
            "writeoffs": [0, ""],
            "new_patients": ["invalid", -1],
        }
    )


def get_zero_values_eod_data() -> pd.DataFrame:
    """Get EOD data with zero values for testing edge cases."""
    return pd.DataFrame(
        {
            "date": ["2024-01-15"],
            "total_production": [0],
            "total_collections": [0],
            "adjustments": [0],
            "writeoffs": [0],
            "new_patients": [0],
        }
    )
