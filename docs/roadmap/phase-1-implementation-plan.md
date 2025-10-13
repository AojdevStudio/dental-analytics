<!-- v1.0 | 2025-10-02 -->
# Phase 1 Implementation Plan: TypedDict Elimination

## Objectives
- Replace every `TypedDict` usage with the existing Pydantic contracts.
- Collapse `apps/backend/types.py` without breaking KPI service behavior.
- Capture regression notes so future you remembers validation scope.

## Shared Data Structure
Phase 1 standardizes all KPI payloads around `core.models.kpi_models`. The
primary objects reused across the migration are:

```python
from core.models.kpi_models import (
    KPIResponse,
    KPIValues,
    KPIValue,
    CalculationResult,
    DataAvailabilityStatus,
    ValidationIssue,
)
```

- `KPIResponse`: service-level contract returned to presentation layers.
- `KPIValues`: grouped KPI bundle that replaces legacy `TypedDict` aggregates.
- `KPIValue` / `CalculationResult`: building blocks for metric-level payloads and
  calculator outputs.
- `ValidationIssue` / `DataAvailabilityStatus`: shared enums referenced by both
  services and UI adapters.

All call sites must source types from this module so there is a single source of
truth once `types.py` is removed.

## Implementation Order
1. **Audit consumers**
   - Run `rg "apps/backend/types"` to list every import.
   - Classify each usage (service layer, Streamlit adapters, tests) and note
     the replacement Pydantic model.
2. **Update core/service dependencies**
   - Refactor `apps/backend/metrics.py` to import `KPIResponse` and related
     models, adapting function signatures as needed.
   - Adjust calculators/services expecting `TypedDict` inputs to accept the new
     Pydantic models.
3. **Migrate presentation & integration points**
   - Update Streamlit/back-end adapters, CLI scripts, and fixtures to instantiate
     or parse `KPIResponse` objects.
   - Replace any dictionary literals with `.model_dump()` outputs when raw
     dicts are required.
4. **Retire legacy definitions**
   - Delete `apps/backend/types.py` and remove its entry from `__all__` exports
     or import blocks.
   - Ensure no remaining `TypedDict` references exist in the repository.
5. **Regression & documentation**
   - Run `./scripts/quick-test.sh`, `uv run pytest`, and lint/type checks.
   - Record regression comparisons, test outcomes, and any manual KPI checks in
     personal notes before closing the phase.

## Deliverables & Exit Criteria
- No repository references to `apps/backend/types.py` or `TypedDict`.
- KPI service and adapters rely exclusively on `core.models.kpi_models`.
- Automated quality gates green; manual KPI sanity checks logged for future
  reference.
- Personal regression checklist updated with findings, screenshots, and data
  snapshots.
