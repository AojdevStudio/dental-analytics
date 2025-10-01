# Tests for the pure KPI calculator functions.
"""Unit coverage for the CalculationResult-producing KPI helpers."""

from __future__ import annotations

from math import isclose

from core.calculators.kpi_calculator import (
    compute_case_acceptance,
    compute_collection_rate,
    compute_hygiene_reappointment,
    compute_new_patients,
    compute_production_total,
)


class TestComputeProductionTotal:
    def test_happy_path(self) -> None:
        result = compute_production_total(5000, -250, -150)
        assert result.can_calculate is True
        assert isclose(result.value or 0.0, 4600.0)

    def test_requires_gross_production(self) -> None:
        result = compute_production_total(None, -100, -50)
        assert result.can_calculate is False
        assert (
            result.reason == "Production total is required to compute net production."
        )

    def test_invalid_numeric_input(self) -> None:
        result = compute_production_total("abc", -100, 0)  # type: ignore[arg-type]
        assert result.can_calculate is False
        assert (
            result.reason == "Production total is required to compute net production."
        )


class TestComputeCollectionRate:
    def test_normal_collection_rate(self) -> None:
        result = compute_collection_rate(7000, -400, -200, 3200, 400, 2600)
        assert result.can_calculate is True
        assert isclose(result.value or 0.0, 96.875, rel_tol=1e-4)
        assert result.warnings == []

    def test_zero_adjusted_production(self) -> None:
        result = compute_collection_rate(0, 0, 0, 1000, 100, 1000)
        assert result.can_calculate is False
        assert (
            result.reason
            == "Adjusted production is zero; cannot compute collection rate."
        )

    def test_missing_production_value(self) -> None:
        result = compute_collection_rate(None, 0, 0, 0, 0, 0)
        assert result.can_calculate is False
        assert (
            result.reason == "Production value is required to compute collection rate."
        )

    def test_outlier_warning_triggered(self) -> None:
        result = compute_collection_rate(2000, -10, -10, 4000, 0, 0)
        assert result.can_calculate is True
        assert result.warnings == [
            "Collection rate exceeds 110%; verify production and collection values."
        ]

    def test_negative_adjusted_production_warning(self) -> None:
        result = compute_collection_rate(1000, -2000, 0, 500, 0, 0)
        assert result.can_calculate is True
        assert result.value is not None
        assert result.warnings == [
            "Adjusted (net) production is negative; review write-offs and adjustments."
        ]

    def test_positive_adjustment_values_reduce_denominator(self) -> None:
        result = compute_collection_rate(6000, 300, 200, 3000, 100, 1500)
        assert result.can_calculate is True
        assert isclose(result.value or 0.0, 83.6363636, rel_tol=1e-4)
        assert result.warnings == []

    def test_missing_adjustment_is_treated_as_zero(self) -> None:
        result = compute_collection_rate(4000, None, -200, 1500, 0, 800)
        assert result.can_calculate is True
        assert result.warnings == []
        assert isclose(result.value or 0.0, 60.5263158, rel_tol=1e-4)


class TestComputeNewPatients:
    def test_positive_count(self) -> None:
        result = compute_new_patients(7.0)
        assert result.can_calculate is True
        assert result.value == 7

    def test_negative_count_rejected(self) -> None:
        result = compute_new_patients(-1)
        assert result.can_calculate is False
        assert result.reason == "New patient total cannot be negative."

    def test_missing_count(self) -> None:
        result = compute_new_patients(None)
        assert result.can_calculate is False
        assert result.reason == "New patient total is unavailable."


class TestComputeCaseAcceptance:
    def test_standard_acceptance(self) -> None:
        result = compute_case_acceptance(40, 28, 4)
        assert result.can_calculate is True
        assert isclose(result.value or 0.0, 80.0)
        assert result.warnings == []

    def test_requires_presented_treatments(self) -> None:
        result = compute_case_acceptance(0, 10, 0)
        assert result.can_calculate is False
        assert result.reason == "Presented treatments must be greater than zero."

    def test_acceptance_above_hundred_warns(self) -> None:
        result = compute_case_acceptance(10, 12, 2)
        assert result.can_calculate is True
        assert result.warnings == [
            "Case acceptance exceeds 100%; confirm presented and scheduled totals."
        ]


class TestComputeHygieneReappointment:
    def test_normal_reappointment_rate(self) -> None:
        result = compute_hygiene_reappointment(20, 1)
        assert result.can_calculate is True
        assert isclose(result.value or 0.0, 95.0)

    def test_total_required(self) -> None:
        result = compute_hygiene_reappointment(0, 0)
        assert result.can_calculate is False
        assert result.reason == "Total hygiene appointments must be greater than zero."

    def test_not_reappointed_capped(self) -> None:
        result = compute_hygiene_reappointment(10, 15)
        assert result.can_calculate is True
        assert result.value == 0.0
        assert result.warnings == [
            "Not reappointed exceeds total hygiene appointments; capped value."
        ]

    def test_negative_not_reappointed_clamped(self) -> None:
        result = compute_hygiene_reappointment(10, -5)
        assert result.can_calculate is True
        assert result.warnings == []
        assert result.value == 100.0
