# KPI calculator functions for the decoupled core.
"""Pure calculation helpers for the five primary dental KPIs.

Each function accepts already-normalized numeric inputs (converted from raw
spreadsheets by the transformer layer) and returns a :class:`CalculationResult`
that describes the computed value plus any warnings or failure reasons.
"""

from __future__ import annotations

from typing import Final

from core.models.kpi_models import CalculationResult

Number = float | int | None
_WARNING_COLLECTION_OUTLIER: Final[str] = (
    "Collection rate exceeds 110%; verify production and collection values."
)
_WARNING_NEGATIVE_ADJUSTED: Final[str] = (
    "Adjusted (net) production is negative; review write-offs and adjustments."
)
_WARNING_ACCEPTANCE_OUTLIER: Final[str] = (
    "Case acceptance exceeds 100%; confirm presented and scheduled totals."
)
_WARNING_HYGIENE_CAP: Final[str] = (
    "Not reappointed exceeds total hygiene appointments; capped value."
)


def _to_float(value: Number) -> float | None:
    """Coerce optional numeric inputs to floats, preserving ``None``."""

    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compute_production_total(
    production: Number,
    adjustments: Number,
    writeoffs: Number,
) -> CalculationResult:
    """Calculate the daily net production.

    Parameters
    ----------
    production:
        Gross production total for the day.
    adjustments:
        Sum of financial adjustments applied (typically negative).
    writeoffs:
        Sum of write-offs applied (typically negative).

    Returns
    -------
    CalculationResult
        ``value`` contains the net production (gross + adjustments + write-offs)
        when the calculation is possible. ``reason`` explains why the
        computation failed when ``can_calculate`` is ``False``.

    Examples
    --------
    >>> compute_production_total(5000, -250, -150).value
    4600.0
    """

    gross = _to_float(production)
    if gross is None:
        return CalculationResult(
            value=None,
            can_calculate=False,
            reason="Production total is required to compute net production.",
        )

    adj = _to_float(adjustments) or 0.0
    write = _to_float(writeoffs) or 0.0
    total = gross + adj + write
    return CalculationResult(value=total, can_calculate=True)


def compute_collection_rate(
    production: Number,
    adjustments: Number,
    writeoffs: Number,
    patient_income: Number,
    unearned_income: Number,
    insurance_income: Number,
) -> CalculationResult:
    """Calculate the collection rate percentage using adjusted production.

    Parameters
    ----------
    production:
        Gross production figure prior to adjustments and write-offs.
    adjustments:
        Sum of adjustments applied to production (sign is ignored).
    writeoffs:
        Total write-offs applied (sign is ignored).
    patient_income:
        Payments collected directly from patients for the same period.
    unearned_income:
        Unearned income applied; may be negative when credits are consumed.
    insurance_income:
        Insurance payments collected during the period.

    Returns
    -------
    CalculationResult
        ``value`` contains the collection rate expressed as a percentage when the
        denominator is positive. ``warnings`` highlight abnormal values.

    Examples
    --------
    >>> result = compute_collection_rate(7000, -400, -200, 3200, 400, 2600)
    >>> round(result.value, 3)
    96.875
    """

    gross = _to_float(production)
    if gross is None:
        return CalculationResult(
            value=None,
            can_calculate=False,
            reason="Production value is required to compute collection rate.",
        )

    adj = _to_float(adjustments)
    write = _to_float(writeoffs)
    adjusted_production = gross

    for offset in (adj, write):
        if offset is None:
            continue
        if offset >= 0:
            adjusted_production -= offset
        else:
            adjusted_production += offset
    if adjusted_production == 0:
        return CalculationResult(
            value=None,
            can_calculate=False,
            reason="Adjusted production is zero; cannot compute collection rate.",
        )

    collections_total = (
        (_to_float(patient_income) or 0.0)
        + (_to_float(unearned_income) or 0.0)
        + (_to_float(insurance_income) or 0.0)
    )

    rate = (collections_total / adjusted_production) * 100
    warnings: list[str] = []
    if adjusted_production < 0:
        warnings.append(_WARNING_NEGATIVE_ADJUSTED)
    if rate > 110:
        warnings.append(_WARNING_COLLECTION_OUTLIER)

    return CalculationResult(value=rate, can_calculate=True, warnings=warnings)


def compute_new_patients(new_patients_mtd: Number) -> CalculationResult:
    """Return the count of new patients recorded for the period.

    Parameters
    ----------
    new_patients_mtd:
        Number of new patients attributed to the period. Expected to be
        non-negative.

    Returns
    -------
    CalculationResult
        ``value`` contains an integer count when available. Negative or missing
        inputs set ``can_calculate`` to ``False``.

    Examples
    --------
    >>> compute_new_patients(7).value
    7
    """

    count = _to_float(new_patients_mtd)
    if count is None:
        return CalculationResult(
            value=None,
            can_calculate=False,
            reason="New patient total is unavailable.",
        )
    if count < 0:
        return CalculationResult(
            value=None,
            can_calculate=False,
            reason="New patient total cannot be negative.",
        )

    return CalculationResult(value=int(round(count)), can_calculate=True)


def compute_case_acceptance(
    treatments_presented: Number,
    treatments_scheduled: Number,
    same_day_treatment: Number,
) -> CalculationResult:
    """Calculate the case acceptance percentage.

    Parameters
    ----------
    treatments_presented:
        Count of treatment plans presented to patients.
    treatments_scheduled:
        Number of treatments scheduled for future visits.
    same_day_treatment:
        Dollar value or count of same-day treatment acceptances.

    Returns
    -------
    CalculationResult
        ``value`` contains the acceptance percentage when the denominator is
        non-zero. ``warnings`` flag rates above 100 percent.

    Examples
    --------
    >>> round(compute_case_acceptance(40, 28, 4).value, 1)
    80.0
    """

    presented = _to_float(treatments_presented)
    if presented is None or presented <= 0:
        return CalculationResult(
            value=None,
            can_calculate=False,
            reason="Presented treatments must be greater than zero.",
        )

    scheduled = _to_float(treatments_scheduled) or 0.0
    same_day = _to_float(same_day_treatment) or 0.0
    acceptance = ((scheduled + same_day) / presented) * 100

    warnings: list[str] = []
    if acceptance > 100:
        warnings.append(_WARNING_ACCEPTANCE_OUTLIER)

    return CalculationResult(value=acceptance, can_calculate=True, warnings=warnings)


def compute_hygiene_reappointment(
    total_hygiene: Number,
    not_reappointed: Number,
) -> CalculationResult:
    """Compute the hygiene reappointment percentage.

    Parameters
    ----------
    total_hygiene:
        Total number of hygiene appointments during the measurement period.
    not_reappointed:
        Patients who left without rebooking a future hygiene appointment.

    Returns
    -------
    CalculationResult
        ``value`` contains the reappointment percentage when the total is
        positive. ``warnings`` note when values are capped following abnormal
        inputs.

    Examples
    --------
    >>> round(compute_hygiene_reappointment(20, 1).value, 1)
    95.0
    """

    total = _to_float(total_hygiene)
    if total is None or total <= 0:
        return CalculationResult(
            value=None,
            can_calculate=False,
            reason="Total hygiene appointments must be greater than zero.",
        )

    not_reap = _to_float(not_reappointed) or 0.0
    warnings: list[str] = []
    if not_reap < 0:
        not_reap = 0.0
    if not_reap > total:
        not_reap = total
        warnings.append(_WARNING_HYGIENE_CAP)

    reappointed = total - not_reap
    percentage = (reappointed / total) * 100
    return CalculationResult(value=percentage, can_calculate=True, warnings=warnings)
