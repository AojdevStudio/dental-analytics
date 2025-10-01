# Tests for sheets_transformer.py
"""Comprehensive tests for the SheetsToKPIInputs data transformer.

Tests cover:
- Currency formatting ($1,234.56 → 1234.56)
- Null/NaN handling
- Mixed data types (strings, numbers)
- Empty DataFrames
- Missing columns
- Edge cases (empty strings, whitespace)
"""

import pandas as pd
import pytest

from core.transformers.sheets_transformer import SheetsToKPIInputs


class TestSafeExtract:
    """Tests for the _safe_extract helper method."""

    def test_extracts_numeric_value(self):
        """Should extract numeric value from DataFrame column."""
        df = pd.DataFrame({"Production": [1000.0, 2000.0, 3000.0]})
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Production")

        assert result == 3000.0  # Last row (iloc[-1])

    def test_cleans_currency_formatting(self):
        """Should remove $ and commas from currency strings."""
        df = pd.DataFrame({"Production": ["$1,234.56", "$2,345.67"]})
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Production")

        assert result == 2345.67

    def test_handles_currency_with_no_cents(self):
        """Should handle currency formatting without cents."""
        df = pd.DataFrame({"Production": ["$1,234", "$2,345"]})
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Production")

        assert result == 2345.0

    def test_handles_null_values(self):
        """Should return default when value is None or NaN."""
        df = pd.DataFrame({"Production": [1000.0, 2000.0, None]})  # None in last row
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Production", default=0.0)

        assert result == 0.0

    def test_handles_empty_dataframe(self):
        """Should return default when DataFrame is empty."""
        df = pd.DataFrame()
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Production", default=0.0)

        assert result == 0.0

    def test_handles_none_dataframe(self):
        """Should return default when DataFrame is None."""
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(None, "Production", default=0.0)

        assert result == 0.0

    def test_handles_missing_column(self):
        """Should return default when column doesn't exist."""
        df = pd.DataFrame({"Other": [1000.0, 2000.0]})
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Production", default=0.0)

        assert result == 0.0

    def test_handles_empty_string(self):
        """Should return default when value is empty string."""
        df = pd.DataFrame({"Production": ["100", ""]})  # Empty string in last row
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Production", default=0.0)

        assert result == 0.0

    def test_handles_whitespace_only(self):
        """Should return default when value is only whitespace."""
        df = pd.DataFrame({"Production": ["100", "   "]})  # Whitespace in last row
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Production", default=0.0)

        assert result == 0.0

    def test_handles_mixed_types_last_value_numeric(self):
        """Should extract numeric value even if earlier rows are strings."""
        df = pd.DataFrame({"Production": ["$1,234", 2345.67, "$3,456"]})
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Production")

        assert result == 3456.0

    def test_converts_integer_to_float(self):
        """Should convert integer values to float."""
        df = pd.DataFrame({"Count": [10, 20, 30]})
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Count")

        assert result == 30.0
        assert isinstance(result, float)

    def test_handles_negative_values(self):
        """Should correctly handle negative numbers."""
        df = pd.DataFrame({"Adjustments": ["-1,572.00", "-2,000.00"]})
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Adjustments")

        assert result == -2000.0

    def test_handles_negative_currency(self):
        """Should correctly handle negative currency formatting."""
        df = pd.DataFrame({"Adjustments": ["-$1,572.00", "-$2,000.00"]})
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Adjustments")

        assert result == -2000.0

    def test_handles_accounting_parentheses(self):
        """Should interpret parentheses-wrapped currency as negative."""
        df = pd.DataFrame({"Adjustments": ["($1,572.00)", "($2,000.00)"]})
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Adjustments")

        assert result == -2000.0


class TestExtractProductionInputs:
    """Tests for extract_production_inputs method."""

    def test_extracts_all_production_values(self, sample_eod_data):
        """Should extract production, adjustments, and writeoffs."""
        transformer = SheetsToKPIInputs()

        production, adjustments, writeoffs = transformer.extract_production_inputs(
            sample_eod_data
        )

        # Last row from fixture: production=13000, adj=-1059, writeoffs=-1396
        assert production == 13000.0
        assert adjustments == -1059.0
        assert writeoffs == -1396.0

    def test_handles_missing_adjustments(self):
        """Should default adjustments to 0.0 if column missing."""
        df = pd.DataFrame(
            {
                "Total Production Today": [5000.0],
                # Missing "Adjustments Today"
                "Write-offs Today": [-100.0],
            }
        )
        transformer = SheetsToKPIInputs()

        production, adjustments, writeoffs = transformer.extract_production_inputs(df)

        assert production == 5000.0
        assert adjustments == 0.0  # Default
        assert writeoffs == -100.0

    def test_handles_empty_dataframe(self):
        """Should return None values for empty DataFrame."""
        df = pd.DataFrame()
        transformer = SheetsToKPIInputs()

        production, adjustments, writeoffs = transformer.extract_production_inputs(df)

        assert production is None
        assert adjustments == 0.0  # Has default
        assert writeoffs == 0.0  # Has default


class TestExtractCollectionInputs:
    """Tests for extract_collection_inputs method."""

    def test_extracts_all_collection_values(self, sample_eod_data):
        """Should extract all 6 values needed for collection rate."""
        transformer = SheetsToKPIInputs()

        (
            production,
            adjustments,
            writeoffs,
            patient_income,
            unearned_income,
            insurance_income,
        ) = transformer.extract_collection_inputs(sample_eod_data)

        # Last row from fixture
        assert production == 13000.0
        assert adjustments == -1059.0
        assert writeoffs == -1396.0
        assert patient_income == 3428.61
        assert unearned_income == 0.0
        assert insurance_income == 0.0

    def test_handles_missing_income_columns(self):
        """Should default missing income columns to 0.0."""
        df = pd.DataFrame(
            {
                "Total Production Today": [5000.0],
                "Adjustments Today": [-100.0],
                "Write-offs Today": [-50.0],
                # Missing all income columns
            }
        )
        transformer = SheetsToKPIInputs()

        (
            production,
            adjustments,
            writeoffs,
            patient_income,
            unearned_income,
            insurance_income,
        ) = transformer.extract_collection_inputs(df)

        assert production == 5000.0
        assert adjustments == -100.0
        assert writeoffs == -50.0
        assert patient_income == 0.0  # Default
        assert unearned_income == 0.0  # Default
        assert insurance_income == 0.0  # Default


class TestExtractNewPatientsInputs:
    """Tests for extract_new_patients_inputs method."""

    def test_extracts_new_patients_count(self, sample_eod_data):
        """Should extract month-to-date new patient count."""
        transformer = SheetsToKPIInputs()

        (new_patients_mtd,) = transformer.extract_new_patients_inputs(sample_eod_data)

        # Last row from fixture
        assert new_patients_mtd == 45.0

    def test_handles_missing_column(self):
        """Should return None when new patients column missing."""
        df = pd.DataFrame({"Other Column": [100]})
        transformer = SheetsToKPIInputs()

        (new_patients_mtd,) = transformer.extract_new_patients_inputs(df)

        assert new_patients_mtd is None


class TestExtractCaseAcceptanceInputs:
    """Tests for extract_case_acceptance_inputs method."""

    def test_extracts_case_acceptance_values(self, sample_front_kpi_data):
        """Should extract presented, scheduled, and same day values."""
        transformer = SheetsToKPIInputs()

        (
            presented,
            scheduled,
            same_day,
        ) = transformer.extract_case_acceptance_inputs(sample_front_kpi_data)

        # Last row from fixture
        assert presented == 40141.0
        assert scheduled == 26739.0
        assert same_day == 2606.0

    def test_cleans_currency_from_same_day(self):
        """Should handle currency formatting in same day treatment."""
        df = pd.DataFrame(
            {
                "treatments_presented": [50000],
                "treatments_scheduled": [30000],
                "$ Same Day Treatment": ["$1,907"],  # Currency formatted
            }
        )
        transformer = SheetsToKPIInputs()

        presented, scheduled, same_day = transformer.extract_case_acceptance_inputs(df)

        assert presented == 50000.0
        assert scheduled == 30000.0
        assert same_day == 1907.0  # Cleaned


class TestExtractHygieneInputs:
    """Tests for extract_hygiene_inputs method."""

    def test_extracts_hygiene_values(self, sample_front_kpi_data):
        """Should extract total hygiene and not reappointed counts."""
        transformer = SheetsToKPIInputs()

        total, not_reappointed = transformer.extract_hygiene_inputs(
            sample_front_kpi_data
        )

        # Last row from fixture
        assert total == 6.0
        assert not_reappointed == 0.0

    def test_handles_missing_columns(self):
        """Should return None values when columns missing."""
        df = pd.DataFrame({"Other": [100]})
        transformer = SheetsToKPIInputs()

        total, not_reappointed = transformer.extract_hygiene_inputs(df)

        assert total is None
        assert not_reappointed is None


class TestEdgeCases:
    """Edge case tests for transformer robustness."""

    def test_handles_single_row_dataframe(self):
        """Should work with single-row DataFrame."""
        df = pd.DataFrame({"Production": [5000.0]})
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Production")

        assert result == 5000.0

    def test_handles_very_large_numbers(self):
        """Should handle very large currency values."""
        df = pd.DataFrame({"Production": ["$1,234,567.89"]})
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Production")

        assert result == 1234567.89

    def test_handles_zero_values(self):
        """Should correctly extract zero values."""
        df = pd.DataFrame({"Production": [0.0, 0, "$0.00"]})
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Production")

        assert result == 0.0

    def test_preserves_precision(self):
        """Should preserve decimal precision."""
        df = pd.DataFrame({"Rate": [98.123456789]})
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Rate")

        assert result == pytest.approx(98.123456789)

    def test_handles_scientific_notation(self):
        """Should handle values in scientific notation."""
        df = pd.DataFrame({"Value": [1.23e4]})
        transformer = SheetsToKPIInputs()

        result = transformer._safe_extract(df, "Value")

        assert result == 12300.0
