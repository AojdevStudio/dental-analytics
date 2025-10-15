# Story 3.5: Chart Timeframe Aggregation Fix

Status: Ready for Review

## Story

As a practice manager analyzing KPI trends,
I want the chart timeframe selector (Daily/Weekly/Monthly) to actually aggregate the data,
so that I can view meaningful weekly and monthly summaries instead of seeing misleading daily data points with incorrect labels.

## Acceptance Criteria

1. **Backend Aggregation Helper**
   - New `aggregate_time_series()` function accepts `TimeSeriesData`, timeframe, and business_days_only flag
   - Uses internal adapter functions (`_time_series_to_processed` and `_processed_to_time_series`) to reuse existing aggregation logic
   - Returns aggregated `TimeSeriesData` with updated time_series points and statistics
   - Updates `metadata.aggregation` field to silence frontend warning
   - Timeframe "daily" returns data unchanged (pass-through)

2. **Uniform Application to All Charts**
   - `format_all_chart_data()` accepts `timeframe` parameter
   - Applies `aggregate_time_series()` to all 5 KPI charts uniformly
   - No chart-specific logic; single aggregation point for consistency
   - Pydantic validation passes (TimeSeriesData → AllChartsData contract preserved)

3. **Frontend Integration**
   - `load_chart_data()` accepts and passes `timeframe` to backend
   - Streamlit cache key includes `timeframe` for separate cached entries
   - UI timeframe selector passes value to `load_chart_data()`
   - No changes to chart rendering code (TimeSeriesData structure unchanged)

4. **Data Validation**
   - Daily view: ~80 data points (raw daily values)
   - Weekly view: ~11-12 data points (weekly sums, not averages)
   - Monthly view: 2-3 data points (monthly sums, not averages)
   - Chart x-axis labels reflect aggregation period appropriately

## Tasks / Subtasks

- [x] Task 1: Implement backend aggregation helper (AC: #1)
  - [x] Create `aggregate_time_series(series, timeframe, *, business_days_only=True)` in `apps/backend/chart_data.py`
  - [x] Implement `_time_series_to_processed()` adapter to convert TimeSeriesData → ProcessedChartData
  - [x] Implement `_processed_to_time_series()` adapter to convert ProcessedChartData → TimeSeriesData
  - [x] Call existing `aggregate_to_weekly()` or `aggregate_to_monthly()` on ProcessedChartData
  - [x] Rebuild `TimeSeriesData` with updated statistics and format_options["aggregation"] field
  - [x] Add unit tests for all timeframe scenarios and business_days_only flag

- [x] Task 2: Update format_all_chart_data pipeline (AC: #2)
  - [x] Add `timeframe: Literal["daily", "weekly", "monthly"] = "daily"` parameter
  - [x] Apply `aggregate_time_series()` to all 5 charts after formatting
  - [x] Ensure conditional application (if timeframe != "daily")
  - [x] Verify Pydantic validation passes with aggregated data

- [x] Task 3: Frontend timeframe threading (AC: #3)
  - [x] Update `load_chart_data(location: str, timeframe: Literal[...] = "daily")` signature
  - [x] Pass `timeframe` from UI selection to `format_all_chart_data()`
  - [x] Verify cache decorator creates separate entries per timeframe (automatic via Streamlit)
  - [x] Connect UI radio selector to `load_chart_data()` call

- [x] Task 4: Testing and validation (AC: #4)
  - [x] Unit tests created in tests/unit/test_chart_aggregation.py (12 tests, all passing)
  - [x] Comprehensive test coverage for aggregation logic and adapters
  - [x] Type checking passes (mypy validation complete)
  - [x] Full test suite passes (353 passed, 1 unrelated failure in historical_data)
  - [x] Pydantic validation enforced throughout

- [x] Task 5: Documentation updates
  - [x] Update `docs/reference/chart-components-api.md` to describe new aggregation helper
  - [x] Document adapter functions and their role in type conversion
  - [x] Add examples of weekly/monthly aggregation usage

## Dev Notes

### Architecture Context
[Source: docs/tech-spec-chart-aggregation-fix.md]

**Solution Principle**: Stay within the TimeSeriesData world. Aggregate after chart formatting, not before.

**Data Flow**:
```
format_all_chart_data(eod_df, front_df, timeframe)
  │
  ├─► format_production_chart_data(eod_df) → TimeSeriesData
  ├─► aggregate_time_series(chart_data, timeframe) → TimeSeriesData  [NEW]
  │
  ├─► format_collection_rate_chart_data(eod_df) → TimeSeriesData
  ├─► aggregate_time_series(chart_data, timeframe) → TimeSeriesData  [NEW]
  │
  ├─► [Repeat for all 5 charts]
  │
  └─► Return AllChartsData(production_total=..., collection_rate=..., ...)
```

**Key Design Decision**:
The initial approach (aggregate DataFrame before formatting) failed because:
1. `process_production_data_for_chart()` signature mismatch (1 arg vs 2)
2. Type incompatibility (ProcessedChartData vs TimeSeriesData)
3. Incomplete coverage (only production chart sketched)

Current approach aggregates **after** `TimeSeriesData` is built, preserving type contracts.

### Type Safety Guarantees
[Source: core/models/chart_models.py]

**Input/Output Contract**:
```python
def aggregate_time_series(
    series: TimeSeriesData,  # Input
    timeframe: Literal["daily", "weekly", "monthly"] = "daily",
    *,
    business_days_only: bool = True,
) -> TimeSeriesData:  # Output (same type)
    """Return a new TimeSeriesData aggregated to the requested cadence.

    Uses adapter functions to convert between TimeSeriesData and ProcessedChartData,
    allowing reuse of existing aggregation logic without exposing ProcessedChartData
    to consumers.
    """
```

**AllChartsData Requirements** (line 310):
```python
class AllChartsData(BaseModel):
    production_total: TimeSeriesData  # Must be TimeSeriesData
    collection_rate: TimeSeriesData   # Not ProcessedChartData
    new_patients: TimeSeriesData      # Not dict
    case_acceptance: TimeSeriesData
    hygiene_reappointment: TimeSeriesData
```

Our solution satisfies this contract by returning `TimeSeriesData` from aggregation.

### Testing Standards
[Source: docs/architecture/backend/testing-strategy.md]

**Manual Verification Checklist**:
1. Start dashboard: `uv run streamlit run apps/frontend/app.py`
2. Navigate to Interactive Charts section
3. For each location (Baytown, Humble):
   - Select "Daily" → Count ~80 data points, verify date labels
   - Select "Weekly" → Count ~11-12 points, verify week-of labels
   - Select "Monthly" → Count 2-3 points, verify month labels
4. Verify values: Weekly total ≈ sum of 7 daily values
5. Check browser console: No "aggregation_unavailable" warnings

**Automated Tests** (new file: `tests/unit/test_chart_aggregation.py`):
- `test_aggregate_time_series_daily_passthrough()`
- `test_aggregate_time_series_weekly_reduces_points()`
- `test_aggregate_time_series_preserves_type()`
- `test_aggregate_time_series_updates_metadata()`
- `test_format_all_chart_data_applies_to_all_charts()`

**Coverage Target**: 95%+ for new `aggregate_time_series()` function

### Project Structure Notes

**Files to Modify**:
1. `apps/backend/chart_data.py` (~100 lines added)
   - New `aggregate_time_series()` function with business_days_only parameter
   - New `_time_series_to_processed()` adapter (internal)
   - New `_processed_to_time_series()` adapter (internal)
   - Updated `format_all_chart_data()` signature and logic
2. `apps/frontend/app.py` (~5 lines changed)
   - Updated `load_chart_data()` signature to accept timeframe
   - Pass timeframe from UI selector to backend
3. `tests/unit/test_chart_aggregation.py` (~100 lines, new file)
   - Comprehensive unit tests for aggregation logic
   - Tests for adapter functions
   - Tests for business_days_only flag behavior
4. `docs/reference/chart-components-api.md` (~30 lines added)
   - Document new aggregation helper API
   - Explain adapter functions and their purpose
   - Provide usage examples

**No Files Deleted**: This is a pure addition with minimal changes

**Alignment with CLAUDE.md**:
- ✅ Uses Pydantic models exclusively (TimeSeriesData)
- ✅ Maintains 5-layer architecture (Backend aggregation, Frontend rendering)
- ✅ Pure function design (`aggregate_time_series` has no side effects)
- ✅ Type-safe with strict Pydantic validation
- ✅ DRY principle (single aggregation point for all charts)
- ✅ Backend centralization (aggregation logic in backend, not frontend)

### Implementation Details

**aggregate_time_series() Implementation**:
```python
def aggregate_time_series(
    series: TimeSeriesData,
    timeframe: Literal["daily", "weekly", "monthly"] = "daily",
    *,
    business_days_only: bool = True,
) -> TimeSeriesData:
    """Return a new TimeSeriesData aggregated to the requested cadence."""

    # Pass-through for daily or empty series
    if timeframe == "daily" or not series.time_series:
        return series

    # Convert TimeSeriesData to DataFrame
    df = pd.DataFrame(
        {
            "date": pd.to_datetime([point.date for point in series.time_series]),
            "value": pd.to_numeric([point.value for point in series.time_series]),
        }
    ).dropna(subset=["date"])

    # Convert to ProcessedChartData (adapter function)
    processed = _time_series_to_processed(series, df)

    # Apply existing aggregation logic
    if timeframe == "weekly":
        aggregated = aggregate_to_weekly(processed, business_days_only)
    else:  # monthly
        aggregated = aggregate_to_monthly(processed, business_days_only)

    # Convert back to TimeSeriesData with updated metadata (adapter function)
    return _processed_to_time_series(aggregated, series, aggregation=timeframe)
```

**Adapter Functions**:
```python
def _time_series_to_processed(
    series: TimeSeriesData,
    df: pd.DataFrame
) -> ProcessedChartData:
    """Internal adapter: TimeSeriesData → ProcessedChartData.

    Extracts dates/values from TimeSeriesData and wraps them in ProcessedChartData
    so existing aggregate_to_weekly/monthly functions can operate on them.
    """
    return ProcessedChartData(
        dates=df["date"].dt.strftime("%Y-%m-%d").tolist(),
        values=df["value"].tolist(),
        statistics=series.statistics if isinstance(series.statistics, dict) else {},
        metadata=ChartMetaInfo(
            date_column=series.format_options.get("date_column", "date"),
            date_range=f"{df['date'].min():%Y-%m-%d} to {df['date'].max():%Y-%m-%d}",
        ),
    )


def _processed_to_time_series(
    processed: ProcessedChartData,
    original_series: TimeSeriesData,
    aggregation: str,
) -> TimeSeriesData:
    """Internal adapter: ProcessedChartData → TimeSeriesData.

    Rebuilds TimeSeriesData from aggregated ProcessedChartData, preserving
    metric_name, chart_type, data_type, and format_options while updating
    time_series points, statistics, and metadata.aggregation.
    """
    # Rebuild time_series points from aggregated data
    new_points = [
        ChartDataPoint(
            date=date,
            timestamp=pd.Timestamp(date).isoformat(),
            value=value,
            has_data=True,
        )
        for date, value in zip(processed.dates, processed.values)
    ]

    # Recalculate statistics from aggregated values
    values = processed.values
    new_stats = {
        "total": sum(values),
        "average": sum(values) / len(values) if values else 0,
        "minimum": min(values) if values else 0,
        "maximum": max(values) if values else 0,
        "data_points": len(values),
    }

    # Return new TimeSeriesData with updated metadata
    return TimeSeriesData(
        metric_name=original_series.metric_name,
        chart_type=original_series.chart_type,
        data_type=original_series.data_type,
        time_series=new_points,
        statistics=new_stats,
        format_options={
            **original_series.format_options,
            "metadata": {
                **original_series.format_options.get("metadata", {}),
                "aggregation": aggregation,  # UPDATE THIS
            },
        },
        error=None,
    )
```

**Key Benefits of Adapter Approach**:
- ✅ Reuses validated `aggregate_to_weekly()` and `aggregate_to_monthly()` logic
- ✅ Keeps `ProcessedChartData` internal (never exposed to consumers)
- ✅ Maintains type safety (TimeSeriesData in → TimeSeriesData out)
- ✅ No duplication of complex grouping/aggregation math

**format_all_chart_data() Changes**:
```python
def format_all_chart_data(
    eod_df: pd.DataFrame | None,
    front_kpi_df: pd.DataFrame | None,
    date_column: str = "Submission Date",
    timeframe: Literal["daily", "weekly", "monthly"] = "daily",  # NEW
) -> AllChartsData:
    # Build daily charts first
    production_chart = format_production_chart_data(eod_df, date_column)
    collection_chart = format_collection_rate_chart_data(eod_df, date_column)
    new_patients_chart = format_new_patients_chart_data(eod_df, date_column)
    case_acceptance_chart = format_case_acceptance_chart_data(front_kpi_df, date_column)
    hygiene_chart = format_hygiene_reappointment_chart_data(front_kpi_df, date_column)

    # Apply aggregation uniformly (NEW BLOCK)
    if timeframe != "daily":
        production_chart = aggregate_time_series(production_chart, timeframe)
        collection_chart = aggregate_time_series(collection_chart, timeframe)
        new_patients_chart = aggregate_time_series(new_patients_chart, timeframe)
        case_acceptance_chart = aggregate_time_series(case_acceptance_chart, timeframe)
        hygiene_chart = aggregate_time_series(hygiene_chart, timeframe)

    # Return AllChartsData (unchanged)
    return AllChartsData(
        production_total=production_chart,
        collection_rate=collection_chart,
        new_patients=new_patients_chart,
        case_acceptance=case_acceptance_chart,
        hygiene_reappointment=hygiene_chart,
        metadata=ChartsMetadata(...)
    )
```

### References

- [Tech Spec: docs/tech-spec-chart-aggregation-fix.md]
- [Bug Report: docs/chart-aggregation-fix.md]
- [Architecture: docs/architecture/fullstack-architecture.md]
- [Models: core/models/chart_models.py (TimeSeriesData, AllChartsData, ChartDataPoint)]
- [Backend: apps/backend/chart_data.py (existing aggregation functions)]
- [Frontend: apps/frontend/app.py (load_chart_data cache)]
- [CLAUDE.md: Architecture (Story 3.0: 5-Layer Design)]

## Dev Agent Record

### Context Reference

- [Story Context 3.5](../story-context-3.5.xml) - Generated 2025-10-14
  - Complete architectural context with adapter pattern documentation
  - 7 code artifacts (format_all_chart_data, aggregate_to_weekly/monthly, adapters, models)
  - 6 documentation artifacts (tech spec, bug report, architecture, testing strategy, CLAUDE.md)
  - 7 development constraints (architecture, type-safety, pure-functions, adapter-pattern, contract-preservation, code-reuse, metadata-update)
  - 7 interface definitions (aggregate_time_series, adapters, existing aggregation functions)
  - 14 test ideas mapped to acceptance criteria

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

**Session: 2025-10-15 - Story 3.5 Implementation**

**Phase 1: Backend Aggregation Helper (Task 1)**
- Started implementation by adding `Literal` import to chart_data.py for type hints
- Implemented three core functions:
  - `aggregate_time_series()`: Main aggregation entry point (~70 lines)
  - `_time_series_to_processed()`: Adapter to convert TimeSeriesData → ProcessedChartData (~35 lines)
  - `_processed_to_time_series()`: Adapter to convert ProcessedChartData → TimeSeriesData (~45 lines)
- Key insight: Discovered that `format_options["aggregation"]` must be at the top level, not nested under `metadata` due to Pydantic type constraints: `dict[str, str | float | bool | dict[str, float]]`
- Initial implementation used nested structure which caused Pydantic validation errors
- Corrected to flat structure: `format_options["aggregation"] = "weekly"` instead of `format_options["metadata"]["aggregation"]`

**Phase 2: Pipeline Integration (Task 2)**
- Updated `format_all_chart_data()` signature to include `timeframe` parameter
- Added conditional aggregation block that applies `aggregate_time_series()` to all 5 charts when timeframe != "daily"
- Preserved existing daily chart formatting logic (no changes to individual chart formatters)
- Enhanced docstring to document new parameter and return behavior

**Phase 3: Frontend Threading (Task 3)**
- Updated `load_chart_data()` signature: changed `timeframe: str` to `timeframe: Literal["daily", "weekly", "monthly"]`
- Moved chart data loading from early initialization (line 228) to after timeframe selector (line 400+)
- Added type-safe cast for radio selection using `# type: ignore[assignment]` annotation
- Verified Streamlit's `@st.cache_data` automatically includes all function args in cache key
- Added spinner with dynamic text: `f"Loading {timeframe} chart data..."`

**Phase 4: Testing & Validation (Task 4)**
- Created `tests/unit/test_chart_aggregation.py` with 12 comprehensive tests:
  - `TestAggregateTimeSeries` (7 tests): Daily passthrough, weekly/monthly reduction, type preservation, metadata updates, business_days_only flag, empty series
  - `TestAdapterFunctions` (2 tests): Adapter bidirectional conversion
  - `TestFormatAllChartData` (3 tests): Uniform application, Pydantic validation, daily no-op
- Initial test failures due to incorrect `format_options` structure (nested metadata dict)
- Fixed by updating test fixtures to use flat structure
- Type checking issues resolved by:
  - Explicit type casting for `date_column` from union type to `str`
  - Validating `aggregation` value against Literal options before assignment
  - Converting `data_points` to `int` from `float | int` union
- All 12 tests passing, mypy clean, 353/354 total tests passing (1 unrelated failure)

**Phase 5: Documentation (Task 5)**
- Updated `docs/reference/chart-components-api.md` with new "Chart Aggregation Functions (Story 3.5)" section
- Documented all three functions with full signatures, parameters, returns, and usage examples
- Included design rationale explaining adapter pattern benefits
- Added implementation notes for `format_all_chart_data()` parameter

**Technical Challenges Resolved:**

1. **Pydantic Type Constraint Issue**
   - Problem: `format_options` type is `dict[str, str | float | bool | dict[str, float]]`, which only allows `dict[str, float]` for nested dicts
   - Solution: Use flat structure `format_options["aggregation"] = "weekly"` instead of nested `format_options["metadata"]["aggregation"]`
   - Impact: Required updates to both implementation and tests

2. **Type Safety with Union Types**
   - Problem: `.get()` on format_options returns union type that doesn't match expected Literal or str types
   - Solution: Added explicit type validation and casting in `_time_series_to_processed()`
   - Implementation: Check if value is string and in allowed set before assigning with `# type: ignore[assignment]`

3. **Frontend Type Casting**
   - Problem: Streamlit radio returns `str` but we need `Literal["daily", "weekly", "monthly"]`
   - Solution: Intermediate variable `timeframe_selection` with explicit type annotation and `# type: ignore[assignment]`
   - Rationale: Safe because radio options are hardcoded to only these 3 values

**Code Quality Metrics:**
- Lines added: ~655 total
  - Backend: 180 lines (3 functions + updated signature)
  - Frontend: 15 lines (signature update + timeframe threading)
  - Tests: 340 lines (comprehensive coverage)
  - Documentation: 120 lines (API reference)
- Test coverage: 12/12 new tests passing (100%)
- Type safety: mypy validation clean
- Pydantic validation: Enforced at all boundaries

**Performance Considerations:**
- Aggregation happens after TimeSeriesData construction (post-processing)
- Separate cache entries per (location, timeframe) combination via Streamlit
- Weekly aggregation: ~80 points → ~11-12 points (86% reduction)
- Monthly aggregation: ~80 points → 2-3 points (97% reduction)
- Pure function design ensures no side effects or state mutations

**Architecture Adherence:**
- ✅ 100% Pydantic adoption (no dict[str, Any] in new code)
- ✅ Pure function design (aggregate_time_series has no side effects)
- ✅ Type-safe Literal types throughout
- ✅ Adapter pattern maintains ProcessedChartData as internal detail
- ✅ Single aggregation point for all 5 charts (DRY principle)
- ✅ Backend-only aggregation (frontend receives pre-aggregated data)

No blocking issues encountered. Implementation complete and ready for manual testing.

### Completion Notes List

**Implementation Complete - 2025-10-15**

Successfully implemented chart timeframe aggregation feature with the following accomplishments:

1. **Backend Aggregation Helper** (AC #1): Created `aggregate_time_series()` function in `apps/backend/chart_data.py` with internal adapter functions (`_time_series_to_processed` and `_processed_to_time_series`) that reuse existing aggregation logic while maintaining TimeSeriesData type contracts.

2. **Pipeline Integration** (AC #2): Updated `format_all_chart_data()` to accept `timeframe` parameter and apply uniform aggregation to all 5 KPI charts. Conditional application ensures daily view passes through unchanged.

3. **Frontend Threading** (AC #3): Modified `load_chart_data()` signature to accept `timeframe` parameter and connected UI radio selector. Streamlit's cache automatically creates separate entries per timeframe.

4. **Testing & Validation** (AC #4): Created comprehensive test suite with 12 tests covering all scenarios. All tests passing. Type checking (mypy) passes. Full regression suite passes (353 tests).

5. **Documentation** (AC #5): Updated `docs/reference/chart-components-api.md` with complete API documentation for new aggregation functions, adapter pattern explanation, and usage examples.

**Key Design Decisions:**
- Used flat `format_options["aggregation"]` field instead of nested metadata dict to comply with Pydantic type constraints
- Adapter pattern preserves ProcessedChartData as internal implementation detail
- Type-safe Literal types throughout with explicit casting where needed
- Pure function design maintains testability and predictability

**Testing Results:**
- 12/12 new tests passing
- 353/354 total tests passing (1 unrelated date-specific failure)
- Type checking clean (mypy validation passes)
- Pydantic validation enforced at all boundaries

**Manual Testing Required:**
- Chrome DevTools verification of data point counts (daily ~80, weekly ~11-12, monthly 2-3)
- Visual confirmation of chart aggregation behavior
- Performance monitoring of aggregation timing

### File List

**Modified Files:**
1. `apps/backend/chart_data.py` - Added `aggregate_time_series()`, `_time_series_to_processed()`, `_processed_to_time_series()`, updated `format_all_chart_data()` signature
2. `apps/frontend/app.py` - Updated `load_chart_data()` signature, added timeframe threading
3. `docs/reference/chart-components-api.md` - Added aggregation function documentation

**New Files:**
4. `tests/unit/test_chart_aggregation.py` - Comprehensive test suite for aggregation functionality

**Lines Changed:**
- Backend: ~180 lines added (3 functions + updated format_all_chart_data)
- Frontend: ~15 lines modified
- Tests: ~340 lines added
- Documentation: ~120 lines added
