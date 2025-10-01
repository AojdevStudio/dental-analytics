# Story 3.0: Backend Decoupling Phase 0 - Pure Calculation Core

## Status
Draft

## Story
**As a** developer maintaining the dental analytics platform,
**I want** all calculation and data shaping logic decoupled from the UI into a pure Python core with strong types and comprehensive tests,
**so that** I can confidently maintain, test, and extend business logic independently of the presentation layer, with clear validation rules and error handling for all edge cases.

## Story Context

**🚨 CRITICAL APPROACH: Clean Break Strategy**
- **Phase 0 creates NEW isolated code** - Zero modifications to existing backend
- **NO imports from legacy code** (`apps/backend/types.py`, `metrics.py`, `chart_data.py`)
- **Pydantic models only** - No TypedDict usage
- **Parallel systems coexist** - Old dashboard works, new `core/` modules isolated
- **See Dev Notes** for complete clean break rules and enforcement

**Existing System Integration:**
- Integrates with: Current `apps/backend/metrics.py` (~1,217 LOC) and `apps/backend/data_providers.py` (~275 LOC)
- Technology: Python 3.11+, pandas, Streamlit, Google Sheets API
- Follows pattern: Direct calculation in metrics module, minimal validation
- Touch points: `apps/frontend/app.py` calls `get_all_kpis()`, test suite, Google Sheets data sources
- Linear Issue: [DAN-1](https://linear.app/aojdevstudio/issue/DAN-1)
- Migration Analysis: [docs/dan-1.md](../dan-1.md) - TypedDict → Pydantic strategy

**Current Pain Points:**
- Calculation logic tightly coupled to data retrieval
- Limited validation and error categorization
- No business calendar awareness (office closure days)
- Missing goal-based validation framework
- Unclear handling of partial data scenarios
- Type safety could be stronger

## Acceptance Criteria

### **CHECKPOINT 1: Core Logic + Tests** (Target: 2 hours)

**Functional Requirements:**
1. ✅ All 5 KPI calculations implemented as pure functions returning `CalculationResult`
2. ✅ Business calendar logic correctly identifies open/closed days for both locations
3. ✅ Pydantic models define all data contracts (`KPIValue`, `KPIResponse`, `DataFreshness`)
4. ✅ 15+ unit tests written covering happy paths and edge cases

**Quality Requirements:**
5. ✅ 90%+ test coverage achieved for `core/calculators/kpi_calculator.py`
6. ✅ All calculator tests passing (production, collection, new patients, case acceptance, hygiene)
7. ✅ Business calendar tests passing (Monday open, Friday Humble closed, Saturday Baytown alternating)
8. ✅ Zero import errors, all modules loadable

**Technical Gates:**
9. ✅ Directory structure created: `core/models/`, `core/calculators/`, `core/business_rules/`
10. ✅ Configuration files created: `config/business_rules/calendar.yml`, `config/business_rules/goals.yml`
11. ✅ Documentation added to all public functions (docstrings)
12. ✅ Ready to proceed to Checkpoint 2 (transformers + service layer)

### **CHECKPOINT 2: Transformers & Service Orchestration** (Hour 3 - Optional)

**Functional Requirements:**
13. ✅ `SheetsToKPIInputs` transformer converts raw DataFrames to calculation inputs
14. ✅ `KPIService` orchestrates calendar check → data fetch → transform → calculate → validate
15. ✅ Goal-based validation working (production vs daily goal, variance flags)
16. ✅ Graceful degradation for missing data with clear `unavailable_reason` messages

**Integration Requirements:**
17. ✅ Integration tests with fixtures showing end-to-end flow
18. ✅ All 4 data source sheets handled (EOD Baytown, EOD Humble, Front Baytown, Front Humble)
19. ✅ Partial data scenarios handled (EOD only, Front only)
20. ✅ 85%+ test coverage for `services/kpi_service.py`

### **CHECKPOINT 3: Streamlit Integration** (Hour 4 - Optional)

**NOTE:** This checkpoint modifies `apps/frontend/app.py` only - no backend legacy code touched. Frontend switch from old to new service.

**Integration Requirements:**
21. ✅ `apps/frontend/app.py` updated to use new `KPIService`
22. ✅ All 5 KPIs display correctly with new backend
23. ✅ Error states render properly ("Data Unavailable", "Closed Today", "Data Not Yet Available")
24. ✅ Validation warnings displayed appropriately

**Quality Requirements:**
25. ✅ Side-by-side comparison validates new calculations match old calculations
26. ✅ Existing integration tests pass with new architecture
27. ✅ No regression in dashboard functionality
28. ✅ Performance maintained (< 3 second load time)

### **CHECKPOINT 4: Cleanup & Documentation** (Final Hour)

**NOTE:** Cleanup only applies if Checkpoint 3 completed and frontend fully migrated. Otherwise, legacy code stays untouched.

**Quality Requirements:**
29. ✅ Old `apps/backend/metrics.py` calculation logic removed **ONLY IF** Checkpoint 3 complete and frontend migrated
30. ✅ Test coverage report shows 90%+ for all core modules
31. ✅ Architecture documentation updated in `docs/architecture/fullstack-architecture.md`
32. ✅ Testing strategy documentation updated in `docs/architecture/backend/testing-strategy.md`

**Technical Gates:**
33. ✅ All quality tools pass (Black, Ruff, MyPy)
34. ✅ Git history clean (feature branch merged)
35. ✅ Definition of Done checklist complete
36. ✅ Story marked as Done

## Tasks / Subtasks

### **CHECKPOINT 1: Foundation (Hours 0-2)**

- [x] **Setup & Configuration** (AC: 9, 10)
  - [x] Create feature branch: `git checkout -b feature/dan-1`
  - [x] Create directory structure: `core/models/`, `core/calculators/`, `core/business_rules/`, `core/transformers/`, `services/`
  - [x] Create `__init__.py` files in all new directories
  - [x] Create `config/business_rules/calendar.yml` with Baytown/Humble schedules
  - [x] Create `config/business_rules/goals.yml` with daily production goals

- [x] **Data Contracts & Models** (AC: 3, 8)
  - [x] Create `core/models/kpi_models.py` with Pydantic models:
    - [x] `Location = Literal["baytown", "humble"]`
    - [x] `DataAvailabilityStatus` enum
    - [x] `ValidationSeverity` enum
    - [x] `ValidationIssue` model
    - [x] `KPIValue` model (value, available, unavailable_reason, validation_issues)
    - [x] `KPIValues` container model
    - [x] `DataFreshness` model
    - [x] `KPIResponse` top-level response model
  - [x] Create `core/models/exceptions.py` for custom exceptions
  - [x] Test imports work without errors

- [ ] **Business Calendar Implementation** (AC: 2, 7)
  - [ ] Create `core/business_rules/calendar.py` with `BusinessCalendar` class
  - [ ] Implement `is_business_day(location, date)` method
  - [ ] Implement `_is_open_saturday(location, date)` for alternating Baytown Saturdays
  - [ ] Implement `get_expected_closure_reason(location, date)` method
  - [ ] Write unit tests:
    - [ ] Test Monday is open for both locations
    - [ ] Test Friday is closed for Humble
    - [ ] Test Saturday alternating logic for Baytown (reference date: 2025-01-04)
    - [ ] Test Sunday is closed for both locations

- [ ] **Pure Calculation Functions** (AC: 1, 11)
  - [ ] Create `core/calculators/kpi_calculator.py`
  - [ ] Implement `compute_production_total(production, adjustments, writeoffs)` → `CalculationResult`
  - [ ] Implement `compute_collection_rate(production, adjustments, writeoffs, patient_income, unearned_income, insurance_income)` → `CalculationResult`
  - [ ] Implement `compute_new_patients(new_patients_mtd)` → `CalculationResult`
  - [ ] Implement `compute_case_acceptance(treatments_presented, treatments_scheduled, same_day_treatment)` → `CalculationResult`
  - [ ] Implement `compute_hygiene_reappointment(total_hygiene, not_reappointed)` → `CalculationResult`
  - [ ] Add comprehensive docstrings to all functions

- [ ] **Calculator Unit Tests** (AC: 4, 5, 6)
  - [ ] Create `tests/unit/calculators/test_kpi_calculator.py`
  - [ ] Test `compute_production_total`:
    - [ ] Happy path (positive production)
    - [ ] With adjustments and writeoffs
    - [ ] Zero production edge case
  - [ ] Test `compute_collection_rate`:
    - [ ] Happy path (normal rate ~95%)
    - [ ] Zero production (should return `can_calculate=False`)
    - [ ] Outlier rate (>110% warning scenario)
  - [ ] Test `compute_new_patients`:
    - [ ] Happy path (positive count)
    - [ ] Negative count (invalid, should fail)
  - [ ] Test `compute_case_acceptance`:
    - [ ] Happy path (normal acceptance ~85%)
    - [ ] Zero treatments presented (should return N/A)
    - [ ] Acceptance rate > 100% (valid but warning)
  - [ ] Test `compute_hygiene_reappointment`:
    - [ ] Happy path (normal rate ~95%)
    - [ ] Zero total hygiene (should return N/A)
    - [ ] `not_reappointed > total_hygiene` (should cap to total)
  - [ ] Run coverage: `uv run pytest tests/unit/calculators/ --cov=core/calculators --cov-report=term-missing`
  - [ ] Verify 90%+ coverage achieved

- [ ] **Verify Clean Break Compliance** (AC: 8)
  - [ ] Run: `git diff --name-only | grep 'apps/backend/types.py'` → expect empty output
  - [ ] Run: `git diff --name-only | grep 'apps/backend/metrics.py'` → expect empty output
  - [ ] Run: `git diff --name-only | grep 'apps/backend/chart_data.py'` → expect empty output
  - [ ] Run: `grep -r "from apps.backend.types" core/ services/` → expect no results
  - [ ] Run: `grep -r "from .types import" core/ services/` → expect no results
  - [ ] Confirm zero modifications to legacy code (types.py, metrics.py, chart_data.py, historical_data.py)
  - [ ] Confirm all new files only in core/, services/, config/business_rules/, tests/unit/

### **CHECKPOINT 2: Transformers & Service (Hour 3 - Optional)**

- [ ] **Data Transformers** (AC: 13, 18, 19)
  - [ ] Create `core/transformers/sheets_transformer.py`
  - [ ] Implement `SheetsToKPIInputs` class
  - [ ] Implement `extract_production_inputs(eod_df)` method
  - [ ] Implement `extract_collection_inputs(eod_df)` method
  - [ ] Implement `extract_new_patients_inputs(eod_df)` method
  - [ ] Implement `extract_case_acceptance_inputs(front_df)` method
  - [ ] Implement `extract_hygiene_inputs(front_df)` method
  - [ ] Implement `_safe_extract(df, column, default)` helper with currency cleaning
  - [ ] Test with sample DataFrames showing currency formatting, nulls, mixed types

- [ ] **Validation Rules** (AC: 15)
  - [ ] Create `core/business_rules/validation_rules.py`
  - [ ] Implement `KPIValidationRules` class
  - [ ] Implement `get_daily_production_goal(location, date)` method
  - [ ] Implement `validate_production(value, location, date)` with goal-based variance checks
  - [ ] Add validation methods for other KPIs (collection rate, case acceptance, hygiene)
  - [ ] Test validation with goals from `config/business_rules/goals.yml`

- [ ] **Service Orchestration** (AC: 14, 16, 20)
  - [ ] Create `services/kpi_service.py`
  - [ ] Implement `KPIService` class with constructor dependencies
  - [ ] Implement `get_kpis(location, target_date)` main entry point
  - [ ] Implement flow: calendar check → data fetch → transform → calculate → validate
  - [ ] Implement `_create_kpi_value(result, field, location, date)` helper
  - [ ] Implement `_create_closed_response(location, date, reason)` helper
  - [ ] Implement `_create_error_response(location, date, status, error)` helper
  - [ ] Write integration tests with fixtures
  - [ ] Verify 85%+ coverage for service layer

### **CHECKPOINT 3: Streamlit Integration (Hour 4 - Optional)**

- [ ] **Frontend Integration** (AC: 21, 22, 23, 24)
  - [ ] Update `apps/frontend/app.py` to import `KPIService`
  - [ ] Replace `get_all_kpis()` call with `KPIService.get_kpis(location)`
  - [ ] Update UI to handle new `KPIResponse` structure
  - [ ] Render `DataFreshness` information
  - [ ] Display closure reasons for non-business days
  - [ ] Show validation warnings appropriately
  - [ ] Test with both Baytown and Humble locations

- [ ] **Validation & Testing** (AC: 25, 26, 27, 28)
  - [ ] Create side-by-side comparison script
  - [ ] Run old calculation logic vs new logic on same data
  - [ ] Verify all KPI values match (or document intentional differences)
  - [ ] Run existing integration tests: `uv run pytest tests/integration/`
  - [ ] Measure dashboard load time (target: < 3 seconds)
  - [ ] Test all error states render correctly

### **CHECKPOINT 4: Cleanup & Documentation (Final Hour)**

- [ ] **Code Cleanup** (AC: 29) - **CONDITIONAL: Only if Checkpoint 3 complete**
  - [ ] **Skip this task if Checkpoint 3 not completed** (legacy code stays untouched)
  - [ ] IF Checkpoint 3 complete: Review `apps/backend/metrics.py` for legacy calculation code
  - [ ] IF Checkpoint 3 complete: Remove duplicate calculation logic (keep only orchestration if needed)
  - [ ] IF Checkpoint 3 complete: Update imports in remaining files
  - [ ] IF Checkpoint 3 complete: Remove unused helper functions

- [ ] **Quality Gates** (AC: 30, 33)
  - [ ] Run full test suite: `uv run pytest --cov=core --cov=services --cov-report=term-missing`
  - [ ] Verify 90%+ coverage for all core modules
  - [ ] Run Black: `uv run black .`
  - [ ] Run Ruff: `uv run ruff check .`
  - [ ] Run MyPy: `uv run mypy apps/ core/ services/`
  - [ ] All quality tools must pass

- [ ] **Documentation Updates** (AC: 31, 32)
  - [ ] Update `docs/architecture/fullstack-architecture.md`:
    - [ ] Add 5-layer architecture diagram
    - [ ] Document new core modules
    - [ ] Update data flow section
  - [ ] Update `docs/architecture/backend/testing-strategy.md`:
    - [ ] Document new test structure
    - [ ] Add calculator test coverage goals
    - [ ] Document fixture strategy for transformers
  - [ ] Update `CLAUDE.md` if needed (new commands, structure)

- [ ] **Git & Story Completion** (AC: 34, 35, 36)
  - [ ] Commit all changes with clear messages
  - [ ] Push feature branch
  - [ ] Create pull request with story reference
  - [ ] Complete Definition of Done checklist
  - [ ] Mark story as Done

## Dev Notes

**Relevant Source Tree Information:**

```
Current Structure (~4,545 lines backend):
apps/backend/
├── __init__.py
├── chart_data.py
├── data_providers.py
├── historical_data.py
├── metrics.py
└── types.py

Target Structure (5-Layer Design):
apps/backend/
├── __init__.py
├── data_providers.py (SheetsProvider + DataProvider protocol)
├── chart_data.py
├── historical_data.py
├── metrics.py
└── types.py

core/
├── models/
│   ├── __init__.py
│   ├── kpi_models.py (Pydantic data contracts)
│   └── exceptions.py (custom exceptions)
├── calculators/
│   ├── __init__.py
│   └── kpi_calculator.py (pure calculation functions)
├── business_rules/
│   ├── __init__.py
│   ├── calendar.py (business day logic)
│   └── validation_rules.py (goal-based validation)
├── transformers/
│   ├── __init__.py
│   └── sheets_transformer.py (DataFrame → calculation inputs)

services/
├── __init__.py
└── kpi_service.py (orchestration layer)

config/business_rules/
├── calendar.yml (office schedules)
└── goals.yml (daily production targets)

tests/unit/
├── calculators/
│   └── test_kpi_calculator.py
├── business_rules/
│   └── test_calendar.py
└── transformers/
    └── test_sheets_transformer.py

tests/integration/
└── test_kpi_service.py (end-to-end flow tests)
```

---

## 🚨 **CRITICAL: Phase 0 Clean Break Rules**

**This is a feature branch with ZERO legacy dependencies. NO modifications to existing backend code.**

### **DO's (Phase 0 Code - NEW, ISOLATED):**

✅ **ONLY import from `core/` modules**
```python
# ✅ CORRECT
from core.models.kpi_models import KPIResponse
from core.calculators.kpi_calculator import compute_production_total
from core.business_rules.calendar import BusinessCalendar
```

✅ **ONLY use Pydantic models** (never TypedDicts)
```python
# ✅ CORRECT
class KPIValue(BaseModel):  # Pydantic in core/models/
    value: float | None
    available: bool
```

✅ **Create NEW test fixtures using Pydantic**
```python
# ✅ CORRECT - tests/unit/fixtures/pydantic_fixtures.py
def sample_kpi_response() -> KPIResponse:
    return KPIResponse(location="baytown", values=...)
```

✅ **All new files in `core/`, `services/`, `config/business_rules/`, `tests/unit/`**

---

### **DON'Ts (Legacy Code - DO NOT TOUCH):**

❌ **NEVER import from `apps/backend/types.py`**
```python
# ❌ INCORRECT - BREAKS CLEAN BREAK
from apps.backend.types import KPIData  # TypedDict - FORBIDDEN
```

❌ **NEVER modify existing backend files**
- `apps/backend/types.py` - 22 TypedDict definitions (untouched)
- `apps/backend/metrics.py` - Current KPI logic (untouched)
- `apps/backend/chart_data.py` - Chart generation (untouched)
- `apps/backend/historical_data.py` - Historical logic (untouched)

❌ **NEVER reuse legacy test fixtures**
```python
# ❌ INCORRECT
from tests.fixtures.sample_data import legacy_fixture  # NO
```

❌ **NEVER modify existing tests**
- `tests/test_metrics.py` (unchanged)
- `tests/test_data_providers.py` (unchanged)
- Existing integration tests (unchanged)

---

### **Why This Matters:**

**Clean Break Strategy** (per docs/dan-1.md):
- Phase 0 creates isolated new code using Pydantic
- Legacy code continues using TypedDicts (no changes)
- Zero cross-contamination between old and new systems
- Easy rollback if Phase 0 fails
- TypedDict deprecation deferred to Phase 1 (post-merge)

**Naming Conflicts Avoided:**
- Legacy: `KPIData` (TypedDict in `apps/backend/types.py`)
- Phase 0: `KPIResponse` (Pydantic in `core/models/kpi_models.py`)
- Legacy: `KPIValue` (TypedDict in `apps/backend/types.py`)
- Phase 0: `KPIValue` (Pydantic in `core/models/kpi_models.py`) - Same name OK because no imports between systems

---

### **Enforcement Validation:**

After implementation, verify clean break with:
```bash
# Zero changes to legacy backend files
git diff --name-only | grep 'apps/backend/types.py' | wc -l  # expect: 0
git diff --name-only | grep 'apps/backend/metrics.py' | wc -l  # expect: 0
git diff --name-only | grep 'apps/backend/chart_data.py' | wc -l  # expect: 0

# Zero imports from legacy types in new code
grep -r "from apps.backend.types" core/ services/ | wc -l  # expect: 0
grep -r "from .types import" core/ services/ | wc -l  # expect: 0

# All new files in correct locations
git diff --name-only | grep 'core/' | wc -l  # expect: >10
```

**See docs/dan-1.md for complete TypedDict → Pydantic migration strategy.**

---

**Critical Integration Points:**

**Phase 0 Integration Strategy (Read-Only from Legacy):**
- `apps/frontend/app.py` currently calls `from apps.backend.metrics import get_all_kpis` → **UNCHANGED in Phase 0**
- Phase 0 creates parallel system - old dashboard continues working
- **ONLY integration point**: New `KPIService` will READ from existing `SheetsProvider` in `apps/backend/data_providers.py`
- No modifications to `metrics.py`, `chart_data.py`, `historical_data.py`, or `types.py` during Phase 0

**Data Provider Integration (Read-Only):**
- The Google Sheets data provider lives in `apps/backend/data_providers.py` as `SheetsProvider`
- Implements `DataProvider` protocol: `fetch(alias)`, `list_available_aliases()`, `validate_alias()`
- New `KPIService` depends on `DataProvider` protocol (dependency injection)
- Use `build_sheets_provider()` to construct provider instance for `KPIService`
- **No changes to data_providers.py** - only consume its interface

**Post-Phase 0 (Future - NOT THIS STORY):**
- Phase 1: Update `apps/frontend/app.py` to call new `KPIService.get_kpis(location)`
- Phase 2: Deprecate old `get_all_kpis()` in `metrics.py`
- Phase 3: Migrate `chart_data.py` and `historical_data.py` to new architecture

**Important Business Logic Requirements:**

**Business Schedules:**
- **Baytown:** Monday-Friday + Alternating Saturdays (reference: 2025-01-04 open, every 2 weeks)
- **Humble:** Monday-Thursday ONLY (Closed: Fri, Sat, Sun)

**Daily Production Goals (from goals.yml):**
- **Baytown:** Mon-Thu $6,000, Fri $5,500, Sat $4,000
- **Humble:** Mon-Thu $5,500

**Data Availability Categories:**
1. **Expected Closure** (not an error): Office closed per schedule
2. **Data Not Ready** (not an error): EOD not run yet (<5-6 PM)
3. **Data Quality Issues** (recoverable): Currency format errors, negative values, outliers
4. **Infrastructure Errors** (critical): Sheet not found, auth failure, network timeout
5. **Partial Data** (calculable subset): EOD only, Front only, missing optional columns

**Validation Rules (Goal-Based):**
- **Production:** Flag if >50% over goal OR <30% under goal
- **Collection Rate:** Warning if >110% or <50%, target 98-100%
- **Case Acceptance:** Warning if >100%, target 80-90%
- **Hygiene Reappointment:** Error if not in 0-100% range, target 95%+

### Testing

**Testing Standards:**
- **Test Coverage Target:** 90%+ for all core modules (calculators, models, business_rules)
- **Test Coverage Target:** 85%+ for service orchestration layer
- **Unit Test Priority:** Focus Checkpoint 1 on calculator tests (15+ tests minimum)
- **Integration Tests:** Checkpoint 2+ with fixtures for end-to-end flow
- **Test Location:** `tests/unit/` and `tests/integration/`
- **Test Execution:** `uv run pytest --cov=core --cov=services --cov-report=term-missing`
- **Quality Tools:** Black (formatting), Ruff (linting), MyPy (type checking)

**Critical Test Scenarios:**
- **Calculator Tests:** Happy path, edge cases (zero, negative, division by zero, outliers)
- **Business Calendar Tests:** Open days, closed days, alternating Saturdays, holidays
- **Transformer Tests:** Currency formatting, null handling, missing columns, type coercion
- **Service Integration Tests:** Full flow with fixtures, partial data scenarios, error handling

**Test Fixtures Strategy:**
- Sample EOD DataFrames with realistic data (August/September 2025 samples)
- Sample Front KPI DataFrames
- Edge case fixtures (empty, null, negative, mixed types, large values)
- Backward compatibility fixtures (legacy column names)

## Technical Notes

**Integration Approach:**
- Feature branch development (`feature/dan-1`)
- All-at-once migration (no incremental rollout)
- Merge when all checkpoints complete and tests pass
- Old calculation logic removed only after new logic verified

**Architecture Pattern:**
- **5-Layer Design:**
  1. Data Contracts (Pydantic models)
  2. Business Rules (calendar, validation)
  3. Pure Calculators (stateless functions)
  4. Data Transformers (DataFrame → calculation inputs)
  5. Service Orchestration (flow control)

**Key Constraints:**
- Maintain existing KPI calculation accuracy (side-by-side validation required)
- No breaking changes to dashboard UI behavior
- Preserve all existing test coverage (update tests, don't delete)
- Zero downtime deployment strategy (feature flag if needed)
- Strong type safety with Pydantic and MyPy

**Design Principles:**
- Pure functions with no side effects (calculators)
- Clear separation of concerns (calculation vs. orchestration)
- Framework independence (core logic has no Streamlit imports)
- Testability first (dependency injection for service layer)
- Explicit error handling (no silent failures, clear reasons)

## Definition of Done

### Checkpoint 1 (Minimum Viable - 2 hours):
- [x] All 5 pure calculation functions implemented
- [x] Business calendar logic working for both locations
- [x] Pydantic models define all data contracts
- [x] 15+ unit tests written and passing
- [x] 90%+ coverage for calculators
- [x] Configuration files created (calendar.yml, goals.yml)
- [x] Zero import errors, all modules loadable
- [x] Ready to proceed to Checkpoint 2

### Checkpoint 2 (Transformers + Service - Hour 3):
- [x] Transformer extracts inputs from DataFrames
- [x] KPIService orchestrates full flow
- [x] Goal-based validation working
- [x] Integration tests with fixtures passing
- [x] 85%+ coverage for service layer

### Checkpoint 3 (Streamlit Integration - Hour 4):
- [x] Frontend uses new KPIService
- [x] All KPIs display correctly
- [x] Error states render properly
- [x] Side-by-side validation shows parity
- [x] No regression in dashboard functionality

### Checkpoint 4 (Cleanup & Documentation - Final):
- [x] Old calculation logic removed
- [x] All quality tools pass (Black, Ruff, MyPy)
- [x] Architecture documentation updated
- [x] Testing strategy documentation updated
- [x] Feature branch merged
- [x] Story marked as Done

## Risk and Compatibility Check

**Primary Risks:**

1. **Scope Underestimation Risk**
   - **Risk:** The initial story was based on a backend size of ~200 lines. The actual codebase is over 4,500 lines. The 2-4 hour estimate is likely insufficient.
   - **Mitigation:** Re-evaluate the story's timeline and complexity based on the actual codebase. Break down the work into smaller, more manageable stories if necessary.
   - **Strategy:** Focus on completing Checkpoint 1 as a discovery phase to better estimate the remaining work.

2. **Calculation Parity Risk**
   - **Risk:** New calculations don't match old calculations
   - **Mitigation:** Side-by-side comparison script, comprehensive unit tests
   - **Rollback:** Feature branch allows easy revert if issues found

3. **Scope Creep Risk**
   - **Risk:** Checkpoints 2-4 extend beyond 4-hour target
   - **Mitigation:** Checkpoint 1 is minimum viable, can stop and continue later
   - **Strategy:** Natural stopping points at each checkpoint

4. **Test Complexity Risk**
   - **Risk:** 90% coverage goal takes longer than expected
   - **Mitigation:** Focus on critical paths first (happy path + key edge cases)
   - **Strategy:** Can add more edge case tests in follow-up story

5. **Integration Risk**
   - **Risk:** Frontend integration breaks existing UI behavior
   - **Mitigation:** Update UI to handle new response structure carefully
   - **Rollback:** Keep old `get_all_kpis()` as fallback during testing

**Compatibility Verification:**

✅ **Breaking Changes Managed:**
- **API Change:** `get_all_kpis()` signature changes from simple dict to `KPIResponse` model
- **Migration Strategy:** Update all call sites in same PR (only `apps/frontend/app.py`)
- **No Aliases:** Remove old calculation code after verification complete
- **Commit Prefix:** Use `BREAKING:` for any commits that change public interfaces

✅ **Database Changes:** None required (no database in system)

✅ **UI Changes:**
- Minimal - may need to adjust error message display logic
- Add display for new fields (closure_reason, validation_issues)
- Follow existing design patterns (current Streamlit components)

✅ **Performance Impact:**
- Expected: Negligible (same calculation logic, better organized)
- Validation: Measure dashboard load time before/after (target: < 3 seconds)
- Monitoring: Add timing logs to KPIService if needed

✅ **Testing Impact:**
- All existing tests must be updated to work with new structure
- No test deletion - update assertions to match new return types
- Add new tests for pure calculation functions

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2025-10-01 | 1.0 | Initial story creation for Backend Decoupling Phase 0 | Sarah (PO) |

## Dev Agent Record

### Agent Model Used
_To be filled after implementation_

### Completion Notes List
_To be filled after implementation_

### File List
_To be filled after implementation_

### Debug Log References
_To be filled after implementation_

### Change Log
| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2025-10-01 | 1.0 | Story draft created | Sarah (PO) |

## QA Results

_To be filled after QA review_
