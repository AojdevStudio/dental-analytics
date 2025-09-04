# AGENTS.md

This file provides guidance to AI agents when working with agents in this repository.

## Project Overview
Simple dental analytics dashboard that reads KPI data from Google Sheets, processes it with pandas, and displays metrics in a Streamlit web interface. Built for a dental practice to automate daily production, collection rate, new patient count, treatment acceptance, and hygiene reappointment tracking.

**Goal**: Get 5 numbers on screen from Google Sheets in under 200 lines of code.

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

## Dental Practice Specific Guidelines

### KPI Calculation Standards
```python
# Always use these exact formulas
def calculate_collection_rate(df: pd.DataFrame) -> float:
    """Collection Rate = (Collections / Production) × 100"""
    return (df['Collections'].sum() / df['Production'].sum()) * 100

def calculate_treatment_acceptance(df: pd.DataFrame) -> float:
    """Treatment Acceptance = (Scheduled / Presented) × 100"""
    return (df['Scheduled'].sum() / df['Presented'].sum()) * 100
```

### Data Validation
```python
# Always validate dental data
def validate_dental_data(df: pd.DataFrame) -> bool:
    """Ensure data meets dental practice requirements."""
    required_columns = ['Date', 'Provider', 'Production', 'Collections']
    return all(col in df.columns for col in required_columns)
```

### Error Handling for Production
```python
# Handle missing Google Sheets gracefully
def safe_sheet_read(spreadsheet_id: str) -> Optional[pd.DataFrame]:
    try:
        return sheets_client.get_data(spreadsheet_id)
    except Exception as e:
        logger.error(f"Sheet read failed: {e}")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=['Date', 'Provider', 'Production'])
```
