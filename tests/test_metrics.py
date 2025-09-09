# Unit tests for metrics calculations

import pandas as pd
import pytest

from backend.metrics import (
    calculate_collection_rate,
    calculate_hygiene_reappointment,
    calculate_new_patients,
    calculate_production_total,
    calculate_treatment_acceptance,
)


class TestKPICalculations:
    """Test suite for KPI calculation functions."""

    @pytest.mark.unit
    def test_calculate_production_total_success(self) -> None:
        """Test successful production total calculation for single day (MVP)."""
        # MVP: Single day snapshot
        test_data = pd.DataFrame({"total_production": [1000]})
        result = calculate_production_total(test_data)
        assert result == 1000.0  # Single day value
        assert isinstance(result, float)

    @pytest.mark.unit
    def test_calculate_production_total_empty(self) -> None:
        """Test production calculation with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = calculate_production_total(empty_df)
        assert result is None

    @pytest.mark.unit
    def test_calculate_production_total_none(self) -> None:
        """Test production calculation with None input."""
        result = calculate_production_total(None)
        assert result is None

    @pytest.mark.unit
    def test_calculate_production_total_missing_column(self) -> None:
        """Test production calculation with missing column."""
        test_data = pd.DataFrame({"other_column": [1, 2, 3]})
        result = calculate_production_total(test_data)
        assert result is None

    @pytest.mark.unit
    def test_calculate_collection_rate_success(self) -> None:
        """Test successful collection rate calculation for single day (MVP)."""
        # MVP: Single day snapshot
        test_data = pd.DataFrame(
            {"total_production": [1000], "total_collections": [900]}
        )
        result = calculate_collection_rate(test_data)
        assert result == 90.0  # (900/1000) * 100
        assert isinstance(result, float)

    @pytest.mark.unit
    def test_calculate_collection_rate_zero_production(self) -> None:
        """Test collection rate with zero production (division by zero)."""
        test_data = pd.DataFrame(
            {"total_production": [0, 0, 0], "total_collections": [100, 200, 300]}
        )
        result = calculate_collection_rate(test_data)
        assert result is None

    @pytest.mark.unit
    def test_calculate_collection_rate_empty(self) -> None:
        """Test collection rate calculation with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = calculate_collection_rate(empty_df)
        assert result is None

    @pytest.mark.unit
    def test_calculate_collection_rate_none(self) -> None:
        """Test collection rate calculation with None input."""
        result = calculate_collection_rate(None)
        assert result is None

    @pytest.mark.unit
    def test_calculate_new_patients_success(self) -> None:
        """Test successful new patient count calculation for single day (MVP)."""
        # MVP: Single day snapshot
        test_data = pd.DataFrame({"new_patients": [3]})
        result = calculate_new_patients(test_data)
        assert result == 3  # Single day value
        assert isinstance(result, int)

    @pytest.mark.unit
    def test_calculate_new_patients_with_nulls(self) -> None:
        """Test new patient count with null values for single day (MVP)."""
        # MVP: Single day with null value
        test_data = pd.DataFrame({"new_patients": [None]})
        result = calculate_new_patients(test_data)
        assert result == 0  # Null treated as 0 for single day

    @pytest.mark.unit
    def test_calculate_new_patients_empty(self) -> None:
        """Test new patient count with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = calculate_new_patients(empty_df)
        assert result is None

    @pytest.mark.unit
    def test_calculate_treatment_acceptance_success(self) -> None:
        """Test treatment acceptance rate calculation for single day (MVP)."""
        # MVP: Single day snapshot
        test_data = pd.DataFrame(
            {
                "treatments_presented": [1000],
                "treatments_scheduled": [500],
            }
        )
        result = calculate_treatment_acceptance(test_data)
        # (500 / 1000) * 100 = 50%
        assert result is not None and result == 50.0

    @pytest.mark.unit
    def test_calculate_treatment_acceptance_zero_presented(self) -> None:
        """Test treatment acceptance with zero presented for single day (MVP)."""
        # MVP: Single day with zero presented
        test_data = pd.DataFrame(
            {"treatments_presented": [0], "treatments_scheduled": [0]}
        )
        result = calculate_treatment_acceptance(test_data)
        assert result is None

    @pytest.mark.unit
    def test_calculate_hygiene_reappointment_success(self) -> None:
        """Test hygiene reappointment rate calculation for single day (MVP)."""
        # MVP: Single day snapshot
        test_data = pd.DataFrame(
            {
                "total_hygiene_appointments": [10],
                "patients_not_reappointed": [1],
            }
        )
        result = calculate_hygiene_reappointment(test_data)
        # ((10 - 1) / 10) * 100 = 90%
        assert result is not None and result == 90.0

    @pytest.mark.unit
    def test_calculate_hygiene_reappointment_zero_appointments(self) -> None:
        """Test hygiene reappointment with zero appointments."""
        test_data = pd.DataFrame(
            {"total_hygiene_appointments": [0, 0], "patients_not_reappointed": [0, 0]}
        )
        result = calculate_hygiene_reappointment(test_data)
        assert result is None

    @pytest.mark.unit
    def test_column_name_mismatch_handling(self) -> None:
        """Test handling of incorrect column names."""
        test_data = pd.DataFrame({"wrong_column": [100, 200]})
        result = calculate_production_total(test_data)
        assert result is None

    @pytest.mark.unit
    def test_unprefixed_column_name_support(self) -> None:
        """Test that unprefixed column names work correctly."""
        # Test with unprefixed column names (Production, Collections)
        df_unprefixed = pd.DataFrame({"Production": [1000], "Collections": [900]})

        production = calculate_production_total(df_unprefixed)
        collection_rate = calculate_collection_rate(df_unprefixed)

        assert production == 1000.0
        assert collection_rate == 90.0

    @pytest.mark.unit
    def test_prefixed_column_name_support(self) -> None:
        """Test that prefixed column names still work correctly."""
        # Test with prefixed column names (total_production, total_collections)
        df_prefixed = pd.DataFrame(
            {"total_production": [1000], "total_collections": [900]}
        )

        production = calculate_production_total(df_prefixed)
        collection_rate = calculate_collection_rate(df_prefixed)

        assert production == 1000.0
        assert collection_rate == 90.0

    @pytest.mark.unit
    def test_mixed_column_name_scenarios(self) -> None:
        """Test various column name combinations."""
        # Test when only unprefixed exists
        df_unprefixed_only = pd.DataFrame({"Production": [500], "Collections": [450]})
        assert calculate_collection_rate(df_unprefixed_only) == 90.0

        # Test when prefixed takes precedence
        df_both = pd.DataFrame(
            {
                "total_production": [1000],
                "Production": [500],  # Should be ignored
                "total_collections": [800],
                "Collections": [400],  # Should be ignored
            }
        )
        assert calculate_collection_rate(df_both) == 80.0  # 800/1000


class TestKPIThresholds:
    """Test KPI threshold validations."""

    def test_production_threshold_categories(self) -> None:
        """Test production categorization."""
        assert self._categorize_production(28000) == "excellent"
        assert self._categorize_production(20000) == "good"
        assert self._categorize_production(14000) == "needs_improvement"

    def test_collection_rate_thresholds(self) -> None:
        """Test collection rate categorization."""
        assert self._categorize_collection_rate(96) == "excellent"
        assert self._categorize_collection_rate(90) == "good"
        assert self._categorize_collection_rate(84) == "needs_improvement"

    def test_hygiene_reappointment_thresholds(self) -> None:
        """Test hygiene reappointment categorization."""
        assert self._categorize_hygiene(95) == "excellent"
        assert self._categorize_hygiene(85) == "good"
        assert self._categorize_hygiene(79) == "needs_improvement"

    def _categorize_production(self, value: float) -> str:
        if value >= 25000:
            return "excellent"
        elif value >= 15000:
            return "good"
        else:
            return "needs_improvement"

    def _categorize_collection_rate(self, value: float) -> str:
        if value >= 95:
            return "excellent"
        elif value >= 85:
            return "good"
        else:
            return "needs_improvement"

    def _categorize_hygiene(self, value: float) -> str:
        if value >= 90:
            return "excellent"
        elif value >= 80:
            return "good"
        else:
            return "needs_improvement"
