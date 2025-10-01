# Developer Checklist: Analytics Enhancement Epic - Multi-Location Support

**PRD Reference:** [../prds/ENG-200-analytics-enhancement-epic.md]
**Issue ID:** ENG-200
**Priority:** High
**Estimated Time:** 2-4 Weeks

## Pre-Development

- [ ] Review PRD and acceptance criteria for Analytics Enhancement Epic
- [ ] Set up epic branch: `epic/ENG-200-analytics-enhancement`
- [ ] Review existing codebase patterns:
  - [ ] `/apps/backend/data_providers.py` - Google Sheets integration patterns
  - [ ] `/backend/metrics.py` - KPI calculation structure
  - [ ] `/frontend/app.py` - Streamlit dashboard organization
  - [ ] `/tests/` - Testing patterns and coverage standards
- [ ] Identify integration points for multi-location support
- [ ] Confirm Google Sheets access for both Baytown and Humble locations
- [ ] Validate current 99% test coverage baseline

## Story 2.1: Multi-Location Architecture Foundation

### Backend Architecture Setup

- [ ] **Location Configuration System**
  - [ ] Create `config/locations.py` with location mappings
  - [ ] Define location metadata structure (names, sheet indices, sheet names)
  - [ ] Add location validation and error handling
  - [ ] Create location enumeration and selection logic

- [ ] **LocationManager Class Implementation**
  - [ ] Create `backend/location_manager.py`
  - [ ] Implement `get_all_locations() -> List[str]`
  - [ ] Implement `get_location_data(location: str) -> pd.DataFrame`
  - [ ] Implement `get_combined_data() -> pd.DataFrame`
  - [ ] Add location-specific error handling and isolation

- [ ] **Backend/Frontend Interface Contracts**
  - [ ] Design data exchange formats (JSON-serializable)
  - [ ] Create interface documentation for frontend consumption
  - [ ] Implement abstract base classes for frontend adapters
  - [ ] Define error response formats for location failures

### Testing Framework Setup

- [ ] **Multi-Location Test Structure**
  - [ ] Create `tests/test_location_manager.py`
  - [ ] Set up test fixtures for multi-location data
  - [ ] Create mock data generators for both locations
  - [ ] Implement location-specific test scenarios

- [ ] **Test Coverage Validation**
  - [ ] Run baseline coverage: `uv run pytest --cov=backend --cov-report=html`
  - [ ] Document current coverage percentages
  - [ ] Set up coverage tracking for new modules

## Story 2.2: Enhanced Data Layer

### Concurrent Google Sheets Reading

- [ ] **Enhanced Sheets Provider**
  - [ ] Extend `apps/backend/data_providers.py` for multi-location support
  - [ ] Implement concurrent API calls with connection pooling
  - [ ] Add rate limiting and retry logic
  - [ ] Create location-aware caching mechanism

- [ ] **Location-Specific Data Validation**
  - [ ] Add data format validation per location
  - [ ] Implement cross-location data consistency checks
  - [ ] Create data cleaning pipelines for each location
  - [ ] Add missing data interpolation strategies

- [ ] **Error Isolation and Recovery**
  - [ ] Implement graceful failure handling per location
  - [ ] Add fallback mechanisms for partial data availability
  - [ ] Create error reporting and alerting system
  - [ ] Test recovery scenarios for single location failures

### Performance Optimization

- [ ] **Multi-Location Call Optimization**
  - [ ] Implement async/await for concurrent sheet reading
  - [ ] Add connection pooling for Google Sheets API
  - [ ] Create intelligent caching with TTL policies
  - [ ] Optimize DataFrame operations for large datasets

- [ ] **Load Time Testing**
  - [ ] Measure baseline single-location load times
  - [ ] Test multi-location data retrieval performance
  - [ ] Validate <5 second load time requirement
  - [ ] Profile and optimize bottlenecks

## Story 2.3: Combined Analytics Engine

### Enhanced Metrics Implementation

- [ ] **Enhanced Metrics Module**
  - [ ] Create `backend/enhanced_metrics.py`
  - [ ] Implement `calculate_location_kpis(location: str) -> Dict[str, float]`
  - [ ] Implement `calculate_combined_kpis() -> Dict[str, float]`
  - [ ] Implement `get_comparative_metrics() -> Dict[str, Dict[str, float]]`

- [ ] **Data Aggregation Algorithms**
  - [ ] Design aggregation strategies for each KPI type:
    - [ ] Production Total: Sum across locations
    - [ ] Collection Rate: Weighted average by production
    - [ ] New Patients: Sum across locations
    - [ ] Treatment Acceptance: Weighted average by cases presented
    - [ ] Hygiene Reappointment: Weighted average by appointments
  - [ ] Implement error handling for missing location data
  - [ ] Add validation for aggregated results

- [ ] **Analytics Engine Development**
  - [ ] Create `backend/analytics_engine.py`
  - [ ] Implement `get_trend_analysis(days: int) -> Dict[str, List[float]]`
  - [ ] Implement `get_location_comparison() -> Dict[str, Dict[str, float]]`
  - [ ] Implement `get_performance_insights() -> List[Dict[str, str]]`

### Advanced Analytics Features

- [ ] **Trend Analysis**
  - [ ] Calculate rolling averages for KPIs
  - [ ] Implement growth rate calculations
  - [ ] Add seasonal adjustment algorithms
  - [ ] Create trend visualization data structures

- [ ] **Comparative Analytics**
  - [ ] Location performance ranking algorithms
  - [ ] Benchmark identification and reporting
  - [ ] Performance gap analysis
  - [ ] Best practice identification logic

## Story 2.4: Frontend Location Controls

### Location Selection Interface

- [ ] **UI Component Development**
  - [ ] Add location selector dropdown in Streamlit
  - [ ] Implement "All Locations", "Baytown", "Humble" options
  - [ ] Create location-specific dashboard layouts
  - [ ] Add visual indicators for selected location

- [ ] **View Switching Logic**
  - [ ] Implement state management for location selection
  - [ ] Add data refresh logic for location changes
  - [ ] Create smooth transitions between views
  - [ ] Preserve user preferences across sessions

- [ ] **Dashboard Layout Updates**
  - [ ] Modify metric displays for multi-location data
  - [ ] Add comparative visualizations
  - [ ] Implement location-specific color coding
  - [ ] Create combined vs individual view layouts

### Frontend Framework Abstraction

- [ ] **Dashboard Controller**
  - [ ] Create `frontend/dashboard_controller.py`
  - [ ] Implement `set_location_filter(location: str) -> None`
  - [ ] Implement `get_current_metrics() -> Dict[str, Any]`
  - [ ] Implement `refresh_data() -> bool`

- [ ] **API-Style Backend Interface**
  - [ ] Create data formatting functions for frontend consumption
  - [ ] Implement JSON serialization for all data structures
  - [ ] Add consistent error response formatting
  - [ ] Create mock backend for frontend testing

## Story 2.5: Testing & Quality Assurance

### Comprehensive Test Suite

- [ ] **Unit Test Development**
  - [ ] Complete `tests/test_location_manager.py`:
    - [ ] Test location enumeration and validation
    - [ ] Test individual location data retrieval
    - [ ] Test combined location data aggregation
    - [ ] Test error handling for invalid locations

  - [ ] Complete `tests/test_enhanced_metrics.py`:
    - [ ] Test all 5 KPIs for individual locations
    - [ ] Test combined KPI calculations
    - [ ] Test comparative metrics generation
    - [ ] Test edge cases (missing data, zero values)

  - [ ] Complete `tests/test_analytics_engine.py`:
    - [ ] Test trend analysis calculations
    - [ ] Test location comparison algorithms
    - [ ] Test performance insight generation
    - [ ] Test data validation and error handling

- [ ] **Integration Test Implementation**
  - [ ] Create `tests/test_multi_location_integration.py`
  - [ ] Test complete data flow from Sheets to dashboard
  - [ ] Test concurrent API calls and performance
  - [ ] Test error isolation between locations
  - [ ] Test caching and data consistency

### Performance and Quality Testing

- [ ] **Performance Validation**
  - [ ] Load test with both locations: `uv run python tests/performance_test.py`
  - [ ] Measure and document load times for each view
  - [ ] Validate <5 second requirement compliance
  - [ ] Test with simulated network delays and failures

- [ ] **Quality Gate Validation**
  - [ ] Run comprehensive test suite: `uv run pytest --cov=backend --cov-report=html`
  - [ ] Verify 90%+ test coverage maintained
  - [ ] Run code quality checks: `./scripts/quality-check.sh`
  - [ ] Validate all pre-commit hooks pass
  - [ ] Test CI/CD pipeline with new code

### End-to-End User Workflow Testing

- [ ] **Dashboard Functionality Testing**
  - [ ] Test initial load with "All Locations" view
  - [ ] Test switching to "Baytown Only" view
  - [ ] Test switching to "Humble Only" view
  - [ ] Test data refresh in each view mode
  - [ ] Test error handling when one location fails

- [ ] **Browser and Device Testing**
  - [ ] Test on Chrome, Firefox, Safari
  - [ ] Test on desktop (1920x1080) resolution
  - [ ] Test on tablet (1024x768) resolution
  - [ ] Test mobile responsiveness
  - [ ] Validate KamDental branding consistency

## Development Commands Reference

### Environment Setup
```bash
# Activate environment and install dependencies
uv sync

# Run application
uv run streamlit run frontend/app.py
```

### Testing Commands
```bash
# Run all tests with coverage
uv run pytest --cov=backend --cov=frontend --cov-report=html

# Run specific test modules
uv run pytest tests/test_location_manager.py -v
uv run pytest tests/test_enhanced_metrics.py -v
uv run pytest tests/test_analytics_engine.py -v

# Run performance tests
uv run python tests/performance_test.py
```

### Quality Assurance
```bash
# Run comprehensive quality checks
./scripts/quality-check.sh

# Individual quality tools
uv run black backend/ frontend/ tests/
uv run ruff check backend/ frontend/ tests/
uv run mypy backend/ frontend/
```

### Google Sheets Testing
```bash
# Test multi-location data retrieval
uv run python -c "
from backend.location_manager import LocationManager
lm = LocationManager()
print('Locations:', lm.get_all_locations())
print('Baytown Data Shape:', lm.get_location_data('baytown').shape)
print('Combined Data Shape:', lm.get_combined_data().shape)
"

# Test enhanced metrics
uv run python -c "
from backend.enhanced_metrics import EnhancedMetrics
em = EnhancedMetrics()
print('Baytown KPIs:', em.calculate_location_kpis('baytown'))
print('Combined KPIs:', em.calculate_combined_kpis())
"
```

## Deployment & Verification

### Pre-Deployment Checklist

- [ ] **Code Quality Validation**
  - [ ] All tests pass: `uv run pytest`
  - [ ] Code coverage ≥90%: Check HTML coverage report
  - [ ] No linting errors: `uv run ruff check`
  - [ ] Type checking passes: `uv run mypy backend/`
  - [ ] Code formatted: `uv run black --check backend/ frontend/ tests/`

- [ ] **Performance Validation**
  - [ ] Multi-location dashboard loads in <5 seconds
  - [ ] All location switching operations complete quickly
  - [ ] Memory usage remains stable during extended use
  - [ ] Google Sheets API rate limits not exceeded

### Pull Request Preparation

- [ ] **PR Documentation**
  - [ ] Create PR with clear description of epic changes
  - [ ] Include screenshots of multi-location dashboard views
  - [ ] Document performance metrics and test coverage
  - [ ] Link to PRD: "Implements ENG-200"

- [ ] **Code Review Preparation**
  - [ ] Self-review all changes for clarity and consistency
  - [ ] Ensure backward compatibility with existing functionality
  - [ ] Validate that single-location operations still work
  - [ ] Check for proper error handling in all new code

### Post-Deployment Verification

- [ ] **Functional Verification**
  - [ ] Verify dashboard loads at http://localhost:8501
  - [ ] Test all location selection options work correctly
  - [ ] Validate KPI calculations for each location and combined view
  - [ ] Test error scenarios (network failures, missing data)
  - [ ] Verify Google Sheets data synchronization

- [ ] **Architecture Verification**
  - [ ] Confirm backend/frontend separation maintained
  - [ ] Validate API-style interfaces work correctly
  - [ ] Test mock backend scenarios for frontend development
  - [ ] Verify location configuration system scalability

## Quality Standards Compliance

- [ ] **Code Standards**
  - [ ] All Python code follows PEP 8 via Black formatting
  - [ ] No Ruff violations in new or modified code
  - [ ] 100% MyPy compliance for all public APIs
  - [ ] Comprehensive docstrings for all new functions

- [ ] **Testing Standards**
  - [ ] Unit test coverage ≥90% for all new backend modules
  - [ ] Integration tests cover all multi-location workflows
  - [ ] End-to-end tests validate complete user scenarios
  - [ ] Performance tests validate load time requirements

- [ ] **Documentation Standards**
  - [ ] All new modules documented in project architecture
  - [ ] API interfaces clearly defined and documented
  - [ ] README updated with multi-location setup instructions
  - [ ] Troubleshooting guide updated for location-specific issues

## Risk Mitigation

### Technical Risk Monitoring

- [ ] **Google Sheets API Risks**
  - [ ] Monitor API usage against rate limits
  - [ ] Test authentication token refresh scenarios
  - [ ] Validate data consistency between location sheets
  - [ ] Implement comprehensive error logging

- [ ] **Performance Risk Monitoring**
  - [ ] Profile memory usage with large datasets
  - [ ] Monitor concurrent API call performance
  - [ ] Test caching effectiveness and TTL policies
  - [ ] Validate responsive performance under load

### Rollback Preparation

- [ ] **Backward Compatibility Assurance**
  - [ ] All existing single-location functionality preserved
  - [ ] Original dashboard layout remains accessible
  - [ ] No breaking changes to existing API interfaces
  - [ ] Configuration changes are additive only

- [ ] **Emergency Procedures**
  - [ ] Document rollback procedures for configuration changes
  - [ ] Create branch protection for critical system files
  - [ ] Establish monitoring and alerting for system health
  - [ ] Prepare communication plan for any user-facing issues

## Epic Completion Criteria

- [ ] **All Stories Completed**
  - [ ] Story 2.1: Multi-Location Architecture Foundation ✓
  - [ ] Story 2.2: Enhanced Data Layer ✓
  - [ ] Story 2.3: Combined Analytics Engine ✓
  - [ ] Story 2.4: Frontend Location Controls ✓
  - [ ] Story 2.5: Testing & Quality Assurance ✓

- [ ] **All PRD Acceptance Criteria Met**
  - [ ] Multi-location data retrieval operational
  - [ ] Combined and individual location reporting working
  - [ ] Performance requirements satisfied (<5 second loads)
  - [ ] Backend/frontend separation maintained
  - [ ] Test coverage ≥90% maintained

- [ ] **Quality Gates Passed**
  - [ ] CI/CD pipeline passes with all checks
  - [ ] Code quality standards met (Black, Ruff, MyPy)
  - [ ] Comprehensive test suite passes
  - [ ] Performance benchmarks satisfied
  - [ ] Documentation updated and accurate

- [ ] **Production Readiness**
  - [ ] Manual verification completed successfully
  - [ ] Error handling tested and validated
  - [ ] User workflows tested across all scenarios
  - [ ] System monitoring and alerting configured
  - [ ] Epic marked as Done in project management system

## Notes

**Development Environment:**
- Python 3.12 with uv dependency management
- Streamlit for frontend (with migration preparation)
- Google Sheets API for data sources
- pytest for comprehensive testing
- Quality automation via pre-commit hooks

**Key Architecture Decisions:**
- Maintain strict backend/frontend separation for technology flexibility
- Implement location-aware error isolation for system resilience
- Use configuration-driven location management for scalability
- Preserve all existing functionality for zero-disruption deployment

**Performance Targets:**
- <5 second dashboard load times for all views
- <2 second location switching response times
- 99%+ uptime with graceful error handling
- Support for future expansion to additional locations
