# Sample Front KPI sheet test data

import pandas as pd


def get_sample_front_kpi_data():
    """Get sample Front KPIs Form responses sheet data based on actual structure."""
    # Based on actual column mappings from spreadsheet
    return pd.DataFrame(
        {
            # Column A - Submission Date
            "Submission Date": [
                "2025-09-04 17:27:38",
                "2025-09-03 15:20:10",
                "2025-09-02 17:21:32",
            ],
            # Column B - Name
            "Name": ["Patience", "Patience", "Patience"],
            # Column C - Total hygiene Appointments
            "Total hygiene Appointments": ["7", "4", "6"],
            # Column D - Number of patients NOT reappointed?
            "Number of patients NOT reappointed?": ["0", "0", "0"],
            # Column L - Total Dollar amount Presented for the day
            "Total Dollar amount Presented for the day": ["52085", "35822", "40141"],
            # Column M - $ Total Dollar amount Scheduled
            "$ Total Dollar amount Scheduled": ["2715", "3019", "26739"],
            # Column N - $ Same Day Treatment
            "$ Same Day Treatment": ["1907", "0", "2606"],
        }
    )


def get_simple_front_kpi_data():
    """Get simplified Front KPI data for unit testing with expected column names."""
    return pd.DataFrame(
        {
            "Date": ["2025-09-04", "2025-09-03", "2025-09-02"],
            "total_hygiene_appointments": [7, 4, 6],
            "patients_not_reappointed": [0, 0, 0],
            "treatments_presented": [52085, 35822, 40141],
            "treatments_scheduled": [2715, 3019, 26739],
        }
    )
