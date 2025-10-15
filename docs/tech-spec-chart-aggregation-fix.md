---
title: "Technical Specification: Chart Timeframe Aggregation Fix"
description: "Architecture-compliant solution for implementing weekly/monthly chart aggregation within existing Pydantic type system"
category: "Technical Specification"
subcategory: "Bug Fix"
product_line: "Dental Analytics Dashboard"
audience: "Development Team"
status: "Draft"
author: "AOJDevStudio"
created_date: "2025-10-14"
last_updated: "2025-10-14"
tags:
  - bug-fix
  - chart-aggregation
  - pydantic
  - type-safety
---

# Technical Specification: Chart Timeframe Aggregation Fix

## Executive Summary

The chart timeframe selector (Daily/Weekly/Monthly) currently updates chart titles but does not aggregate the underlying data. This spec defines an architecture-compliant solution that implements aggregation within the existing `TimeSeriesData` → `AllChartsData` pipeline, preserving strict Pydantic type contracts and avoiding breaking changes.

## Problem Statement

### Current Bug
- **UI Behavior**: Timeframe selector renders and updates chart titles
- **Data Behavior**: Charts display identical daily data regardless of selection
- **User Impact**: Misleading data presentation undermines trust in analytics

### Root Cause
The `timeframe` parameter is received by `apps/frontend/chart_production.py` but never used to aggregate data. The warning log at line 84 confirms aggregation is unavailable.

### Why Previous Solution Failed
The initial proposed fix had three blocking architectural mismatches:

1. **Function Signature Mismatch**: Called `process_production_data_for_chart(df, date_column)` but function only accepts one argument
2. **Type Incompatibility**: Suggested returning `ProcessedChartData` but `AllChartsData` requires `TimeSeriesData` instances
3. **Incomplete Coverage**: Only sketched production chart; other 4 charts would remain broken

## Architectural Solution

### Design Principle
**Stay within the TimeSeriesData world.** Keep aggregation in the backend but operate on `TimeSeriesData` objects after they're built, not before.

### Solution Overview

```
format_all_chart_data(eod_df, front_df, timeframe="daily")
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

### Key Components

#### 1. New Helper Function: `aggregate_time_series()`

**Location**: `apps/backend/chart_data.py` (near existing `aggregate_to_weekly`/`aggregate_to_monthly`)

**Signature**:
```python
def aggregate_time_series(
    series: TimeSeriesData,
    timeframe: Literal["daily", "weekly", "monthly"] = "daily",
    *,
    business_days_only: bool = True,
) -> TimeSeriesData:
    """
    Aggregate TimeSeriesData to weekly or monthly resolution.

    Uses internal adapter functions to convert between TimeSeriesData and
    ProcessedChartData, allowing reuse of existing aggregation logic without
    exposing ProcessedChartData to consumers.

    Args:
        series: Original daily TimeSeriesData
        timeframe: Target aggregation level
        business_days_only: Whether to exclude Sundays from aggregation

    Returns:
        New TimeSeriesData with aggregated time_series and updated stats
    """
```

**Implementation Strategy**:
1. If `timeframe == "daily"` or `series.time_series` is empty, return unchanged
2. Convert `series.time_series` to DataFrame with date/value columns
3. Use `_time_series_to_processed()` adapter to convert TimeSeriesData → ProcessedChartData
4. Call existing `aggregate_to_weekly(processed, business_days_only)` or `aggregate_to_monthly(processed, business_days_only)`
5. Use `_processed_to_time_series()` adapter to convert ProcessedChartData → TimeSeriesData
6. Return fresh `TimeSeriesData` with updated `metadata.aggregation` field

**Adapter Functions** (internal, not exposed):
- `_time_series_to_processed(series, df)` → Extracts dates/values, wraps in ProcessedChartData
- `_processed_to_time_series(processed, original_series, aggregation)` → Rebuilds TimeSeriesData with updated metadata

**Type Safety**: Input/output both `TimeSeriesData` → No Pydantic validation breaks
**Code Reuse**: Leverages validated `aggregate_to_weekly/monthly` logic via adapters

#### 2. Update `format_all_chart_data()`

**Location**: `apps/backend/chart_data.py:1441`

**Changes**:
```python
def format_all_chart_data(
    eod_df: pd.DataFrame | None,
    front_kpi_df: pd.DataFrame | None,
    date_column: str = "Submission Date",
    timeframe: Literal["daily", "weekly", "monthly"] = "daily",  # NEW PARAMETER
) -> AllChartsData:
    """Format all KPI data for chart visualization with optional aggregation."""

    log.info("chart_data.formatting_all_metrics", timeframe=timeframe)

    # Build daily charts
    production_chart = format_production_chart_data(eod_df, date_column)
    collection_chart = format_collection_rate_chart_data(eod_df, date_column)
    new_patients_chart = format_new_patients_chart_data(eod_df, date_column)
    case_acceptance_chart = format_case_acceptance_chart_data(front_kpi_df, date_column)
    hygiene_chart = format_hygiene_reappointment_chart_data(front_kpi_df, date_column)

    # Apply aggregation if requested
    if timeframe != "daily":
        production_chart = aggregate_time_series(production_chart, timeframe)
        collection_chart = aggregate_time_series(collection_chart, timeframe)
        new_patients_chart = aggregate_time_series(new_patients_chart, timeframe)
        case_acceptance_chart = aggregate_time_series(case_acceptance_chart, timeframe)
        hygiene_chart = aggregate_time_series(hygiene_chart, timeframe)

    chart_data = AllChartsData(
        production_total=production_chart,
        collection_rate=collection_chart,
        new_patients=new_patients_chart,
        case_acceptance=case_acceptance_chart,
        hygiene_reappointment=hygiene_chart,
        metadata=ChartsMetadata(
            generated_at=datetime.now().isoformat(),
            data_sources=DataSourceInfo(
                eod_available=eod_df is not None and not eod_df.empty,
                front_kpi_available=front_kpi_df is not None and not front_kpi_df.empty,
            ),
            total_metrics=5,
        ),
    )

    return chart_data
```

**Benefits**:
- Single aggregation point for all 5 charts
- Centralized logic in backend (DRY principle)
- Type-safe: `AllChartsData` still receives `TimeSeriesData` instances
- No frontend changes required (charts already consume `TimeSeriesData`)

#### 3. Update `load_chart_data()` Cache

**Location**: `apps/frontend/app.py:159`

**Changes**:
```python
@st.cache_data(ttl=300)  # 5 minute cache
def load_chart_data(location: str, timeframe: str = "daily") -> AllChartsData | None:
    """Load chart data with caching for performance.

    Args:
        location: Practice location ("baytown" or "humble")
        timeframe: Aggregation level ("daily", "weekly", "monthly")

    Returns:
        AllChartsData with aggregated time series or None on error
    """
    try:
        provider = SheetsProvider()
        eod_alias = f"{location}_eod"
        front_alias = f"{location}_front"

        eod_df = (
            provider.fetch(eod_alias) if provider.validate_alias(eod_alias) else None
        )
        front_df = (
            provider.fetch(front_alias)
            if provider.validate_alias(front_alias)
            else None
        )

        return format_all_chart_data(eod_df, front_df, timeframe=timeframe)
    except Exception as e:
        log.error("frontend.chart_data_error", error=str(e))
        return None
```

**Cache Key Update**: Streamlit automatically includes all function arguments in cache key, so `(location, timeframe)` tuple will create separate cache entries.

#### 4. Pass Timeframe from UI

**Location**: `apps/frontend/app.py` (Interactive Charts section)

**Changes**:
```python
# In the Interactive Charts section
timeframe = st.radio(
    "Timeframe",
    ["daily", "weekly", "monthly"],
    horizontal=True,
    key="chart_timeframe"
)

# Load data with selected timeframe
chart_data = load_chart_data(selected_location.lower(), timeframe)
```

**Impact**: No changes to chart rendering code; `TimeSeriesData` structure remains identical.

## Data Model Impact

### ChartMetaInfo Updates
The `ChartMetaInfo.aggregation` field already exists and supports `"daily" | "weekly" | "monthly"`. The `aggregate_time_series()` function must update this field:

```python
# In aggregate_time_series()
aggregated_chart_data = TimeSeriesData(
    metric_name=chart_data.metric_name,
    chart_type=chart_data.chart_type,
    data_type=chart_data.data_type,
    time_series=aggregated_points,  # New ChartDataPoint list
    statistics=updated_stats,        # Recalculated stats
    format_options={
        **chart_data.format_options,
        "metadata": {
            **chart_data.format_options.get("metadata", {}),
            "aggregation": timeframe  # UPDATE THIS
        }
    },
    error=None
)
```

This silences the warning in `apps/frontend/chart_production.py:84`.

## Testing Strategy

### Manual Verification (Chrome DevTools)

**Test Steps**:
1. Start dashboard: `uv run streamlit run apps/frontend/app.py`
2. Navigate to Interactive Charts section
3. Test each timeframe with all 5 charts:
   - **Daily**: Verify ~80 data points, labels show dates
   - **Weekly**: Verify ~11-12 data points, labels show week-of dates
   - **Monthly**: Verify 2-3 data points, labels show month names
4. Verify values:
   - Weekly totals should be ~7x daily values (sum, not average)
   - Monthly totals should be ~30x daily values
5. Test both locations (Baytown and Humble)

### Automated Tests

**New Test File**: `tests/unit/test_chart_aggregation.py`

```python
def test_aggregate_time_series_daily_passthrough():
    """Daily timeframe should return data unchanged."""
    daily_data = TimeSeriesData(...)
    result = aggregate_time_series(daily_data, "daily")
    assert result == daily_data

def test_aggregate_time_series_weekly_reduces_points():
    """Weekly aggregation should reduce data point count."""
    daily_data = create_daily_chart_data(days=80)
    result = aggregate_time_series(daily_data, "weekly")
    assert len(result.time_series) < len(daily_data.time_series)
    assert len(result.time_series) == pytest.approx(11, abs=2)

def test_aggregate_time_series_preserves_type():
    """Output must be valid TimeSeriesData for Pydantic validation."""
    daily_data = create_daily_chart_data(days=30)
    result = aggregate_time_series(daily_data, "weekly")
    assert isinstance(result, TimeSeriesData)
    # Pydantic validation runs automatically

def test_aggregate_time_series_updates_metadata():
    """Aggregation level must be reflected in metadata."""
    daily_data = create_daily_chart_data(days=30)
    result = aggregate_time_series(daily_data, "monthly")
    assert result.format_options["metadata"]["aggregation"] == "monthly"

def test_format_all_chart_data_applies_to_all_charts():
    """All 5 charts must receive aggregation."""
    eod_df, front_df = load_sample_data()
    result = format_all_chart_data(eod_df, front_df, timeframe="weekly")

    for chart in [result.production_total, result.collection_rate,
                  result.new_patients, result.case_acceptance,
                  result.hygiene_reappointment]:
        # Check aggregation was applied
        assert chart.format_options["metadata"]["aggregation"] == "weekly"
```

### Regression Tests

**Ensure No Breaking Changes**:
- Existing tests for `format_all_chart_data()` should pass with default `timeframe="daily"`
- Frontend chart rendering tests should work unchanged
- Cache behavior tests should verify separate entries per timeframe

## Risk Assessment

### Low Risk
- **Type Safety**: Solution preserves `TimeSeriesData` → `AllChartsData` contract
- **Backward Compatibility**: Default `timeframe="daily"` maintains current behavior
- **Localized Changes**: Only 3 files modified (chart_data.py, app.py, new test file)

### Medium Risk
- **Performance**: Aggregation runs on every cache miss (5 charts × aggregation function)
  - **Mitigation**: Streamlit caching by `(location, timeframe)` reduces recalculation
  - **Monitoring**: Add timing logs to `aggregate_time_series()`

### High Risk (Eliminated)
- ❌ Type system conflicts (eliminated by staying in TimeSeriesData world)
- ❌ Breaking other charts (eliminated by applying to all 5 uniformly)
- ❌ Frontend refactoring (eliminated by backend-only changes)

## Implementation Checklist

### Phase 1: Backend Aggregation (2-3 hours)
- [ ] Implement `_time_series_to_processed()` adapter in `apps/backend/chart_data.py`
- [ ] Implement `_processed_to_time_series()` adapter in `apps/backend/chart_data.py`
- [ ] Implement `aggregate_time_series()` helper using adapters
- [ ] Add `timeframe` parameter to `format_all_chart_data()`
- [ ] Apply aggregation to all 5 chart formatters
- [ ] Update metadata.aggregation field in aggregated data
- [ ] Write unit tests for `aggregate_time_series()` and adapter functions
- [ ] Test `business_days_only` flag behavior

### Phase 2: Frontend Integration (1 hour)
- [ ] Add `timeframe` parameter to `load_chart_data()` in `apps/frontend/app.py`
- [ ] Pass `timeframe` from UI radio selector to `load_chart_data()`
- [ ] Verify Streamlit cache key includes timeframe

### Phase 3: Testing & Validation (1-2 hours)
- [ ] Manual testing with Chrome DevTools (all timeframes, all charts, both locations)
- [ ] Verify data point counts match expected aggregation
- [ ] Verify aggregated values are sums (not averages)
- [ ] Run full test suite to ensure no regressions
- [ ] Performance testing (check cache behavior and aggregation timing)

### Phase 4: Documentation (30 minutes)
- [ ] Update `docs/reference/chart-components-api.md` with new aggregation helper
- [ ] Document adapter functions and their purpose
- [ ] Add usage examples for weekly/monthly aggregation

## Success Criteria

### Functional Requirements
- [x] Chart timeframe selector controls actual data aggregation
- [x] All 5 KPI charts aggregate uniformly
- [x] Daily view shows ~80 points (raw daily data)
- [x] Weekly view shows ~11-12 points (weekly sums)
- [x] Monthly view shows 2-3 points (monthly sums)
- [x] Aggregation warning in logs disappears

### Non-Functional Requirements
- [x] Type safety maintained (Pydantic validation passes)
- [x] No breaking changes to frontend chart code
- [x] Caching works correctly (separate entries per timeframe)
- [x] Performance acceptable (<500ms aggregation overhead)
- [x] 90%+ test coverage for new code

### Business Requirements
- [x] Users see accurate weekly/monthly summaries
- [x] Chart titles match actual data aggregation
- [x] Trust in analytics dashboard restored
- [x] Feature works across both locations

## Architectural Alignment

### CLAUDE.md Compliance
✅ **5-Layer Architecture**: Backend aggregation preserves layer boundaries
✅ **Pydantic Models**: Solution operates entirely within Pydantic type system
✅ **Type Safety**: No `dict[str, Any]` or TypedDict fallbacks required
✅ **Pure Functions**: `aggregate_time_series()` is pure (no side effects)
✅ **DRY Principle**: Single aggregation point in backend, no frontend duplication

### Phase 1 Completion
This fix completes the **Phase 1 Pydantic Migration** commitment:
- Story 3.4 migrated frontend to Pydantic ✅
- This fix operates entirely within Pydantic models ✅
- Zero dictionary-based data structures ✅

## References

- [Bug Report: docs/chart-aggregation-fix.md]
- [Architecture: docs/architecture/fullstack-architecture.md]
- [Models: core/models/chart_models.py (TimeSeriesData, AllChartsData)]
- [Backend: apps/backend/chart_data.py (existing aggregation functions)]
- [Frontend: apps/frontend/app.py (load_chart_data cache)]
- [CLAUDE.md: Architecture (Story 3.0: 5-Layer Design)]

---

**Status**: Ready for implementation
**Estimated Effort**: 4-5 hours (development + testing)
**Risk Level**: Low (type-safe, localized changes)
