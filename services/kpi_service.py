# KPI Service - Orchestration layer for KPI calculation and validation.
"""Service orchestrator that coordinates calendar, data, transformation,
calculation, and validation.

This is the main entry point for retrieving KPIs. It orchestrates the complete flow:
1. Business calendar check (is the location open on this date?)
2. Data fetch from provider (Google Sheets via alias)
3. Data transformation (DataFrames → calculation inputs)
4. Pure calculations (inputs → CalculationResult)
5. Validation (compare results against business goals)
6. Response assembly (CalculationResult → KPIValue → KPIResponse)

The service layer depends on all other core modules via dependency injection,
making it easy to test and swap implementations.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Protocol

import pandas as pd
from pydantic import BaseModel

from core.business_rules.calendar import BusinessCalendar
from core.business_rules.validation_rules import KPIValidationRules
from core.calculators import kpi_calculator
from core.models.kpi_models import (
    CalculationResult,
    DataAvailabilityStatus,
    DataFreshness,
    KPIResponse,
    KPIValue,
    KPIValues,
    Location,
    ValidationIssue,
    ValidationSeverity,
)
from core.transformers.sheets_transformer import SheetsToKPIInputs

logger = logging.getLogger(__name__)


class DataProvider(Protocol):
    """Protocol for data access providers (matches apps.backend.data_providers)."""

    def fetch(self, alias: str) -> pd.DataFrame | None:
        """Fetch data by alias."""
        ...

    def list_available_aliases(self) -> list[str]:
        """Get list of available data aliases."""
        ...

    def validate_alias(self, alias: str) -> bool:
        """Check if alias is valid and accessible."""
        ...


class KPIService(BaseModel):
    """Service orchestrator for KPI retrieval and validation.

    This service coordinates all the layers of the KPI calculation system:
    - Business calendar (when is the location open?)
    - Data provider (fetch from Google Sheets)
    - Transformer (DataFrame → calculation inputs)
    - Calculators (inputs → results)
    - Validation rules (results → business validation)

    All dependencies are injected via constructor for testability.

    Attributes
    ----------
    data_provider:
        Provider for fetching data (e.g., SheetsProvider).
    calendar:
        Business calendar for checking open/closed days.
    validation_rules:
        Validation rules for comparing KPIs against goals.
    transformer:
        Transformer for extracting calculation inputs from DataFrames.

    Examples
    --------
    >>> from apps.backend.data_providers import SheetsProvider
    >>> provider = SheetsProvider()
    >>> calendar = BusinessCalendar()
    >>> rules = KPIValidationRules()
    >>> transformer = SheetsToKPIInputs()
    >>> service = KPIService(
    ...     data_provider=provider,
    ...     calendar=calendar,
    ...     validation_rules=rules,
    ...     transformer=transformer
    ... )
    >>> response = service.get_kpis("baytown", date(2025, 1, 6))
    >>> response.location
    'baytown'
    """

    data_provider: Any  # DataProvider protocol
    calendar: BusinessCalendar
    validation_rules: KPIValidationRules
    transformer: SheetsToKPIInputs

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True

    def get_kpis(self, location: Location, target_date: date) -> KPIResponse:
        """Main entry point for retrieving KPIs for a location on a specific date.

        Orchestrates the complete flow:
        1. Check if location is open on target_date
        2. If closed, return closure response
        3. If open, fetch data from provider
        4. Transform data to calculation inputs
        5. Run calculations
        6. Validate results against business goals
        7. Assemble and return KPIResponse

        Parameters
        ----------
        location:
            Practice location ("baytown" or "humble").
        target_date:
            The date to calculate KPIs for.

        Returns
        -------
        KPIResponse
            Complete KPI response with all 5 KPIs, validation issues,
            and data freshness information.

        Examples
        --------
        >>> service = KPIService(...)
        >>> response = service.get_kpis("baytown", date(2025, 1, 6))
        >>> response.values.production_total.value
        7650.0
        """
        logger.info(
            "kpi_service.get_kpis_started",
            extra={"location": location, "target_date": str(target_date)},
        )

        # Step 1: Check business calendar
        if not self.calendar.is_business_day(location, target_date):
            reason = self.calendar.get_expected_closure_reason(location, target_date)
            logger.info(
                "kpi_service.location_closed",
                extra={
                    "location": location,
                    "target_date": str(target_date),
                    "reason": reason,
                },
            )
            return self._create_closed_response(location, target_date, reason)

        # Step 2: Fetch data from provider
        try:
            eod_alias = f"{location}_eod"
            front_alias = f"{location}_front"

            eod_df = self.data_provider.fetch(eod_alias)
            front_df = self.data_provider.fetch(front_alias)

            logger.info(
                "kpi_service.data_fetched",
                extra={
                    "location": location,
                    "eod_rows": len(eod_df) if eod_df is not None else 0,
                    "front_rows": len(front_df) if front_df is not None else 0,
                },
            )

        except Exception as e:
            logger.error(
                "kpi_service.data_fetch_failed",
                extra={
                    "location": location,
                    "target_date": str(target_date),
                    "error": str(e),
                },
            )
            return self._create_error_response(
                location,
                target_date,
                DataAvailabilityStatus.INFRASTRUCTURE_ERROR,
                f"Failed to fetch data: {str(e)}",
            )

        # Handle partial data scenarios
        if eod_df is None and front_df is None:
            logger.warning(
                "kpi_service.no_data_available",
                extra={"location": location, "target_date": str(target_date)},
            )
            return self._create_error_response(
                location,
                target_date,
                DataAvailabilityStatus.DATA_NOT_READY,
                "No data available for this date",
            )

        # Step 3: Transform data to calculation inputs & Step 4: Calculate KPIs
        kpi_values = self._calculate_all_kpis(location, target_date, eod_df, front_df)

        # Step 5: Collect data freshness metadata
        data_freshness = self._collect_freshness_metadata(location, eod_df, front_df)

        # Step 6: Determine overall availability status
        availability = self._determine_availability_status(kpi_values)

        # Step 7: Collect all validation issues
        validation_summary = self._collect_validation_summary(kpi_values)

        logger.info(
            "kpi_service.get_kpis_completed",
            extra={
                "location": location,
                "target_date": str(target_date),
                "availability": availability.value,
                "validation_issues": len(validation_summary),
            },
        )

        return KPIResponse(
            location=location,
            business_date=target_date,
            availability=availability,
            values=kpi_values,
            data_freshness=data_freshness,
            closure_reason=None,
            validation_summary=validation_summary,
        )

    def _calculate_all_kpis(
        self,
        location: Location,
        target_date: date,
        eod_df: pd.DataFrame | None,
        front_df: pd.DataFrame | None,
    ) -> KPIValues:
        """Calculate all 5 KPIs using transformer and calculators.

        Parameters
        ----------
        location:
            Practice location.
        target_date:
            Date for calculation.
        eod_df:
            EOD billing DataFrame (may be None).
        front_df:
            Front KPI DataFrame (may be None).

        Returns
        -------
        KPIValues
            Container with all 5 KPI values.
        """
        # Calculate production total
        production_total = self._calculate_production(location, target_date, eod_df)

        # Calculate collection rate
        collection_rate = self._calculate_collection_rate(location, target_date, eod_df)

        # Calculate new patients
        new_patients = self._calculate_new_patients(location, target_date, eod_df)

        # Calculate case acceptance
        case_acceptance = self._calculate_case_acceptance(
            location, target_date, front_df
        )

        # Calculate hygiene reappointment
        hygiene_reappointment = self._calculate_hygiene_reappointment(
            location, target_date, front_df
        )

        return KPIValues(
            production_total=production_total,
            collection_rate=collection_rate,
            new_patients=new_patients,
            case_acceptance=case_acceptance,
            hygiene_reappointment=hygiene_reappointment,
        )

    def _calculate_production(
        self, location: Location, target_date: date, eod_df: pd.DataFrame | None
    ) -> KPIValue:
        """Calculate production total KPI."""
        if eod_df is None or eod_df.empty:
            return self._create_unavailable_kpi(
                "Production data not available",
                DataAvailabilityStatus.DATA_NOT_READY,
            )

        # Extract inputs from DataFrame
        production, adjustments, writeoffs = self.transformer.extract_production_inputs(
            eod_df
        )

        # Run calculation
        result = kpi_calculator.compute_production_total(
            production, adjustments, writeoffs
        )

        # Validate and return
        return self._create_kpi_value(result, "production", location, target_date)

    def _calculate_collection_rate(
        self, location: Location, target_date: date, eod_df: pd.DataFrame | None
    ) -> KPIValue:
        """Calculate collection rate KPI."""
        if eod_df is None or eod_df.empty:
            return self._create_unavailable_kpi(
                "Collection data not available",
                DataAvailabilityStatus.DATA_NOT_READY,
            )

        # Extract inputs
        (
            production,
            adjustments,
            writeoffs,
            patient_income,
            unearned_income,
            insurance_income,
        ) = self.transformer.extract_collection_inputs(eod_df)

        # Run calculation
        result = kpi_calculator.compute_collection_rate(
            production,
            adjustments,
            writeoffs,
            patient_income,
            unearned_income,
            insurance_income,
        )

        # Validate and return
        return self._create_kpi_value(result, "collection_rate", location, target_date)

    def _calculate_new_patients(
        self, location: Location, target_date: date, eod_df: pd.DataFrame | None
    ) -> KPIValue:
        """Calculate new patients KPI."""
        if eod_df is None or eod_df.empty:
            return self._create_unavailable_kpi(
                "New patients data not available",
                DataAvailabilityStatus.DATA_NOT_READY,
            )

        # Extract inputs
        (new_patients_mtd,) = self.transformer.extract_new_patients_inputs(eod_df)

        # Run calculation
        result = kpi_calculator.compute_new_patients(new_patients_mtd)

        # Validate and return
        return self._create_kpi_value(result, "new_patients", location, target_date)

    def _calculate_case_acceptance(
        self, location: Location, target_date: date, front_df: pd.DataFrame | None
    ) -> KPIValue:
        """Calculate case acceptance KPI."""
        if front_df is None or front_df.empty:
            return self._create_unavailable_kpi(
                "Case acceptance data not available",
                DataAvailabilityStatus.PARTIAL,
            )

        # Extract inputs
        treatments_presented, treatments_scheduled, same_day_treatment = (
            self.transformer.extract_case_acceptance_inputs(front_df)
        )

        # Run calculation
        result = kpi_calculator.compute_case_acceptance(
            treatments_presented, treatments_scheduled, same_day_treatment
        )

        # Validate and return
        return self._create_kpi_value(result, "case_acceptance", location, target_date)

    def _calculate_hygiene_reappointment(
        self, location: Location, target_date: date, front_df: pd.DataFrame | None
    ) -> KPIValue:
        """Calculate hygiene reappointment KPI."""
        if front_df is None or front_df.empty:
            return self._create_unavailable_kpi(
                "Hygiene data not available",
                DataAvailabilityStatus.PARTIAL,
            )

        # Extract inputs
        total_hygiene, not_reappointed = self.transformer.extract_hygiene_inputs(
            front_df
        )

        # Run calculation
        result = kpi_calculator.compute_hygiene_reappointment(
            total_hygiene, not_reappointed
        )

        # Validate and return
        return self._create_kpi_value(
            result, "hygiene_reappointment", location, target_date
        )

    def _create_kpi_value(
        self,
        result: CalculationResult,
        kpi_field: str,
        location: Location,
        target_date: date,
    ) -> KPIValue:
        """Convert CalculationResult to KPIValue with validation.

        Parameters
        ----------
        result:
            Result from calculator function.
        kpi_field:
            KPI field name for validation routing.
        location:
            Practice location.
        target_date:
            Date for validation context.

        Returns
        -------
        KPIValue
            KPI value with validation issues attached.
        """
        if not result.can_calculate:
            return KPIValue(
                value=None,
                available=False,
                availability_status=DataAvailabilityStatus.DATA_QUALITY_ISSUE,
                unavailable_reason=result.reason,
                validation_issues=[],
            )

        # Run validation based on KPI type
        validation_issues: list[ValidationIssue] = []

        if kpi_field == "production":
            validation_issues = self.validation_rules.validate_production(
                result.value, location, target_date
            )
        elif kpi_field == "collection_rate":
            validation_issues = self.validation_rules.validate_collection_rate(
                result.value
            )
        elif kpi_field == "new_patients":
            validation_issues = self.validation_rules.validate_new_patients(
                int(result.value) if result.value is not None else None
            )
        elif kpi_field == "case_acceptance":
            validation_issues = self.validation_rules.validate_case_acceptance(
                result.value
            )
        elif kpi_field == "hygiene_reappointment":
            validation_issues = self.validation_rules.validate_hygiene_reappointment(
                result.value
            )

        # Add calculator warnings as validation issues if present
        for warning in result.warnings:
            validation_issues.append(
                ValidationIssue(
                    code=f"{kpi_field}.calculator_warning",
                    message=warning,
                    severity=ValidationSeverity.WARNING,
                )
            )

        return KPIValue(
            value=result.value,
            available=True,
            availability_status=DataAvailabilityStatus.AVAILABLE,
            unavailable_reason=None,
            validation_issues=validation_issues,
        )

    def _create_unavailable_kpi(
        self, reason: str, status: DataAvailabilityStatus
    ) -> KPIValue:
        """Create KPIValue for unavailable data."""
        return KPIValue(
            value=None,
            available=False,
            availability_status=status,
            unavailable_reason=reason,
            validation_issues=[],
        )

    def _create_closed_response(
        self, location: Location, target_date: date, reason: str | None
    ) -> KPIResponse:
        """Create KPIResponse for a closed day.

        Parameters
        ----------
        location:
            Practice location.
        target_date:
            The closed date.
        reason:
            Reason for closure (e.g., "Closed on Sundays").

        Returns
        -------
        KPIResponse
            Response indicating the location was closed.
        """
        # Create unavailable KPI values
        unavailable_kpi = KPIValue(
            value=None,
            available=False,
            availability_status=DataAvailabilityStatus.EXPECTED_CLOSURE,
            unavailable_reason=reason or "Location closed",
            validation_issues=[],
        )

        return KPIResponse(
            location=location,
            business_date=target_date,
            availability=DataAvailabilityStatus.EXPECTED_CLOSURE,
            values=KPIValues(
                production_total=unavailable_kpi,
                collection_rate=unavailable_kpi,
                new_patients=unavailable_kpi,
                case_acceptance=unavailable_kpi,
                hygiene_reappointment=unavailable_kpi,
            ),
            data_freshness=[],
            closure_reason=reason,
            validation_summary=[],
        )

    def _create_error_response(
        self,
        location: Location,
        target_date: date,
        status: DataAvailabilityStatus,
        error_message: str,
    ) -> KPIResponse:
        """Create KPIResponse for an error condition.

        Parameters
        ----------
        location:
            Practice location.
        target_date:
            The target date.
        status:
            Availability status describing the error.
        error_message:
            Human-readable error message.

        Returns
        -------
        KPIResponse
            Error response with appropriate status.
        """
        unavailable_kpi = KPIValue(
            value=None,
            available=False,
            availability_status=status,
            unavailable_reason=error_message,
            validation_issues=[],
        )

        return KPIResponse(
            location=location,
            business_date=target_date,
            availability=status,
            values=KPIValues(
                production_total=unavailable_kpi,
                collection_rate=unavailable_kpi,
                new_patients=unavailable_kpi,
                case_acceptance=unavailable_kpi,
                hygiene_reappointment=unavailable_kpi,
            ),
            data_freshness=[],
            closure_reason=None,
            validation_summary=[],
        )

    def _collect_freshness_metadata(
        self,
        location: Location,
        eod_df: pd.DataFrame | None,
        front_df: pd.DataFrame | None,
    ) -> list[DataFreshness]:
        """Collect data freshness metadata from source DataFrames.

        Parameters
        ----------
        location:
            Practice location.
        eod_df:
            EOD billing DataFrame.
        front_df:
            Front KPI DataFrame.

        Returns
        -------
        list[DataFreshness]
            List of freshness metadata for each source.
        """
        freshness_list: list[DataFreshness] = []
        now = datetime.now()

        # For simplicity, we'll use the current time as both as_of and retrieved_at
        # In a real system, you'd extract these from the DataFrame or metadata
        if eod_df is not None and not eod_df.empty:
            freshness_list.append(
                DataFreshness(
                    source_alias=f"{location}_eod",
                    as_of=now,
                    retrieved_at=now,
                    timezone="America/Chicago",
                )
            )

        if front_df is not None and not front_df.empty:
            freshness_list.append(
                DataFreshness(
                    source_alias=f"{location}_front",
                    as_of=now,
                    retrieved_at=now,
                    timezone="America/Chicago",
                )
            )

        return freshness_list

    def _determine_availability_status(
        self, kpi_values: KPIValues
    ) -> DataAvailabilityStatus:
        """Determine overall availability status based on individual KPIs.

        Parameters
        ----------
        kpi_values:
            Container with all 5 KPI values.

        Returns
        -------
        DataAvailabilityStatus
            Overall availability status.
        """
        all_kpis = [
            kpi_values.production_total,
            kpi_values.collection_rate,
            kpi_values.new_patients,
            kpi_values.case_acceptance,
            kpi_values.hygiene_reappointment,
        ]

        # If any KPI is available, consider overall status as available
        # (even if some are partial)
        if any(kpi.available for kpi in all_kpis):
            # Check if we have partial data (some KPIs available, some not)
            if not all(kpi.available for kpi in all_kpis):
                return DataAvailabilityStatus.PARTIAL
            return DataAvailabilityStatus.AVAILABLE

        # If no KPIs are available, check the reason
        # Priority: INFRASTRUCTURE_ERROR > DATA_QUALITY_ISSUE > DATA_NOT_READY
        statuses = {kpi.availability_status for kpi in all_kpis}

        if DataAvailabilityStatus.INFRASTRUCTURE_ERROR in statuses:
            return DataAvailabilityStatus.INFRASTRUCTURE_ERROR
        if DataAvailabilityStatus.DATA_QUALITY_ISSUE in statuses:
            return DataAvailabilityStatus.DATA_QUALITY_ISSUE

        return DataAvailabilityStatus.DATA_NOT_READY

    def _collect_validation_summary(
        self, kpi_values: KPIValues
    ) -> list[ValidationIssue]:
        """Collect all validation issues from individual KPIs.

        Parameters
        ----------
        kpi_values:
            Container with all 5 KPI values.

        Returns
        -------
        list[ValidationIssue]
            Combined list of all validation issues.
        """
        all_issues: list[ValidationIssue] = []

        for kpi in [
            kpi_values.production_total,
            kpi_values.collection_rate,
            kpi_values.new_patients,
            kpi_values.case_acceptance,
            kpi_values.hygiene_reappointment,
        ]:
            all_issues.extend(kpi.validation_issues)

        return all_issues
