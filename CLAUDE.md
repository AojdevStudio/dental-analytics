# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
**COMPLETED**: Full-stack dental analytics dashboard that reads KPI data from Google Sheets, processes it with pandas, and displays metrics in a Streamlit web interface. Built for KamDental practice to automate daily production, collection rate, new patient count, treatment acceptance, and hygiene reappointment tracking.

**Status**: ✅ **Stories 1.1-1.5 Complete** - All 5 KPIs implemented with Streamlit dashboard
**Current Line Count**: 249 lines (Backend: 169 + Frontend: 80)
**Goal Achieved**: 5 KPI dashboard operational with brand styling

## Development Commands

### Environment Management
```bash
# Create and activate environment
uv sync

# Run application
uv run streamlit run frontend/app.py

# Access dashboard
# Local URL: http://localhost:8501
```

### Package Management
```bash
# Add new dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Update all packages
uv sync --upgrade

# Show installed packages
uv pip list
```

### Testing Commands
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=backend --cov=frontend

# Run specific test file
uv run pytest tests/test_metrics.py

# Run tests in watch mode
uv run pytest-watch
```

### Code Quality Commands

**Quick Scripts (Recommended):**
```bash
# Run comprehensive quality checks (Black, Ruff, MyPy, pytest, coverage)
./scripts/quality-check.sh

# Quick test run (pytest + manual calculations, no coverage)
./scripts/quick-test.sh

# Auto-format code (Black + Ruff fixes)
./scripts/format-code.sh
```

**Individual Tools:**
```bash
# Format code with Black
uv run black backend/ frontend/ tests/ test_calculations.py

# Lint with Ruff
uv run ruff check backend/ frontend/ tests/ test_calculations.py

# Type checking with MyPy
uv run mypy backend/ test_calculations.py

# Run pre-commit hooks
uv run pre-commit run --all-files

# Install/update pre-commit hooks
uv run pre-commit install
```

**Coverage Analysis:**
```bash
# Run tests with detailed coverage report
uv run pytest --cov=backend --cov-report=html

# View coverage report in browser
open htmlcov/index.html
```

### Development Tools
```bash
# Interactive Python shell with project context
uv run python

# Jupyter notebook for data exploration
uv run jupyter notebook

# Test Google Sheets connection and KPI data
uv run python -c "from backend.metrics import get_all_kpis; print(get_all_kpis())"
```
### Dashboard Testing Procedures
```bash
# Start dashboard server
uv run streamlit run frontend/app.py

# Access dashboard locally
# URL: http://localhost:8501

# Test complete data flow
uv run python test_calculations.py

# Verify KPI calculations manually
uv run python -c "from backend.metrics import get_all_kpis; print(get_all_kpis())"
```

### Memory & Knowledge System

- **Markdown-based storage** in `.serena/memories/` directories
- **Project-specific knowledge** persistence across sessions
- **Contextual retrieval** based on relevance
- **Onboarding support** for new projects

## Technology Stack

### Core Technologies ✅ Implemented
- **Python 3.10+**: Primary language
- **uv**: Dependency management and project runner
- **Streamlit**: Frontend web framework (dashboard live)
- **pandas**: Data processing and analysis

### UI/UX Stack ✅ Complete
- **Streamlit**: Web dashboard framework
- **Brand Colors**: Navy (#142D54), Teal (#007E9E) 
- **Layout**: 2-column primary + 3-column secondary metrics
- **Theme Configuration**: Custom .streamlit/config.toml

### Data Science & ML ✅ Implemented
- **pandas>=2.1**: Data manipulation and analysis
- **plotly>=5.17**: Interactive charts (future phase)

### External APIs ✅ Connected
- **google-auth>=2.23**: Google authentication
- **google-api-python-client>=2.103**: Google Sheets API client
- **Google Sheets Integration**: Live KPI data retrieval

### Testing Framework (Story 1.6 Pending)
- **pytest**: Test runner (to be implemented)
- **pytest-cov**: Coverage reporting (to be implemented)
- **Manual Tests**: Current test_calculations.py

### Code Quality Tools ✅ Active
- **black**: Code formatting
- **ruff**: Modern linting (replaced flake8)
- **mypy**: Type checking with modern Python 3.10+ syntax

## Project Structure Guidelines

### File Organization
```
dental-analytics/
├── frontend/
│   ├── app.py                    # Streamlit dashboard (80 lines) ✅
│   └── .streamlit/
│       └── config.toml           # Brand theme config ✅
├── backend/
│   ├── __init__.py
│   ├── sheets_reader.py          # Google Sheets API (77 lines) ✅
│   └── metrics.py                # KPI calculations (92 lines) ✅
├── config/
│   └── credentials.json          # Google API credentials
├── tests/                        # Manual test suite (Story 1.6 pending)
│   └── test_calculations.py      # Current manual tests
├── docs/stories/                 # Story documentation
│   ├── story-1.1.md             # Project setup ✅
│   ├── story-1.2.md             # Production & collection ✅
│   ├── story-1.3.md             # New patients & treatment ✅
│   ├── story-1.4.md             # Hygiene reappointment ✅
│   ├── story-1.5.md             # Streamlit dashboard ✅
│   └── story-1.6.md             # Testing framework (pending)
├── pyproject.toml               # Project configuration
└── uv.lock                      # Dependency lockfile
```

### Naming Conventions
- Follow the naming conventions in the @ai-docs/naming-conventions.md file.

### Documentation Standards
- Use clear, descriptive filenames
- Include creation/modification dates
- Link related documents
- Maintain consistent formatting
- Update index.md when adding new sections

#### Standard Metadata Structure for All Markdown Files

```yaml
---
title: "Document Title"
description: "A brief, one-sentence summary of the document's purpose."
category: "Primary Category"
subcategory: "Secondary Category"
product_line: "Associated Product"
audience: "Intended Audience"
status: "Document Status"
author: "AOJDevStudio"
created_date: "YYYY-MM-DD"
last_updated: "YYYY-MM-DD"
tags:
  - keyword1
  - keyword2
  - keyword3
---
```

## Python Guidelines

### Type Hints
```python
from typing import Dict, List, Optional
import pandas as pd

def calculate_kpis(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate all 5 core KPIs from dental data."""
    pass

def get_sheet_data(spreadsheet_id: str, range_name: str) -> Optional[pd.DataFrame]:
    """Fetch data from Google Sheets."""
    pass
```

### Code Style
- Follow PEP 8 style guide
- Use meaningful names: `production_total` not `pt`
- Keep functions focused: one KPI calculation per function
- Use docstrings for all public functions
- Limit line length to 88 characters (Black default)

### Best Practices
```python
# Good: Use pandas for data operations
production_total = df['Production'].sum()

# Good: Use pathlib for file paths
from pathlib import Path
credentials_path = Path("config/credentials.json")

# Good: Use context managers
try:
    result = service.spreadsheets().values().get(...)
except Exception as e:
    logger.error(f"Failed to read sheet: {e}")
    return None

# Good: Use logging instead of print
import logging
logger = logging.getLogger(__name__)
```

## Testing Standards

### Test Structure
```python
# tests/test_metrics.py
import pytest
import pandas as pd
from backend.metrics import calculate_production_total, calculate_collection_rate

class TestKPICalculations:
    def test_production_total_calculation(self):
        # Arrange
        test_data = pd.DataFrame({
            'Production': [1000, 2000, 1500]
        })

        # Act
        result = calculate_production_total(test_data)

        # Assert
        assert result == 4500

    def test_collection_rate_calculation(self):
        # Arrange
        test_data = pd.DataFrame({
            'Production': [1000, 2000],
            'Collections': [900, 1800]
        })

        # Act
        result = calculate_collection_rate(test_data)

        # Assert
        assert result == 90.0  # (2700/3000) * 100
```

### Coverage Goals
- **90%+ coverage** for backend business logic
- **Unit tests** for all KPI calculations
- **Integration tests** for Google Sheets connection
- **Mock Google API** responses in tests
- **Test error conditions**: empty data, invalid credentials

### pytest Configuration
```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "--cov=backend --cov=frontend --cov-report=term-missing"
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError"
]
```
## Working with the Codebase

- Project uses Python 3.11 with `uv` for dependency management
- Strict typing with mypy, formatted with black + ruff
- Language servers run as separate processes with LSP communication
- Memory system enables persistent project knowledge
- Context/mode system allows workflow customization

## Current Project Status

### Completed Stories ✅
- **Story 1.1**: Project foundation with Google Sheets connection
- **Story 1.2**: Daily production and collection rate calculations  
- **Story 1.3**: New patient count and treatment acceptance tracking
- **Story 1.4**: Hygiene reappointment rate monitoring
- **Story 1.5**: Streamlit dashboard with brand styling

### Next Steps
- **Story 1.6**: Pytest testing framework implementation
- **Future**: Real-time data refresh, historical trends

### Dashboard Access
- **Local URL**: http://localhost:8501
- **Start Command**: `uv run streamlit run frontend/app.py`
- **All 5 KPIs**: Production, Collection Rate, New Patients, Treatment Acceptance, Hygiene Reappointment

## Dental Practice Specific Guidelines

### Implemented KPI Formulas ✅
```python
# Production Total: Sum of daily production (Column E)
def calculate_production_total(df: pd.DataFrame) -> float | None:
    return float(pd.to_numeric(df["total_production"], errors="coerce").sum())

# Collection Rate: (Collections / Production) × 100  
def calculate_collection_rate(df: pd.DataFrame) -> float | None:
    collections = pd.to_numeric(df["total_collections"], errors="coerce").sum()
    production = pd.to_numeric(df["total_production"], errors="coerce").sum()
    return float((collections / production) * 100)

# New Patients: Count from Column J
def calculate_new_patients(df: pd.DataFrame) -> int | None:
    return int(pd.to_numeric(df["new_patients"], errors="coerce").sum())

# Treatment Acceptance: (Scheduled / Presented) × 100
def calculate_treatment_acceptance(df: pd.DataFrame) -> float | None:
    scheduled = pd.to_numeric(df["treatments_scheduled"], errors="coerce").sum()
    presented = pd.to_numeric(df["treatments_presented"], errors="coerce").sum()
    return float((scheduled / presented) * 100)

# Hygiene Reappointment: ((Total - Not Reappointed) / Total) × 100
def calculate_hygiene_reappointment(df: pd.DataFrame) -> float | None:
    total_hygiene = pd.to_numeric(df["total_hygiene_appointments"], errors="coerce").sum()
    not_reappointed = pd.to_numeric(df["patients_not_reappointed"], errors="coerce").sum()
    return float(((total_hygiene - not_reappointed) / total_hygiene) * 100)
```

### Data Sources ✅ Configured
- **EOD Sheets**: "EOD - Baytown Billing!A:N" (Production, Collections, New Patients)
- **Front KPI Sheets**: "Front KPI - Baytown!A:N" (Treatment Acceptance, Hygiene Reappointment)
- **Spreadsheet ID**: 1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8

### Dashboard Brand Implementation ✅
- **Primary Navy**: #142D54 (headers, text)
- **Teal Accent**: #007E9E (metrics, good status)
- **Emergency Red**: #BB0A0A (poor metrics)
- **Clean Layout**: 2+3 column responsive design
- **Error Handling**: "Data Unavailable" for failed metrics

### Production Error Handling ✅ Implemented
```python
# Robust error handling in all KPI calculations
def calculate_metric(df: pd.DataFrame | None) -> float | None:
    if df is None or df.empty:
        return None
    try:
        # Safe numeric conversion with error handling
        values = pd.to_numeric(df["column"], errors="coerce").sum()
        # Division by zero protection
        if denominator == 0:
            return None
        return float(calculation_result)
    except KeyError:
        return None  # Missing column gracefully handled

# Dashboard displays "Data Unavailable" for None values
if kpis.get("metric_name") is not None:
    st.metric(label="LABEL", value=f"${kpis['metric_name']:,.0f}")
else:
    st.metric(label="LABEL", value="Data Unavailable")
```
