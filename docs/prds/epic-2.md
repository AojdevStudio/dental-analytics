# PRD: Analytics Enhancement Epic - Historical Data Visualization

## Metadata

- **Epic ID:** Epic-2
- **Priority:** High
- **Status:** Draft
- **Created:** 2025-09-15
- **Updated:** 2025-09-15 (Project Structure Enhancement Added)
- **Estimated Effort:** 2-4 Weeks (including 0.5 day structure refactoring)
- **Developer Checklist:** [../checklists/epic-2-developer-checklist.md]

## Executive Summary

The Analytics Enhancement Epic transforms the successful dental analytics dashboard from static daily reporting to dynamic historical data visualization and trend analysis. Building on the complete MVP with 99% test coverage and 5 core KPIs, this epic adds historical data collection, interactive charts using Plotly, and time-series analysis capabilities while maintaining backend/frontend architectural separation to enable future technology stack migration from Streamlit to modern frameworks like Next.js or Vue.js.

This enhancement provides dental practice management with powerful visual insights into performance trends, enabling data-driven decision making through interactive charts, historical comparisons, and predictive analytics while preserving the clean architecture that enables frontend technology flexibility.

## Problem Statement

### What

Transform the existing static daily KPI dashboard into a dynamic historical analytics platform with interactive time-series visualizations, trend analysis, and historical data insights while expanding data sources and analytical capabilities.

### Why

**Business Justification:**
- Current dashboard shows only current-day metrics without historical context
- Management needs trend analysis to identify patterns and seasonal variations
- Historical data visualization enables performance benchmarking and goal setting
- Interactive charts provide deeper insights than static metric displays
- Visual analytics supports data-driven decision making and strategic planning

**Impact Metrics:**
- Enable trend identification across daily, weekly, and monthly timeframes
- Reduce time spent analyzing performance patterns from hours to minutes
- Support predictive insights through historical data analysis
- Improve decision-making confidence with visual data representation
- Establish foundation for advanced analytics and business intelligence

### Context

**Current State:**
- Complete MVP dashboard with 5 KPIs: Production Total, Collection Rate, New Patients, Treatment Acceptance, Hygiene Reappointment
- Backend (363 lines): Google Sheets integration, pandas processing, metrics calculations
- Frontend (135 lines): Streamlit dashboard with KamDental branding
- Tests (207 lines): 99% coverage with automated quality gates
- Data Sources: EOD Billing sheets and Front KPI sheets for single location

**Target State:**
- Historical analytics platform with interactive time-series visualizations
- Daily, weekly, and monthly trend analysis for all 5 core KPIs
- Enhanced data collection supporting historical analysis
- Interactive Plotly charts integrated with Streamlit dashboard
- Maintained backend/frontend separation for technology flexibility
- Scalable architecture supporting future analytics and visualization features

## Goals & Success Metrics

### Primary Goals

1. **Historical Data Collection**: Successfully retrieve and store time-series data for trend analysis
2. **Interactive Visualization**: Implement Plotly charts for all 5 core KPIs with daily/weekly/monthly views
3. **Architecture Scalability**: Maintain clean backend/frontend separation supporting future technology migration
4. **Enhanced Analytics**: Expand data sources and analytical capabilities beyond basic KPIs
5. **Quality Maintenance**: Preserve 90%+ test coverage and code quality standards

### Success Metrics

- **Functional**: All 5 KPIs display as interactive charts with historical data spanning 30+ days
- **Performance**: Dashboard loads charts in <3 seconds with historical data
- **Architecture**: Backend API completely independent of frontend technology
- **Quality**: Maintain 90%+ test coverage across all new functionality
- **User Experience**: Management can switch between daily/weekly/monthly views in <2 clicks
- **Extensibility**: Adding new chart types or timeframes requires <1 day development effort

## User Stories

### Primary User Stories

- As a **practice owner**, I want to view historical trends for all KPIs so that I can identify performance patterns and seasonal variations
- As a **practice manager**, I want to see daily/weekly/monthly charts so that I can track progress toward goals and identify improvement opportunities
- As a **dentist**, I want to visualize patient flow and treatment acceptance trends so that I can optimize scheduling and case presentation
- As a **developer**, I want a clean backend API so that I can migrate to modern frontend frameworks without affecting business logic
- As a **developer**, I want a well-organized project structure so that I can easily navigate and maintain the codebase
- As a **business analyst**, I want interactive charts with drill-down capabilities so that I can perform deeper performance analysis

### Edge Cases

- When historical data is missing for certain days (weekends/holidays), display gaps in charts without breaking trend lines
- When displaying "current" metrics, show the latest available business day data (Friday data on Sunday/Monday)
- When Google Sheets connection fails, display cached historical data with "offline mode" indicator
- When switching between daily/weekly/monthly views, maintain user's current KPI focus
- When new data sources are added, existing charts and visualizations remain unaffected

## Acceptance Criteria

### Functional Requirements

- [ ] **Project Structure Refactoring**: `frontend/` and `backend/` directories successfully moved to `apps/` structure
- [ ] **Historical Data Collection**: Backend successfully retrieves time-series data spanning 30+ days from Google Sheets
- [ ] **Latest Available Data Logic**: "Current" metrics display the most recent business day data (Friday data shown on weekends)
- [ ] **Interactive Chart Display**: All 5 KPIs display as interactive Plotly charts with zoom, hover, and pan capabilities
- [ ] **Time Range Selection**: User can switch between "Daily", "Weekly", and "Monthly" time-series views
- [ ] **Trend Analysis**: Charts display trend lines and identify patterns in historical performance
- [ ] **Business Day Handling**: Charts properly handle weekends/holidays without showing misleading "zero" data
- [ ] **Data Source Expansion**: Additional historical metrics beyond the original 5 KPIs are available
- [ ] **Backend API Separation**: Frontend communicates with backend only through well-defined functions/APIs
- [ ] **Error Resilience**: Missing historical data points don't break chart rendering or trend analysis

### Non-Functional Requirements

- [ ] **Performance**: Dashboard loads historical charts in <3 seconds for 30+ days of data
- [ ] **Scalability**: Architecture supports adding new chart types and timeframes with minimal code changes
- [ ] **Maintainability**: Frontend technology can be replaced without modifying backend logic
- [ ] **Reliability**: 99%+ uptime with graceful handling of Google Sheets API issues and data gaps
- [ ] **Security**: All existing security controls maintained with historical data access
- [ ] **Test Coverage**: Maintain 90%+ test coverage across all new functionality

## Technical Specification

### Architecture Overview

**Enhanced 3-Layer Architecture:**

1. **Data Layer** (Enhanced):
   - Multi-location Google Sheets readers
   - Location-aware data validation and cleaning
   - Centralized configuration for location mappings

2. **Business Logic Layer** (New):
   - Location-agnostic KPI calculation engine
   - Data aggregation and combination logic
   - Enhanced analytics and metrics processing

3. **Presentation Layer** (Abstracted):
   - Frontend-agnostic data formatting
   - Location selection and filtering logic
   - API-style interface for frontend consumption

**Project Structure Changes:**
- **New Structure**: `apps/frontend/` and `apps/backend/` directories
- **Migration Path**: Existing functionality moved to new structure
- **Import Updates**: All internal imports updated to reflect new paths
- **Backward Compatibility**: Maintain existing functionality during transition

### API Changes

**New Backend Modules:**

```python
# backend/historical_data.py
class HistoricalDataManager:
    def get_time_series_data(days: int) -> pd.DataFrame
    def get_latest_available_data() -> pd.DataFrame
    def get_business_day_data(date: datetime) -> pd.DataFrame
    def fill_weekend_gaps() -> pd.DataFrame

# backend/enhanced_metrics.py
class EnhancedMetrics:
    def calculate_historical_kpis(days: int) -> Dict[str, List[float]]
    def calculate_latest_kpis() -> Dict[str, float]
    def get_trend_analysis() -> Dict[str, Dict[str, float]]

# backend/chart_data.py
class ChartDataProcessor:
    def prepare_plotly_data(kpi: str, timeframe: str) -> Dict[str, Any]
    def get_daily_series(days: int) -> Dict[str, List]
    def get_weekly_aggregates() -> Dict[str, List]
    def get_monthly_aggregates() -> Dict[str, List]
```

**Enhanced Frontend Interface:**

```python
# frontend/chart_controller.py
class ChartController:
    def set_timeframe_filter(timeframe: str) -> None  # daily/weekly/monthly
    def get_current_metrics() -> Dict[str, Any]  # latest available data
    def get_chart_data(kpi: str) -> Dict[str, Any]
    def refresh_data() -> bool
```

### Data Model Changes

**Historical Data Configuration:**

```python
# config/data_sources.py
DATA_SOURCES = {
    'eod_billing': {
        'sheet_name': 'EOD - Baytown Billing',
        'date_column': 'Submission Date',
        'business_days_only': True,
        'latest_fallback': True  # Use latest available on weekends
    },
    'front_kpis': {
        'sheet_name': 'Baytown Front KPIs Form responses',
        'date_column': 'Submission Date',
        'business_days_only': True,
        'latest_fallback': True
    }
}

CHART_CONFIG = {
    'default_days': 30,
    'max_days': 90,
    'business_days_only': True,
    'weekend_fallback': 'latest_available'
}
```

**Historical Metrics Structure:**

```python
HistoricalMetrics = {
    'date_range': {
        'start_date': datetime,
        'end_date': datetime,
        'latest_available': datetime  # Most recent business day
    },
    'time_series': {
        'production_total': List[Tuple[datetime, float]],
        'collection_rate': List[Tuple[datetime, float]],
        'new_patients': List[Tuple[datetime, int]],
        'treatment_acceptance': List[Tuple[datetime, float]],
        'hygiene_reappointment': List[Tuple[datetime, float]]
    },
    'latest_values': {
        'production_total': float,
        'collection_rate': float,
        'new_patients': int,
        'treatment_acceptance': float,
        'hygiene_reappointment': float,
        'data_date': datetime  # Date of latest available data
    },
    'trends': {
        'weekly_average': Dict[str, float],
        'monthly_average': Dict[str, float],
        'trend_direction': Dict[str, str]  # 'up', 'down', 'stable'
    }
}
```

### Integration Points

**Google Sheets API Enhancement:**
- Multi-sheet concurrent reading with connection pooling
- Location-specific error handling and retry logic
- Cached data layer for improved performance

**Frontend Framework Preparation:**
- RESTful-style backend interface design
- JSON-serializable data structures
- Stateless backend operations

**Enhanced Analytics Integration:**
- Trend analysis calculations
- Performance benchmarking algorithms
- Comparative reporting engine

### Technical Constraints

**Existing System Preservation:**
- All current functionality must remain operational
- No breaking changes to existing interfaces
- Backward compatibility with single-location operations

**Project Structure Changes:**
- Maintain existing functionality during directory restructuring
- Update all import paths and references appropriately
- Ensure backward compatibility during transition
- No disruption to existing deployment or CI/CD processes

**Performance Requirements:**
- Maximum 5-second load time for multi-location data
- Concurrent Google Sheets API calls for efficiency
- Caching strategy to minimize API rate limits

**Architecture Flexibility:**
- Backend must support any frontend framework
- Clear separation of concerns between layers
- Minimal coupling between components

## Testing Requirements

### Unit Testing

**New Test Coverage Required:**
- Location manager functionality (100% coverage)
- Enhanced metrics calculations (100% coverage)
- Multi-location data aggregation (100% coverage)
- Error handling for partial location failures (100% coverage)

**Test Files to Create:**
- `tests/test_location_manager.py`
- `tests/test_enhanced_metrics.py`
- `tests/test_analytics_engine.py`
- `tests/test_multi_location_integration.py`

### Integration Testing

**Multi-Location Data Flow:**
- Successful data retrieval from both Baytown and Humble sheets
- Correct aggregation of location data into combined metrics
- Proper error isolation when one location fails
- Performance testing with concurrent API calls

**Google Sheets API Testing:**
- Rate limit handling with multiple location requests
- Authentication token refresh across location calls
- Network failure recovery and retry logic

### E2E Testing

**User Workflow Testing:**
- Switch between "All Locations", "Baytown", and "Humble" views
- Verify correct KPI display for each location selection
- Test dashboard responsiveness with multi-location data
- Validate error messaging for location-specific failures

**Frontend Framework Preparation:**
- Mock backend API for frontend development
- Data format validation for different frontend frameworks
- Interface contract testing

## Implementation Roadmap

### Story 2.0: Project Structure Refactoring (NEW)
**Effort: 0.5 days**

- Create new `apps/` directory structure
- Move `frontend/` directory to `apps/frontend/`
- Move `backend/` directory to `apps/backend/`
- Update all import paths and references
- Verify all existing functionality still works
- Update documentation with new structure

### Story 2.1: Historical Data Foundation & Latest Data Logic
**Effort: 3-4 days**

- Implement time-series data collection from Google Sheets
- Create "latest available data" logic for business days
- Add date range functionality to existing data layer
- Create historical data aggregation functions
- Handle weekend/holiday data gaps intelligently

### Story 2.2: Plotly Chart Integration
**Effort: 2-3 days**

- Install and configure Plotly for Streamlit
- Create interactive charts for all 5 KPIs
- Add daily/weekly/monthly view toggles
- Implement hover details and chart interactions

### Story 2.3: Enhanced Analytics Engine
**Effort: 4-5 days**

- Develop trend analysis algorithms
- Implement comparative performance metrics
- Create time-series calculations and forecasting
- Add business day logic to all analytical functions

### Story 2.4: Data Source Expansion
**Effort: 3-4 days**

- Identify and integrate additional Google Sheets
- Expand beyond current EOD + Front KPI data
- Add new calculated metrics and KPIs
- Ensure latest-data logic applies to all sources

### Story 2.5: Testing & Quality Assurance
**Effort: 2-3 days**

- Complete comprehensive test suite including business day logic
- Performance testing with historical data loads
- Chart rendering and interaction testing
- Quality gate validation
- Documentation updates

## Definition of Done

- [ ] All acceptance criteria met for functional and non-functional requirements
- [ ] Project structure refactored with `apps/frontend/` and `apps/backend/` directories
- [ ] Multi-location support operational for both Baytown and Humble locations
- [ ] Combined and individual location reporting working correctly
- [ ] Backend/frontend separation maintained with clear API boundaries
- [ ] 90%+ test coverage across all new functionality
- [ ] Performance requirements met (<5 second load times)
- [ ] Code quality standards maintained (Black, Ruff, MyPy compliance)
- [ ] CI/CD pipeline passes with all quality gates
- [ ] Documentation updated for new multi-location architecture
- [ ] Manual verification completed for all user workflows
- [ ] Frontend framework migration path validated

## References

- **Current Architecture**: `/docs/architecture/fullstack-architecture.md`
- **Data Structure**: `/docs/architecture/data/google-sheets-structure.md`
- **Epic 1 Documentation**: `/docs/prd/epic-1-complete-dental-analytics-dashboard.md`
- **Testing Framework**: `/docs/stories/story-1.6-testing-framework.md`
- **Quality Standards**: `/docs/validation/quality-strategy.md`

## Risk Mitigation

**Technical Risks:**
- Google Sheets API rate limits → Implement caching and request batching
- Data inconsistency between locations → Add validation and reconciliation
- Performance degradation → Optimize concurrent processing and caching

**Architectural Risks:**
- Frontend framework migration complexity → Maintain strict backend/frontend separation
- Location expansion scalability → Design generic location configuration system
- Backward compatibility issues → Preserve existing single-location interfaces

**Business Risks:**
- User workflow disruption → Implement progressive enhancement approach
- Data accuracy concerns → Enhance validation and error reporting
- Management reporting delays → Ensure fallback to existing functionality
