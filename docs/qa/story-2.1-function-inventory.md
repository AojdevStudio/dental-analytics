---
title: "Story 2.1 – Historical KPI Function Inventory"
description: "Blueprint for historical KPI calculations, refactor boundaries, and calendar-based rollups."
category: "QA"
subcategory: "Historical Metrics"
product_line: "Dental Analytics"
audience: "Developers"
status: "Final"
author: "AOJDevStudio"
created_date: "2025-09-16"
last_updated: "2025-09-16"
tags:
  - story-2.1
  - historical-kpis
  - refactor
---

## Canonical KPI Definitions (Story 2.1 Sheets Schema)

### Production
- **Columns:** `Total Production Today`, `Adjustments Today`, `Write-offs Today`
- **Daily value:** sum of the three columns.
- **Weekly aggregation:** Monday–Sunday calendar weeks (practice operates Mon–Sat; Sunday carries zero values).
- **Monthly aggregation:** calendar month of submission date.

### Collections
- **Columns:** `Patient Income Today`, `Unearned Income Today`, `Insurance Income Today`.
- **Daily value:** sum of the three columns.
- **Daily collection rate:** `daily_collections / daily_production * 100`; emit `None` if production is zero.
- **Weekly/monthly rates:** compute weighted rates using period sums (i.e., sum of collections ÷ sum of production).

### New Patients
- **Column:** `New Patients - Total Month to Date` (cumulative).
- **Daily value:** day-over-day delta of the cumulative column, clipped at zero when the month resets.
- **Weekly/monthly totals:** sum of the derived daily values within the calendar window; averages available as needed.

### Case Acceptance (renamed from Treatment Acceptance)
- **Columns:** `treatments_presented`, `treatments_scheduled`, `$ Same Day Treatment`.
- **Daily rate:** `(treatments_scheduled + same_day_treatment) / treatments_presented * 100`; return `None` when presented equals zero.
- **Weekly/monthly rates:** use weighted sums of numerator and denominator across the period.

### Hygiene Reappointment
- **Columns:** `Total hygiene Appointments`, `Number of patients NOT reappointed?`.
- **Daily rate:** `(total - not_reappointed) / total * 100`; guard against zero totals.
- **Weekly/monthly rates:** simple average of valid daily rates; optional weighted version if future data requires it.

## Module Responsibilities After Refactor

### `apps/backend/historical_metrics.py` (≤100 lines target)
- Provide one function per metric to return canonical daily series with normalized column names.
- Accept optional period parameter (`daily`, `weekly`, `monthly`) to emit aggregated views using calendar boundaries.

### `apps/backend/historical_data.py`
- Continue handling Google Sheets retrieval, operational-day filtering, and latest-available extraction.
- Expose helper to pivot daily series into calendar-week/month buckets using Monday week starts.

### `apps/backend/chart_data/`
- Split into small modules (≤100 lines) per KPI that transform canonical series into chart payloads.
- Share utility module (`apps/backend/utils/time_series.py`) for numeric coercion, date parsing, and calendar grouping.

### `apps/backend/metrics.py`
- Retain real-time single-day calculations for dashboard display; delegate historical work to the new module.

## Testing Expectations
- Add fixtures mirroring Story 2.1 column names for both EOD and Front KPI sheets.
- Unit tests must cover calendar aggregation edges: month rollovers, weeks that include Sundays, and zero-denominator guards.
- Integration tests should mock the historical manager to validate daily → weekly/monthly chart flows.

## Implementation Notes
- Calendar logic relies on submission date in sheet rows; convert to timezone-aware datetimes if future APIs demand it.
- Keep all derived calculations in code so the upcoming Supabase migration can reuse the same logic without sheet formulas.
- Maintain fallbacks for legacy column names until earlier stories are retired, but prefer the Story 2.1 schema.
