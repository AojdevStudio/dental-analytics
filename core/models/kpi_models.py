# KPI data models for the decoupled analytics core.
"""Pydantic models describing KPI responses and validation metadata.

This module defines the strongly typed contracts shared across the new
backend core. The types remain framework-agnostic so they can be relied on by
pure calculation logic, service orchestration, and presentation layers.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Location = Literal["baytown", "humble"]


class DataAvailabilityStatus(str, Enum):
    """Enumerates the possible availability states for KPI calculations."""

    AVAILABLE = "available"
    EXPECTED_CLOSURE = "expected_closure"
    DATA_NOT_READY = "data_not_ready"
    PARTIAL = "partial"
    DATA_QUALITY_ISSUE = "data_quality_issue"
    INFRASTRUCTURE_ERROR = "infrastructure_error"


class ValidationSeverity(str, Enum):
    """Expresses how serious a validation finding is for a KPI result."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ValidationIssue(BaseModel):
    """Captures a single validation finding surfaced during KPI evaluation.

    Attributes
    ----------
    code:
        Machine-friendly identifier used to group similar validation events.
    message:
        Human-readable explanation of the issue that can be displayed in the UI.
    severity:
        Severity level that informs whether the KPI remains usable.
    """

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    severity: ValidationSeverity = Field(default=ValidationSeverity.WARNING)


class KPIValue(BaseModel):
    """Represents the computed value of a single KPI and its validation state."""

    value: float | int | None = Field(default=None)
    available: bool = Field(default=False)
    availability_status: DataAvailabilityStatus = Field(
        default=DataAvailabilityStatus.DATA_NOT_READY
    )
    unavailable_reason: str | None = None
    validation_issues: list[ValidationIssue] = Field(default_factory=list)

    @field_validator("validation_issues", mode="after")
    @classmethod
    def _ensure_unique_issue_codes(
        cls, issues: list[ValidationIssue]
    ) -> list[ValidationIssue]:
        """Ensure duplicate validation codes do not accumulate silently."""

        codes = [issue.code for issue in issues]
        if len(codes) != len(set(codes)):
            raise ValueError("Duplicate validation issue code detected")
        return issues


class KPIValues(BaseModel):
    """Container aggregating the standard KPI outputs for a practice location."""

    production_total: KPIValue
    collection_rate: KPIValue
    new_patients: KPIValue
    case_acceptance: KPIValue
    hygiene_reappointment: KPIValue


class DataFreshness(BaseModel):
    """Metadata describing how current data inputs are for each sheet consumed."""

    source_alias: str = Field(..., min_length=1)
    as_of: datetime
    retrieved_at: datetime
    timezone: str = Field(default="America/Chicago")

    @model_validator(mode="after")
    def _retrieved_at_not_before_as_of(self) -> DataFreshness:
        """Guarantee retrieval timestamps are not earlier than source timestamps."""

        if self.retrieved_at < self.as_of:
            raise ValueError("retrieved_at cannot be earlier than as_of")
        return self


class KPIResponse(BaseModel):
    """Top-level response object returned by the new KPI service."""

    location: Location
    business_date: date
    availability: DataAvailabilityStatus
    values: KPIValues
    data_freshness: list[DataFreshness] = Field(default_factory=list)
    closure_reason: str | None = None
    validation_summary: list[ValidationIssue] = Field(default_factory=list)

    @field_validator("validation_summary", mode="after")
    @classmethod
    def _validate_summary_items(
        cls, issues: list[ValidationIssue]
    ) -> list[ValidationIssue]:
        """Validation summary must contain meaningful, non-empty entries."""

        for issue in issues:
            if not issue.message.strip():
                raise ValueError("Validation summary entries require a message")
        return issues
