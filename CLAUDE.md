# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
**COMPLETED**: Full-stack dental analytics dashboard that reads KPI data from Google Sheets, processes it with pandas, and displays metrics in a Streamlit web interface. Built for KamDental practice to automate daily production, collection rate, new patient count, treatment acceptance, and hygiene reappointment tracking.

**Status**: ✅ **Story 2.1 In Progress** - Multi-location support infrastructure implemented
**Current Architecture**: Provider abstraction with alias-based configuration
**Multi-Location**: Baytown and Humble locations with unified data access
**Historical Data**: Time-series KPI analysis with operational date logic

## Development Commands

### Serena-First Development Approach
- **Before debugging**: Use Serena MCP Workflow Guidelines to explore code structure
- **Before testing**: Use Symbol-Based Code Navigation to understand test targets
- **Before modifying**: Use Efficient Code Modification patterns
- **Always**: Store insights with Memory Management tools

### Core Commands
```bash
# Environment & App
uv sync && uv run streamlit run apps/frontend/app.py  # http://localhost:8501

# Quality & Testing
./scripts/quality-check.sh    # Comprehensive checks
./scripts/quick-test.sh       # Fast verification
uv run pytest --cov=apps.backend --cov=apps.frontend

# Development
uv add package-name          # Dependencies
uv run python               # Interactive shell
```

### Serena MCP Workflow Guidelines

#### Initial Codebase Exploration
```bash
# 1. Check onboarding status first
mcp__serena__check_onboarding_performed

# 2. Get project overview without reading full files
mcp__serena__list_dir --relative_path="apps" --recursive=true
mcp__serena__find_file --file_mask="*.py" --relative_path="apps"

# 3. Explore key files with symbol overview (NOT full reads)
mcp__serena__get_symbols_overview --relative_path="apps/backend/metrics.py"
mcp__serena__get_symbols_overview --relative_path="apps/frontend/app.py"

# 4. Find specific functions/classes when needed
mcp__serena__find_symbol --name_path="calculate_production_total" --relative_path="apps/backend"
```

#### Symbol-Based Code Navigation
```bash
# Find symbols by pattern (avoid full file reads)
mcp__serena__find_symbol --name_path="calculate_*" --substring_matching=true --relative_path="apps/backend/metrics.py"

# Read symbol bodies ONLY when editing needed
mcp__serena__find_symbol --name_path="get_all_kpis" --include_body=true --relative_path="apps/backend/metrics.py"

# Find references before making changes
mcp__serena__find_referencing_symbols --name_path="calculate_production_total" --relative_path="apps/backend/metrics.py"

# Search for patterns across codebase
mcp__serena__search_for_pattern --substring_pattern="pd\.to_numeric" --restrict_search_to_code_files=true
```

#### Efficient Code Modification
```bash
# Replace entire functions/classes
mcp__serena__replace_symbol_body --name_path="calculate_production_total" --relative_path="apps/backend/metrics.py"

# Add new functions after existing ones
mcp__serena__insert_after_symbol --name_path="get_all_kpis" --relative_path="apps/backend/metrics.py"

# Add imports at file beginning
mcp__serena__insert_before_symbol --name_path="get_production_data" --relative_path="apps/backend/metrics.py"
```

#### Memory Management
```bash
# Store project insights for future sessions
mcp__serena__write_memory --memory_name="kpi-calculation-patterns" --content="KPI functions use pd.to_numeric with errors='coerce'"

# Read relevant memories before starting work
mcp__serena__list_memories
mcp__serena__read_memory --memory_file_name="dental-analytics-architecture"

# Think about collected information before proceeding
mcp__serena__think_about_collected_information
mcp__serena__think_about_task_adherence
```

#### Quality Verification Workflows
```bash
# Verify changes don't break references
mcp__serena__find_referencing_symbols --name_path="modified_function" --relative_path="file.py"

# Check task completion
mcp__serena__think_about_whether_you_are_done

# NEVER read entire files unless absolutely necessary
# Use symbolic tools to read only what you need
```

## Story 2.1 Multi-Location Architecture

### Data Provider Pattern ✅ Implemented
- **DataProvider Protocol**: Clean interface for data access with `fetch()`, `list_available_aliases()`, `validate_alias()`
- **SheetsProvider Class**: Replaces legacy SheetsReader with alias-based configuration
- **Configuration-Driven**: YAML-based multi-sheet setup in `config/sheets.yml`
- **Location Support**: Baytown and Humble with clean separation

### Historical Data Management ✅ Implemented
- **HistoricalDataManager**: Sophisticated date filtering and operational logic
- **Smart Date Handling**: Monday-Saturday operational dates with Sunday fallback
- **Time-Series KPIs**: Historical versions of all KPI calculations
- **Data Aggregation**: total_sum, daily_average, latest_value, data_points

### Key Symbol Navigation for Story 2.1
```bash
# Explore new data provider architecture
mcp__serena__get_symbols_overview --relative_path="apps/backend/data_providers.py"
mcp__serena__find_symbol --name_path="SheetsProvider" --include_body=true

# Examine historical data capabilities
mcp__serena__get_symbols_overview --relative_path="apps/backend/historical_data.py"
mcp__serena__find_symbol --name_path="HistoricalDataManager" --include_body=true

# Review enhanced metrics with historical functions
mcp__serena__find_symbol --name_path="calculate_historical_*" --substring_matching=true --relative_path="apps/backend/metrics.py"
mcp__serena__find_symbol --name_path="get_combined_kpis" --include_body=true
```

### Configuration Architecture
```yaml
# config/sheets.yml - Multi-location sheet aliases
sheets:
  baytown_eod: { spreadsheet_id: "...", range: "EOD - Baytown Billing!A:N" }
  humble_eod: { spreadsheet_id: "...", range: "EOD - Humble Billing!A:AG" }
  baytown_front: { spreadsheet_id: "...", range: "Baytown Front KPIs Form responses!A:Z" }
  humble_front: { spreadsheet_id: "...", range: "Humble Front KPIs Form responses!A:Z" }

# Location mapping for backward compatibility
locations:
  baytown: { eod: "baytown_eod", front: "baytown_front" }
  humble: { eod: "humble_eod", front: "humble_front" }
```

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

## Serena-Based Project Navigation

### Dynamic Structure Exploration
```bash
# Don't memorize static file trees - explore dynamically
mcp__serena__list_dir --relative_path="." --recursive=false  # Top level
mcp__serena__list_dir --relative_path="apps" --recursive=true  # Code structure
mcp__serena__find_file --file_mask="*.py" --relative_path="."  # All Python files

# Key file symbol overviews (avoid full reads)
mcp__serena__get_symbols_overview --relative_path="apps/backend/metrics.py"          # KPI logic & historical functions
mcp__serena__get_symbols_overview --relative_path="apps/frontend/app.py"             # Dashboard UI
mcp__serena__get_symbols_overview --relative_path="apps/backend/data_providers.py"   # Multi-location data access
mcp__serena__get_symbols_overview --relative_path="apps/backend/historical_data.py"  # Historical data management

# Find symbols across project
mcp__serena__search_for_pattern --substring_pattern="def calculate_" --restrict_search_to_code_files=true
```

### Architecture Discovery Workflow
```bash
# 1. Start with symbol overview, not file reading
mcp__serena__get_symbols_overview --relative_path="apps/backend/metrics.py"

# 2. Find specific functions when needed
mcp__serena__find_symbol --name_path="get_all_kpis" --include_body=false

# 3. Understand dependencies through references
mcp__serena__find_referencing_symbols --name_path="get_all_kpis" --relative_path="apps/backend/metrics.py"

# 4. Only read function bodies when editing
mcp__serena__find_symbol --name_path="calculate_production_total" --include_body=true
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
from apps.backend.metrics import calculate_production_total, calculate_collection_rate

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
## Serena MCP Best Practices

### Core Principles
- **NEVER read entire files** - Use `get_symbols_overview` first, then targeted `find_symbol`
- **Symbol-first approach** - Navigate by functions/classes, not file browsing
- **Memory-driven** - Store insights across sessions for faster future work
- **Think before acting** - Use reflection tools before major changes

### Dental Analytics Specific Workflows
```bash
# Exploring KPI calculations efficiently
mcp__serena__get_symbols_overview --relative_path="apps/backend/metrics.py"
mcp__serena__find_symbol --name_path="calculate_*" --substring_matching=true

# Modifying Streamlit dashboard components
mcp__serena__find_symbol --name_path="main" --include_body=true --relative_path="apps/frontend/app.py"
mcp__serena__find_referencing_symbols --name_path="get_all_kpis" --relative_path="apps/frontend/app.py"

# Adding new KPI calculations
mcp__serena__insert_after_symbol --name_path="calculate_hygiene_reappointment" --relative_path="apps/backend/metrics.py"
```

### Project Context
- Python 3.11 with `uv` dependency management
- Strict typing with mypy, formatted with black + ruff
- Serena memory system enables persistent project knowledge
- Use symbolic editing for precise, reference-safe modifications

## Compatibility & Migration Policy (Out-with-the-old)

**Default stance:** We do **not** preserve backward compatibility. When a change is requested, replace the old behavior with the new approach. Remove obsolete code, flags, and interfaces immediately unless the request explicitly says "keep legacy support."

### Rules for Agents & Tools
- **BREAK-FIRST mindset:** Prefer deletion and simplification over shims/adapters. No polyfills, toggles, or compatibility layers unless explicitly requested.
- **Single source of truth:** The **latest** interface/spec supersedes all prior versions. Do not consult or retain deprecated variants.
- **Migration over coexistence:** Write **forward-only** migrations. Do **not** add down-migrations unless explicitly requested.
- **Delete deprecated code now:** No deprecation windows. Remove old functions, types, env vars, config keys, and documentation in the same change.
- **Update all call sites:** Rename/replace and fix usages across the repo; do not leave aliases.
- **Tests follow the new world:** Update or replace tests to encode the new behavior. Delete tests that only assert legacy behavior.

## Current Project Status

### Completed Stories ✅
- **Story 1.1**: Project foundation with Google Sheets connection
- **Story 1.2**: Daily production and collection rate calculations
- **Story 1.3**: New patient count and treatment acceptance tracking
- **Story 1.4**: Hygiene reappointment rate monitoring
- **Story 1.5**: Streamlit dashboard with brand styling

### Story 2.1 Multi-Location Infrastructure ✅ Implemented
- **Data Provider Pattern**: `DataProvider` protocol with `SheetsProvider` implementation
- **Configuration System**: YAML-based multi-sheet configuration with location aliases
- **Historical Data Manager**: Smart date filtering with operational business logic
- **Enhanced Metrics**: Historical KPI functions with time-series analysis
- **Multi-Location Support**: Baytown and Humble unified data access

### Next Steps
- **Story 2.1 Frontend**: Multi-location dashboard UI implementation
- **Story 1.6**: Pytest testing framework implementation
- **Future**: Real-time data refresh, advanced historical analytics

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

### Data Sources ✅ Multi-Location Configured
- **Baytown EOD**: "EOD - Baytown Billing!A:N" (Production, Collections, New Patients)
- **Humble EOD**: "EOD - Humble Billing!A:AG" (Production, Collections, New Patients)
- **Baytown Front**: "Baytown Front KPIs Form responses!A:Z" (Treatment Acceptance, Hygiene Reappointment)
- **Humble Front**: "Humble Front KPIs Form responses!A:Z" (Treatment Acceptance, Hygiene Reappointment)
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
