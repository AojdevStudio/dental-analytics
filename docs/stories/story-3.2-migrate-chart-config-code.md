# Story 3.2: Migrate Chart & Config Code to Pydantic

## Status
Draft

## Story
**As a** developer maintaining the dental analytics backend,
**I want** all chart data processing and configuration code migrated from TypedDict to Pydantic models,
**so that** I have runtime validation throughout the data pipeline and eliminate the dual type system.

## Story Context

**Migration Phase**: Phase 1 - TypedDict Elimination (Story 2 of 3)
**Scope**: Update apps/backend/ files to use Pydantic models from Story 3.1
**Duration**: 5-6 hours (includes refactoring metrics.py to clean wrapper)

**Integration Points:**
- Requires: Story 3.1 complete (Pydantic models exist)
- Updates: apps/backend/chart_data.py, data_providers.py, metrics.py
- Prepares: Story 3.3 for final cleanup and TypedDict deletion

**Current State:**
- apps/backend/chart_data.py uses TypedDict return types (10 functions)
- apps/backend/data_providers.py uses TypedDict for configuration
- apps/backend/metrics.py acts as facade (~500+ lines)
- All imports reference apps.backend.types TypedDicts

**Target State (This Story):**
- chart_data.py returns Pydantic models (ProcessedChartData, etc.)
- data_providers.py uses Pydantic config models (SheetsConfig, etc.)
- metrics.py simplified to ~50 lines (clean Pydantic wrapper)
- Zero imports from apps.backend.types for chart/config TypedDicts

**Deferred to Story 3.3:**
- Delete chart/config TypedDicts from types.py
- Update all test files
- Final validation and documentation

## Acceptance Criteria

### **Chart Data Migration (AC 1-6)**

1. ✅ apps/backend/chart_data.py imports updated to use core.models.chart_models
2. ✅ All 10 chart processing functions return Pydantic models (not TypedDicts)
3. ✅ Dictionary return statements converted to Pydantic model instantiation
4. ✅ Error handling returns Pydantic models with error fields populated
5. ✅ No imports from apps.backend.types for chart TypedDicts
6. ✅ MyPy type checking passes for chart_data.py

### **Data Provider Migration (AC 7-10)**

7. ✅ apps/backend/data_providers.py imports updated to use core.models.config_models
8. ✅ SheetsProvider constructor accepts DataProviderConfig (Pydantic)
9. ✅ Configuration handling uses LocationSettings and SheetsConfig models
10. ✅ MyPy type checking passes for data_providers.py

### **Metrics Refactoring (AC 11-16)**

11. ✅ apps/backend/metrics.py simplified to ~50-100 lines (clean wrapper)
12. ✅ All legacy calculation functions deleted (NO deprecated code)
13. ✅ Only 2 functions remain: get_kpi_service() and get_all_kpis()
14. ✅ get_all_kpis() calls KPIService and returns KPIResponse (Pydantic)
15. ✅ Zero duplicate calculation logic (all in core/)
16. ✅ MyPy type checking passes for metrics.py

### **Quality & Validation (AC 17-20)**

17. ✅ All Ruff linting passes for modified files (zero warnings)
18. ✅ Black formatting applied to all modified files
19. ✅ No broken imports or circular dependencies
20. ✅ Ready for Story 3.3 (test updates and TypedDict deletion)

## Tasks / Subtasks

### **Pre-Migration Validation** (15 minutes) - AC: 19

- [ ] Verify Story 3.1 complete:
  ```bash
  ls core/models/chart_models.py core/models/config_models.py
  ```
  - [ ] Both files exist
  - [ ] Unit tests passing
- [ ] Create feature branch (if not continuing from 3.1):
  ```bash
  git checkout feature/phase-1-pydantic-models
  ```
- [ ] List files to modify:
  ```bash
  grep -l "from apps.backend.types import.*Chart\|Config\|Sheet" apps/backend/*.py
  ```
  - [ ] Expected: chart_data.py, data_providers.py, metrics.py
- [ ] Backup current metrics.py for side-by-side validation

### **Update chart_data.py** (3 hours) - AC: 1, 2, 3, 4, 5, 6

- [ ] Update imports:
  ```python
  # OLD
  from apps.backend.types import ChartData, ChartStatistics, ChartMetadata

  # NEW
  from core.models.chart_models import ProcessedChartData, ChartStats, ChartMetaInfo
  ```
- [ ] Update `process_production_data_for_chart()`:
  - [ ] Change return type: `ChartData` → `ProcessedChartData`
  - [ ] Replace dictionary return with:
    ```python
    return ProcessedChartData(
        dates=dates,
        values=values,
        statistics=ChartStats(total=..., average=..., ...),
        metadata=ChartMetaInfo(date_column=..., date_range=..., error=None),
        error=None,
    )
    ```
  - [ ] Update error handling to return ProcessedChartData with error field
- [ ] Update `process_collection_rate_data_for_chart()`:
  - [ ] Same pattern as production (TypedDict → Pydantic)
- [ ] Update `process_new_patients_data_for_chart()`:
  - [ ] Same pattern
- [ ] Update `process_case_acceptance_data_for_chart()`:
  - [ ] Same pattern
- [ ] Update `process_hygiene_reappointment_data_for_chart()`:
  - [ ] Same pattern
- [ ] Update `aggregate_to_weekly()`:
  - [ ] Parameter type: `ChartData` → `ProcessedChartData`
  - [ ] Return type: `ChartData` → `ProcessedChartData`
- [ ] Update `aggregate_to_monthly()`:
  - [ ] Same pattern as aggregate_to_weekly
- [ ] Update `filter_data_by_date_range()`:
  - [ ] Same pattern
- [ ] Update `create_empty_chart_data()`:
  - [ ] Return `ProcessedChartData` with empty lists
- [ ] Update `validate_processed_chart_data()`:
  - [ ] Parameter type: `ChartData` → `ProcessedChartData`
  - [ ] Use Pydantic validation instead of manual checks
- [ ] Run MyPy validation:
  ```bash
  uv run mypy apps/backend/chart_data.py
  ```
  - [ ] Expect zero errors

### **Update data_providers.py** (1 hour) - AC: 7, 8, 9, 10

- [ ] Update imports:
  ```python
  # OLD
  from apps.backend.types import SheetConfig, LocationConfig, ProviderConfig

  # NEW
  from core.models.config_models import SheetsConfig, LocationSettings, DataProviderConfig
  ```
- [ ] Update `SheetsProvider` class:
  - [ ] Constructor parameter: `ProviderConfig` → `DataProviderConfig`
  - [ ] Update type hints for all config-related attributes
- [ ] Update `build_sheets_provider()` function:
  - [ ] Return type annotation: DataProviderConfig usage
  - [ ] Pydantic model instantiation for configuration
- [ ] Test imports work:
  ```bash
  python -c "from apps.backend.data_providers import SheetsProvider"
  ```
  - [ ] Expect no import errors
- [ ] Run MyPy validation:
  ```bash
  uv run mypy apps/backend/data_providers.py
  ```
  - [ ] Expect zero errors

### **Refactor metrics.py to Clean Wrapper** (2 hours) - AC: 11, 12, 13, 14, 15, 16

- [ ] **CRITICAL DECISION**: Delete legacy calculation code, keep ONLY wrapper functions
- [ ] Create new metrics.py structure:
  ```python
  """Simplified metrics module - pure Pydantic wrapper.

  This module provides a simplified interface to the KPI service layer.
  All business logic has been moved to core/ for framework independence.

  Migrated: Phase 1 - TypedDict Elimination
  """
  from datetime import date

  from core.models.kpi_models import KPIResponse, Location
  from services.kpi_service import KPIService
  from core.business_rules.calendar import BusinessCalendar
  from core.business_rules.validation_rules import KPIValidationRules
  from core.transformers.sheets_transformer import SheetsToKPIInputs
  from apps.backend.data_providers import build_sheets_provider


  # Singleton service instance
  _kpi_service: KPIService | None = None


  def get_kpi_service() -> KPIService:
      """Get or create the singleton KPI service instance."""
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

      Args:
          location: Practice location ("baytown" or "humble")
          target_date: Date to calculate KPIs for (defaults to today)

      Returns:
          KPIResponse with all KPI values and validation metadata
      """
      service = get_kpi_service()
      if target_date is None:
          target_date = date.today()
      return service.get_kpis(location, target_date)
  ```
- [ ] **Delete** all legacy functions:
  - [ ] Individual KPI calculation helpers (keep in core/)
  - [ ] Data transformation logic (now in core/transformers/)
  - [ ] TypedDict conversion helpers (no longer needed)
  - [ ] Duplicate validation logic (now in core/business_rules/)
- [ ] Verify metrics.py is ~50-100 lines total (target: ~50)
- [ ] Run MyPy validation:
  ```bash
  uv run mypy apps/backend/metrics.py
  ```
  - [ ] Expect zero errors

### **Quality Gates & Validation** (30 minutes) - AC: 17, 18, 19, 20

- [ ] Run Ruff on all modified files:
  ```bash
  uv run ruff check apps/backend/chart_data.py apps/backend/data_providers.py apps/backend/metrics.py
  ```
  - [ ] Expect zero warnings
- [ ] Run Black formatting:
  ```bash
  uv run black apps/backend/chart_data.py apps/backend/data_providers.py apps/backend/metrics.py
  ```
- [ ] Check for circular dependencies:
  ```bash
  python -c "from apps.backend.metrics import get_all_kpis; from apps.backend.chart_data import process_production_data_for_chart"
  ```
  - [ ] Expect no import errors
- [ ] Verify no chart/config TypedDict imports remain:
  ```bash
  grep "from apps.backend.types import.*Chart\|Config\|Sheet" apps/backend/chart_data.py apps/backend/data_providers.py apps/backend/metrics.py
  ```
  - [ ] Expect empty output
- [ ] Commit changes:
  ```bash
  git add apps/backend/chart_data.py apps/backend/data_providers.py apps/backend/metrics.py
  git commit -m "refactor: migrate chart/config code to Pydantic models

  - Update chart_data.py to return Pydantic models
  - Update data_providers.py to use Pydantic config models
  - Simplify metrics.py to clean wrapper (~50 lines)
  - Delete all legacy calculation/transformation code
  - Zero imports from apps.backend.types for chart/config

  Refs: Story 3.2, Phase 1 TypedDict Elimination"
  ```

## Dev Notes

**Source Tree Changes (Story 3.2 Modifies):**

```
apps/backend/
├── chart_data.py          # MODIFIED - Pydantic returns
├── data_providers.py      # MODIFIED - Pydantic config
├── metrics.py             # REFACTORED - Clean wrapper (~50 lines)
├── historical_data.py     # UNCHANGED (Phase 3 scope)
└── types.py               # UNCHANGED (Story 3.3 deletes TypedDicts)

core/models/
├── chart_models.py        # Story 3.1 - Used by chart_data.py
└── config_models.py       # Story 3.1 - Used by data_providers.py
```

**Migration Patterns from Spec:**

**Pattern 1: Update Function Signatures**
```python
# OLD
def process_production_data_for_chart(df: pd.DataFrame) -> ChartData:
    ...

# NEW
def process_production_data_for_chart(df: pd.DataFrame) -> ProcessedChartData:
    ...
```
[Source: specs/phase-1-typeddict-elimination.md, Step 3]

**Pattern 2: Convert Return Statements**
```python
# OLD
return {
    "dates": dates,
    "values": values,
    "statistics": {
        "total": total,
        "average": avg,
        ...
    },
    "metadata": {...},
    "error": None,
}

# NEW
return ProcessedChartData(
    dates=dates,
    values=values,
    statistics=ChartStats(
        total=total,
        average=avg,
        ...
    ),
    metadata=ChartMetaInfo(...),
    error=None,
)
```
[Source: specs/phase-1-typeddict-elimination.md, Step 3]

**Pattern 3: Update Error Handling**
```python
# OLD
except Exception as e:
    return {
        "dates": [],
        "values": [],
        "statistics": {...},
        "metadata": {..., "error": str(e)},
        "error": str(e),
    }

# NEW
except Exception as e:
    return ProcessedChartData(
        dates=[],
        values=[],
        statistics=ChartStats(),
        metadata=ChartMetaInfo(
            date_column="",
            date_range="No data",
            error=str(e),
        ),
        error=str(e),
    )
```
[Source: specs/phase-1-typeddict-elimination.md, Step 3]

**Functions to Update (10 chart functions):**
- `process_production_data_for_chart()`
- `process_collection_rate_data_for_chart()`
- `process_new_patients_data_for_chart()`
- `process_case_acceptance_data_for_chart()`
- `process_hygiene_reappointment_data_for_chart()`
- `aggregate_to_weekly()`
- `aggregate_to_monthly()`
- `filter_data_by_date_range()`
- `create_empty_chart_data()`
- `validate_processed_chart_data()`

[Source: specs/phase-1-typeddict-elimination.md, Section: Implementation Steps, Step 3]

**Metrics.py Clean Wrapper Pattern:**

**Target Implementation** (~50 lines total):
```python
# Singleton service instance
_kpi_service: KPIService | None = None

def get_kpi_service() -> KPIService:
    """Get or create the singleton KPI service instance."""
    # ... (singleton pattern)

def get_all_kpis(location: Location, target_date: date | None = None) -> KPIResponse:
    """Get all KPIs for a location on a specific date."""
    service = get_kpi_service()
    return service.get_kpis(location, target_date or date.today())
```

**Delete Everything Else:**
- Legacy data transformation functions
- Duplicate calculation logic
- TypedDict conversion helpers
- Individual KPI accessor functions

[Source: specs/phase-1-typeddict-elimination.md, Step 5]

**Key Migration Constraints:**

1. **NO Deprecated Functions**:
   - Clean break - delete legacy code immediately
   - No `@deprecated` wrappers
   - No backward compatibility shims
   - Direct migration to Pydantic API

2. **NO Partial Updates**:
   - Update entire file at once (all functions in chart_data.py)
   - Don't mix TypedDict and Pydantic returns in same file
   - Commit complete file migrations

3. **Import Organization**:
   - Group by source: stdlib, third-party, local core, local apps
   - Modern typing (dict[], list[], not typing.Dict)
   - Explicit imports (no `import *`)

[Source: specs/phase-1-typeddict-elimination.md, Section: Architecture Decisions]

**Configuration Migration Details:**

**data_providers.py Pydantic Usage:**
```python
# NEW imports
from core.models.config_models import SheetsConfig, LocationSettings, DataProviderConfig

# NEW constructor
class SheetsProvider:
    def __init__(self, config: DataProviderConfig):
        self.config = config
        # Access nested Pydantic models
        baytown_eod: SheetsConfig = config.locations["baytown"].eod_sheet
```

[Source: specs/phase-1-typeddict-elimination.md, Step 4]

### Testing

**Testing Strategy for Story 3.2:**

⚠️ **IMPORTANT**: Story 3.2 does NOT update test files.

**Tests Updated in Story 3.3:**
- `tests/test_chart_data.py` - Dictionary access → Pydantic attribute access
- `tests/test_metrics.py` - Verify simplified wrapper
- `tests/test_data_sources.py` - Pydantic config validation

**Manual Validation (This Story):**
1. Run existing tests (expect failures - known, acceptable)
2. Verify imports work without errors
3. Verify MyPy type checking passes
4. Verify Ruff linting passes

**Acceptance**:
- Test failures expected and documented
- Story 3.3 will fix all test failures
- Focus on code migration quality, not test passing

[Source: specs/phase-1-typeddict-elimination.md, Step 6]

**Quality Tools Validation:**

```bash
# Type checking (must pass in Story 3.2)
uv run mypy apps/backend/chart_data.py apps/backend/data_providers.py apps/backend/metrics.py

# Linting (must pass in Story 3.2)
uv run ruff check apps/backend/chart_data.py apps/backend/data_providers.py apps/backend/metrics.py

# Formatting (apply in Story 3.2)
uv run black apps/backend/chart_data.py apps/backend/data_providers.py apps/backend/metrics.py

# Tests (failures expected - Story 3.3 fixes)
uv run pytest tests/test_chart_data.py tests/test_metrics.py -v
```

[Source: docs/architecture/backend/code-quality-standards.md]

## Technical Notes

**Phase 1 Story Sequence:**
- Story 3.1: ✅ Create Pydantic models (complete)
- Story 3.2: 🏗️ Migrate code to use models (this story)
- Story 3.3: Update tests, delete TypedDicts, final cleanup

**Story 3.2 Focus:**
- Code migration only
- MyPy/Ruff must pass
- Test failures acceptable (fixed in 3.3)
- No TypedDict deletion yet (deferred to 3.3)

**Dependencies:**
- Requires: Story 3.1 (Pydantic models exist)
- Blocks: Story 3.3 (tests need migrated code)
- Follows: Story 3.0 Pydantic patterns

**Risk Mitigation:**
- Commit each file migration separately (rollback granularity)
- Keep backup of original metrics.py for validation
- Document expected test failures for Story 3.3

## Definition of Done

**Code Migration Complete:**
- [x] chart_data.py migrated to Pydantic returns (10 functions)
- [x] data_providers.py uses Pydantic config models
- [x] metrics.py simplified to ~50-100 line wrapper
- [x] All legacy calculation code deleted from metrics.py

**Quality Gates:**
- [x] MyPy passes for all modified files (zero errors)
- [x] Ruff passes for all modified files (zero warnings)
- [x] Black formatting applied
- [x] No circular import errors

**Import Validation:**
- [x] Zero imports from apps.backend.types for chart/config
- [x] All Pydantic imports from core.models.*
- [x] No broken imports or missing modules

**Readiness:**
- [x] Story 3.3 can proceed (test updates)
- [x] Code committed with clear message
- [x] Known test failures documented

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2025-10-02 | 1.0 | Initial story creation for Phase 1 code migration | Bob (Scrum Master) |

## Dev Agent Record

### Agent Model Used
_To be populated during implementation_

### Debug Log References
_To be populated during implementation_

### Completion Notes List
_To be populated during implementation_

### File List
_To be populated during implementation_

## QA Results
_To be populated after QA review_
