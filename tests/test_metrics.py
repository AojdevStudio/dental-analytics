# Unit tests for legacy metrics compatibility wrappers backed by core calculators.

import pandas as pd
import pytest

from apps.backend.metrics import (
    calculate_case_acceptance,
    calculate_collection_rate,
    calculate_hygiene_reappointment,
    calculate_new_patients,
    calculate_production_total,
)


class TestKPICalculations:
    """Surface-level regression tests for metrics compatibility helpers."""

    @pytest.mark.unit
    def test_calculate_production_total_success(self) -> None:
        eod_df = pd.DataFrame(
            {
                "Total Production Today": [1000.0],
                "Adjustments Today": [0.0],
                "Write-offs Today": [0.0],
            }
        )

        result = calculate_production_total(eod_df)

        assert result == 1000.0

    @pytest.mark.unit
    def test_calculate_production_total_missing_columns(self) -> None:
        result = calculate_production_total(pd.DataFrame({"foo": [1]}))
        assert result is None

    @pytest.mark.unit
    def test_calculate_collection_rate_success(self) -> None:
        eod_df = pd.DataFrame(
            {
                "Total Production Today": [1000.0],
                "Adjustments Today": [0.0],
                "Write-offs Today": [0.0],
                "Patient Income Today": [900.0],
                "Unearned Income Today": [0.0],
                "Insurance Income Today": [0.0],
            }
        )

        result = calculate_collection_rate(eod_df)

        assert result == pytest.approx(90.0)

    @pytest.mark.unit
    def test_calculate_collection_rate_zero_production(self) -> None:
        zero_df = pd.DataFrame(
            {
                "Total Production Today": [0.0],
                "Adjustments Today": [0.0],
                "Write-offs Today": [0.0],
                "Patient Income Today": [100.0],
                "Unearned Income Today": [0.0],
                "Insurance Income Today": [0.0],
            }
        )

        assert calculate_collection_rate(zero_df) is None

    @pytest.mark.unit
    def test_calculate_new_patients_success(self) -> None:
        eod_df = pd.DataFrame({"New Patients - Total Month to Date": [48]})

        assert calculate_new_patients(eod_df) == 48

    @pytest.mark.unit
    def test_calculate_new_patients_null(self) -> None:
        df = pd.DataFrame({"New Patients - Total Month to Date": [None]})
        assert calculate_new_patients(df) is None

    @pytest.mark.unit
    def test_calculate_case_acceptance_success(self) -> None:
        front_df = pd.DataFrame(
            {
                "treatments_presented": [1000.0],
                "treatments_scheduled": [500.0],
                "$ Same Day Treatment": [100.0],
            }
        )

        result = calculate_case_acceptance(front_df)

        assert result == pytest.approx(60.0)

    @pytest.mark.unit
    def test_calculate_case_acceptance_zero_presented(self) -> None:
        front_df = pd.DataFrame(
            {
                "treatments_presented": [0.0],
                "treatments_scheduled": [100.0],
                "$ Same Day Treatment": [0.0],
            }
        )

        assert calculate_case_acceptance(front_df) is None

    @pytest.mark.unit
    def test_calculate_hygiene_reappointment_success(self) -> None:
        front_df = pd.DataFrame(
            {
                "Total hygiene Appointments": [10.0],
                "Number of patients NOT reappointed?": [1.0],
            }
        )

        result = calculate_hygiene_reappointment(front_df)

        assert result == pytest.approx(90.0)

    @pytest.mark.unit
    def test_calculate_hygiene_reappointment_zero_total(self) -> None:
        front_df = pd.DataFrame(
            {
                "Total hygiene Appointments": [0.0],
                "Number of patients NOT reappointed?": [0.0],
            }
        )

        assert calculate_hygiene_reappointment(front_df) is None
