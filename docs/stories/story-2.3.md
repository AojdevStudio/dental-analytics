# Story 2.3: Advanced Chart Features and Dashboard Integration

## Status
Draft

## Story
**As a** practice manager,
**I want** advanced chart features including time-range selection and full dashboard integration,
**so that** I can analyze historical trends and have charts fully integrated into my workflow.

## Acceptance Criteria

1. **Time Range Selection**: User can switch between "Daily", "Weekly", and "Monthly" time-series views
2. **Trend Analysis**: Charts display trend lines and identify patterns in historical performance
3. **Business Day Handling**: Charts properly handle weekends/holidays without showing misleading "zero" data
4. **Dashboard Integration**: Charts are fully integrated with existing dashboard layout and location selector
5. **Performance**: Dashboard loads historical charts in <3 seconds for 30+ days of data
6. **Scalability**: Architecture supports adding new chart types and timeframes with minimal code changes

## Tasks / Subtasks

- [ ] **Task 1: Add Time Range Selection UI** (AC: 1, 3)
  - [ ] Add radio buttons or selectbox for "Daily", "Weekly", "Monthly" timeframe selection
  - [ ] Implement session state management for timeframe persistence
  - [ ] Create data aggregation logic for weekly and monthly views
  - [ ] Add business day filtering that respects operational schedule (Monday-Saturday)

- [ ] **Task 2: Enhance Charts with Advanced Features** (AC: 2, 3)
  - [ ] Add trend line calculations and pattern identification to each chart
  - [ ] Implement advanced hover tooltips with detailed historical KPI information
  - [ ] Add chart zoom, pan, and reset functionality
  - [ ] Implement business day logic to handle weekend/holiday gaps properly

- [ ] **Task 3: Integrate Charts with Dashboard** (AC: 4)
  - [ ] Replace existing static metrics with interactive chart displays
  - [ ] Maintain current KPI metric cards above charts for quick reference
  - [ ] Add chart containers that work with existing location selector
  - [ ] Implement loading states and error handling for chart data
  - [ ] Ensure charts update properly when location is changed

- [ ] **Task 4: Performance Optimization** (AC: 5, 6)
  - [ ] Implement chart data caching using Streamlit's caching mechanisms
  - [ ] Optimize chart rendering for 30+ days of historical data
  - [ ] Add lazy loading for charts that aren't immediately visible
  - [ ] Profile dashboard performance and ensure <3 second load times
  - [ ] Create extensible architecture for adding new chart types

## Dev Notes

### Previous Story Context
[Source: docs/stories/story-2.2.md] Story 2.2 implemented the basic Plotly integration with:
- Plotly dependency installed and configured
- Basic chart component module in `apps/frontend/chart_components.py`
- Integration with existing chart data functions from `apps/backend/chart_data.py`
- Basic chart functions for all 5 KPIs with hover tooltips
- Foundation for advanced features

### Prerequisites from Story 2.1 & 2.2
[Source: docs/stories/story-2.1.md] Story 2.1 implemented the historical data foundation with:
- `HistoricalDataManager` class providing time-series data collection
- Chart data processing functions in `apps/backend/chart_data.py`
- Currency parsing fixes for historical calculations
- Framework-agnostic backend design supporting frontend flexibility

[Source: docs/stories/story-2.2.md] Story 2.2 implemented basic Plotly charts with:
- Plotly installed and configured for Streamlit
- Chart component module with KamDental branding
- Integration with existing chart data functions
- Basic chart rendering for all 5 KPIs

### Relevant Source Tree Information
[Source: docs/architecture/source-tree.md]

**Frontend Structure:**
```
apps/frontend/
├── __init__.py              # Module initialization
├── app.py                   # Main Streamlit application
└── chart_components.py      # Chart component module (from Story 2.2)
```

**Backend Chart Data Module:**
```
apps/backend/chart_data.py   # Chart data processing functions
- format_production_chart_data()
- format_collection_rate_chart_data()
- format_new_patients_chart_data()
- format_case_acceptance_chart_data()
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
from apps.frontend.chart_components import create_production_chart, create_collection_rate_chart  # New from Story 2.2
```

### Technical Implementation Details
[Source: docs/architecture/fullstack/technology-stack.md]

**Core Technologies:**
- Frontend: Streamlit 1.30+
- Data Processing: pandas 2.1+
- Visualization: plotly (added in Story 2.2)
- Language: Python 3.10+
- Package Manager: uv

**Time Range Implementation:**
- Daily: Direct data from chart_data functions
- Weekly: Aggregate daily data into weekly periods
- Monthly: Aggregate daily data into monthly periods
- Business Day Logic: Monday-Saturday operational schedule

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
- `format_case_acceptance_chart_data()` - Returns percentage data for treatment acceptance
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

**Test File Location:** `tests/test_chart_integration.py` (advanced features)

**Testing Framework:** Manual validation scripts (pytest framework planned for Story 1.6)

**Test Patterns Required:**
- Arrange-Act-Assert pattern for test structure
- Mock Google API responses for consistent testing
- Test error conditions: empty data, invalid credentials

**Specific Testing Requirements for Advanced Charts:**
- Time-range switching functionality (daily/weekly/monthly)
- Performance testing with 30+ days of data
- Error handling when chart data is unavailable
- Business day filtering validation
- Chart interaction testing (zoom, hover, pan, reset)
- Dashboard integration with location selector
- Chart update behavior when location changes

**Manual Validation Points:**
```python
# Time Range Switching Test
daily_charts = create_all_charts(timeframe="daily", days=30)
weekly_charts = create_all_charts(timeframe="weekly", days=30)
monthly_charts = create_all_charts(timeframe="monthly", days=30)
assert all(charts is not None for charts in [daily_charts, weekly_charts, monthly_charts])

# Performance Test
import time
start_time = time.time()
charts = create_dashboard_with_charts(location="baytown", days=30)
load_time = time.time() - start_time
assert load_time < 3.0  # 3 second requirement

# Dashboard Integration Test
location_switch_test = test_location_chart_updates("baytown", "humble")
assert location_switch_test.success

# Business Day Logic Test
weekend_data = get_chart_data_for_weekend()
assert weekend_data.handles_gaps_properly
```

**Coverage Goals:**
- 90%+ coverage for advanced chart functionality
- Integration tests for time-range switching
- Performance validation for chart rendering with historical data

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2025-09-23 | 1.0 | Initial story creation - split from Story 2.2 | Bob (Scrum Master) |

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