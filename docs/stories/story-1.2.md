# Story 1.2: Production and Collection KPI Calculations

## Status
Done
## Story

**As a** practice manager,
**I want** to see daily production totals and collection rates calculated from EOD sheets,
**so that** I can monitor practice financial performance.

## Acceptance Criteria

1. metrics.py module created with calculate_production_total() function
2. Production total correctly sums columns B-D or reads column E from EOD sheets
3. calculate_collection_rate() function implements formula: (Column F / Column E) × 100
4. Both functions handle missing or zero data gracefully
5. Functions return numeric values or None if data unavailable
6. Manual verification shows calculations match expected values from sample data

## Tasks / Subtasks

- [x] **Task 1: Create metrics.py Module Structure** (AC: 1)
  - [x] Create backend/metrics.py with MetricsCalculator class
  - [x] Add proper imports: pandas, typing for type hints
  - [x] Implement class structure with static methods pattern
  - [x] Ensure module stays under 50-line limit per architecture

- [x] **Task 2: Implement Production Total Calculation** (AC: 2)
  - [x] Create calculate_production_total() static method
  - [x] Read Column E (total_production) from EOD sheets DataFrame
  - [x] Apply pd.to_numeric() for robust type conversion with errors='coerce'
  - [x] Sum all values using pandas .sum() method
  - [x] Return float value or None if DataFrame empty/invalid

- [x] **Task 3: Implement Collection Rate Calculation** (AC: 3)
  - [x] Create calculate_collection_rate() static method
  - [x] Extract Column F (total_collections) and Column E (total_production)
  - [x] Convert both to numeric using pd.to_numeric() with error handling
  - [x] Apply formula: (collections_sum / production_sum) × 100
  - [x] Return percentage as float

- [x] **Task 4: Add Defensive Error Handling** (AC: 4, 5)
  - [x] Add None/empty DataFrame checks at start of each function
  - [x] Wrap column access in try/except for KeyError handling
  - [x] Handle division by zero in collection rate (return None)
  - [x] Use pandas errors='coerce' for type conversion safety
  - [x] Return None consistently for all error conditions

- [x] **Task 5: Create Manual Verification Script** (AC: 6)
  - [x] Create test_calculations.py in project root for verification
  - [x] Use sample data with known expected results
  - [x] Test calculate_production_total() with sample EOD data
  - [x] Test calculate_collection_rate() with same sample data
  - [x] Verify calculations match manual Excel/calculator results
  - [x] Test error conditions (empty data, missing columns, zero production)

## Dev Notes

### Technology Stack Context
[Source: architecture/fullstack/technology-stack.md]
- **Language:** Python 3.10+
- **Data Processing:** pandas 2.1+
- **Type Hints:** Required throughout for clarity
- **Package Manager:** uv (already configured)

### Previous Story Context
[Source: docs/stories/story-1.1.md - Dev Agent Record]
- **SheetsProvider Module Available:** Successfully implemented and tested (43/50 lines)
- **Google Sheets Connection:** Verified working with 25 rows from "EOD - Baytown Billing"
- **DataFrame Structure:** Confirmed data returns as pandas DataFrame with proper column headers
- **Error Handling Pattern:** Returns None on failure, logs errors (established in Story 1.1)

### Module Architecture Requirements
[Source: architecture/backend-architecture.md#core-components]

**MetricsCalculator Class Pattern:**
```python
import pandas as pd
from typing import Dict, Optional

class MetricsCalculator:
    """Calculates dental KPIs from raw data."""

    @staticmethod
    def calculate_production_total(df: pd.DataFrame) -> Optional[float]:
        """Sum daily production from Column E."""
        if df is None or df.empty:
            return None
        try:
            # Column E = total_production
            return pd.to_numeric(df['total_production'], errors='coerce').sum()
        except KeyError:
            return None

    @staticmethod
    def calculate_collection_rate(df: pd.DataFrame) -> Optional[float]:
        """Calculate collection rate percentage."""
        if df is None or df.empty:
            return None
        try:
            collections = pd.to_numeric(df['total_collections'], errors='coerce').sum()
            production = pd.to_numeric(df['total_production'], errors='coerce').sum()

            if production == 0:
                return None

            return (collections / production) * 100
        except KeyError:
            return None
```

### Google Sheets Data Schema
[Source: Story 1.1 Dev Agent Record]
- **EOD Sheet:** "EOD - Baytown Billing" with 33 columns identified
- **Key Columns for Story 1.2:**
  - Column E: `total_production` (primary production value)
  - Column F: `total_collections` (collections received)
  - Columns B-D: Individual provider production (backup calculation if E unavailable)

### File Location Requirements
[Source: architecture/source-tree.md#backend-directory]
- **File:** `backend/metrics.py`
- **Max Lines:** 50 lines (current backend: data_providers.py = 43 lines)
- **Pattern:** Static methods in MetricsCalculator class
- **Imports:** pandas, typing only (minimal dependencies)

### Error Handling Philosophy
[Source: architecture/backend-architecture.md#error-handling-philosophy]
- **Never crash the application**
- **Return None for calculation errors** (consistent with SheetsProvider)
- **Use pd.to_numeric(errors='coerce')** for safe type conversion
- **Division by zero → return None**
- **Missing columns → KeyError → return None**
- **Empty DataFrame checks at method start**

### Data Types and Validation
[Source: architecture/backend-architecture.md#calculation-flow]
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
```

### Testing Requirements
[Source: architecture/backend-architecture.md#testing-strategy]

**Manual Verification Points for Story 1.2:**
1. **Production Total Test:**
   ```python
   test_df = pd.DataFrame({
       'total_production': [1000, 2000, 3000]
   })
   result = calculate_production_total(test_df)
   assert result == 6000
   ```

2. **Collection Rate Test:**
   ```python
   test_df = pd.DataFrame({
       'total_production': [1000, 2000, 3000],
       'total_collections': [900, 1800, 2700]
   })
   rate = calculate_collection_rate(test_df)
   assert rate == 90.0  # (5400/6000) * 100
   ```

**Test Script Location:** `test_calculations.py` (project root)
**Test Framework:** Manual scripts (pytest implementation in Story 1.6)
**Validation Method:** Assert statements with known sample data

### Line Count Compliance
[Source: architecture/backend/code-quality-standards.md]
- **Current Backend Total:** 43 lines (data_providers.py)
- **Target for metrics.py:** 48 lines (under 50 limit)
- **Total Backend Limit:** 100 lines (will be 91 total after Story 1.2)
- **Single Responsibility:** One calculation per static method

### Integration with Existing Code
[Source: apps/backend/data_providers.py implementation]
- **Import Pattern:** `from apps.backend.data_providers import SheetsProvider`
- **Data Source:** Use `reader.get_sheet_data('EOD - Baytown Billing!A:N')`
- **DataFrame Structure:** First row headers, data rows follow (established pattern)
- **Connection Testing:** Already verified working with 25 data rows

## Testing

### Testing Standards
[Source: Story 1.1 testing approach and future Story 1.6 framework]
- **Test Location:** Create `test_calculations.py` in project root (manual verification)
- **Test Framework:** Manual assertion scripts for Story 1.2 (pytest in Story 1.6)
- **Coverage Requirements:** All calculation functions must be manually verified
- **Test Data:** Use sample data with known expected results
- **Error Testing:** Verify graceful handling of empty data, missing columns, division by zero

### Manual Test Script Pattern
```python
# test_calculations.py
import pandas as pd
from backend.metrics import MetricsCalculator

def test_production_calculation():
    """Test production total calculation with known data."""
    test_data = pd.DataFrame({
        'total_production': [1000, 2000, 1500]
    })
    result = MetricsCalculator.calculate_production_total(test_data)
    assert result == 4500, f"Expected 4500, got {result}"
    print("✅ Production calculation test passed")

def test_collection_rate_calculation():
    """Test collection rate calculation with known data."""
    test_data = pd.DataFrame({
        'total_production': [1000, 2000],
        'total_collections': [900, 1800]
    })
    result = MetricsCalculator.calculate_collection_rate(test_data)
    expected = 90.0  # (2700/3000) * 100
    assert abs(result - expected) < 0.01, f"Expected {expected}, got {result}"
    print("✅ Collection rate calculation test passed")

if __name__ == "__main__":
    test_production_calculation()
    test_collection_rate_calculation()
    print("🎉 All manual tests passed!")
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
- Type hint diagnostics resolved through proper pandas import structure

### Completion Notes List
- **Production Calculation**: Successfully implemented using Column E (total_production) with pd.to_numeric conversion
- **Collection Rate**: Correctly calculates (collections/production) × 100 with division-by-zero protection
- **Error Handling**: Comprehensive defensive programming with None returns for all error conditions
- **Line Count**: 33 lines total in metrics.py (under 50-line constraint)
- **Testing**: Manual verification covers positive cases and all edge cases (empty, None, missing columns, division by zero)
- **Architecture Compliance**: Static methods in MetricsCalculator class follow established backend patterns

### File List
**New Files Created:**
- `backend/metrics.py` (33 lines) - Core KPI calculation module with MetricsCalculator class
- `test_calculations.py` (67 lines) - Manual verification script for production and collection rate calculations

**Modified Files:**
- None (no existing files modified)

**Total Backend Code**: 76 lines (data_providers.py: 43 + metrics.py: 33)

## QA Results

### Review Date: 2025-09-04

### Reviewed By: Quinn (Test Architect)

**Summary:** Story 1.2 successfully implements production total and collection rate KPI calculations with comprehensive error handling and defensive programming practices. The MetricsCalculator class provides clean static methods that handle all edge cases gracefully while maintaining the architectural constraints.

**Key Findings:**
- **Implementation Quality:** Clean, well-structured code following established patterns
- **Test Coverage:** 100% coverage on metrics.py with 16 comprehensive unit tests
- **Code Quality:** Passes all linting (Black, Ruff) and type checking (MyPy)
- **Error Handling:** Comprehensive defensive programming with proper None returns
- **Architecture Compliance:** 33 lines total, well under 50-line constraint
- **Manual Verification:** All calculation tests pass with expected results

**Acceptance Criteria Verification:**
1. ✅ metrics.py module created with MetricsCalculator class
2. ✅ Production total correctly reads Column E with robust error handling
3. ✅ Collection rate implements correct formula (collections/production) × 100
4. ✅ Both functions handle missing/zero data gracefully with None returns
5. ✅ Functions return proper numeric values or None for errors
6. ✅ Manual verification confirms calculations match expected values

### Gate Status

Gate: PASS → docs/qa/gates/1.2-production-and-collection-kpi-calculations.yml
