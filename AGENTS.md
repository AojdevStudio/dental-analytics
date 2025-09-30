# AGENTS.md

This file provides guidance to AI agents when working with agents in this repository.

## Project Overview
Full-stack dental analytics dashboard that reads KPI data from Google Sheets, processes it with pandas, and displays metrics in a Streamlit web interface. Built for KamDental practice to automate daily production, collection rate, new patient count, treatment acceptance, and hygiene reappointment tracking.

**Current Architecture**: view @docs/architecture/fullstack-architecture.md
**Multi-Location**: Baytown and Humble locations with unified data access
**Historical Data**: Time-series KPI analysis with operational date logic

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
```bash
# Format code
uv run black .

# Check code style
uv run flake8 backend/ frontend/

# Type checking
uv run mypy backend/ frontend/

# Run all quality checks
uv run pre-commit run --all-files
```

### Development Tools
```bash
# Interactive Python shell with project context
uv run python

# Jupyter notebook for data exploration
uv run jupyter notebook

# Test Google Sheets connection
uv run python -c "from backend.sheets_reader import test_connection; test_connection()"
```
### Memory & Knowledge System

- **Markdown-based storage** in `.serena/memories/` directories
- **Project-specific knowledge** persistence across sessions
- **Contextual retrieval** based on relevance
- **Onboarding support** for new projects

## Technology Stack

### Core Technologies
- **Python 3.10+**: Primary language
- **uv**: Dependency management and project runner
- **Streamlit**: Frontend web framework
- **pandas**: Data processing and analysis

### Data Science & ML
- **pandas>=2.1**: Data manipulation and analysis
- **plotly>=5.17**: Interactive charts (future phase)

### External APIs
- **google-auth>=2.23**: Google authentication
- **google-api-python-client>=2.103**: Google Sheets API client

### Testing Framework
- **pytest**: Test runner
- **pytest-cov**: Coverage reporting

### Code Quality Tools
- **black**: Code formatting
- **flake8**: Style checking
- **mypy**: Type checking

## Project Structure Guidelines

### File Organization
```
dental-analytics/
├── frontend/
│   └── app.py             # Streamlit UI (100 lines max)
├── backend/
│   ├── __init__.py
│   ├── sheets_reader.py   # Google Sheets API (50 lines)
│   └── metrics.py         # KPI calculations (50 lines)
├── config/
│   └── credentials.json   # Google API credentials
├── tests/                 # Test files (mirror backend structure)
│   ├── test_sheets_reader.py
│   └── test_metrics.py
├── pyproject.toml         # Project configuration
└── uv.lock               # Dependency lockfile
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
### Strict Typing with Narrow Expectations
- ALWAYS yse TypedDicts for:
    - Chart data structures
    - KPI response structures
    - Any function returning structured dicts
- ALWAYS use Plotly types:
    - go.Layout instead of dict[str, Any]
    - layout.XAxism layout.YAxis for axis configs
    - Import from plotly.graph_objects.layout submodules
- ONLY allow Any for:
    - YAML ingestion: config: dict[str, Any] = yaml.safe_load(f)
    - Reason: YAML is external, untyped data source we don't control
- NEVER use Any for:
    - Function return types (use TypedDict)
    - Plotly configurations (use Plotly-stubs types)
    - Internal data structions (define explicit types)
Example:
```python
# Bad:
def get_data() -> dict[str, Any]:
    return {"values": [1, 2, 3]}

# Good:
class ChartData(TypedDict):
    values: list[int]

def get_data() -> ChartData:
    return {"values": [1, 2, 3]}
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

## Instruction for Code Comments (All Languages)

- YOU MUST comment code for readability and intent, NOT for restating the obvious. Every file must start with a short header comment describing its purpose. Every public function, class, or API must have a docblock that explains what it does, its inputs, its outputs, and edge cases.

**JavaScript/TypeScript**: Use JSDoc/TSDoc format with @fileoverview, @param, @returns, @example.
**Python**: Use PEP 257 docstrings with triple quotes; include a one-line summary, parameters, returns, and example usage.
**All languages**: Explain why a decision was made, list invariants/assumptions, and add examples where useful. Keep comments updated when code changes.

**Rule of thumb**: ALWAYS comment intent, constraints, and non-obvious logic. Code shows “what,” comments explain “why.”

## Compatibility & Migration Policy (Out-with-the-old)

**Default stance:** We do **not** preserve backward compatibility. When a change is requested, replace the old behavior with the new approach. Remove obsolete code, flags, and interfaces immediately unless the request explicitly says "keep legacy support."

### Rules for Agents & Tools

- **BREAK-FIRST mindset:** Prefer deletion and simplification over shims/adapters. No polyfills, toggles, or compatibility layers unless explicitly requested.
- **Single source of truth:** The **latest** interface/spec supersedes all prior versions. Do not consult or retain deprecated variants.
- **Migration over coexistence:** Write **forward-only** migrations. Do **not** add down-migrations unless explicitly requested.
- **Delete deprecated code now:** No deprecation windows. Remove old functions, types, env vars, config keys, and documentation in the same change.
- **Update all call sites:** Rename/replace and fix usages across the repo; do not leave aliases.
- **Tests follow the new world:** Update or replace tests to encode the new behavior. Delete tests that only assert legacy behavior.


### Versioning & Communication

- **Docs header:** Update the HTML header stamp on modified docs: `<!-- vMAJOR.MINOR | YYYY-MM-DD -->` and increment **MAJOR** on any breaking change.
- **Commit prefix:** Start the commit title with `BREAKING:` when the change removes/renames public symbols, config, or endpoints.
- **Changelog note:** Add a concise migration note (what changed, one-liner on how to migrate) in the relevant README or module doc.

### Examples (apply literally)

- **API surface:** If `getPatient()` becomes `fetchPatient()`, **remove** `getPatient()` and update all imports/usages; **no wrappers**.
- **Config keys:** If `RECALL_WINDOW_DAYS` becomes `RECALL_WINDOW`, migrate values and **delete** the old key and its references.
- **Data models:** If a column is renamed, write a one-off script to migrate; **do not** keep both columns.

> If you need compatibility, the request must say so explicitly. Otherwise, assume **out with the old, in with the new**.

## Current Project Status
- **Story Location**: @docs/stories

### Dashboard Access
- **Local URL**: http://localhost:8501
- **Start Command**: `uv run streamlit run apps/frontend/app.py`
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

# Case Acceptance: (Scheduled / Presented) × 100
def calculate_case_acceptance(df: pd.DataFrame) -> float | None:
    scheduled = pd.to_numeric(df["treatments_scheduled"], errors="coerce").sum()
    presented = pd.to_numeric(df["treatments_presented"], errors="coerce").sum()
    return float((scheduled / presented) * 100)

# Hygiene Reappointment: ((Total - Not Reappointed) / Total) × 100
def calculate_hygiene_reappointment(df: pd.DataFrame) -> float | None:
    total_hygiene = pd.to_numeric(df["total_hygiene_appointments"], errors="coerce").sum()
    not_reappointed = pd.to_numeric(df["patients_not_reappointed"], errors="coerce").sum()
    return float(((total_hygiene - not_reappointed) / total_hygiene) * 100)
```

### Data Sources ✅ Multi-Location Configured
- **Baytown EOD**: "EOD - Baytown Billing!A:N" (Production, Collections, New Patients)
- **Humble EOD**: "EOD - Humble Billing!A:AG" (Production, Collections, New Patients)
- **Baytown Front**: "Baytown Front KPIs Form responses!A:Z" (Case Acceptance, Hygiene Reappointment)
- **Humble Front**: "Humble Front KPIs Form responses!A:Z" (Case Acceptance, Hygiene Reappointment)
- **Spreadsheet ID**: 1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8
- **Configuration**: Alias-based access via `config/sheets.yml`

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
