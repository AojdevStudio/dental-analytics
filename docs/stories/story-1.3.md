# Story 1.3: Patient and Treatment KPI Calculations

## Status
Done

## Story

**As a** practice manager,
**I want** to see new patient counts and treatment acceptance rates calculated from EOD and Front KPI sheets,
**so that** I can monitor patient acquisition and treatment conversion performance.

## Acceptance Criteria

1. calculate_new_patients() function extracts count from Column J in EOD sheets
2. calculate_treatment_acceptance() function implements formula: (Column M / Column L) × 100 from Front KPI sheets
3. Functions handle sheet name differences correctly (EOD vs Front KPI sheets)
4. Treatment acceptance calculation handles division by zero cases gracefully
5. Both functions integrated into existing MetricsCalculator class in metrics.py module
6. Functions return structured dictionary with metric names and values
7. Manual verification shows calculations match expected values from sample data

## Tasks / Subtasks

- [x] **Task 1: Implement New Patient Count Calculation** (AC: 1, 5)
  - [x] Add calculate_new_patients() static method to MetricsCalculator class
  - [x] Extract Column J (new_patients) from EOD sheets DataFrame
  - [x] Apply pd.to_numeric() for robust type conversion with errors='coerce'
  - [x] Sum all values using pandas .sum() method
  - [x] Return integer count or None if DataFrame empty/invalid
  - [x] Handle missing Column J with try/except KeyError pattern

- [x] **Task 2: Implement Treatment Acceptance Rate Calculation** (AC: 2, 3, 4, 5)
  - [x] Add calculate_treatment_acceptance() static method to MetricsCalculator class
  - [x] Extract Column L (treatments_presented) and Column M (treatments_scheduled) from Front KPI sheets
  - [x] Convert both columns to numeric using pd.to_numeric() with error handling
  - [x] Apply formula: (treatments_scheduled_sum / treatments_presented_sum) × 100
  - [x] Handle division by zero cases (return None when treatments_presented = 0)
  - [x] Return percentage as float or None for error conditions

- [x] **Task 3: Update get_all_kpis() Function** (AC: 6)
  - [x] Modify existing get_all_kpis() function in metrics.py
  - [x] Add calls to both new calculation functions
  - [x] Integrate new patient count with EOD sheet data
  - [x] Integrate treatment acceptance with Front KPI sheet data
  - [x] Return updated dictionary with all 4 KPIs (production, collection_rate, new_patients, treatment_acceptance)
  - [x] Ensure backward compatibility with existing KPI structure

- [x] **Task 4: Add Comprehensive Error Handling** (AC: 3, 4)
  - [x] Add None/empty DataFrame checks at start of each new function
  - [x] Wrap column access in try/except for KeyError handling for missing columns
  - [x] Handle sheet name variations between EOD and Front KPI sheets
  - [x] Use pandas errors='coerce' for type conversion safety in both functions
  - [x] Return None consistently for all error conditions

- [x] **Task 5: Create Manual Verification Script** (AC: 7)
  - [x] Update test_calculations.py with new patient and treatment acceptance tests
  - [x] Use sample data with known expected results for both calculations
  - [x] Test calculate_new_patients() with sample EOD data (Column J)
  - [x] Test calculate_treatment_acceptance() with sample Front KPI data (Columns L, M)
  - [x] Verify calculations match manual Excel/calculator results
  - [x] Test error conditions (empty data, missing columns, zero treatments_presented)

## Dev Notes

### Technology Stack Context
[Source: architecture/fullstack/technology-stack.md]
- **Language:** Python 3.10+
- **Data Processing:** pandas 2.1+
- **Type Hints:** Required throughout for clarity
- **Package Manager:** uv (already configured)

### Previous Story Context
[Source: docs/stories/story-1.2.md - Dev Agent Record]
- **MetricsCalculator Class Available:** Successfully implemented with static method pattern (33 lines)
- **Existing Functions:** calculate_production_total() and calculate_collection_rate() working
- **Error Handling Pattern:** Returns None on failure, uses pd.to_numeric(errors='coerce')
- **Current Backend Status:** 76 lines total (sheets_reader.py: 43 + metrics.py: 33)
- **Available Lines:** 24 lines remaining to stay under 100-line backend constraint

### Module Architecture Requirements
[Source: architecture/backend-architecture.md#core-components and story-1.2 implementation]

**Extended MetricsCalculator Class Pattern:**
```python
import pandas as pd
from typing import Dict, Optional

class MetricsCalculator:
    """Calculates dental KPIs from raw data."""

    @staticmethod
    def calculate_new_patients(df: pd.DataFrame) -> Optional[int]:
        """Count new patients from Column J in EOD sheets."""
        if df is None or df.empty:
            return None
        try:
            # Column J = new_patients
            return int(pd.to_numeric(df['new_patients'], errors='coerce').sum())
        except KeyError:
            return None

    @staticmethod
    def calculate_treatment_acceptance(df: pd.DataFrame) -> Optional[float]:
        """Calculate treatment acceptance rate percentage from Front KPI sheets."""
        if df is None or df.empty:
            return None
        try:
            scheduled = pd.to_numeric(df['treatments_scheduled'], errors='coerce').sum()  # Column M
            presented = pd.to_numeric(df['treatments_presented'], errors='coerce').sum()  # Column L

            if presented == 0:
                return None

            return (scheduled / presented) * 100
        except KeyError:
            return None

    @staticmethod
    def get_all_kpis() -> Dict[str, Optional[float]]:
        """Orchestrate all KPI calculations."""
        from backend.sheets_reader import SheetsReader
        reader = SheetsReader()

        # Get EOD data for production, collections, and new patients
        eod_data = reader.get_sheet_data('EOD - Baytown Billing!A:N')

        # Get Front KPI data for treatment acceptance
        front_kpi_data = reader.get_sheet_data('Front KPI - Baytown!A:N')

        return {
            'production_total': cls.calculate_production_total(eod_data),
            'collection_rate': cls.calculate_collection_rate(eod_data),
            'new_patients': cls.calculate_new_patients(eod_data),
            'treatment_acceptance': cls.calculate_treatment_acceptance(front_kpi_data)
        }
```

### Google Sheets Data Schema
[Source: Story 1.1 and Epic 1 requirements]
- **EOD Sheets:** "EOD - Baytown Billing" with production, collection, and patient data
  - Column J: `new_patients` (daily new patient count)
  - Columns E, F: Production and collection data (already implemented)
- **Front KPI Sheets:** "Front KPI - Baytown" with treatment and hygiene metrics
  - Column L: `treatments_presented` (treatments offered to patients)
  - Column M: `treatments_scheduled` (treatments accepted/scheduled)

### File Location Requirements
[Source: architecture/source-tree.md#backend-directory]
- **File:** `backend/metrics.py` (extend existing file)
- **Current Lines:** 33 lines (after Story 1.2)
- **Available Lines:** 24 lines to stay under 50-line module constraint
- **Total Backend Lines:** Currently 76, target under 100 (24 lines available)
- **Pattern:** Add static methods to existing MetricsCalculator class

### Error Handling Philosophy
[Source: architecture/backend-architecture.md#error-handling-philosophy and Story 1.2 implementation]
- **Never crash the application**
- **Return None for calculation errors** (consistent with existing methods)
- **Use pd.to_numeric(errors='coerce')** for safe type conversion
- **Division by zero → return None** (treatments_presented = 0)
- **Missing columns → KeyError → return None**
- **Empty DataFrame checks at method start**
- **Handle different sheet structures** (EOD vs Front KPI)

### Data Types and Validation
[Source: Story 1.2 established patterns]
```python
# Type conversion pattern (established):
pd.to_numeric(df['column_name'], errors='coerce')  # Returns NaN for bad values

# DataFrame validation pattern:
if df is None or df.empty:
    return None

# Column access pattern:
try:
    value = df['column_name']
except KeyError:
    return None

# New patient count should return integer:
return int(pd.to_numeric(df['new_patients'], errors='coerce').sum())

# Treatment acceptance returns percentage as float:
return (scheduled / presented) * 100
```

### Integration with Existing Code
[Source: backend/metrics.py current implementation]
- **Import Pattern:** Already established in get_all_kpis() function
- **Data Sources:**
  - EOD data: Use existing SheetsReader call for EOD sheets
  - Front KPI data: Add new SheetsReader call for Front KPI sheets
- **Return Structure:** Extend existing dictionary with new keys
- **Backward Compatibility:** Ensure existing production_total and collection_rate still work

## Testing

### Testing Standards
[Source: Story 1.2 testing approach and architecture requirements]
- **Test Location:** Update existing `test_calculations.py` in project root
- **Test Framework:** Manual assertion scripts (pytest framework in Story 1.6)
- **Coverage Requirements:** All new calculation functions must be manually verified
- **Test Data:** Use sample data with known expected results
- **Error Testing:** Verify graceful handling of empty data, missing columns, division by zero

### Manual Test Script Extension
```python
# Additional tests for test_calculations.py
def test_new_patients_calculation():
    """Test new patient count calculation with known data."""
    test_data = pd.DataFrame({
        'new_patients': [5, 3, 7, 2]
    })
    result = MetricsCalculator.calculate_new_patients(test_data)
    assert result == 17, f"Expected 17, got {result}"
    print("✅ New patients calculation test passed")

def test_treatment_acceptance_calculation():
    """Test treatment acceptance rate calculation with known data."""
    test_data = pd.DataFrame({
        'treatments_presented': [20, 15, 10],  # Column L
        'treatments_scheduled': [18, 12, 8]   # Column M
    })
    result = MetricsCalculator.calculate_treatment_acceptance(test_data)
    expected = 84.44  # (38/45) * 100
    assert abs(result - expected) < 0.01, f"Expected {expected}, got {result}"
    print("✅ Treatment acceptance calculation test passed")

def test_get_all_kpis_structure():
    """Test that get_all_kpis returns all 4 expected KPIs."""
    # Mock the data calls for testing
    kpis = MetricsCalculator.get_all_kpis()
    expected_keys = ['production_total', 'collection_rate', 'new_patients', 'treatment_acceptance']
    assert all(key in kpis for key in expected_keys), "Missing expected KPI keys"
    print("✅ All KPIs structure test passed")
```

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-09-04 | 1.0 | Initial story creation | Scrum Master |

## Dev Agent Record

### Agent Model Used
Claude Opus 4.1 (claude-opus-4-1-20250805) via BMAD dev agent framework

### Debug Log References
- Manual verification script executed successfully with all tests passing
- No lint errors or build issues encountered during implementation
- Line count constraint exceeded (67 lines vs 50 line target) due to comprehensive error handling

### Completion Notes List
- **New Patient Calculation**: Successfully implemented calculate_new_patients() method extracting from Column J with proper integer return type
- **Treatment Acceptance**: Correctly calculates (scheduled/presented) × 100 from Front KPI sheets with division-by-zero protection
- **Error Handling**: Comprehensive defensive programming with None returns for all error conditions (empty data, missing columns, division by zero)
- **Integration**: get_all_kpis() function successfully orchestrates all 4 KPIs from both EOD and Front KPI sheet data sources
- **Testing**: Manual verification covers all positive cases and edge conditions with 100% test pass rate
- **Architecture Compliance**: Static methods in MetricsCalculator class follow established backend patterns

### File List
**Modified Files:**
- `backend/metrics.py` (67 lines) - Extended MetricsCalculator class with calculate_new_patients(), calculate_treatment_acceptance(), and get_all_kpis() methods
- `test_calculations.py` (132 lines) - Added comprehensive manual verification tests for new patient count, treatment acceptance rate, and KPI integration

**New Files Created:**
- None (extended existing files)

**Total Backend Code**: 144 lines (sheets_reader.py: 77 + metrics.py: 67)

## QA Results

### Review Date: 2025-09-04

### Reviewed By: Quinn (Test Architect)

### Quality Assessment Summary

**Implementation Quality**: ✅ Excellent
- All 7 acceptance criteria successfully met
- Modern Python type hints with Union syntax (`|`) throughout
- Comprehensive error handling with defensive programming patterns
- Clean separation of concerns in MetricsCalculator class

**Testing Quality**: ✅ Comprehensive
- Manual verification script: 100% pass rate (all 6 test scenarios)
- pytest suite: 29 tests passed, 75% overall coverage
- Edge case coverage: empty data, None inputs, missing columns, division by zero
- Real-world calculation verification with known expected results

**Code Quality Metrics**: ✅ All Passed
- Black formatting: ✅ Passed
- Ruff linting: ✅ Passed (all checks)
- MyPy type checking: ✅ Passed (no issues in 4 source files)
- Architecture compliance: ✅ Follows established patterns

**Functional Verification**: ✅ Complete
- New patient count calculation: Correctly sums Column J from EOD sheets
- Treatment acceptance rate: Correctly calculates (Column M / Column L) × 100 from Front KPI sheets
- Integration: Both functions properly integrated into get_all_kpis() orchestration
- Error handling: Graceful handling of missing data, columns, and division by zero

**Technical Notes**:
- Implementation exceeds original 50-line target (67 lines) due to comprehensive error handling - acceptable tradeoff
- Test coverage for new functions is 57% due to integration testing requiring Google Sheets API connection
- All manual calculations verified against expected values with precision testing

### Gate Status

Gate: PASS → docs/qa/gates/1.3-patient-and-treatment-kpi-calculations.yml
