---
title: "Fix Recurring Import Errors and Prevention Plan"
description: "Comprehensive plan to fix the add_trend_line import error and prevent similar issues from recurring"
category: "Technical Documentation"
subcategory: "Bug Fix & Prevention"
product_line: "Dental Analytics Dashboard"
audience: "Development Team"
status: "Active"
author: "AOJDevStudio"
created_date: "2025-09-29"
last_updated: "2025-09-29"
tags:
  - import-errors
  - code-quality
  - pre-commit-hooks
  - testing-strategy
  - refactoring-guidelines
---

# Fix Recurring Import Errors and Prevention Plan

## Problem Statement

The dental analytics dashboard is experiencing recurring import errors where functions are being renamed during refactoring but not all references are updated. Specifically, `add_trend_line` was renamed to `add_trend_line_to_figure` in `chart_utils.py` but the imports and calls in `chart_kpis.py` were not updated, causing an `ImportError` that breaks the application.

### Root Causes Identified

1. **Uncoordinated Development**: Multiple developers/AI assistants working without proper coordination
2. **Incomplete Refactoring**: Function renames not updating all references
3. **Insufficient Pre-commit Validation**: Current hooks only format/lint, don't catch import errors
4. **Manual Test Execution**: Tests are set to manual stage, not running automatically
5. **Large Atomic Commits**: 3500+ line changes in single commits make it easy to miss references

## Objectives

1. Fix the immediate import error to restore application functionality
2. Implement preventive measures to catch import errors before commits
3. Establish refactoring best practices to prevent similar issues
4. Improve development workflow coordination
5. Ensure all changes are properly tested before merging

## Technical Approach

### Phase 1: Immediate Fix (Critical - Do First)

Fix the current import error to restore application functionality.

#### Implementation Steps

1. **Update Import Statement** in `apps/frontend/chart_kpis.py` (line 25):
```python
# FROM:
from .chart_utils import (
    add_pattern_annotation,
    add_trend_line,  # OLD NAME - BROKEN
    add_trend_pattern_annotation,
    apply_alpha_to_color,
)

# TO:
from .chart_utils import (
    add_pattern_annotation,
    add_trend_line_to_figure,  # NEW NAME - FIXED
    add_trend_pattern_annotation,
    apply_alpha_to_color,
)
```

2. **Update All Function Calls** in `apps/frontend/chart_kpis.py`:
```python
# Line 95 - Collection Rate Chart
# FROM: add_trend_line(fig, dates, clean_values, "Collection Rate Trend")
# TO:
trend_values, slope, r_squared = add_trend_line_to_figure(
    fig, dates, clean_values, "Collection Rate Trend"
)

# Line 190 - New Patients Chart
# FROM: add_trend_line(fig, dates, values, "New Patients Trend")
# TO:
trend_values, slope, r_squared = add_trend_line_to_figure(
    fig, dates, values, "New Patients Trend"
)

# Line 290 - Case Acceptance Chart
# FROM: add_trend_line(fig, dates, values, "Acceptance Trend")
# TO:
trend_values, slope, r_squared = add_trend_line_to_figure(
    fig, dates, values, "Acceptance Trend"
)

# Line 387 - Hygiene Reappointment Chart
# FROM: add_trend_line(fig, dates, values, "Reappointment Trend")
# TO:
trend_values, slope, r_squared = add_trend_line_to_figure(
    fig, dates, values, "Reappointment Trend"
)
```

3. **Note**: The new function returns a tuple `(trend_values, slope, r_squared)` which can be used for additional analytics if needed, or ignored if not required.

### Phase 2: Add Import Validation (High Priority)

Implement pre-commit hooks that actually validate Python imports.

#### Implementation Steps

1. **Create Import Validation Script** at `scripts/validate-imports.py`:
```python
#!/usr/bin/env python3
"""Validate all Python imports in the project."""

import ast
import sys
from pathlib import Path
from typing import Set, List, Tuple

def get_imports_from_file(filepath: Path) -> Set[str]:
    """Extract all imports from a Python file."""
    imports = set()
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    if module:
                        imports.add(f"{module}.{alias.name}")
                    else:
                        imports.add(alias.name)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")

    return imports

def validate_project_imports() -> Tuple[bool, List[str]]:
    """Validate all imports in the project."""
    errors = []
    project_root = Path(__file__).parent.parent

    # Check all Python files
    for py_file in project_root.rglob("*.py"):
        # Skip virtual environments and cache
        if any(part in str(py_file) for part in ['.venv', '__pycache__', '.git']):
            continue

        # Try to import the module to catch import errors
        relative_path = py_file.relative_to(project_root)
        module_path = str(relative_path).replace('/', '.').replace('.py', '')

        try:
            # Use compile to check syntax and imports
            with open(py_file, 'r') as f:
                compile(f.read(), py_file, 'exec')
        except SyntaxError as e:
            errors.append(f"Syntax error in {relative_path}: {e}")
        except Exception as e:
            if "cannot import name" in str(e):
                errors.append(f"Import error in {relative_path}: {e}")

    return len(errors) == 0, errors

if __name__ == "__main__":
    success, errors = validate_project_imports()

    if not success:
        print("❌ Import validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ All imports validated successfully")
        sys.exit(0)
```

2. **Add to Pre-commit Config** in `.pre-commit-config.yaml`:
```yaml
  # Import validation hook
  - repo: local
    hooks:
      - id: validate-imports
        name: Validate Python Imports
        entry: python scripts/validate-imports.py
        language: system
        files: '\.py$'
        pass_filenames: false
```

### Phase 3: Enable Automatic Testing (High Priority)

Make tests run automatically on every commit to catch errors early.

#### Implementation Steps

1. **Update Pre-commit Config** - Remove manual stage from pytest:
```yaml
  # Pytest testing - MAKE AUTOMATIC
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest
        language: system
        files: '^(backend/|tests/).*\.py$'
        pass_filenames: false
        args: [--maxfail=1, -x]
        # stages: [manual]  # REMOVE THIS LINE
```

2. **Add Quick Import Test** at `tests/test_imports.py`:
```python
"""Test that all critical imports work correctly."""

def test_chart_utils_imports():
    """Verify all chart_utils functions can be imported."""
    from apps.frontend.chart_utils import (
        format_currency_hover,
        handle_empty_data,
        add_pattern_annotation,
        safe_float_conversion,
        parse_currency_string,
        calculate_trend_line,
        add_trend_line_to_figure,  # Critical function
        apply_alpha_to_color,
    )
    assert callable(add_trend_line_to_figure)

def test_chart_kpis_imports():
    """Verify chart_kpis can import all dependencies."""
    from apps.frontend.chart_kpis import (
        create_collection_rate_chart,
        create_new_patients_chart,
        create_case_acceptance_chart,
        create_hygiene_reappointment_chart,
        create_chart_from_data,
    )
    assert callable(create_chart_from_data)
```

### Phase 4: Establish Refactoring Guidelines (Medium Priority)

Create clear guidelines for safe refactoring practices.

#### Implementation Steps

1. **Create Refactoring Checklist** at `docs/refactoring-guidelines.md`:
```markdown
# Refactoring Guidelines

## Before Refactoring
- [ ] Pull latest changes from main branch
- [ ] Create a feature branch for the refactoring
- [ ] Run all tests to ensure starting from working state

## During Refactoring
- [ ] Use IDE refactoring tools (not manual find/replace)
- [ ] Keep refactoring commits separate from feature changes
- [ ] Make one type of change at a time (e.g., rename OR move, not both)

## Function/Class Renaming Checklist
- [ ] Use IDE "Rename Symbol" feature (Cmd+Shift+R in VS Code)
- [ ] Search entire codebase for string references
- [ ] Update all imports
- [ ] Update all function calls
- [ ] Update documentation and comments
- [ ] Update test function names if applicable

## After Refactoring
- [ ] Run `uv run pytest` to ensure all tests pass
- [ ] Run `uv run streamlit run apps/frontend/app.py` to test manually
- [ ] Run `./scripts/quality-check.sh` for full validation
- [ ] Commit with clear message: "refactor: rename X to Y"
```

2. **Add VS Code Settings** for safer refactoring in `.vscode/settings.json`:
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.analysis.autoImportCompletions": true,
  "python.analysis.typeCheckingMode": "strict",
  "editor.renameOnType": false,
  "search.exclude": {
    "**/.venv": true,
    "**/__pycache__": true,
    "**/.pytest_cache": true
  }
}
```

### Phase 5: Improve Workflow Coordination (Medium Priority)

Establish better coordination between team members and AI assistants.

#### Implementation Steps

1. **Create Development Log** at `DEVELOPMENT_LOG.md`:
```markdown
# Development Log

## Active Refactoring
Document any ongoing refactoring work here before starting.

| Date | Developer | Changes | Status |
|------|-----------|---------|--------|
| 2025-09-29 | AOJDevStudio | Rename add_trend_line to add_trend_line_to_figure | In Progress |

## Known Issues
List any known issues that need fixing.

| Issue | File | Description | Priority |
|-------|------|-------------|----------|
| Import Error | chart_kpis.py | add_trend_line import broken | HIGH |
```

2. **Add Git Commit Message Template** at `.gitmessage`:
```
# <type>: <subject> (50 chars)

# <body> (72 chars per line)
# What changed and why?

# <footer>
# Breaking changes or issues closed

# Types: feat, fix, docs, style, refactor, test, chore
# Example:
# refactor: rename add_trend_line to add_trend_line_to_figure
#
# Updated all imports and function calls in:
# - apps/frontend/chart_kpis.py
# - apps/frontend/chart_production.py
#
# Closes #123
```

Configure git to use template:
```bash
git config --local commit.template .gitmessage
```

## Testing Strategy

### Unit Tests
- Test each renamed function individually
- Verify import statements work correctly
- Check function signatures match expectations

### Integration Tests
- Run full dashboard to ensure charts render
- Test data flow from backend to frontend
- Verify all KPIs calculate correctly

### Manual Testing Checklist
```bash
# 1. Run import validation
python scripts/validate-imports.py

# 2. Run unit tests
uv run pytest tests/test_imports.py -v

# 3. Run full test suite
uv run pytest --cov=apps.backend --cov=apps.frontend

# 4. Start application and verify
uv run streamlit run apps/frontend/app.py
# Then check:
# - [ ] Dashboard loads without errors
# - [ ] All charts render correctly
# - [ ] Trend lines appear when enabled
# - [ ] No console errors in browser
```

## Potential Challenges and Solutions

### Challenge 1: Circular Import Dependencies
**Solution**: Use TYPE_CHECKING imports and forward references:
```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chart_utils import SomeType
```

### Challenge 2: IDE Refactoring Tools Not Available
**Solution**: Use grep and sed carefully:
```bash
# Find all occurrences
grep -r "add_trend_line" apps/ tests/

# Update with confirmation
find apps tests -name "*.py" -exec grep -l "add_trend_line" {} \; | \
  xargs -I {} bash -c 'echo "Update {}? (y/n)"; read ans; \
  [ "$ans" = "y" ] && sed -i "" "s/add_trend_line/add_trend_line_to_figure/g" {}'
```

### Challenge 3: Pre-commit Hooks Slow Down Development
**Solution**: Add `--no-verify` flag for WIP commits, but enforce on PR:
```bash
# For work in progress
git commit --no-verify -m "WIP: refactoring"

# For final commit
git commit -m "refactor: complete function rename"
```

## Success Criteria

### Immediate Success (Phase 1)
- [ ] Application runs without ImportError
- [ ] All charts display correctly
- [ ] Trend lines work when enabled
- [ ] All existing tests pass

### Short-term Success (Phases 2-3)
- [ ] Import validation catches errors before commit
- [ ] Tests run automatically on every commit
- [ ] No import errors reach main branch
- [ ] Refactoring doesn't break functionality

### Long-term Success (Phases 4-5)
- [ ] Team follows refactoring guidelines
- [ ] Coordination prevents duplicate work
- [ ] Code quality improves over time
- [ ] Fewer emergency fixes needed

## Implementation Timeline

1. **Immediate** (Today):
   - Fix import error in chart_kpis.py
   - Test and deploy fix

2. **Day 1-2**:
   - Add import validation script
   - Enable automatic testing
   - Update pre-commit hooks

3. **Week 1**:
   - Document refactoring guidelines
   - Set up VS Code configuration
   - Train team on new processes

4. **Ongoing**:
   - Monitor for similar issues
   - Refine processes based on feedback
   - Maintain development log

## Maintenance and Monitoring

### Weekly Checks
- Review DEVELOPMENT_LOG.md for active work
- Check for any import-related errors in logs
- Validate pre-commit hooks are running

### Monthly Review
- Analyze commit history for refactoring patterns
- Update guidelines based on lessons learned
- Review and update test coverage

## Conclusion

This plan addresses both the immediate import error and the systemic issues causing recurring problems. By implementing proper validation, testing, and coordination processes, we can prevent similar issues while maintaining development velocity.

The key is to make the right thing (proper refactoring with full reference updates) easier than the wrong thing (partial refactoring that breaks imports).