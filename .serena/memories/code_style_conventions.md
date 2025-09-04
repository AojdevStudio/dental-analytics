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
- **NO COMMENTS** in code unless explicitly requested

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
    """Collection Rate = (Collections / Production) × 100"""
    return (df['Collections'].sum() / df['Production'].sum()) * 100

def calculate_treatment_acceptance(df: pd.DataFrame) -> float:
    """Treatment Acceptance = (Scheduled / Presented) × 100"""
    return (df['Scheduled'].sum() / df['Presented'].sum()) * 100
```

### Data Validation
```python
def validate_dental_data(df: pd.DataFrame) -> bool:
    """Ensure data meets dental practice requirements."""
    required_columns = ['Date', 'Provider', 'Production', 'Collections']
    return all(col in df.columns for col in required_columns)
```

## Key Principles
- **DRY** (Don't Repeat Yourself) - eliminate code duplication
- **KISS** (Keep It Simple) - avoid overengineering
- **YAGNI** (You Aren't Gonna Need It) - only implement what's required now
- **Separation of Concerns** - distinct modules with focused responsibilities
- **Consistent patterns** across the codebase
