---
title: "Chart Aggregation Bug Report & Fix"
date: "2025-10-14"
status: "Action Required"
severity: "High - User-Facing Feature Broken"
---

# Chart Aggregation Bug Report

## Executive Summary

The weekly/monthly aggregation feature in interactive charts is **non-functional**. While the UI allows users to select "Daily", "Weekly", or "Monthly" timeframes, **only the chart title changes** - the underlying data remains identical across all selections.

## Test Results

### ✅ What Works
- Timeframe selector UI (radio buttons render correctly)
- Chart title updates dynamically:
  - Daily → "Daily Production Total"
  - Weekly → "Weekly Production Total"
  - Monthly → "Monthly Production Total"

### ❌ What's Broken
- **Data aggregation does not occur**
- Chart displays identical daily data points regardless of timeframe selection
- Users see the same granular daily values in weekly/monthly views

## Root Cause Analysis

### Location: `apps/frontend/chart_production.py:84-88`

```python
if timeframe != "daily" and not aggregation_value:
    log.warning(
        "chart.production_aggregation_unavailable",
        timeframe=timeframe,
    )
```

**Problem:** The `timeframe` parameter is received but **never used** to aggregate data.

### Current Data Flow (Broken)

```
User selects "Weekly"
  ↓
app.py passes timeframe="weekly" to create_chart_from_data()
  ↓
chart_production.py:create_production_chart() receives timeframe
  ↓
⚠️  ISSUE: Chart updates title but uses raw daily data
  ↓
User sees daily data points with "Weekly Production Total" title
```

### Expected Data Flow (Not Implemented)

```
User selects "Weekly"
  ↓
app.py calls aggregate_to_weekly() BEFORE chart creation
  ↓
create_production_chart() receives aggregated data
  ↓
Chart displays actual weekly totals
```

## Available Infrastructure

The aggregation logic **already exists** in `apps/backend/chart_data.py`:

- `aggregate_to_weekly()` (line 842) - Groups daily data by week, sums values
- `aggregate_to_monthly()` (line 919) - Groups daily data by month, sums values

These functions are fully functional but **never called** by the frontend.

## Solution

### Backend Aggregation (Cleaner Architecture)

**File:** `apps/backend/chart_data.py:1441`

Modify `format_all_chart_data()` to accept timeframe parameter and aggregate before returning:

```python
def format_all_chart_data(
    eod_df: pd.DataFrame | None,
    front_kpi_df: pd.DataFrame | None,
    date_column: str = "Submission Date",
    timeframe: str = "daily",  # NEW PARAMETER
) -> AllChartsData:
    """Format all KPI data with optional aggregation."""

    # Create base charts (daily)
    production_data = process_production_data_for_chart(eod_df, date_column)

    # Apply aggregation if requested
    if timeframe == "weekly":
        production_data = aggregate_to_weekly(production_data)
    elif timeframe == "monthly":
        production_data = aggregate_to_monthly(production_data)

    # Return aggregated data
    return AllChartsData(...)
```

Then update `app.py:load_chart_data()` to pass timeframe:

```python
@st.cache_data(ttl=300)
def load_chart_data(location: str, timeframe: str = "daily") -> AllChartsData | None:
    ...
    return format_all_chart_data(eod_df, front_df, timeframe=timeframe)

# In main body
chart_data = load_chart_data(location, timeframe)
```

## Recommendation

**Use Backend Aggregation** because:

1. **Single source of truth** - Aggregation logic stays in backend
2. **Cacheable** - Streamlit can cache aggregated results
3. **DRY** - Apply once, all charts benefit
4. **Type-safe** - Pydantic models ensure data integrity
5. **Testable** - Aggregation functions already have unit tests

## Implementation Checklist

- [ ] Add `timeframe` parameter to `format_all_chart_data()`
- [ ] Add `timeframe` parameter to `load_chart_data()`
- [ ] Apply aggregation conditionally in `format_all_chart_data()`
- [ ] Pass `timeframe` from UI selection to `load_chart_data()`
- [ ] Update cache key to include timeframe
- [ ] Apply same fix to all 5 KPI charts
- [ ] Test with Chrome DevTools MCP
- [ ] Verify data actually aggregates (check axis labels/values)

## Verification Steps

1. Start dashboard: `uv run streamlit run apps/frontend/app.py`
2. Navigate to Interactive Charts section
3. Select "Daily" - count data points (should be ~80 days)
4. Select "Weekly" - count data points (should be ~11-12 weeks)
5. Select "Monthly" - count data points (should be 2-3 months)
6. Verify values change (weekly totals > daily values)

## Impact

- **User Experience:** Feature appears broken, misleading data presentation
- **Trust:** Users may question data accuracy across dashboard
- **Urgency:** High - affects primary analytics feature

---

**Status:** Bug confirmed via browser testing
**Next Step:** Implement Option 2 (Backend Aggregation)
**Estimated Effort:** 2-3 hours (including testing)
