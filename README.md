# Dental Analytics Dashboard

✅ **COMPLETED**: Full-stack dental analytics dashboard that reads KPI data from Google Sheets, processes it with pandas, and displays metrics in a Streamlit web interface. Built for KamDental practice to automate daily production, collection rate, new patient count, treatment acceptance, and hygiene reappointment tracking.

## Project Status
- **Stories 1.1-1.5**: ✅ Complete
- **Story 2.0**: ✅ Complete - Project Structure Refactoring
- **Total Lines**: 283 (Backend: 169 + Frontend: 114)
- **Dashboard**: 🚀 Live at http://localhost:8501
- **All 5 KPIs**: ✅ Operational with brand styling
- **Next**: Story 1.6 - pytest testing framework

## Quick Start

### Dashboard Access
```bash
# Install dependencies
uv sync

# Start dashboard server
uv run streamlit run apps/frontend/app.py

# View dashboard in browser
# Local URL: http://localhost:8501
```

### Verify KPI Data
```bash
# Test all KPI calculations
uv run python -c "from apps.backend.metrics import get_all_kpis; print(get_all_kpis())"

# Run manual test suite
uv run python test_calculations.py
```

### Configuration ✅ Complete
1. ✅ Google Cloud project with Sheets API enabled
2. ✅ Service account credentials configured 
3. ✅ Credentials saved as `config/credentials.json`
4. ✅ Target spreadsheet access: `1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8`
5. ✅ Data sources connected:
   - **EOD Sheets**: "EOD - Baytown Billing!A:N" (Production, Collections, New Patients)
   - **Front KPI Sheets**: "Baytown Front KPIs Form responses!A:N" (Treatment Acceptance, Hygiene Reappointment)

## Dashboard Features ✅

- **5 Core KPIs**: Daily Production, Collection Rate, New Patients, Treatment Acceptance, Hygiene Reappointment
- **Brand Styling**: KamDental colors (Navy #142D54, Teal #007E9E)
- **Responsive Layout**: 2-column primary + 3-column secondary metrics
- **Real-time Data**: Live Google Sheets integration with automatic refresh
- **Error Handling**: "Data Unavailable" display for failed metrics
- **Performance**: <3 second load time, optimized data calls

## Architecture ✅ Complete

- **Backend**: Python modules (`sheets_reader.py` 77 lines, `metrics.py` 92 lines)
- **Frontend**: Streamlit dashboard (`app.py` 80 lines) with custom theming
- **Data**: Google Sheets API with robust error handling
- **Testing**: Manual test suite (Story 1.6: pytest framework pending)

## Technology Stack ✅ Implemented

### Core Framework
- **Python 3.10+**: Modern typing with `|` union syntax
- **Streamlit 1.30+**: Web dashboard with custom theme configuration
- **pandas 2.1+**: Data processing with robust error handling
- **Google Sheets API v4**: Real-time KPI data retrieval
- **uv**: Fast dependency management and task runner

### UI/UX Implementation 
- **Brand Colors**: Navy (#142D54), Teal (#007E9E), White (#FFFFFF)
- **Layout**: Responsive column-based design
- **Typography**: Clean sans-serif fonts
- **Theme Config**: Custom `.streamlit/config.toml`

### Code Quality
- **Black**: Code formatting
- **Ruff**: Modern Python linting
- **MyPy**: Type checking with modern syntax
- **Error Handling**: Comprehensive None-safe patterns

## Project Structure ✅ Complete

### Directory Layout

```
dental-analytics/
├── apps/                          # Application source code (Story 2.0)
│   ├── frontend/                  # Streamlit web interface
│   │   ├── app.py                 # Main dashboard (114 lines) ✅
│   │   └── .streamlit/
│   │       └── config.toml        # Brand theme configuration ✅
│   └── backend/                   # Business logic and data access
│       ├── __init__.py            # Package initialization
│       ├── sheets_reader.py       # Google Sheets API client (77 lines) ✅
│       └── metrics.py             # KPI calculation functions (92 lines) ✅
├── config/                        # Configuration and credentials
│   └── credentials.json           # Google API service account credentials ✅
├── docs/                          # Documentation and project artifacts
│   ├── stories/                   # User story documentation
│   │   ├── story-1.1.md          # Project setup ✅
│   │   ├── story-1.2.md          # Production & collections ✅
│   │   ├── story-1.3.md          # New patients & treatment ✅
│   │   ├── story-1.4.md          # Hygiene reappointment ✅
│   │   ├── story-1.5.md          # Streamlit dashboard ✅
│   │   └── story-2.0.md          # Project structure refactoring ✅
│   ├── qa/                       # Quality assurance artifacts
│   ├── prd/                      # Product requirements
│   └── architecture/             # System architecture documentation
├── tests/                         # Test suite
│   ├── conftest.py               # Shared test fixtures
│   ├── test_metrics.py           # KPI calculation unit tests
│   ├── test_sheets_reader.py     # Data retrieval integration tests
│   ├── test_gdrive_validation.py # Google Drive validation tests
│   ├── fixtures/                 # Test data and mock objects
│   └── integration/              # End-to-end integration tests
├── scripts/                       # Development and maintenance scripts
│   ├── format-code.sh            # Code formatting automation
│   ├── quality-check.sh          # Comprehensive quality validation
│   └── quick-test.sh             # Fast test execution
├── test_calculations.py           # Manual test suite for validation
├── pyproject.toml                # Project configuration and dependencies
├── uv.lock                       # Dependency lock file
├── CLAUDE.md                     # Claude Code development guide
└── README.md                     # This documentation
```

### Architecture Overview for Maintainers

This project follows a **clean architecture pattern** with clear separation of concerns:

#### 🏗️ **Application Layer (`apps/`)**

- **`apps/frontend/`**: Presentation layer
  - Single-page Streamlit application
  - Brand-themed UI components
  - Real-time KPI visualization
  - Error handling and user feedback

- **`apps/backend/`**: Business logic and data access layer
  - `metrics.py`: KPI calculation algorithms
  - `sheets_reader.py`: External data source integration
  - Pure functions with clear input/output contracts
  - Comprehensive error handling

#### 🧪 **Testing Strategy**

- **Unit Tests**: Individual function and method testing
- **Integration Tests**: Component interaction validation
- **Manual Tests**: End-to-end workflow verification
- **Coverage Target**: 90%+ for backend business logic

#### 📚 **Documentation Structure**

- **Stories**: Feature implementation history and requirements
- **QA Reports**: Quality assurance findings and resolutions
- **Architecture**: System design and technical decisions
- **Guides**: Development workflow and troubleshooting

### Key Design Principles

#### 🔄 **Clean Architecture**
- Clear separation between presentation, business logic, and data access
- Dependency injection pattern for testability
- Interface-based design for flexibility

#### 🛡️ **Error Handling**
- Graceful degradation on data source failures
- User-friendly error messages in UI
- Comprehensive logging for debugging
- None-safe patterns throughout codebase

#### 📊 **Data Flow**
```
Google Sheets → SheetsReader → Metrics Calculator → Streamlit UI
     ↓              ↓              ↓               ↓
  Raw Data    DataFrames    KPI Objects    Dashboard
```

#### 🧪 **Testing Pyramid**
```
End-to-End Tests (Integration)
    ↕️
Unit Tests (Business Logic)
    ↕️
Manual Tests (Workflow Validation)
```

### Development Workflow

#### 🚀 **Getting Started**
```bash
# Setup environment
uv sync

# Start development
uv run streamlit run apps/frontend/app.py

# Run tests
uv run pytest tests/ -v

# Check code quality
uv run ruff check apps/backend/ apps/frontend/
uv run mypy apps/backend/
```

#### 📝 **Adding New Features**
1. Create user story in `docs/stories/`
2. Implement backend logic in `apps/backend/`
3. Add UI components in `apps/frontend/`
4. Write comprehensive tests
5. Update documentation

#### 🔧 **Code Quality Standards**
- **Formatting**: Black (88 character line length)
- **Linting**: Ruff (comprehensive Python linting)
- **Type Checking**: MyPy (strict mode)
- **Testing**: pytest with 90%+ coverage target

### Maintenance Guidelines

#### 📁 **File Organization**
- Keep business logic in `apps/backend/`
- UI components in `apps/frontend/`
- Tests mirror application structure
- Documentation in `docs/` with clear categorization

#### 🔗 **Import Structure**
- Use absolute imports within apps: `from apps.backend.metrics import calculate_kpi`
- Relative imports within packages: `from .sheets_reader import SheetsReader`
- No circular dependencies between frontend and backend

#### 🏷️ **Naming Conventions**
- Functions: `snake_case` (e.g., `calculate_production_total`)
- Classes: `PascalCase` (e.g., `SheetsReader`)
- Constants: `UPPER_CASE` (e.g., `SPREADSHEET_ID`)
- Files: `snake_case.py` (e.g., `sheets_reader.py`)

#### 📊 **Performance Considerations**
- KPI calculations are optimized for real-time display
- Google Sheets API calls are cached where appropriate
- Error handling doesn't impact performance
- Memory usage is minimal for single-user application

### Troubleshooting Guide

#### 🔍 **Common Issues**
- **Import Errors**: Check Python path and ensure `apps/` is in sys.path
- **Google API Errors**: Verify credentials.json and spreadsheet permissions
- **Test Failures**: Check mock patch paths match new structure
- **UI Issues**: Verify Streamlit configuration and theme files

#### 🐛 **Debugging Steps**
1. Check logs for error messages
2. Verify environment setup with `uv sync`
3. Test individual components in isolation
4. Review recent changes for import path issues

This structure provides a solid foundation for maintainable, scalable development while preserving the simplicity that makes this project effective for dental practice analytics.

## Testing

### Running Tests
```bash
# Run all tests with coverage
uv run pytest --cov=apps.backend --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_metrics.py

# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Generate HTML coverage report
uv run pytest --cov=apps.backend --cov-report=html
# View report: open htmlcov/index.html
```

### Test Coverage Requirements
- Backend modules: 90% minimum coverage
- All KPI calculations have unit tests
- Integration tests verify full data flow
- G-Drive validation tests ensure correct column mappings

## KPI Calculations ✅ Implemented

### Daily Production
- **Source**: EOD - Baytown Billing (Column E: total_production)
- **Formula**: `sum(total_production)`
- **Display**: Currency format with thousands separator

### Collection Rate  
- **Source**: EOD - Baytown Billing (Columns E, F: total_production, total_collections)
- **Formula**: `(total_collections / total_production) × 100`
- **Display**: Percentage with 1 decimal place

### New Patients
- **Source**: EOD - Baytown Billing (Column J: new_patients)
- **Formula**: `sum(new_patients)`
- **Display**: Integer count

### Treatment Acceptance
- **Source**: Baytown Front KPIs Form responses (treatments_scheduled, treatments_presented)
- **Formula**: `(treatments_scheduled / treatments_presented) × 100`
- **Display**: Percentage with 1 decimal place

### Hygiene Reappointment
- **Source**: Baytown Front KPIs Form responses (total_hygiene_appointments, patients_not_reappointed)
- **Formula**: `((total_hygiene - not_reappointed) / total_hygiene) × 100`
- **Display**: Percentage with 1 decimal place

## Development Commands

```bash
# Start dashboard
uv run streamlit run apps/frontend/app.py

# Test KPI calculations
uv run python test_calculations.py

# Check code quality
uv run black apps/backend/ apps/frontend/
uv run ruff check apps/backend/ apps/frontend/
uv run mypy apps/backend/

# Verify Google Sheets connection
uv run python -c "from apps.backend.metrics import get_all_kpis; print(get_all_kpis())"
```

## Next Steps (Story 1.6)

- [ ] Implement pytest testing framework
- [ ] Add automated test coverage reporting
- [ ] Create CI/CD pipeline integration
- [ ] Performance optimization and monitoring

## Troubleshooting

### Dashboard Won't Load
- Verify credentials: `config/credentials.json` exists and valid
- Check Google Sheets access: service account has viewer permissions
- Test backend: `uv run python -c "from apps.backend.metrics import get_all_kpis; print(get_all_kpis())"`

### "Data Unavailable" Displayed
- Check Google Sheets API quota and permissions
- Verify sheet names and column mappings in `apps/backend/metrics.py`
- Review logs for specific error messages

### Dependencies Issues
- Update environment: `uv sync --upgrade`
- Clear cache: `uv cache clean`
- Reinstall: `rm uv.lock && uv sync`