# Dental Analytics Dashboard - Project Overview

## Purpose
Simple dental analytics dashboard built for KamDental practice to automate KPI tracking. The goal is to display 5 core metrics from Google Sheets data in under 200 lines of code:
- Daily production totals
- Collection rate percentage
- New patient count
- Treatment acceptance rate
- Hygiene reappointment tracking

## Technology Stack
- **Python 3.10+**: Primary language
- **uv**: Modern Python package and project manager
- **Streamlit**: Web framework for dashboard UI
- **pandas>=2.1**: Data processing and analysis
- **Google Sheets API**: Data source integration
  - google-auth>=2.23
  - google-api-python-client>=2.103
- **Testing**: pytest with pytest-cov for coverage
- **Code Quality**: black (formatting), flake8 (linting), mypy (type checking)

## Project Structure
```
dental-analytics/
├── frontend/
│   └── app.py             # Streamlit UI (100 lines max)
├── backend/
│   ├── __init__.py
│   ├── data_providers.py   # Google Sheets API (50 lines)
│   └── metrics.py         # KPI calculations (50 lines)
├── config/
│   └── credentials.json   # Google API credentials
├── tests/
│   ├── test_data_providers.py
│   └── test_metrics.py
├── pyproject.toml         # Project configuration
└── uv.lock               # Dependency lockfile
```

## Current Status
- Documentation and planning phase complete
- Core implementation not yet started
- No pyproject.toml or dependencies installed yet
- Git repository initialized on development branch
