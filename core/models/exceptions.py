# Custom exception hierarchy for KPI core models.
"""Domain-specific exceptions thrown by the KPI core models and validators."""

from __future__ import annotations


class KPIModelError(Exception):
    """Base class for all KPI model related errors."""


class DataMappingError(KPIModelError):
    """Raised when external data cannot be mapped into KPI models safely."""


class ValidationRuleError(KPIModelError):
    """Raised when validation rules produce inconsistent or fatal results."""
