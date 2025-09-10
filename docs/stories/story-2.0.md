# Story 2.0: Project Structure Refactoring - Brownfield Addition

## Status
Draft

## Story
**As a** developer,
**I want** the project directories restructured from `frontend/` and `backend/` to `apps/frontend/` and `apps/backend/`,
**so that** I can easily navigate and maintain the codebase with a well-organized project structure that supports future scalability.

## Story Context

**Existing System Integration:**
- Integrates with: Current project structure with `frontend/` and `backend/` directories
- Technology: Python 3.11, uv dependency management, Streamlit, pandas
- Follows pattern: Clean architectural separation between frontend and backend
- Touch points: All import statements, deployment scripts, documentation references

## Acceptance Criteria

**Functional Requirements:**
1. Create new `apps/` directory structure in project root
2. Move `frontend/` directory to `apps/frontend/` preserving all files and structure
3. Move `backend/` directory to `apps/backend/` preserving all files and structure
4. Update all internal import paths to reflect new directory structure

**Integration Requirements:**
5. Existing dashboard functionality continues to work unchanged after restructuring
6. New directory structure follows existing clean architecture pattern
7. Integration with Google Sheets API maintains current behavior
8. Streamlit application startup process remains unchanged

**Quality Requirements:**
9. All existing tests pass after directory restructuring
10. Code quality tools (Black, Ruff, MyPy) continue to work with new structure
11. No regression in existing KPI calculations or dashboard display
12. Documentation updated to reference new directory paths

## Tasks / Subtasks

- [ ] **Create new directory structure** (AC: 1)
  - [ ] Create `apps/` directory in project root
  - [ ] Create `apps/frontend/` subdirectory
  - [ ] Create `apps/backend/` subdirectory

- [ ] **Move existing directories** (AC: 2, 3)
  - [ ] Move all files from `frontend/` to `apps/frontend/`
  - [ ] Move all files from `backend/` to `apps/backend/`
  - [ ] Remove original `frontend/` and `backend/` directories
  - [ ] Verify file integrity after move

- [ ] **Update import statements** (AC: 4)
  - [ ] Update imports in `apps/frontend/app.py`
  - [ ] Update imports in `apps/backend/` modules
  - [ ] Update imports in test files
  - [ ] Update any relative imports between modules

- [ ] **Update configuration and scripts** (AC: 8)
  - [ ] Update CLAUDE.md run commands
  - [ ] Update pyproject.toml paths if needed
  - [ ] Update any shell scripts referencing old paths
  - [ ] Update CI/CD configuration if present

- [ ] **Verify functionality** (AC: 5, 6, 7)
  - [ ] Test Streamlit dashboard startup: `uv run streamlit run apps/frontend/app.py`
  - [ ] Verify all 5 KPIs display correctly
  - [ ] Test Google Sheets data retrieval
  - [ ] Confirm existing functionality unchanged

- [ ] **Update documentation** (AC: 12)
  - [ ] Update CLAUDE.md with new directory paths
  - [ ] Update any README or docs referencing old structure
  - [ ] Update file path references in documentation

## Dev Notes

**Relevant Source Tree Information:**
```
Current Structure:
dental-analytics/
├── frontend/
│   ├── app.py (80 lines - Streamlit dashboard)
│   └── .streamlit/config.toml (brand theme)
├── backend/
│   ├── sheets_reader.py (77 lines - Google Sheets API)
│   └── metrics.py (92 lines - KPI calculations)
├── tests/
└── pyproject.toml
```

**Target Structure:**
```
dental-analytics/
├── apps/
│   ├── frontend/
│   │   ├── app.py
│   │   └── .streamlit/config.toml
│   └── backend/
│       ├── sheets_reader.py
│       └── metrics.py
├── tests/
└── pyproject.toml
```

**Critical Integration Points:**
- `frontend/app.py` imports from `backend.metrics` and `backend.sheets_reader`
- Tests import from both frontend and backend modules
- Streamlit configuration in `.streamlit/config.toml` must remain functional
- Google API credentials path references may need updates

**Important Notes from Epic-1:**
- Backend (169 lines total): Google Sheets integration, pandas processing, metrics calculations
- Frontend (80 lines): Streamlit dashboard with KamDental branding
- Current system has 99% test coverage that must be maintained
- All 5 KPIs operational: Production Total, Collection Rate, New Patients, Treatment Acceptance, Hygiene Reappointment

### Testing
**Testing Standards:**
- Test files location: `tests/` directory (unchanged)
- Run all tests: `uv run pytest`
- Coverage requirement: Maintain 90%+ coverage
- Quality tools: `uv run black`, `uv run ruff check`, `uv run mypy`
- Integration test: Full dashboard functionality via `uv run streamlit run apps/frontend/app.py`

## Technical Notes

**Integration Approach:** Simple directory move with systematic import path updates
**Existing Pattern Reference:** Maintain clean backend/frontend separation established in Epic-1
**Key Constraints:**
- Zero downtime - existing functionality must work immediately after restructuring
- No breaking changes to external interfaces
- Preserve all file permissions and Git history

## Definition of Done

- [ ] Functional requirements met (new directory structure created and populated)
- [ ] Integration requirements verified (existing functionality unchanged)
- [ ] Existing functionality regression tested (all KPIs display correctly)
- [ ] Code follows existing patterns and standards (clean architecture maintained)
- [ ] Tests pass (existing and updated import paths)
- [ ] Documentation updated (CLAUDE.md and relevant docs reflect new structure)

## Risk and Compatibility Check

**Primary Risk:** Import path errors breaking existing functionality
**Mitigation:** Systematic testing after each import update, rollback plan ready
**Rollback:** Revert directory structure and import changes if issues arise

**Compatibility Verification:**
- [x] No breaking changes to existing APIs (directory restructure only)
- [x] Database changes: None required
- [x] UI changes follow existing design patterns (no UI changes)
- [x] Performance impact is negligible (directory structure change only)

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2025-09-15 | 1.0 | Initial story creation for project structure refactoring | Sarah (PO) |

## Dev Agent Record
*This section will be populated by the development agent during implementation*

## QA Results
*This section will be populated by the QA agent after story completion*
