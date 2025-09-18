---
title: "Developer Workflow Guide"
description: "Comprehensive guide for developers working on the dental analytics project with integrated quality processes."
category: "Development Process"
subcategory: "Workflow"
product_line: "Dental Analytics"
audience: "Development Team"
status: "Active"
author: "AOJDevStudio"
created_date: "2025-09-04"
last_updated: "2025-09-04"
tags:
  - workflow
  - development-process
  - quality
  - testing
  - tdd
---

# Developer Workflow Guide

## Overview

This guide outlines the complete developer workflow for the dental analytics project, emphasizing quality-first development practices, Test-Driven Development (TDD), and seamless integration of quality gates into the development process.

**Philosophy**: Quality is built in, not bolted on. Every step in our workflow is designed to catch issues early and maintain high code quality standards.

## Quick Start Commands

```bash
# Initial setup
uv sync
uv run pre-commit install
uv run python scripts/setup-dev.py

# Daily development
uv run python scripts/check-quality.py  # Full quality check
uv run streamlit run apps/frontend/app.py     # Start application
uv run pytest --cov=apps.backend --cov=apps.frontend  # Run tests with coverage
```

## Development Workflow Phases

### Phase 1: Story Preparation

#### Before Starting Development
1. **Environment Verification**
   ```bash
   uv sync  # Ensure all dependencies are current
   uv run python scripts/check-quality.py  # Verify clean baseline
   ```

2. **Story Analysis**
   - Review acceptance criteria thoroughly
   - Identify testable requirements
   - Plan test scenarios before writing code
   - Understand quality gates that must be met

3. **Branch Management**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b story-X.X-feature-name
   ```

#### Pre-Development Checklist
- [ ] Story requirements understood and clarified
- [ ] Test scenarios planned and documented
- [ ] Development environment verified and clean
- [ ] Quality baseline established (all checks passing)

### Phase 2: Test-Driven Development (TDD)

#### TDD Cycle Implementation

**Red → Green → Refactor** approach is mandatory for all new features:

1. **Red Phase: Write Failing Test**
   ```bash
   # Create test that defines expected behavior
   # Test should fail initially (no implementation yet)
   uv run pytest tests/test_new_feature.py -v
   ```

2. **Green Phase: Make Test Pass**
   ```bash
   # Implement minimal code to make test pass
   # Run test to verify it passes
   uv run pytest tests/test_new_feature.py -v
   ```

3. **Refactor Phase: Improve Code Quality**
   ```bash
   # Refactor implementation while keeping tests green
   # Ensure all quality gates still pass
   uv run python scripts/check-quality.py
   ```

#### Testing Strategy by Component

**Backend Business Logic (90%+ coverage required)**
```python
# Example: KPI calculation testing
def test_calculate_production_total():
    # Arrange: Set up test data
    test_data = pd.DataFrame({
        'Production': [1000, 2000, 1500]
    })

    # Act: Execute function
    result = calculate_production_total(test_data)

    # Assert: Verify result
    assert result == 4500
```

**Integration Testing**
```python
# Example: Google Sheets integration
@mock.patch('backend.sheets_reader.build')
def test_sheets_connection(mock_build):
    # Mock external dependencies
    # Test integration points
    # Verify error handling
```

**Frontend Components**
```python
# Example: Streamlit UI testing
def test_dashboard_rendering():
    # Test UI component behavior
    # Verify data display logic
    # Test user interactions
```

### Phase 3: Continuous Quality Validation

#### Quality Gates Integration

Every development session should include continuous quality validation:

1. **Pre-Commit Validation** (Automatic)
   ```bash
   # Runs automatically on git commit
   # Includes: Black, Ruff, MyPy, basic tests
   git commit -m "feat: add new KPI calculation"
   ```

2. **Manual Quality Check** (Frequent)
   ```bash
   # Run during development for immediate feedback
   uv run python scripts/check-quality.py
   ```

3. **Comprehensive Validation** (Before PR)
   ```bash
   # Full test suite with coverage
   uv run pytest --cov=apps.backend --cov=apps.frontend --cov-report=term-missing
   ```

#### Quality Check Interpretation

**Coverage Report Analysis**
```
Name                           Stmts   Miss  Cover   Missing
----------------------------------------------------------
backend/metrics.py                25      0   100%
backend/sheets_reader.py          30      2    93%   45-46
frontend/app.py                   50      5    90%   78-82
----------------------------------------------------------
TOTAL                            105      7    93%
```

- **Target**: 90%+ for backend, reasonable coverage for frontend
- **Missing Lines**: Investigate and add tests for uncovered paths
- **Quality Gate**: Must maintain or improve overall coverage

### Phase 4: Feature Integration

#### Code Quality Validation

**Type Checking Excellence**
```python
# All public functions must have comprehensive type hints
def calculate_kpis(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate all KPIs with proper type safety."""
    pass

def get_sheet_data(
    spreadsheet_id: str,
    range_name: str
) -> Optional[pd.DataFrame]:
    """Fetch data with error handling."""
    pass
```

**Code Organization Standards**
- **Backend**: Pure business logic, no UI concerns
- **Frontend**: UI logic only, delegate calculations to backend
- **Tests**: Mirror source structure, comprehensive coverage
- **Documentation**: Clear docstrings, inline comments for complex logic

#### Error Handling Patterns

**Graceful Degradation**
```python
def safe_kpi_calculation(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate KPIs with robust error handling."""
    try:
        return {
            'production_total': calculate_production_total(df),
            'collection_rate': calculate_collection_rate(df),
            # ... other KPIs
        }
    except Exception as e:
        logger.error(f"KPI calculation failed: {e}")
        return default_kpi_values()
```

**External API Resilience**
```python
def get_sheets_data_with_retry(
    spreadsheet_id: str,
    max_retries: int = 3
) -> Optional[pd.DataFrame]:
    """Fetch with retry logic and graceful failure."""
    for attempt in range(max_retries):
        try:
            return sheets_client.get_data(spreadsheet_id)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Final attempt failed: {e}")
                return None
            time.sleep(2 ** attempt)  # Exponential backoff
```

### Phase 5: Story Completion

#### Definition of Done Validation

Use the comprehensive DoD checklist (`.bmad-core/checklists/story-dod-checklist.md`):

**Quality Gates Verification**
- [ ] Test coverage ≥90% for backend business logic
- [ ] All quality tools pass (Black, Ruff, MyPy, pytest)
- [ ] Pre-commit hooks execute successfully
- [ ] CI/CD pipeline completes successfully
- [ ] Application runs locally without issues

**Functional Verification**
- [ ] All acceptance criteria met
- [ ] Manual testing completed
- [ ] Edge cases handled gracefully
- [ ] Error conditions tested

#### Story Documentation

**Implementation Summary**
```markdown
## Story X.X Implementation Summary

### Changes Made
- Added KPI calculation for [specific metric]
- Implemented error handling for [specific scenario]
- Created [number] unit tests with [coverage]% coverage

### Quality Metrics
- **Test Coverage**: 97% (target: 90%)
- **Type Coverage**: 100% for public APIs
- **Quality Gates**: All passing
- **Performance**: No regressions detected

### Technical Decisions
- Chose pandas for data processing (efficiency)
- Implemented exponential backoff for API calls (reliability)
- Used dependency injection for testability

### Follow-up Items
- Consider caching for frequently accessed data
- Monitor API rate limits in production
- Review error alerting thresholds
```

## Common Development Scenarios

### Scenario 1: Adding New KPI

```bash
# 1. Create failing test
echo "def test_new_kpi_calculation():
    # Test implementation
    assert False  # Failing test" >> tests/test_metrics.py

# 2. Run test (should fail)
uv run pytest tests/test_metrics.py::test_new_kpi_calculation -v

# 3. Implement KPI calculation
# Add function to backend/metrics.py

# 4. Make test pass
uv run pytest tests/test_metrics.py::test_new_kpi_calculation -v

# 5. Verify quality gates
uv run python scripts/check-quality.py

# 6. Integrate with frontend
# Add to frontend/app.py

# 7. Final validation
uv run pytest --cov=apps.backend --cov=apps.frontend
```

### Scenario 2: Bug Fix with TDD

```bash
# 1. Create test that reproduces bug
echo "def test_bug_reproduction():
    # Create test case that demonstrates the bug
    # This test should fail initially" >> tests/test_bug_fix.py

# 2. Verify test fails (confirms bug exists)
uv run pytest tests/test_bug_fix.py -v

# 3. Fix the bug
# Modify source code to address issue

# 4. Verify test now passes
uv run pytest tests/test_bug_fix.py -v

# 5. Ensure no regression
uv run pytest

# 6. Quality validation
uv run python scripts/check-quality.py
```

### Scenario 3: Refactoring with Quality Assurance

```bash
# 1. Establish baseline
uv run pytest --cov=apps.backend --cov=apps.frontend  # Note current coverage
uv run python scripts/check-quality.py     # Ensure clean state

# 2. Refactor incrementally
# Make small changes, run tests frequently

# 3. Validate after each change
uv run pytest  # Ensure no functionality broken
uv run python scripts/check-quality.py  # Maintain quality standards

# 4. Final validation
# Coverage should be maintained or improved
# All quality gates should pass
# Performance should not degrade
```

## Performance and Quality Balance

### Code Quality vs Performance

**Priority Order**:
1. **Correctness**: Code must work correctly
2. **Quality**: Code must meet quality standards
3. **Performance**: Code should be efficient
4. **Features**: Additional features come last

**Performance Optimization Guidelines**:
- Profile before optimizing
- Maintain test coverage during optimization
- Document performance-critical sections
- Use type hints to enable optimizations

### Technical Debt Management

**Acceptable Technical Debt**:
- Temporary workarounds with TODO comments and tracking issues
- Performance optimizations deferred for later iterations
- Non-critical edge case handling

**Unacceptable Technical Debt**:
- Skipping tests to meet deadlines
- Ignoring quality gate failures
- Hard-coding values without documentation
- Disabling quality tools without justification

## Troubleshooting Common Issues

### Quality Gate Failures

**Black Formatting Issues**
```bash
# Fix: Apply formatting
uv run black .

# Verify: Check formatting
uv run black --check .
```

**Ruff Linting Violations**
```bash
# Identify: Show violations
uv run ruff check .

# Fix: Auto-fix where possible
uv run ruff check --fix .
```

**MyPy Type Errors**
```bash
# Identify: Show type errors
uv run mypy backend/ frontend/

# Common fixes:
# - Add missing type hints
# - Use Optional[T] for nullable values
# - Import proper typing constructs
```

**Test Coverage Drops**
```bash
# Identify: Show uncovered lines
uv run pytest --cov=apps.backend --cov=apps.frontend --cov-report=term-missing

# Fix: Add tests for uncovered lines
# Focus on backend business logic first
```

### Development Environment Issues

**Dependency Conflicts**
```bash
# Reset: Clean environment
rm -rf .venv
uv sync

# Verify: Check installation
uv run python -c "import streamlit; print('OK')"
```

**Pre-commit Hook Failures**
```bash
# Reinstall: Reset hooks
uv run pre-commit uninstall
uv run pre-commit install

# Test: Run hooks manually
uv run pre-commit run --all-files
```

## Success Metrics

### Individual Developer Success
- **Quality Gate Pass Rate**: >95% on first attempt
- **Test Coverage**: Maintain >90% for backend logic
- **Bug Regression Rate**: <5% of stories introduce regressions
- **Code Review Velocity**: <24 hours for quality feedback

### Team Quality Metrics
- **Build Success Rate**: >98% of CI/CD pipeline runs pass
- **Production Incidents**: <1 quality-related incident per month
- **Technical Debt**: Decreasing trend in TODO count
- **Developer Satisfaction**: High confidence in code quality

## Quick Reference

### Essential Commands
```bash
# Full development cycle
uv run python scripts/check-quality.py  # Quality validation
uv run pytest --cov=apps.backend --cov=apps.frontend  # Test with coverage
uv run streamlit run apps/frontend/app.py  # Start application

# Quality tools individual runs
uv run black .           # Format code
uv run ruff check .      # Lint code
uv run mypy backend/ frontend/  # Type check
uv run pytest           # Run tests
```

### Quality Standards Summary
- **Test Coverage**: ≥90% backend business logic
- **Type Coverage**: 100% public APIs
- **Code Style**: Black formatting, Ruff linting
- **Documentation**: Comprehensive docstrings
- **Error Handling**: Graceful degradation everywhere

**Remember**: Quality is not about perfection—it's about building reliable, maintainable software that serves our users well while enabling rapid, confident development.
