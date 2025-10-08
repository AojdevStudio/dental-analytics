# Story 3.21: Eliminate Dict Container Returns

## Status
Draft

## Story
**As a** developer maintaining strict Pydantic type safety,
**I want** all dict container returns replaced with Pydantic container models,
**so that** we have zero dict returns anywhere in the chart data pipeline and full type validation throughout.

## Story Context

**Migration Phase**: Phase 1 - TypedDict Elimination (Cleanup Story)
**Scope**: Eliminate remaining dict returns missed in Story 3.2
**Duration**: 1-2 hours (focused cleanup)

**Integration Points:**
- Requires: Story 3.2 complete (individual functions return Pydantic)
- Updates: apps/backend/chart_data.py, core/models/chart_models.py
- Blocks: Story 3.3 (test updates should work with pure Pydantic)

**Current State (Post-3.2):**
- Individual chart functions return Pydantic models ✅
- Container function `format_all_chart_data()` returns `dict[str, TimeSeriesData | ChartsMetadata]` ❌
- Validation functions accept `| dict[str, Any]` unions for backward compatibility ❌
- 3 remaining dict-related signatures in chart_data.py

**Target State (This Story):**
- `format_all_chart_data()` returns `AllChartsData` Pydantic model
- Validation functions accept ONLY Pydantic models (no dict unions)
- ZERO dict returns or dict unions in chart_data.py
- Full end-to-end Pydantic type safety

**Why This Story Exists:**
Story 3.2 AC was ambiguous: "All 10 chart processing functions return Pydantic models" didn't catch:
1. Container/aggregator functions returning dicts of Pydantic models
2. Validation functions accepting dict unions for backward compatibility

This story fixes the gap with explicit "no dict anywhere" enforcement.

## Acceptance Criteria

### **Container Model Creation (AC 1-3)**

1. ✅ Create `AllChartsData` Pydantic model in core/models/chart_models.py
2. ✅ Model contains typed fields for all 5 KPI charts + metadata
3. ✅ Model includes validation and serialization support

### **Function Signature Updates (AC 4-6)**

4. ✅ `format_all_chart_data()` return type: `dict[...]` → `AllChartsData`
5. ✅ `validate_chart_data()` parameter: remove `| dict[str, Any]` union
6. ✅ `validate_processed_chart_data()` parameter: remove `| dict[str, Any]` union

### **Implementation Updates (AC 7-9)**

7. ✅ `format_all_chart_data()` returns `AllChartsData(...)` instantiation
8. ✅ Validation functions use Pydantic-only validation logic
9. ✅ Remove all dict-handling branches from validation functions

### **Quality & Validation (AC 10-13)**

10. ✅ Zero matches for `grep "-> dict\[" apps/backend/chart_data.py`
11. ✅ Zero matches for `grep "| dict\[str, Any\]" apps/backend/chart_data.py`
12. ✅ MyPy type checking passes for chart_data.py and chart_models.py
13. ✅ All Ruff linting passes (zero warnings)

## Tasks / Subtasks

### **Create AllChartsData Container Model** (30 minutes) - AC: 1, 2, 3

- [ ] Add model to core/models/chart_models.py:
  ```python
  class AllChartsData(BaseModel):
      """Container for all chart data with metadata.

      Replaces dict[str, TimeSeriesData | ChartsMetadata] with
      strongly-typed Pydantic container model.
      """

      production_total: TimeSeriesData
      collection_rate: TimeSeriesData
      new_patients: TimeSeriesData
      case_acceptance: TimeSeriesData
      hygiene_reappointment: TimeSeriesData
      metadata: ChartsMetadata

      model_config = ConfigDict(
          frozen=False,
          validate_assignment=True,
          extra="forbid",
      )

      def to_dict(self) -> dict[str, TimeSeriesData | ChartsMetadata]:
          """Legacy compatibility: convert to dict format.

          Use for gradual migration of consumers.
          Will be removed in Phase 2.
          """
          return {
              "production_total": self.production_total,
              "collection_rate": self.collection_rate,
              "new_patients": self.new_patients,
              "case_acceptance": self.case_acceptance,
              "hygiene_reappointment": self.hygiene_reappointment,
              "metadata": self.metadata,
          }
  ```
- [ ] Run MyPy on chart_models.py:
  ```bash
  uv run mypy core/models/chart_models.py
  ```
  - [ ] Expect zero errors

### **Update format_all_chart_data()** (20 minutes) - AC: 4, 7

- [ ] Update function signature in apps/backend/chart_data.py:
  ```python
  # OLD
  def format_all_chart_data(
      eod_df: pd.DataFrame | None,
      front_kpi_df: pd.DataFrame | None,
      date_column: str = "Submission Date",
  ) -> dict[str, TimeSeriesData | ChartsMetadata]:

  # NEW
  def format_all_chart_data(
      eod_df: pd.DataFrame | None,
      front_kpi_df: pd.DataFrame | None,
      date_column: str = "Submission Date",
  ) -> AllChartsData:
  ```
- [ ] Update return statement:
  ```python
  # OLD
  chart_data: dict[str, TimeSeriesData | ChartsMetadata] = {
      "production_total": format_production_chart_data(eod_df, date_column),
      "collection_rate": format_collection_rate_chart_data(eod_df, date_column),
      "new_patients": format_new_patients_chart_data(eod_df, date_column),
      "case_acceptance": format_case_acceptance_chart_data(front_kpi_df, date_column),
      "hygiene_reappointment": format_hygiene_reappointment_chart_data(
          front_kpi_df, date_column
      ),
  }

  metadata = ChartsMetadata(...)
  chart_data["metadata"] = metadata

  return chart_data

  # NEW
  return AllChartsData(
      production_total=format_production_chart_data(eod_df, date_column),
      collection_rate=format_collection_rate_chart_data(eod_df, date_column),
      new_patients=format_new_patients_chart_data(eod_df, date_column),
      case_acceptance=format_case_acceptance_chart_data(front_kpi_df, date_column),
      hygiene_reappointment=format_hygiene_reappointment_chart_data(
          front_kpi_df, date_column
      ),
      metadata=ChartsMetadata(
          generated_at=datetime.now().isoformat(),
          data_sources=DataSourceInfo(
              eod_available=eod_df is not None and not eod_df.empty,
              front_kpi_available=front_kpi_df is not None and not front_kpi_df.empty,
          ),
          total_metrics=5,
      ),
  )
  ```
- [ ] Update import at top of file:
  ```python
  from core.models.chart_models import (
      AllChartsData,  # ← Add this
      ChartsMetadata,
      ChartDataPoint,
      # ... rest of imports
  )
  ```

### **Remove Dict Unions from Validation** (20 minutes) - AC: 5, 6, 8, 9

- [ ] Update `validate_chart_data()` signature:
  ```python
  # OLD
  def validate_chart_data(
      chart_data: TimeSeriesData | dict[str, Any]
  ) -> bool:

  # NEW
  def validate_chart_data(chart_data: TimeSeriesData) -> bool:
  ```
- [ ] Simplify validation logic:
  ```python
  # OLD
  try:
      # If we have a Pydantic model, it's already validated
      if isinstance(chart_data, TimeSeriesData):
          log.debug("chart_data.validation_passed", metric=chart_data.metric_name)
          return True

      TimeSeriesData.model_validate(chart_data)
      metric_name = (
          chart_data.get("metric_name")
          if isinstance(chart_data, dict)
          else None
      )
      log.warning("chart_data.dict_input_validated", metric=metric_name)
      return True
  except ValidationError as error:
      log.error("chart_data.validation_error", errors=error.errors())
      return False

  # NEW
  # Pydantic models are self-validating at instantiation
  # This function validates already-created instances
  try:
      log.debug("chart_data.validation_passed", metric=chart_data.metric_name)
      return True
  except AttributeError as error:
      log.error("chart_data.validation_error", error=str(error))
      return False
  ```
- [ ] Update `validate_processed_chart_data()` signature:
  ```python
  # OLD
  def validate_processed_chart_data(
      data: ProcessedChartData | dict[str, Any]
  ) -> bool:

  # NEW
  def validate_processed_chart_data(data: ProcessedChartData) -> bool:
  ```
- [ ] Simplify validation logic:
  ```python
  # OLD
  try:
      if isinstance(data, ProcessedChartData):
          log.debug("chart_data.validation_passed", metric_dates=len(data.dates))
          return True

      ProcessedChartData.model_validate(data)
      log.warning("chart_data.dict_input_validated")
      return True
  except ValidationError as error:
      log.error("chart_data.validation_error", errors=error.errors())
      return False

  # NEW
  try:
      log.debug("chart_data.validation_passed", metric_dates=len(data.dates))
      return True
  except AttributeError as error:
      log.error("chart_data.validation_error", error=str(error))
      return False
  ```

### **Update Consumers** (10 minutes)

- [ ] Check apps/frontend/app.py usage:
  ```bash
  grep -n "format_all_chart_data" apps/frontend/app.py
  ```
- [ ] Update dict access to Pydantic attribute access:
  ```python
  # OLD
  chart_data = format_all_chart_data(eod_df, front_df)
  if chart_data and "collection_rate" in chart_data:
      collection_chart = create_chart_from_data(
          chart_data["collection_rate"], show_trend=True
      )

  # NEW
  chart_data = format_all_chart_data(eod_df, front_df)
  if chart_data and chart_data.collection_rate:
      collection_chart = create_chart_from_data(
          chart_data.collection_rate, show_trend=True
      )
  ```
- [ ] Update all 5 KPI access patterns (production, collection_rate, new_patients, case_acceptance, hygiene_reappointment)

### **Quality Gates & Validation** (10 minutes) - AC: 10, 11, 12, 13

- [ ] Verify zero dict returns:
  ```bash
  grep -n "-> dict\[" apps/backend/chart_data.py
  ```
  - [ ] Expected: ZERO matches
- [ ] Verify zero dict unions:
  ```bash
  grep -n "| dict\[str, Any\]" apps/backend/chart_data.py
  ```
  - [ ] Expected: ZERO matches
- [ ] Run MyPy validation:
  ```bash
  uv run mypy apps/backend/chart_data.py core/models/chart_models.py apps/frontend/app.py
  ```
  - [ ] Expect zero errors
- [ ] Run Ruff linting:
  ```bash
  uv run ruff check apps/backend/chart_data.py core/models/chart_models.py apps/frontend/app.py
  ```
  - [ ] Expect zero warnings
- [ ] Run Black formatting:
  ```bash
  uv run black apps/backend/chart_data.py core/models/chart_models.py apps/frontend/app.py
  ```
- [ ] Commit changes:
  ```bash
  git add core/models/chart_models.py apps/backend/chart_data.py apps/frontend/app.py
  git commit -m "refactor: eliminate dict container returns (Story 3.21)

  - Add AllChartsData Pydantic container model
  - Update format_all_chart_data() to return AllChartsData
  - Remove | dict[str, Any] unions from validation functions
  - Update app.py to use Pydantic attribute access
  - Zero dict returns or unions in chart_data.py

  BREAKING: format_all_chart_data() now returns AllChartsData model
  Migration: Use .to_dict() method for legacy dict access

  Refs: Story 3.21, Phase 1 TypedDict Elimination Cleanup"
  ```

## Dev Notes

**Why This Story Exists:**

Story 3.2 AC 2 said: "All 10 chart processing functions return Pydantic models"

We interpreted this as the 10 individual processor functions (format_production_chart_data, etc.), which we successfully migrated. But we missed:

1. **Container functions** returning `dict[str, BaseModel]`
2. **Validation functions** accepting `BaseModel | dict[str, Any]` unions

This story closes that gap with explicit "no dict anywhere" enforcement.

**Pattern: Pydantic Container Models**

```python
# ❌ ANTI-PATTERN: Dict of Pydantic models
def get_all_data() -> dict[str, TimeSeriesData]:
    return {
        "metric1": TimeSeriesData(...),
        "metric2": TimeSeriesData(...),
    }

# ✅ PATTERN: Pydantic container model
class AllData(BaseModel):
    metric1: TimeSeriesData
    metric2: TimeSeriesData

def get_all_data() -> AllData:
    return AllData(
        metric1=TimeSeriesData(...),
        metric2=TimeSeriesData(...),
    )
```

**Benefits:**
- Full type safety (MyPy catches field access errors)
- IDE autocomplete for all fields
- Runtime validation of container structure
- Pydantic serialization/deserialization
- No more `dict.get()` or `KeyError` risks

**Migration Path for Consumers:**

For gradual migration, `AllChartsData.to_dict()` provides temporary dict access:

```python
# Immediate migration (preferred)
charts = format_all_chart_data(eod_df, front_df)
prod_chart = create_chart_from_data(charts.production_total)

# Gradual migration (temporary)
charts = format_all_chart_data(eod_df, front_df)
chart_dict = charts.to_dict()  # Legacy dict access
prod_chart = create_chart_from_data(chart_dict["production_total"])
```

`.to_dict()` method will be removed in Phase 2.

**Files Modified:**
```
core/models/
├── chart_models.py        # ADD: AllChartsData model

apps/backend/
├── chart_data.py          # MODIFY: format_all_chart_data() return type
                           # MODIFY: Remove dict unions from validation

apps/frontend/
├── app.py                 # MODIFY: Dict access → Pydantic attribute access
```

**Grep Audit Commands:**

```bash
# Verify zero dict returns
grep -n "-> dict\[" apps/backend/chart_data.py

# Verify zero dict unions
grep -n "| dict\[str, Any\]" apps/backend/chart_data.py

# Both should return: ZERO matches
```

## Testing

**Test Updates (Story 3.3 Scope):**
- Update tests to expect `AllChartsData` model instead of dict
- Update validation function tests to remove dict input tests
- Add tests for `AllChartsData.to_dict()` migration helper

**Manual Validation (This Story):**
```bash
# Type checking must pass
uv run mypy apps/backend/chart_data.py core/models/chart_models.py

# Linting must pass
uv run ruff check apps/backend/chart_data.py core/models/chart_models.py

# Dashboard should still load
uv run streamlit run apps/frontend/app.py
```

## Technical Notes

**Story Sequence Context:**
- Story 3.1: ✅ Create Pydantic models
- Story 3.2: ✅ Migrate individual functions to Pydantic
- Story 3.21: 🏗️ Eliminate remaining dict containers (this story)
- Story 3.3: Update tests, delete TypedDicts

**Breaking Change:**
`format_all_chart_data()` return type changes from `dict` to `AllChartsData`.

**Migration:**
```python
# Before (dict access)
charts = format_all_chart_data(...)
if "production_total" in charts:
    data = charts["production_total"]

# After (Pydantic access)
charts = format_all_chart_data(...)
if charts.production_total:
    data = charts.production_total
```

**Validation Function Changes:**
- `validate_chart_data()`: Now Pydantic-only (no dict validation)
- `validate_processed_chart_data()`: Now Pydantic-only

Tests passing dict inputs will fail (expected, fixed in Story 3.3).

## Definition of Done

**Model Creation:**
- [ ] `AllChartsData` model created in core/models/chart_models.py
- [ ] Model has all 5 KPI fields + metadata field
- [ ] Model includes `.to_dict()` migration helper

**Function Updates:**
- [ ] `format_all_chart_data()` returns `AllChartsData` (not dict)
- [ ] Validation functions accept only Pydantic models (no dict unions)
- [ ] All dict-handling logic removed from validation functions

**Consumer Updates:**
- [ ] apps/frontend/app.py uses Pydantic attribute access
- [ ] All 5 KPI charts accessed via attributes (not dict keys)

**Quality Gates:**
- [ ] Zero matches: `grep "-> dict\[" apps/backend/chart_data.py`
- [ ] Zero matches: `grep "| dict\[str, Any\]" apps/backend/chart_data.py`
- [ ] MyPy passes for all modified files
- [ ] Ruff passes for all modified files
- [ ] Black formatting applied

**Documentation:**
- [ ] Story committed with clear breaking change notice
- [ ] Migration guide included in commit message

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2025-10-08 | 1.0 | Story creation to eliminate dict container returns | James (Dev Agent) |

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
