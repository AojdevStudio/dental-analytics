# DAN-1: TypedDict → Pydantic Migration Analysis

**Created:** 2025-10-01
**Context:** Backend Decoupling Phase 0
**Status:** Critical Gap Identified

---

## Executive Summary

The DAN-1 issue proposes Pydantic models but **does not address the existing TypedDict infrastructure** in `apps/backend/types.py`. This document analyzes the current state and proposes a **clean migration strategy**.

---

## Current State Analysis

### Existing TypedDict Infrastructure

**Location:** `apps/backend/types.py`
**Created:** 2025-01-30
**Phase:** 3 of 4-phase TypedDict refactoring plan
**Purpose:** Replace `dict[str, Any]` with strongly-typed structures

**Current TypedDicts (22 total):**

#### Core Data Structures
1. **KPIData** - Response for 5 core KPI calculations
2. **MultiLocationKPIData** - KPIs for Baytown + Humble
3. **TimeSeriesPoint** - Individual chart data point
4. **ChartData** - Complete chart data for frontend
5. **TimeSeriesChartData** - Advanced time series with metadata

#### Historical Metrics (4 specialized variants)
6. **HistoricalProductionData** - Production time series + aggregations
7. **HistoricalRateData** - Rate-based metrics (Collection, Hygiene)
8. **HistoricalCountData** - Count-based metrics (New Patients, Case Acceptance)
9. **HistoricalKPIData** - Complete historical response structure

#### Statistics & Metadata
10. **ChartStatistics** - Basic statistics (min/max/average)
11. **ChartSummaryStats** - Advanced statistics with coverage metrics
12. **ChartMetadata** - Data source and processing info
13. **DataSourceMetadata** - Data availability flags
14. **AllChartsMetadata** - Complete chart collection metadata

#### Configuration
15. **SheetConfig** - Google Sheets data source configuration
16. **LocationConfig** - Location-to-sheets mapping
17. **ProviderConfig** - Google Sheets API configuration
18. **ConfigData** - Complete YAML configuration post-ingestion

#### Type Aliases
19. **HistoricalMetricData** - Union of historical variants
20. **AllChartData** - Dict of chart data + metadata
21. **SpreadsheetInfo** - Spreadsheet ID + range mapping

### Dependency Graph

**Module Imports:**
```python
# metrics.py (Line 22-31)
from .types import (
    HistoricalCountData,
    HistoricalKPIData,
    HistoricalMetricData,
    HistoricalProductionData,
    HistoricalRateData,
    KPIData,
    MultiLocationKPIData,
)

# chart_data.py (Line 14-20)
from .types import (
    AllChartData,
    ChartData,
    ChartStatistics,
    ChartSummaryStats,
    TimeSeriesChartData,
    TimeSeriesPoint,
)
```

**No imports found in:**
- `data_providers.py` (likely uses types implicitly or internally)
- `historical_data.py` (not checked, but likely imports from types.py)

---

## Problem Statement

DAN-1 proposes creating `core/models/kpi_models.py` with Pydantic models, but:

1. ❌ **No transition strategy** from TypedDict → Pydantic
2. ❌ **No plan** for handling existing imports in `metrics.py` and `chart_data.py`
3. ❌ **Unclear** if TypedDicts will be deprecated, coexist, or replaced
4. ❌ **No adapter layer** defined for compatibility during migration
5. ❌ **Potential naming conflicts** between TypedDict KPIData and Pydantic KPIData

---

## Proposed Migration Strategy

### **Option A: Clean Break (RECOMMENDED)**

**Strategy:** Isolate Phase 0 code from existing codebase

**Approach:**
1. Create new `core/models/` with Pydantic models (as planned in DAN-1)
2. Old code continues using `apps/backend/types.py` TypedDicts
3. New Phase 0 code uses **only** Pydantic models
4. Coexist temporarily on feature branch
5. After Phase 0 merge, deprecate TypedDicts in Phase 1

**Benefits:**
- ✅ Fits "feature branch, all-at-once migration" strategy (DAN-1)
- ✅ No risk to existing production code
- ✅ Clean separation of concerns
- ✅ Easy rollback if Phase 0 fails
- ✅ Minimal refactoring during 2-hour Checkpoint 1

**Implementation:**

```python
# NEW: core/models/kpi_models.py (Pydantic)
from pydantic import BaseModel

class KPIValue(BaseModel):
    value: float | None
    available: bool
    unavailable_reason: str | None = None
    # ... (as defined in DAN-1)

class KPIResponse(BaseModel):
    location: Location
    values: KPIValues
    # ... (as defined in DAN-1)

# OLD: apps/backend/types.py (TypedDict) - UNCHANGED
class KPIData(TypedDict):
    production_total: float | None
    collection_rate: float | None
    # ... (existing code)

# OLD: apps/backend/metrics.py - UNCHANGED
from .types import KPIData  # Still using TypedDict

def get_all_kpis(location: str) -> KPIData:
    # Existing implementation
    pass

# NEW: services/kpi_service.py (Phase 0)
from core.models.kpi_models import KPIResponse  # Using Pydantic

class KPIService:
    def get_kpis(self, location: Location) -> KPIResponse:
        # New implementation with Pydantic
        pass
```

**Coexistence Period:**
- Phase 0: Both systems exist on feature branch
- Phase 1: Deprecate `apps/backend/types.py` after Phase 0 merge
- Phase 2: Remove TypedDicts entirely

---

### **Option B: In-Place Migration (NOT RECOMMENDED)**

**Strategy:** Replace TypedDicts in `types.py` with Pydantic models

**Approach:**
1. Replace all TypedDicts in `apps/backend/types.py` with Pydantic models
2. Update all imports in `metrics.py`, `chart_data.py`, etc.
3. Fix all call sites to use `.model_dump()` instead of dict casting
4. Run tests to catch breakage

**Problems:**
- ❌ Risky for 2-hour Checkpoint 1 timeline
- ❌ Requires updating **all** existing code at once
- ❌ Breaks "all-at-once migration, merge when complete" strategy
- ❌ Hard to isolate Phase 0 changes
- ❌ Difficult rollback if issues arise

**Recommendation:** Avoid this approach for Phase 0

---

### **Option C: Gradual Hybrid with Adapters**

**Strategy:** Add Pydantic alongside TypedDicts with adapter layer

**Approach:**
1. Keep `apps/backend/types.py` TypedDicts
2. Add new `core/models/` Pydantic models
3. Create adapter functions to convert between formats
4. Gradually migrate modules over time

**Implementation:**

```python
# NEW: core/adapters/kpi_adapters.py
from apps.backend.types import KPIData as LegacyKPIData
from core.models.kpi_models import KPIResponse

def legacy_to_pydantic(legacy: LegacyKPIData, location: str) -> KPIResponse:
    """Convert legacy TypedDict to Pydantic model"""
    return KPIResponse(
        location=location,
        values=KPIValues(
            production_total=KPIValue(
                value=legacy["production_total"],
                available=legacy["production_total"] is not None
            ),
            # ... convert all fields
        )
    )

def pydantic_to_legacy(response: KPIResponse) -> LegacyKPIData:
    """Convert Pydantic model to legacy TypedDict"""
    return {
        "production_total": response.values.production_total.value,
        "collection_rate": response.values.collection_rate.value,
        # ... convert all fields
    }
```

**Problems:**
- ❌ Complex adapter layer adds cognitive overhead
- ❌ Performance penalty for conversions
- ❌ Longer timeline (not suitable for 2-hour Checkpoint 1)
- ❌ More code to maintain during transition

**Recommendation:** Only use if gradual migration is required

---

## Recommended Approach: Option A (Clean Break)

### Phase 0 Implementation Plan

**Hour 1: Foundation (0:00 - 1:00)**

**0:00 - 0:15: Setup**
- Create `core/models/` directory
- Create `core/models/kpi_models.py` with Pydantic models (as DAN-1 spec)
- Create `core/models/__init__.py`

**0:15 - 0:45: Pydantic Models**
- Implement all models from DAN-1 Section 3 (Layer 1: Data Contracts)
- Add validators as needed
- Test imports work

**0:45 - 1:00: Business Calendar**
- Create `core/business_rules/calendar.py` (unchanged from DAN-1)
- Write 3 tests for business day logic

**Hour 2: Core Logic (1:00 - 2:00)**

**1:00 - 1:20: Pure Calculators**
- Create `core/calculators/kpi_calculator.py`
- All functions return `CalculationResult` (Pydantic model, not TypedDict)
- **No imports from `apps/backend/types.py`**

**1:20 - 2:00: Calculator Tests**
- Write 15-20 tests for calculators
- All tests use Pydantic models
- **No dependencies on legacy TypedDict code**

**CHECKPOINT 1 REACHED:** Core logic is pure, isolated, and uses only Pydantic

---

### Post-Phase 0 Migration Plan

**Phase 1: Deprecation (After Phase 0 merge)**
1. Add deprecation warnings to `apps/backend/types.py`
2. Update `metrics.py` to use new `services/kpi_service.py`
3. Update `chart_data.py` to use Pydantic models

**Phase 2: Removal (Future)**
1. Remove all TypedDict imports from backend modules
2. Delete `apps/backend/types.py`
3. Update all tests to use Pydantic models

---

## Critical Decision Points

### Naming Conventions

**Problem:** Both systems define `KPIData`

**Resolution:**
```python
# Legacy (apps/backend/types.py)
class KPIData(TypedDict):  # Keep name for backward compatibility
    pass

# New (core/models/kpi_models.py)
class KPIResponse(BaseModel):  # Use different name to avoid conflicts
    pass
```

### Import Isolation

**Rule:** Phase 0 code **NEVER** imports from `apps/backend/types.py`

```python
# ✅ CORRECT
from core.models.kpi_models import KPIResponse
from core.calculators.kpi_calculator import calculate_production_total

# ❌ INCORRECT (violates isolation)
from apps.backend.types import KPIData
```

### Testing Strategy

**Fixtures:**
- Create new fixtures using Pydantic models
- Do NOT reuse legacy fixtures from `tests/fixtures/sample_data.py`
- Keep Phase 0 tests completely isolated

---

## Risk Mitigation

### Risk 1: Import Confusion
**Mitigation:** Use different names (`KPIData` vs `KPIResponse`)

### Risk 2: Accidental Legacy Imports
**Mitigation:** Add linter rule to block imports from `apps/backend/types.py` in `core/`

### Risk 3: Integration Issues Post-Merge
**Mitigation:** Create adapter layer in Phase 1 if needed

---

## Documentation Requirements

### Update DAN-1 Issue

Add new section:

```markdown
## TypedDict → Pydantic Migration Strategy

### Current State
- Existing TypedDict infrastructure in `apps/backend/types.py`
- Used by `metrics.py`, `chart_data.py`, and other modules

### Migration Approach: Clean Break
- Phase 0 uses **only** Pydantic models in `core/models/`
- Legacy code continues using TypedDicts (unchanged)
- No cross-contamination between old and new systems
- Deprecation of TypedDicts deferred to Phase 1

### Import Rules
- Phase 0 code: `from core.models.kpi_models import ...`
- Legacy code: `from apps.backend.types import ...`
- NO mixing of imports

### Post-Phase 0 Plan
- Phase 1: Deprecate TypedDicts, migrate `metrics.py` to Pydantic
- Phase 2: Remove `apps/backend/types.py` entirely
```

---

## Validation Checklist - Pre-Implementation

Before starting Phase 0:

- [ ] Confirm Option A (Clean Break) as migration strategy
- [ ] Verify no naming conflicts (`KPIData` vs `KPIResponse`)
- [ ] Document import rules in CLAUDE.md
- [ ] Add linter rule to prevent legacy imports in `core/`
- [ ] Create Phase 1 migration plan document
- [ ] Update DAN-1 issue with this analysis

---

## Appendix: TypedDict Inventory

### From `apps/backend/types.py`

**KPI Data Structures (3):**
- `KPIData` - Single location KPIs
- `MultiLocationKPIData` - Multi-location KPIs
- `KPIValue` - ❌ **CONFLICT** - DAN-1 also defines this as Pydantic

**Chart Data Structures (5):**
- `TimeSeriesPoint` - Single data point
- `ChartData` - Complete chart structure
- `TimeSeriesChartData` - Advanced time series
- `ChartStatistics` - Basic statistics
- `ChartSummaryStats` - Advanced statistics

**Historical Data Structures (4):**
- `HistoricalProductionData` - Production time series
- `HistoricalRateData` - Rate-based time series
- `HistoricalCountData` - Count-based time series
- `HistoricalKPIData` - Complete historical response

**Metadata Structures (3):**
- `ChartMetadata` - Processing metadata
- `DataSourceMetadata` - Source availability
- `AllChartsMetadata` - Complete collection metadata

**Configuration Structures (4):**
- `SheetConfig` - Google Sheets config
- `LocationConfig` - Location mapping
- `ProviderConfig` - API configuration
- `ConfigData` - Complete YAML config

**Type Aliases (3):**
- `HistoricalMetricData` - Union type
- `AllChartData` - Chart collection
- `SpreadsheetInfo` - Spreadsheet mapping

**Total:** 22 TypedDict definitions + 3 type aliases

---

## Recommendations

1. **CRITICAL:** Add this migration analysis to DAN-1 issue
2. **CRITICAL:** Use Option A (Clean Break) for Phase 0
3. **CRITICAL:** Rename Pydantic `KPIValue` to `KPIMetric` to avoid conflict
4. Create Phase 1 migration plan document
5. Add linter rules to enforce import isolation
6. Document in CLAUDE.md

---

**Next Steps:**
1. Review this analysis with team
2. Update DAN-1 issue
3. Confirm Checkpoint 1 implementation approach
4. Begin Phase 0 implementation with clean separation
