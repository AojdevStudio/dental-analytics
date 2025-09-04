# Development Commands Reference

## Environment Setup
```bash
# First-time setup (when pyproject.toml exists)
uv sync

# Run the application
uv run streamlit run frontend/app.py
```

## Package Management
```bash
# Add production dependency
uv add package-name

# Add development dependency  
uv add --dev package-name

# Update all packages
uv sync --upgrade

# List installed packages
uv pip list
```

## Testing
```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=backend --cov=frontend

# Run specific test file
uv run pytest tests/test_metrics.py

# Run tests in watch mode
uv run pytest-watch
```

## Code Quality
```bash
# Format code with black
uv run black .

# Check code style with flake8
uv run flake8 backend/ frontend/

# Type checking with mypy
uv run mypy backend/ frontend/

# Run all quality checks
uv run pre-commit run --all-files
```

## Development Tools
```bash
# Interactive Python shell
uv run python

# Jupyter notebook for data exploration
uv run jupyter notebook

# Test Google Sheets connection (when implemented)
uv run python -c "from backend.sheets_reader import test_connection; test_connection()"
```

## Git Commands (Darwin/macOS)
```bash
# Check status
git status

# Stage changes
git add .

# Commit with message
git commit -m "feat: description"

# Push to remote
git push origin development

# List files
ls -la

# Search in files
grep -r "pattern" .

# Find files
find . -name "*.py"
```

## Application URLs
- Local dashboard: http://localhost:8501 (after running streamlit)