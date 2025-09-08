# Dental Analytics Dashboard

✅ **COMPLETED**: Full-stack dental analytics dashboard that reads KPI data from Google Sheets, processes it with pandas, and displays metrics in a Streamlit web interface. Built for KamDental practice to automate daily production, collection rate, new patient count, treatment acceptance, and hygiene reappointment tracking.

## Project Status
- **Stories 1.1-1.5**: ✅ Complete 
- **Total Lines**: 249 (Target: <200)
- **Dashboard**: 🚀 Live at http://localhost:8501
- **All 5 KPIs**: ✅ Operational with brand styling
- **Next**: Story 1.6 - pytest testing framework

## Quick Start

### Dashboard Access
```bash
# Install dependencies
uv sync

# Start dashboard server
uv run streamlit run frontend/app.py

# View dashboard in browser
# Local URL: http://localhost:8501
```

### Verify KPI Data
```bash
# Test all KPI calculations
uv run python -c "from backend.metrics import get_all_kpis; print(get_all_kpis())"

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
   - **Front KPI Sheets**: "Front KPI - Baytown!A:N" (Treatment Acceptance, Hygiene Reappointment)

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

```
dental-analytics/
├── frontend/
│   ├── app.py                    # Main dashboard (80 lines) ✅
│   └── .streamlit/
│       └── config.toml           # Brand theme config ✅
├── backend/
│   ├── __init__.py
│   ├── sheets_reader.py          # Google Sheets API (77 lines) ✅
│   └── metrics.py                # KPI calculations (92 lines) ✅
├── config/
│   └── credentials.json          # Google API credentials ✅
├── docs/
│   └── stories/                  # Development documentation
│       ├── story-1.1.md         # Project setup ✅
│       ├── story-1.2.md         # Production & collections ✅
│       ├── story-1.3.md         # New patients & treatment ✅
│       ├── story-1.4.md         # Hygiene reappointment ✅
│       ├── story-1.5.md         # Streamlit dashboard ✅
│       └── story-1.6.md         # Testing framework ✅
├── tests/                        # Pytest test suite ✅
│   ├── conftest.py             # Shared fixtures
│   ├── test_metrics.py         # KPI calculation tests
│   ├── test_sheets_reader.py   # Data retrieval tests
│   ├── test_gdrive_validation.py # Spreadsheet validation
│   ├── fixtures/               # Test data
│   └── integration/            # Integration tests
├── test_calculations.py          # Manual test suite ✅
├── pytest.ini                   # Pytest configuration ✅
├── .coveragerc                  # Coverage settings ✅
├── pyproject.toml               # Project configuration
├── uv.lock                      # Dependency lockfile
├── CLAUDE.md                    # Claude development guide
└── README.md                    # This file
```

## Testing

### Running Tests
```bash
# Run all tests with coverage
uv run pytest --cov=backend --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_metrics.py

# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Generate HTML coverage report
uv run pytest --cov=backend --cov-report=html
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
- **Source**: Front KPI - Baytown (treatments_scheduled, treatments_presented)
- **Formula**: `(treatments_scheduled / treatments_presented) × 100`
- **Display**: Percentage with 1 decimal place

### Hygiene Reappointment
- **Source**: Front KPI - Baytown (total_hygiene_appointments, patients_not_reappointed)
- **Formula**: `((total_hygiene - not_reappointed) / total_hygiene) × 100`
- **Display**: Percentage with 1 decimal place

## Development Commands

```bash
# Start dashboard
uv run streamlit run frontend/app.py

# Test KPI calculations
uv run python test_calculations.py

# Check code quality
uv run black backend/ frontend/
uv run ruff check backend/ frontend/
uv run mypy backend/

# Verify Google Sheets connection
uv run python -c "from backend.metrics import get_all_kpis; print(get_all_kpis())"
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
- Test backend: `uv run python -c "from backend.metrics import get_all_kpis; print(get_all_kpis())"`

### "Data Unavailable" Displayed
- Check Google Sheets API quota and permissions
- Verify sheet names and column mappings in `backend/metrics.py`
- Review logs for specific error messages

### Dependencies Issues
- Update environment: `uv sync --upgrade`
- Clear cache: `uv cache clean`
- Reinstall: `rm uv.lock && uv sync`