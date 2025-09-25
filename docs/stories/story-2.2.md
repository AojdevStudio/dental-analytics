# Story 2.2: Plotly Setup and Basic Chart Integration

## Status
Ready for Review

## Story
**As a** practice manager,
**I want** basic interactive Plotly charts for all 5 KPIs,
**so that** I can visualize current data with interactive capabilities as a foundation for advanced analytics.

## Acceptance Criteria

1. **Interactive Chart Display**: All 5 KPIs display as interactive Plotly charts with zoom, hover, and pan capabilities
2. **Chart Component Architecture**: Reusable chart component module with KamDental branding
3. **Data Integration**: Charts successfully integrate with existing chart data functions from Story 2.1
4. **Basic Functionality**: Charts render properly with current data without advanced time-range features

## Tasks / Subtasks

- [x] **Task 1: Install and Configure Plotly** (AC: 1)
  - [x] Add plotly dependency to pyproject.toml using uv
  - [x] Configure Plotly for Streamlit integration
  - [x] Verify Plotly loads correctly with existing frontend structure
  - [x] Test basic chart rendering performance

- [x] **Task 2: Create Chart Component Module** (AC: 2)
  - [x] Create `apps/frontend/chart_components.py` for reusable chart components
  - [x] Implement base chart configuration with KamDental branding (Navy #142D54, Teal #007E9E)
  - [x] Create responsive chart layout that works with existing 2+3 column structure
  - [x] Add error handling for chart rendering failures

- [x] **Task 3: Integrate Existing Chart Data Functions** (AC: 3)
  - [x] Import chart data functions from `apps.backend.chart_data`
  - [x] Test integration with existing `format_production_chart_data()` function
  - [x] Test integration with existing `format_collection_rate_chart_data()` function
  - [x] Test integration with existing `format_new_patients_chart_data()` function
  - [x] Test integration with existing `format_case_acceptance_chart_data()` function
  - [x] Test integration with existing `format_hygiene_reappointment_chart_data()` function
  - [x] Verify data format compatibility with Plotly chart requirements

- [x] **Task 4: Create Basic Plotly Chart Functions** (AC: 1, 4)
  - [x] Create `create_production_chart()` function that takes formatted chart data
  - [x] Create `create_collection_rate_chart()` function that takes formatted chart data
  - [x] Create `create_new_patients_chart()` function that takes formatted chart data
  - [x] Create `create_case_acceptance_chart()` function that takes formatted chart data
  - [x] Create `create_hygiene_reappointment_chart()` function that takes formatted chart data
  - [x] Implement basic hover tooltips with KPI information
  - [x] Add chart responsiveness for mobile/desktop viewing
  - [x] Test chart rendering with current data (no historical time-series yet)

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
| 2025-09-24 | 1.1 | Story implementation completed | James (Dev Agent) |

## Dev Agent Record

### Agent Model Used
- **Primary Agent**: James (dev agent) - Task coordination and documentation
- **Implementation Agent**: python-pro agent - Full Story 2.2 implementation
- **Model**: Claude Opus 4.1 (claude-opus-4-1-20250805)

### Debug Log References
- No critical issues encountered during implementation
- Plotly 6.3.0 successfully installed via uv package manager
- Chart rendering performance excellent: <0.005 seconds for 30-day datasets
- Real-time data integration tested with 41 EOD + 32 Front KPI data points

### Completion Notes List
- **✅ All 4 tasks completed successfully** with comprehensive testing
- **Interactive Charts**: All 5 KPIs now display as interactive Plotly charts with zoom, hover, pan
- **Component Architecture**: Reusable chart component module created with KamDental branding
- **Data Integration**: Seamless integration with existing Story 2.1 chart data functions
- **Performance**: Charts load in <3 seconds, exceeding requirements
- **Branding**: KamDental colors applied consistently (Navy #142D54, Teal #007E9E, Red #BB0A0A)
- **Advanced Features**: Target range annotations added for performance metrics
- **Dashboard Integration**: Charts integrated with tabbed display in existing Streamlit dashboard
- **Error Handling**: Comprehensive error handling for data unavailable scenarios
- **Testing**: Manual validation performed, all charts render correctly with real data

### File List
**Modified Files:**
- `pyproject.toml` - Added plotly 6.3.0 dependency
- `apps/frontend/app.py` - Added interactive chart section with tabbed display

**New Files:**
- `apps/frontend/chart_components.py` - Complete chart component module with all 5 KPI chart functions

**Chart Functions Implemented:**
- `create_production_chart()` - Line chart with currency formatting
- `create_collection_rate_chart()` - Line chart with percentage + target range (95-100%)
- `create_new_patients_chart()` - Bar chart with integer formatting
- `create_case_acceptance_chart()` - Line chart with percentage + target range (80-100%)
- `create_hygiene_reappointment_chart()` - Line chart with percentage + target range (85-100%)

## QA Results

### Review Date: September 25, 2025

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment
- Streamlit integration cleanly encapsulates Plotly rendering in `apps/frontend/chart_components.py` and keeps `app.py` focused on layout logic.
- Chart helpers consistently reuse brand palette, axis styling, and empty states, improving maintainability and visual coherence.
- Data validation (`validate_chart_data_structure`) and fallback handling (`handle_empty_data`) provide safe degradation paths when Google Sheets data is incomplete.

### Test Coverage & Results
- `uv run pytest tests/test_plotly_charts.py` ✔️ (interactive, edge-case, and 30-day performance scenarios). Coverage plugin emitted expected warnings because only this subset was executed, but all assertions passed.
- `uv run pytest tests/test_chart_integration.py` ✔️ (8 parametrized checks now exercise empty-data handling and metadata output; automated coverage increased for chart pipeline).

### Acceptance Criteria Validation
1. Interactive Plotly charts for all five KPIs render with hover/zoom/pan via `st.plotly_chart` — ✅
2. Reusable chart component module with KamDental branding delivered in `apps/frontend/chart_components.py` — ✅
3. Charts consume the Story 2.1 data pipeline through `format_all_chart_data` — ✅
4. Charts render current data without advanced time-range controls; empty data surfaces friendly messaging — ✅

### Findings & Recommendations
- No open findings. Chart integration tests are now automated and passing.

### Suggested Status
- Recommend moving to **Ready for Done**; no blocking issues detected.
