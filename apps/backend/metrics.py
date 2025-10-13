"""Simplified metrics module - Pure Pydantic wrapper (Story 3.2).

This module provides a simplified interface to the KPI service layer.
All business logic has been moved to core/ for framework independence.

Migrated: Phase 1 - TypedDict Elimination
Target: ~50-100 lines (clean wrapper, NO duplicate logic)
"""

from datetime import date

from core.business_rules.calendar import BusinessCalendar
from core.business_rules.validation_rules import KPIValidationRules
from core.models.kpi_models import KPIResponse, Location
from core.transformers.sheets_transformer import SheetsToKPIInputs
from services.kpi_service import KPIService

from .data_providers import build_sheets_provider

# Singleton service instance
_kpi_service: KPIService | None = None


def get_kpi_service() -> KPIService:
    """Get or create the singleton KPI service instance.

    Returns:
        Configured KPIService ready for use
    """
    global _kpi_service
    if _kpi_service is None:
        _kpi_service = KPIService(
            data_provider=build_sheets_provider(),
            calendar=BusinessCalendar(),
            validation_rules=KPIValidationRules(),
            transformer=SheetsToKPIInputs(),
        )
    return _kpi_service


def get_all_kpis(location: Location, target_date: date | None = None) -> KPIResponse:
    """Get all KPIs for a location on a specific date.

    This is the PRIMARY interface for KPI retrieval. All other KPI functions
    are considered legacy and should be migrated to use this interface.

    Args:
        location: Practice location ("baytown" or "humble")
        target_date: Date to calculate KPIs for (defaults to today)

    Returns:
        KPIResponse with all KPI values and validation metadata

    Example:
        >>> response = get_all_kpis("baytown")
        >>> print(response.production_total.value)
        15000.0
        >>> print(response.availability)
        "partial_data"
    """
    service = get_kpi_service()
    if target_date is None:
        target_date = date.today()
    return service.get_kpis(location, target_date)


# Legacy compatibility helper (Story 3.3 will remove this)
def clean_currency_string(value: object) -> object:
    """Clean currency strings by removing $ and commas.

    DEPRECATION NOTICE: This function will be removed in Story 3.3.
    Use core.transformers.sheets_transformer utilities instead.

    Args:
        value: Input value (str, number, or other)

    Returns:
        Cleaned value (str or original type)
    """
    if isinstance(value, str):
        return value.replace("$", "").replace(",", "").strip()
    return value


# ============================================================================
# BREAKING CHANGES - Story 3.2
# ============================================================================
# The following legacy functions have been removed from this module:
# - calculate_production_total() → Use get_all_kpis().production_total
# - calculate_collection_rate() → Use get_all_kpis().collection_rate
# - calculate_new_patients() → Use get_all_kpis().new_patients
# - calculate_case_acceptance() → Use get_all_kpis().case_acceptance
# - calculate_hygiene_reappointment() → Use get_all_kpis().hygiene_reappointment
# - calculate_historical_*() → Will be migrated in Story 3.4
#
# Tests requiring these functions should be updated in Story 3.3
# ============================================================================
