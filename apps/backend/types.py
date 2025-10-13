"""Legacy TypedDict definitions - Phase 3 Migration Target.

⚠️ MIGRATION STATUS: Phase 1 Complete (Story 3.3)
- All chart and config TypedDicts deleted and replaced with Pydantic models
- Only historical data TypedDicts remain (Phase 3 target)

📍 PHASE 3 TODO:
- Migrate historical_data.py to use Pydantic models
- Delete these 4 remaining TypedDicts
- Remove this file entirely

Created: 2025-01-30
Last Updated: 2025-10-13 (Story 3.3 - Phase 1 cleanup)
Remaining: 4 TypedDicts (was 18)
"""

from __future__ import annotations

from typing import TypedDict

# =============================================================================
# HISTORICAL DATA STRUCTURES - PHASE 3 MIGRATION TARGET
# =============================================================================


class HistoricalProductionData(TypedDict):
    """Historical production data for trend analysis.

    ⚠️ PHASE 3: Replace with Pydantic model in core/models/historical_models.py

    Used by: apps/backend/historical_data.py
    Purpose: Time-series aggregation of production metrics

    Migration Target: HistoricalProductionModel (Pydantic)
    """

    dates: list[str]  # ["2025-01-01", "2025-01-02", ...]
    values: list[float]  # [15000.0, 16000.0, ...]
    total: float  # Sum of all values
    average: float  # Mean of all values
    trend: str  # "increasing" | "decreasing" | "stable"
    period_label: str  # "Last 30 Days" | "This Month" | etc.


class HistoricalRateData(TypedDict):
    """Historical rate data (percentages) for trend analysis.

    ⚠️ PHASE 3: Replace with Pydantic model in core/models/historical_models.py

    Used by: apps/backend/historical_data.py
    Purpose: Time-series aggregation of rate-based KPIs (collection rate, etc.)

    Migration Target: HistoricalRateModel (Pydantic)
    """

    dates: list[str]  # ["2025-01-01", "2025-01-02", ...]
    values: list[float]  # [92.5, 93.0, ...]
    average: float  # Mean rate across period
    trend: str  # "improving" | "declining" | "stable"
    period_label: str  # "Last 30 Days" | "This Month" | etc.
    target_rate: float | None  # Goal rate for comparison (e.g., 90.0)


class HistoricalCountData(TypedDict):
    """Historical count data (integers) for trend analysis.

    ⚠️ PHASE 3: Replace with Pydantic model in core/models/historical_models.py

    Used by: apps/backend/historical_data.py
    Purpose: Time-series aggregation of count-based KPIs (new patients, etc.)

    Migration Target: HistoricalCountModel (Pydantic)
    """

    dates: list[str]  # ["2025-01-01", "2025-01-02", ...]
    values: list[int]  # [12, 15, ...]
    total: int  # Sum of all counts
    average: float  # Mean count across period
    trend: str  # "increasing" | "decreasing" | "stable"
    period_label: str  # "Last 30 Days" | "This Month" | etc.


class HistoricalKPIData(TypedDict):
    """Container for all historical KPI data structures.

    ⚠️ PHASE 3: Replace with Pydantic model in core/models/historical_models.py

    Used by: apps/backend/historical_data.py
    Purpose: Unified response for historical KPI queries

    Migration Target: HistoricalKPIResponse (Pydantic)
    """

    production: HistoricalProductionData
    collection_rate: HistoricalRateData
    new_patients: HistoricalCountData
    case_acceptance: HistoricalRateData
    hygiene_reappointment: HistoricalRateData
    location: str  # "baytown" | "humble"
    date_range: dict[str, str]  # {"start": "2025-01-01", "end": "2025-01-30"}
