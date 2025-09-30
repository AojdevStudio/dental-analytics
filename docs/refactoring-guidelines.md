---
title: "Refactoring Guidelines"
description: "Best practices and checklists for safely refactoring code without breaking imports or functionality"
category: "Development Guidelines"
subcategory: "Code Quality"
product_line: "Dental Analytics Dashboard"
audience: "Development Team, AI Assistants"
status: "Active"
author: "AOJDevStudio"
created_date: "2025-09-29"
last_updated: "2025-09-29"
tags:
  - refactoring
  - best-practices
  - code-quality
  - import-errors
---

# Refactoring Guidelines

## Purpose

This document provides guidelines for safely refactoring code to prevent recurring import errors and maintain code quality. Follow these checklists when renaming functions, moving modules, or making structural changes.

## Before Refactoring

- [ ] Pull latest changes from main branch
- [ ] Create a feature branch for the refactoring
- [ ] Run all tests to ensure starting from working state
- [ ] Document the refactoring plan in `DEVELOPMENT_LOG.md`
- [ ] Check for other developers' active work that might conflict

## During Refactoring

- [ ] Use IDE refactoring tools (not manual find/replace)
- [ ] Keep refactoring commits separate from feature changes
- [ ] Make one type of change at a time (e.g., rename OR move, not both)
- [ ] Commit frequently with clear messages

## Function/Class Renaming Checklist

When renaming functions or classes:

### 1. Find All References
- [ ] Use IDE "Find in Files" to locate all references
- [ ] Check imports: `grep -r "from .module import old_name" .`
- [ ] Check direct calls: `grep -r "old_name(" .`
- [ ] Check string references in tests, docs, and comments
- [ ] Check configuration files (YAML, JSON, etc.)

### 2. Use IDE Rename Symbol Feature
- [ ] Use IDE "Rename Symbol" feature (Cmd+Shift+R in VS Code, F2 in PyCharm)
- [ ] This automatically updates all references within the IDE's scope
- [ ] Review all changes the IDE makes before accepting

### 3. Manual Updates (if IDE refactoring unavailable)
- [ ] Update the function/class definition
- [ ] Update all imports
- [ ] Update all function calls
- [ ] Update documentation and comments
- [ ] Update test function names if applicable
- [ ] Update any string references

### 4. Verify Changes
- [ ] Run import validation: `python3 scripts/validate-imports.py`
- [ ] Run all tests: `uv run pytest`
- [ ] Start the application: `uv run streamlit run apps/frontend/app.py`
- [ ] Test manually to ensure functionality is preserved

## Module Moving/Reorganization Checklist

When moving files or reorganizing modules:

### 1. Plan the Move
- [ ] Document the new structure in `docs/architecture/`
- [ ] Identify all files that need to move
- [ ] List all affected imports
- [ ] Plan for backward compatibility if needed

### 2. Execute the Move
- [ ] Use IDE "Move/Refactor" feature if available
- [ ] Move one file at a time
- [ ] Update imports in the moved file
- [ ] Update imports in all files that reference the moved file
- [ ] Update `__init__.py` files if applicable

### 3. Update References
- [ ] Update absolute imports
- [ ] Update relative imports
- [ ] Update test imports
- [ ] Update documentation references
- [ ] Update configuration paths

### 4. Verify
- [ ] Run import validation
- [ ] Run all tests
- [ ] Check for circular import issues
- [ ] Test the application manually

## Code Style Refactoring

When changing code style or formatting:

### 1. Automated Formatting
- [ ] Use Black for Python formatting: `black .`
- [ ] Use Ruff for linting: `ruff check --fix .`
- [ ] Run MyPy for type checking: `mypy apps/backend`

### 2. Manual Style Changes
- [ ] Make one type of style change at a time
- [ ] Run tests after each change
- [ ] Commit each style change separately

## After Refactoring

### 1. Quality Checks
- [ ] Run `./scripts/quality-check.sh` for comprehensive validation
- [ ] Ensure 90%+ test coverage maintained
- [ ] Check for new linting issues
- [ ] Review type hints and documentation

### 2. Testing
- [ ] Run full test suite: `uv run pytest --cov=apps.backend --cov=apps.frontend`
- [ ] Test manually: `uv run streamlit run apps/frontend/app.py`
- [ ] Verify all KPIs display correctly
- [ ] Check for console errors in browser

### 3. Documentation
- [ ] Update architectural documentation
- [ ] Update API documentation if applicable
- [ ] Add migration notes if breaking changes
- [ ] Update DEVELOPMENT_LOG.md

### 4. Commit and Push
- [ ] Write clear commit message following format:
  ```
  refactor: rename add_trend_line to add_trend_line_to_figure

  Updated all imports and function calls in:
  - apps/frontend/chart_kpis.py
  - apps/frontend/chart_production.py

  Closes #123
  ```
- [ ] Push to feature branch
- [ ] Create pull request with detailed description
- [ ] Request code review

## Common Pitfalls to Avoid

### 1. Incomplete Reference Updates
**Problem**: Renaming a function but missing some import statements or calls.

**Solution**: Always use IDE refactoring tools or comprehensive grep searches.

**Example**:
```bash
# Find all references before renaming
grep -r "add_trend_line" apps/ tests/

# Verify after refactoring
grep -r "add_trend_line" apps/ tests/
# Should return 0 matches for old name
```

### 2. Changing Function Signatures
**Problem**: Renaming parameters or changing return types without updating all callers.

**Solution**: Change signatures separately from renames. Add type hints to catch issues.

**Example**:
```python
# Before
def calculate_rate(production: float, collections: float) -> float:
    return (collections / production) * 100

# After - add type hints first
def calculate_rate(production: float, collections: float) -> float:
    return (collections / production) * 100

# Then rename if needed
def calculate_collection_rate(production: float, collections: float) -> float:
    return (collections / production) * 100
```

### 3. Batch Refactoring
**Problem**: Making multiple types of changes in one commit (rename + move + style).

**Solution**: Separate refactoring into discrete commits.

**Example**:
```bash
# Bad - all in one commit
git commit -m "refactor: reorganize chart modules"

# Good - separate commits
git commit -m "refactor: rename add_trend_line to add_trend_line_to_figure"
git commit -m "refactor: move chart utilities to chart_utils.py"
git commit -m "style: apply black formatting to chart modules"
```

### 4. Skipping Tests
**Problem**: Not running tests before committing refactoring changes.

**Solution**: Always run tests, even for "simple" refactoring.

**Example**:
```bash
# Run quick validation
python3 scripts/validate-imports.py

# Run tests
uv run pytest

# Run quality checks
./scripts/quality-check.sh
```

## IDE-Specific Tips

### VS Code
- **Rename Symbol**: F2 or Cmd+Shift+R
- **Find All References**: Shift+F12
- **Go to Definition**: F12
- **Search in Files**: Cmd+Shift+F

### PyCharm
- **Rename**: Shift+F6
- **Find Usages**: Alt+F7
- **Go to Declaration**: Cmd+B
- **Search Everywhere**: Double Shift

### Vim/Neovim with LSP
- **Rename**: `:lua vim.lsp.buf.rename()`
- **Find References**: `:lua vim.lsp.buf.references()`
- **Go to Definition**: `gd`

## Emergency Rollback Procedure

If refactoring breaks the application:

1. **Immediate Revert**:
   ```bash
   git revert HEAD
   git push
   ```

2. **Branch Rollback**:
   ```bash
   git reset --hard HEAD~1
   git push --force-with-lease
   ```

3. **Cherry-pick Good Changes**:
   ```bash
   git cherry-pick <commit-hash>
   ```

4. **Start Fresh**:
   ```bash
   git checkout main
   git pull
   git checkout -b refactor-fix
   # Make changes carefully
   ```

## Pre-commit Hook Integration

Our pre-commit hooks will automatically catch many refactoring issues:

- **Import Validation**: Catches broken imports before commit
- **Black Formatting**: Ensures consistent style
- **Ruff Linting**: Catches unused imports and other issues
- **MyPy Type Checking**: Verifies type hints are correct
- **Pytest**: Runs tests automatically on changed files

To run pre-commit hooks manually:
```bash
pre-commit run --all-files
```

## Refactoring Communication

### Document Active Work
Update `DEVELOPMENT_LOG.md` before starting:
```markdown
| Date | Developer | Changes | Status |
|------|-----------|---------|--------|
| 2025-09-29 | AOJDevStudio | Rename add_trend_line to add_trend_line_to_figure | In Progress |
```

### Code Review Checklist
When reviewing refactoring PRs:
- [ ] All imports updated
- [ ] All function calls updated
- [ ] Tests pass
- [ ] No decrease in coverage
- [ ] Documentation updated
- [ ] Breaking changes documented
- [ ] Migration guide provided if needed

## Refactoring Decision Matrix

| Type of Change | Risk Level | Required Actions |
|----------------|-----------|------------------|
| Rename internal function | Low | Update imports, run tests |
| Rename public API | High | Update imports, tests, docs, add migration notes |
| Move file within module | Medium | Update imports, run tests, update docs |
| Move file between modules | High | Update all imports, check circular deps, run all tests |
| Change function signature | High | Update all callers, type hints, tests, docs |
| Split large module | High | Plan carefully, update imports, extensive testing |

## Success Criteria

Refactoring is successful when:
- [ ] All tests pass
- [ ] Import validation passes
- [ ] Application runs without errors
- [ ] Coverage is maintained or improved
- [ ] Documentation is updated
- [ ] Team is informed
- [ ] No new linting issues
- [ ] Performance is maintained or improved

## Questions or Issues?

If you encounter issues during refactoring:

1. Check this document first
2. Review recent git history for similar changes
3. Check `DEVELOPMENT_LOG.md` for active work
4. Ask team members before making large changes
5. Document issues for future reference

---

**Remember**: The best refactoring is safe refactoring. Take your time, follow the checklists, and don't skip the testing steps!