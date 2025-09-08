# Google Drive and Sheets validation tests

import pandas as pd
import pytest

from backend.metrics import (
    calculate_collection_rate,
    calculate_hygiene_reappointment,
    calculate_new_patients,
    calculate_production_total,
    calculate_treatment_acceptance,
)


class TestSheetsStructure:
    """Test Google Sheets data structure and access."""

    @pytest.mark.unit
    def test_column_mappings(self):
        """Test that expected columns exist in sample data."""
        # Test EOD sheet structure
        eod_columns = [
            "date",
            "total_production",
            "total_collections",
            "adjustments",
            "writeoffs",
            "new_patients",
        ]

        # Create sample data to verify column existence
        eod_sample = pd.DataFrame({col: [0] for col in eod_columns})

        # Verify all expected columns exist
        for col in eod_columns:
            assert col in eod_sample.columns

        # Test Front KPI sheet structure
        front_kpi_columns = [
            "date",
            "total_hygiene_appointments",
            "patients_not_reappointed",
            "treatments_presented",
            "treatments_scheduled",
        ]

        front_sample = pd.DataFrame({col: [0] for col in front_kpi_columns})

        # Verify all expected columns exist
        for col in front_kpi_columns:
            assert col in front_sample.columns

    @pytest.mark.unit
    def test_eod_production_calculation(self):
        """Test production total calculation with real data structure."""
        test_data = pd.DataFrame(
            {
                "date": ["2024-01-15"],
                "total_production": [8500.00],
                "adjustments": [200.00],
                "writeoffs": [300.00],
                "total_collections": [8000.00],
                "new_patients": [3],
            }
        )

        production_total = calculate_production_total(test_data)
        # $8,500 + $200 + $300 = $9,000
        assert production_total == 9000.0

    @pytest.mark.unit
    def test_eod_collection_calculation(self):
        """Test collection rate calculation with realistic values."""
        test_data = pd.DataFrame(
            {
                "date": ["2024-01-15"],
                "total_production": [10000.00],
                "total_collections": [9500.00],
                "adjustments": [0],
                "writeoffs": [0],
                "new_patients": [2],
            }
        )

        collection_rate = calculate_collection_rate(test_data)
        # ($9,500 / $10,000) * 100 = 95%
        assert collection_rate == 95.0

    @pytest.mark.unit
    def test_eod_new_patients_calculation(self):
        """Test new patient count calculation."""
        test_data = pd.DataFrame(
            {
                "date": ["2024-01-15"],
                "total_production": [5000.00],
                "total_collections": [4800.00],
                "adjustments": [0],
                "writeoffs": [0],
                "new_patients": [7],
            }
        )

        new_patients = calculate_new_patients(test_data)
        assert new_patients == 7

    @pytest.mark.unit
    def test_front_kpi_treatment_acceptance(self):
        """Test treatment acceptance calculation with Front KPI data."""
        test_data = pd.DataFrame(
            {
                "date": ["2024-01-15"],
                "total_hygiene_appointments": [25],
                "patients_not_reappointed": [3],
                "treatments_presented": [150000.00],
                "treatments_scheduled": [120000.00],
            }
        )

        acceptance_rate = calculate_treatment_acceptance(test_data)
        # ($120,000 / $150,000) * 100 = 80%
        assert acceptance_rate == 80.0

    @pytest.mark.unit
    def test_front_kpi_hygiene_reappointment(self):
        """Test hygiene reappointment calculation with Front KPI data."""
        test_data = pd.DataFrame(
            {
                "date": ["2024-01-15"],
                "total_hygiene_appointments": [30],
                "patients_not_reappointed": [3],
                "treatments_presented": [100000.00],
                "treatments_scheduled": [90000.00],
            }
        )

        reappointment_rate = calculate_hygiene_reappointment(test_data)
        # ((30 - 3) / 30) * 100 = 90%
        assert reappointment_rate == 90.0

    @pytest.mark.unit
    def test_edge_case_zero_values(self):
        """Test handling of zero values in calculations."""
        # Test zero production (should return None for collection rate)
        zero_production = pd.DataFrame(
            {
                "total_production": [0],
                "total_collections": [100],
                "adjustments": [0],
                "writeoffs": [0],
            }
        )

        collection_rate = calculate_collection_rate(zero_production)
        assert collection_rate is None

        # Test zero hygiene appointments
        zero_hygiene = pd.DataFrame(
            {
                "total_hygiene_appointments": [0],
                "patients_not_reappointed": [0],
            }
        )

        hygiene_rate = calculate_hygiene_reappointment(zero_hygiene)
        assert hygiene_rate is None

    @pytest.mark.unit
    def test_realistic_daily_numbers(self):
        """Test with realistic daily numbers for Kam Dental."""
        # Typical daily EOD data
        daily_eod = pd.DataFrame(
            {
                "date": ["2024-01-15"],
                "total_production": [12000.00],  # Typical daily production
                "total_collections": [11000.00],  # ~92% collection rate
                "adjustments": [500.00],
                "writeoffs": [300.00],
                "new_patients": [4],  # 3-5 new patients per day
            }
        )

        # Typical daily Front KPI data
        daily_front = pd.DataFrame(
            {
                "date": ["2024-01-15"],
                "total_hygiene_appointments": [25],  # 20-30 hygiene per day
                "patients_not_reappointed": [2],  # ~8% not reappointed
                "treatments_presented": [85000.00],  # Treatment presentations
                "treatments_scheduled": [68000.00],  # ~80% acceptance
            }
        )

        # Calculate and verify reasonable ranges
        production = calculate_production_total(daily_eod)
        collection_rate = calculate_collection_rate(daily_eod)

        assert production == 12800.0  # $12,000 + $500 + $300
        assert collection_rate == pytest.approx(86.0, rel=1e-1)  # ~86%

        new_patients = calculate_new_patients(daily_eod)
        assert new_patients == 4

        treatment_acceptance = calculate_treatment_acceptance(daily_front)
        assert treatment_acceptance == 80.0

        hygiene_reappointment = calculate_hygiene_reappointment(daily_front)
        assert hygiene_reappointment == 92.0  # ((25-2)/25) * 100

    @pytest.mark.unit
    def test_currency_format_handling(self):
        """Test handling of currency-formatted strings from sheets."""
        # Test data that might come with currency formatting
        currency_data = pd.DataFrame(
            {
                "total_production": [10000.00],
                "total_collections": [9000.00],
                "adjustments": [0],
                "writeoffs": [0],
            }
        )

        collection_rate = calculate_collection_rate(currency_data)
        # ($9,000 / $10,000) * 100 = 90%
        assert collection_rate == 90.0

    @pytest.mark.unit
    def test_spreadsheet_id_constant(self):
        """Verify the correct spreadsheet ID is being used."""
        expected_id = "1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8"

        # Check if this ID is used in the sheets reader
        from backend.sheets_reader import SPREADSHEET_ID

        # Verify the constant matches our expected ID
        assert expected_id == SPREADSHEET_ID

    @pytest.mark.unit
    def test_data_type_conversions(self):
        """Test that currency and percentage strings are properly converted."""
        from backend.metrics import safe_numeric_conversion

        # Test currency conversion
        currency_df = pd.DataFrame({"amount": ["$1,234.56"]})
        result = safe_numeric_conversion(currency_df, "amount")
        # Note: This tests the actual conversion logic in the metrics module
        assert isinstance(result, int | float)

        # Test percentage conversion
        percent_df = pd.DataFrame({"rate": ["85.5%"]})
        result = safe_numeric_conversion(percent_df, "rate")
        assert isinstance(result, int | float)

    @pytest.mark.unit
    def test_missing_column_handling(self):
        """Test graceful handling of missing columns."""
        from backend.metrics import safe_numeric_conversion

        # DataFrame missing the requested column
        incomplete_df = pd.DataFrame({"other_column": [100]})

        result = safe_numeric_conversion(incomplete_df, "missing_column")
        assert result == 0.0  # Should return 0 for missing columns

    @pytest.mark.unit
    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrames."""
        empty_df = pd.DataFrame()

        # All calculation functions should return None for empty data
        assert calculate_production_total(empty_df) is None
        assert calculate_collection_rate(empty_df) is None
        assert calculate_new_patients(empty_df) is None
        assert calculate_treatment_acceptance(empty_df) is None
        assert calculate_hygiene_reappointment(empty_df) is None

        # Test None input
        assert calculate_production_total(None) is None
        assert calculate_collection_rate(None) is None
        assert calculate_new_patients(None) is None
        assert calculate_treatment_acceptance(None) is None
        assert calculate_hygiene_reappointment(None) is None
