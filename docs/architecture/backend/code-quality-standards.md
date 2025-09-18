# Code Quality Standards

## Line Count Compliance
- sheets_reader.py: 45 lines (under 50 limit)
- metrics.py: 48 lines (under 50 limit)
- Total backend: 93 lines (under 100 limit)

## Maintainability Metrics
- Single responsibility per function
- No nested complexity beyond 2 levels

# Code Style and Conventions

## Python Style Guidelines

### Type Hints
- **Always use type hints** for function parameters and return types
- Import from `typing` module: `Dict, List, Optional`
- Example:
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

### Code Style Rules
- Follow **PEP 8** style guide
- Line length limit: **88 characters** (Black default)
- Use **meaningful variable names**: `production_total` not `pt`
- **One function per KPI calculation** - keep functions focused
- **Docstrings required** for all public functions
- **Comments are allowed** in code if needed

### Best Practices
- Use **pandas** for data operations
- Use **pathlib** for file paths instead of string concatenation
- Use **context managers** for resource handling
- Use **logging** instead of print statements
- Handle errors gracefully with try/except blocks

## File Naming Conventions
- Python files: **snake_case** (e.g., `sheets_reader.py`, `test_metrics.py`)
- Directories: **lowercase** (e.g., `backend/`, `frontend/`, `tests/`)
- Configuration files: **lowercase with extension** (e.g., `pyproject.toml`)
- Special markdown files: **ALL_CAPS** (README.md, CHANGELOG.md, CLAUDE.md)
- Regular markdown: **kebab-case** (e.g., `naming-conventions.md`)

## Testing Conventions
- Test files: `test_*.py` pattern
- Test classes: `TestClassName` (PascalCase with Test prefix)
- Test methods: `test_descriptive_name()` (snake_case with test prefix)
- Use **Arrange-Act-Assert** pattern
- Target **90%+ coverage** for backend business logic

## Dental Domain Specific
### KPI Formulas (exact implementations required)
```python
def calculate_collection_rate(df: pd.DataFrame) -> float:
    """Collection Rate = (Patient + Unearned + Insurance Income) / Production × 100"""
    production_total = (
        df['Total Production Today'].sum()
        + df['Adjustments Today'].sum()
        + df['Write-offs Today'].sum()
    )
    collections_total = (
        df['Patient Income Today'].sum()
        + df['Unearned Income Today'].sum()
        + df['Insurance Income Today'].sum()
    )
    if production_total == 0:
        return 0.0
    return (collections_total / production_total) * 100


def calculate_case_acceptance(df: pd.DataFrame) -> float:
    """Case Acceptance = (Scheduled + Same Day) / Presented × 100"""
    presented = df['treatments_presented'].sum()
    scheduled = df['treatments_scheduled'].sum()
    same_day = df['$ Same Day Treatment'].sum()
    if presented == 0:
        return 0.0
    return ((scheduled + same_day) / presented) * 100


def calculate_hygiene_reappointment(df: pd.DataFrame) -> float:
    """Hygiene Reappointment = (Reappointed / Total) × 100"""
    total = df['Total hygiene Appointments'].sum()
    not_reappointed = df['Number of patients NOT reappointed?'].sum()
    if total == 0:
        return 0.0
    return ((total - not_reappointed) / total) * 100


def calculate_daily_new_patients(df: pd.DataFrame) -> pd.Series:
    """Daily new patients from month-to-date cumulative values."""
    ordered = df.sort_values('Submission Date')
    cumulative = ordered['New Patients - Total Month to Date'].astype(float)
    deltas = cumulative.diff().fillna(cumulative).clip(lower=0)
    return deltas
```

### Data Validation
```python
def validate_dental_data(df: pd.DataFrame) -> bool:
    """Ensure Story 2.1 columns required for KPI calculations exist."""
    required_columns = [
        'Submission Date',
        'Total Production Today',
        'Adjustments Today',
        'Write-offs Today',
        'Patient Income Today',
        'Unearned Income Today',
        'Insurance Income Today',
        'New Patients - Total Month to Date',
        'treatments_presented',
        'treatments_scheduled',
        '$ Same Day Treatment',
        'Total hygiene Appointments',
        'Number of patients NOT reappointed?',
    ]
    return all(col in df.columns for col in required_columns)
```

## Key Principles
- **DRY** (Don't Repeat Yourself) - eliminate code duplication
- **KISS** (Keep It Simple) - avoid overengineering
- **YAGNI** (You Aren't Gonna Need It) - only implement what's required now
- **Separation of Concerns** - distinct modules with focused responsibilities
- **Consistent patterns** across the codebase
