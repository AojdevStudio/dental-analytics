# Story 2.2: Plotly Chart Integration

## Status
Draft

## Story
**As a** practice manager,
**I want** interactive Plotly charts for all 5 KPIs with daily/weekly/monthly views,
**so that** I can visualize trends and drill down into performance data for better decision making.

## Acceptance Criteria

1. **Interactive Chart Display**: All 5 KPIs display as interactive Plotly charts with zoom, hover, and pan capabilities
2. **Time Range Selection**: User can switch between "Daily", "Weekly", and "Monthly" time-series views
3. **Trend Analysis**: Charts display trend lines and identify patterns in historical performance
4. **Business Day Handling**: Charts properly handle weekends/holidays without showing misleading "zero" data
5. **Performance**: Dashboard loads historical charts in <3 seconds for 30+ days of data
6. **Scalability**: Architecture supports adding new chart types and timeframes with minimal code changes

## Tasks / Subtasks

- [ ] **Task 1: Install and Configure Plotly** (AC: 1, 5)
  - [ ] Add plotly dependency to pyproject.toml using uv
  - [ ] Configure Plotly for Streamlit integration
  - [ ] Verify Plotly loads correctly with existing frontend structure
  - [ ] Test basic chart rendering performance

- [ ] **Task 2: Create Chart Component Module** (AC: 1, 6)
  - [ ] Create `apps/frontend/chart_components.py` for reusable chart components
  - [ ] Implement base chart configuration with KamDental branding (Navy #142D54, Teal #007E9E)
  - [ ] Create responsive chart layout that works with existing 2+3 column structure
  - [ ] Add error handling for chart rendering failures

- [ ] **Task 3: Implement KPI Chart Functions** (AC: 1, 3)
  - [ ] Create `create_production_chart()` function using data from `format_production_chart_data()`
  - [ ] Create `create_collection_rate_chart()` function using data from `format_collection_rate_chart_data()`
  - [ ] Create `create_new_patients_chart()` function using data from `format_new_patients_chart_data()`
  - [ ] Create `create_treatment_acceptance_chart()` function using data from `format_treatment_acceptance_chart_data()`
  - [ ] Create `create_hygiene_reappointment_chart()` function using data from `format_hygiene_reappointment_chart_data()`
  - [ ] Add trend line calculations and pattern identification

- [ ] **Task 4: Add Time Range Selection UI** (AC: 2, 4)
  - [ ] Add radio buttons or selectbox for "Daily", "Weekly", "Monthly" timeframe selection
  - [ ] Implement session state management for timeframe persistence
  - [ ] Create data aggregation logic for weekly and monthly views
  - [ ] Add business day filtering that respects operational schedule (Monday-Saturday)

- [ ] **Task 5: Integrate Charts with Dashboard** (AC: 1, 2, 5)
  - [ ] Replace existing static metrics with interactive chart displays
  - [ ] Maintain current KPI metric cards above charts for quick reference
  - [ ] Add chart containers that work with existing location selector
  - [ ] Implement loading states and error handling for chart data

- [ ] **Task 6: Performance Optimization** (AC: 5, 6)
  - [ ] Implement chart data caching using Streamlit's caching mechanisms
  - [ ] Optimize chart rendering for 30+ days of historical data
  - [ ] Add lazy loading for charts that aren't immediately visible
  - [ ] Profile dashboard performance and ensure <3 second load times

## Dev Notes

### Previous Story Context
[Source: docs/stories/story-2.1.md] Story 2.1 implemented the historical data foundation with:
- `HistoricalDataManager` class providing time-series data collection
- Chart data processing functions in `apps/backend/chart_data.py`
- Currency parsing fixes for historical calculations
- Framework-agnostic backend design supporting frontend flexibility

### Relevant Source Tree Information
[Source: docs/architecture/source-tree.md]

**Frontend Structure:**
```
apps/frontend/
├── __init__.py              # Module initialization
└── app.py                   # Main Streamlit application
```

**Backend Chart Data Module:**
```
apps/backend/chart_data.py   # Chart data processing functions
- format_production_chart_data()
- format_collection_rate_chart_data()
- format_new_patients_chart_data()
- format_treatment_acceptance_chart_data()
- format_hygiene_reappointment_chart_data()
- format_all_chart_data()
```

**Import Structure for Frontend:**
```python
# apps/frontend/app.py
import streamlit as st
import pandas as pd
from datetime import datetime
from apps.backend.metrics import get_all_kpis
from apps.backend.chart_data import get_chart_data
from apps.backend.historical_data import get_historical_data
```

### Technical Implementation Details
[Source: docs/architecture/fullstack/technology-stack.md]

**Core Technologies:**
- Frontend: Streamlit 1.30+
- Data Processing: pandas 2.1+
- Language: Python 3.10+
- Package Manager: uv

**New Dependency Required:**
- plotly (to be added via `uv add plotly`)

### Brand Guidelines
[Source: docs/architecture/source-tree.md]
- Primary Navy: #142D54 (headers, text)
- Teal Accent: #007E9E (metrics, good status)
- Emergency Red: #BB0A0A (poor metrics)
- Clean Layout: 2+3 column responsive design

### Existing Dashboard Structure
[Source: apps/frontend/app.py symbols overview]
Current dashboard uses:
- Location selector with session state persistence
- 2+3 column layout for KPI metrics
- Color-coded metric displays based on performance
- Error handling for data unavailability

### Chart Data Interface
[Source: apps/backend/chart_data.py symbols overview]
Available chart data functions:
- `format_production_chart_data()` - Returns time-series data for production charts
- `format_collection_rate_chart_data()` - Returns percentage data for collection rate trends
- `format_new_patients_chart_data()` - Returns integer counts for patient acquisition
- `format_treatment_acceptance_chart_data()` - Returns percentage data for treatment acceptance
- `format_hygiene_reappointment_chart_data()` - Returns percentage data for hygiene reappointments
- `format_all_chart_data()` - Returns combined data structure for all KPIs

### Historical Data Context
[Source: docs/stories/story-2.1.md completion notes]
- Historical data collection spans 30+ days
- Operational day logic implemented (Monday-Saturday)
- Currency parsing fixes ensure proper numerical calculations
- Latest available data logic handles weekend/holiday fallbacks

### Performance Requirements
[Source: docs/prds/epic-2.md]
- Dashboard loads charts in <3 seconds with historical data
- Architecture supports adding new chart types with <1 day development effort
- Maintain existing 90%+ test coverage

### Testing

#### Testing Standards
[Source: docs/architecture/backend/testing-strategy.md]

**Test File Location:** `tests/test_chart_components.py`

**Testing Framework:** Manual validation scripts (pytest framework planned for Story 1.6)

**Test Patterns Required:**
- Arrange-Act-Assert pattern for test structure
- Mock Google API responses for consistent testing
- Test error conditions: empty data, invalid credentials

**Specific Testing Requirements for Charts:**
- Chart rendering with various data scenarios (empty, partial, full datasets)
- Timeframe switching functionality (daily/weekly/monthly)
- Performance testing with 30+ days of data
- Error handling when chart data is unavailable
- Business day filtering validation
- Chart interaction testing (zoom, hover, pan)

**Manual Validation Points:**
```python
# Chart Component Test
chart_data = format_production_chart_data(days=30)
chart = create_production_chart(chart_data)
assert chart is not None
assert len(chart.data) > 0

# Timeframe Switching Test
daily_data = get_daily_chart_data(days=30)
weekly_data = get_weekly_chart_data(days=30)
monthly_data = get_monthly_chart_data(days=30)
assert all(data is not None for data in [daily_data, weekly_data, monthly_data])

# Performance Test
import time
start_time = time.time()
charts = create_all_kpi_charts(days=30)
load_time = time.time() - start_time
assert load_time < 3.0  # 3 second requirement
```

**Coverage Goals:**
- 90%+ coverage for new chart component functions
- Integration tests for chart data pipeline
- Performance validation for chart rendering

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2025-09-23 | 1.0 | Initial story creation | Bob (Scrum Master) |

## Dev Agent Record

*This section will be populated by the development agent during implementation*

### Agent Model Used
*To be filled by dev agent*

### Debug Log References
*To be filled by dev agent*

### Completion Notes List
*To be filled by dev agent*

### File List
*To be filled by dev agent*

## QA Results

*Results from QA Agent review will be populated here after implementation*
