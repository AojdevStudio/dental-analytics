# Task Completion Checklist

When completing any development task, follow these steps:

## Code Quality Checks
1. **Format code with Black**
   ```bash
   uv run black .
   ```

2. **Check code style with Flake8**
   ```bash
   uv run flake8 backend/ frontend/
   ```

3. **Run type checking with mypy**
   ```bash
   uv run mypy backend/ frontend/
   ```

## Testing
4. **Run all tests**
   ```bash
   uv run pytest
   ```

5. **Check test coverage**
   ```bash
   uv run pytest --cov=backend --cov=frontend --cov-report=term-missing
   ```
   - Ensure 90%+ coverage for backend business logic

## Pre-commit (if configured)
6. **Run all quality checks**
   ```bash
   uv run pre-commit run --all-files
   ```

## Validation
7. **Test the application locally**
   ```bash
   uv run streamlit run frontend/app.py
   ```
   - Verify all 5 KPIs display correctly
   - Check Google Sheets connection works
   - Ensure error handling works for missing data

## Documentation
8. **Update relevant documentation** if needed:
   - Update CLAUDE.md if development commands change
   - Update index.md in docs/ if new sections added
   - Ensure docstrings are present for new functions

## Git
9. **Stage and commit changes** (only when explicitly asked):
   ```bash
   git add .
   git status  # Verify correct files staged
   git commit -m "type: descriptive message"
   ```

## Important Notes
- **NEVER commit unless explicitly requested** by the user
- Run linting and type checking **before** considering task complete
- If commands are not available (e.g., no pyproject.toml yet), ask user for guidance
- Mark todos as completed immediately after finishing each task
