# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Full-stack dental analytics dashboard that reads KPI data from Google Sheets, processes it with pandas, and displays metrics in a Streamlit web interface. Built for KamDental practice to automate daily production, collection rate, new patient count, treatment acceptance, and hygiene reappointment tracking.

**Current Architecture**: view @docs/architecture/fullstack-architecture.md
**Multi-Location**: Baytown and Humble locations with unified data access
**Historical Data**: Time-series KPI analysis with operational date logic

## Architecture (Story 3.0: 5-Layer Design)

**Directory Structure:**
```
core/                           # Pure business logic (framework-independent)
├── models/kpi_models.py       # Pydantic data contracts
├── calculators/kpi_calculator.py  # Pure KPI calculation functions
├── business_rules/
│   ├── calendar.py            # Business day logic (Baytown/Humble schedules)
│   └── validation_rules.py    # Goal-based validation (production variance, rate thresholds)
└── transformers/
    └── sheets_transformer.py  # DataFrame → calculator inputs

services/
└── kpi_service.py             # Orchestration layer (calendar → fetch → transform → calculate → validate)

apps/backend/
├── data_providers.py          # Google Sheets API integration
└── metrics.py                 # Legacy facade (compatibility wrapper)

config/business_rules/
├── calendar.yml               # Location schedules (Baytown alternating Saturdays, Humble Mon-Thu)
└── goals.yml                  # Daily production goals and KPI thresholds
```

**Key Principles:**
- **core/** uses Pydantic models exclusively (type-safe, validated)
- **apps/backend/types.py** uses TypedDict (legacy compatibility)
- Pure functions in calculators (no side effects, easy to test)
- Dependency injection in services (testable, flexible)

## Development Commands

### Best Practices
- **Use Grep tool for searches** (never bash grep/find)
- **Store key insights** with Serena memory for future sessions
- **Choose tools based on task**: Simple → Native, Search → Grep, Symbols → Serena
- **Let Claude decide**: Trust the AI's tool selection judgment

## When to Use Serena MCP

Serena excels at surgical symbol-based operations and cross-session memory. Use it when these capabilities add value, not as a default for everything.

### Primary Use Case: Cross-Session Memory
Store project insights that persist between sessions - architectural decisions, key patterns, important context that future Claude instances should know.

### Secondary Use Cases:
- **Large unfamiliar codebases**: Get symbol overviews instead of reading entire files
- **Impact analysis**: Find all references before making breaking changes
- **Surgical edits**: Replace specific functions without touching surrounding code

**Let Claude decide when these add value over native tools.**


### Core Commands
```bash
# Environment & App
uv sync && uv run streamlit run apps/frontend/app.py  # http://localhost:8501

# Quality & Testing
./scripts/quality-check.sh    # Comprehensive checks
./scripts/quick-test.sh       # Fast verification
uv run pytest --cov=core --cov=services --cov-report=term-missing

# Development
uv add package-name          # Dependencies
uv run python               # Interactive shell
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

### Testing Framework
- Follow the testing standards in the @docs/architecture/backend/testing-strategy.md file.

### Code Quality Tools ✅ Active
- **black**: Code formatting
- **ruff**: Modern linting (replaced flake8)
- **mypy**: Type checking with modern Python 3.10+ syntax

### Naming Conventions
- Follow the naming conventions in the @ai-docs/naming-conventions.md file.

### Documentation Standards
- Use clear, descriptive filenames
- Include creation/modification dates
- Link related documents
- Maintain consistent formatting
- Update index.md when adding new sections

## Python Guidelines

### Type Hints (Modern Python 3.10+ Syntax)
```python
import pandas as pd
from pydantic import BaseModel

# Use built-in types (NOT typing.Dict, typing.List, typing.Optional)
def calculate_kpis(df: pd.DataFrame) -> dict[str, float]:
    """Calculate all 5 core KPIs from dental data."""
    pass

def get_sheet_data(spreadsheet_id: str, range_name: str) -> pd.DataFrame | None:
    """Fetch data from Google Sheets (use | None instead of Optional)."""
    pass

# For structured data in core/, use Pydantic models
class KPIResponse(BaseModel):
    location: str
    values: dict[str, float | None]
    availability: str

# For legacy compatibility in apps/backend/types.py, use TypedDict
from typing import TypedDict

class LegacyKPIData(TypedDict):
    production_total: float | None
    collection_rate: float | None
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
- **New code in core/services/** uses Pydantic models:
    - KPI response structures → Pydantic (validation + type safety)
    - Business logic models → Pydantic (CalculationResult, KPIValue, etc.)
    - Configuration models → Pydantic when validation needed
- **Legacy apps/backend/types.py** uses TypedDict:
    - Chart data structures (backward compatibility)
    - Legacy KPI response (for scripts/tests still using old API)
    - Don't add new TypedDicts; use Pydantic for new structures
- **ALWAYS use Plotly types:**
    - go.Layout instead of dict[str, Any]
    - layout.XAxis, layout.YAxis for axis configs
    - Import from plotly.graph_objects.layout submodules
- **ONLY allow Any for:**
    - YAML ingestion: `config: dict[str, Any] = yaml.safe_load(f)`
    - Reason: YAML is external, untyped data source we don't control
- **NEVER use Any for:**
    - Function return types (use Pydantic or TypedDict)
    - Plotly configurations (use Plotly-stubs types)
    - Internal data structures (define explicit types)
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

### Project Context
- Python 3.11 with `uv` dependency management
- Strict typing with mypy, formatted with black + ruff
- Serena memory system enables persistent project knowledge
- Use symbolic editing for precise, reference-safe modifications

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
