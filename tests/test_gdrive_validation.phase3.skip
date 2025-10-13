# Google Sheets data validation tests aligned with the decoupled KPI core.

import pandas as pd
import pytest

from apps.backend.metrics import (
    calculate_case_acceptance,
    calculate_collection_rate,
    calculate_hygiene_reappointment,
    calculate_new_patients,
    calculate_production_total,
)


class TestSheetsStructure:
    """Validate that sample Google Sheets structures work with the new calculators."""

    @pytest.mark.unit
    def test_eod_production_calculation(self) -> None:
        eod_df = pd.DataFrame(
            {
                "Submission Date": ["2024-01-15"],
                "Total Production Today": [8500.0],
                "Adjustments Today": [200.0],
                "Write-offs Today": [300.0],
                "Patient Income Today": [6000.0],
                "Unearned Income Today": [1000.0],
                "Insurance Income Today": [2000.0],
                "New Patients - Total Month to Date": [3],
            }
        )

        production_total = calculate_production_total(eod_df)
        assert production_total == 9000.0

    @pytest.mark.unit
    def test_eod_collection_calculation(self) -> None:
        eod_df = pd.DataFrame(
            {
                "Submission Date": ["2024-01-15"],
                "Total Production Today": [10000.0],
                "Adjustments Today": [0.0],
                "Write-offs Today": [0.0],
                "Patient Income Today": [5000.0],
                "Unearned Income Today": [1500.0],
                "Insurance Income Today": [3000.0],
            }
        )

        collection_rate = calculate_collection_rate(eod_df)
        assert collection_rate == pytest.approx(95.0)

    @pytest.mark.unit
    def test_eod_new_patients_calculation(self) -> None:
        eod_df = pd.DataFrame(
            {
                "Submission Date": ["2024-01-15"],
                "Total Production Today": [5000.0],
                "Adjustments Today": [0.0],
                "Write-offs Today": [0.0],
                "Patient Income Today": [4200.0],
                "Unearned Income Today": [400.0],
                "Insurance Income Today": [200.0],
                "New Patients - Total Month to Date": [7],
            }
        )

        new_patients = calculate_new_patients(eod_df)
        assert new_patients == 7

    @pytest.mark.unit
    def test_front_kpi_case_acceptance(self) -> None:
        front_df = pd.DataFrame(
            {
                "Submission Date": ["2024-01-15"],
                "treatments_presented": [150000.0],
                "treatments_scheduled": [120000.0],
                "$ Same Day Treatment": [15000.0],
                "Total hygiene Appointments": [25],
                "Number of patients NOT reappointed?": [3],
            }
        )

        acceptance_rate = calculate_case_acceptance(front_df)
        assert acceptance_rate == pytest.approx(90.0)

    @pytest.mark.unit
    def test_front_kpi_hygiene_reappointment(self) -> None:
        front_df = pd.DataFrame(
            {
                "Submission Date": ["2024-01-15"],
                "Total hygiene Appointments": [30],
                "Number of patients NOT reappointed?": [3],
            }
        )

        reappointment_rate = calculate_hygiene_reappointment(front_df)
        assert reappointment_rate == pytest.approx(90.0)

    @pytest.mark.unit
    def test_edge_case_zero_values(self) -> None:
        zero_production = pd.DataFrame(
            {
                "Submission Date": ["2024-01-15"],
                "Total Production Today": [0.0],
                "Adjustments Today": [0.0],
                "Write-offs Today": [0.0],
                "Patient Income Today": [0.0],
                "Unearned Income Today": [0.0],
                "Insurance Income Today": [0.0],
            }
        )
        assert calculate_collection_rate(zero_production) is None

        zero_hygiene = pd.DataFrame(
            {
                "Submission Date": ["2024-01-15"],
                "Total hygiene Appointments": [0],
                "Number of patients NOT reappointed?": [0],
            }
        )
        assert calculate_hygiene_reappointment(zero_hygiene) is None

    @pytest.mark.unit
    def test_realistic_daily_numbers(self) -> None:
        eod_df = pd.DataFrame(
            {
                "Submission Date": ["2024-01-15"],
                "Total Production Today": [12000.0],
                "Adjustments Today": [500.0],
                "Write-offs Today": [300.0],
                "Patient Income Today": [8500.0],
                "Unearned Income Today": [500.0],
                "Insurance Income Today": [2500.0],
            }
        )
        front_df = pd.DataFrame(
            {
                "Submission Date": ["2024-01-15"],
                "treatments_presented": [85000.0],
                "treatments_scheduled": [68000.0],
                "$ Same Day Treatment": [4250.0],
                "Total hygiene Appointments": [25],
                "Number of patients NOT reappointed?": [2],
            }
        )

        production = calculate_production_total(eod_df)
        collection_rate = calculate_collection_rate(eod_df)
        acceptance = calculate_case_acceptance(front_df)
        hygiene = calculate_hygiene_reappointment(front_df)

        assert production == 12800.0
        assert collection_rate == pytest.approx(102.68, rel=1e-2)
        assert acceptance == pytest.approx(85.0, rel=1e-2)
        assert hygiene == pytest.approx(92.0, rel=1e-1)

    @pytest.mark.unit
    def test_currency_format_handling(self) -> None:
        eod_df = pd.DataFrame(
            {
                "Submission Date": ["2024-01-15"],
                "Total Production Today": ["$10,000.00"],
                "Adjustments Today": ["$0.00"],
                "Write-offs Today": ["$0.00"],
                "Patient Income Today": ["$6,000.00"],
                "Unearned Income Today": ["$2,000.00"],
                "Insurance Income Today": ["$1,000.00"],
            }
        )

        collection_rate = calculate_collection_rate(eod_df)
        assert collection_rate == pytest.approx(90.0)
