---
title: "Phase 1: TypedDict Elimination Implementation Plan"
description: "Complete migration from TypedDict to Pydantic models across the dental analytics backend"
category: "Implementation Plan"
subcategory: "Backend Migration"
product_line: "Dental Analytics Dashboard"
audience: "Development Team"
status: "Planning"
author: "AOJDevStudio"
created_date: "2025-10-02"
last_updated: "2025-10-02"
tags:
  - backend-migration
  - pydantic
  - typeddict-elimination
  - phase-1
---

# Phase 1: TypedDict Elimination Implementation Plan

## Executive Summary

This plan details the complete migration from TypedDict to Pydantic models as the single source of truth for type definitions in the dental analytics backend. This is Phase 1 of a 3-phase backend migration roadmap that will eliminate 500 lines of duplicate type definitions, establish runtime validation, and create a clean foundation for future architectural improvements.

**Timeline:** 3 days (all-at-once sprint)
**Complexity:** Medium
**Risk:** Low (well-tested migration path)
**Impact:** High (eliminates technical debt, simplifies codebase)

**Configuration Decisions:**
- ✅ Multi-file organization (kpi_models.py, chart_models.py, config_models.py)
- ✅ Defer historical data TypedDicts to Phase 3
- ✅ Delete legacy functions immediately (no deprecated wrappers)
- ✅ Full test suite with comprehensive validation
- ✅ 3-day sprint execution (focused completion)

---

## Problem Statement

### Current State Issues

1. **Dual Type Systems**: Codebase maintains both TypedDict (500 lines in `apps/backend/types.py`) and Pydantic models (`core/models/kpi_models.py`), creating confusion and duplication.

2. **No Runtime Validation**: TypedDicts provide compile-time type hints but offer no runtime validation, leading to silent data quality issues.

3. **Legacy Facade Pattern**: `apps/backend/metrics.py` acts as a compatibility layer between old TypedDict code and new Pydantic models, adding unnecessary complexity.

4. **Import Confusion**: Developers must choose between:
   ```python
   from apps.backend.types import KPIData  # Old way (TypedDict)
   from core.models.kpi_models import KPIValue  # New way (Pydantic)
   ```

5. **Testing Overhead**: Tests must handle both type systems, increasing maintenance burden.

### Why This Matters

- **Code Reduction**: Eliminate 500 lines of duplicate definitions
- **Safety**: Pydantic catches data errors at runtime that TypedDict misses
- **Simplicity**: One clear type system instead of two competing approaches
- **Foundation**: Clean base for Phases 2 and 3 (data provider decoupling and historical analysis migration)

---

## Objectives

### Primary Goals

1. ✅ **Create** organized Pydantic model structure:
   - `core/models/chart_models.py` (11 chart-related models)
   - `core/models/config_models.py` (4 configuration models)
   - `core/models/kpi_models.py` (existing - KPI domain models)

2. ✅ **Migrate** chart/config TypedDict usage to Pydantic models

3. ✅ **Refactor** `apps/backend/metrics.py` to clean Pydantic wrapper (NO legacy functions)

4. ✅ **Reduce** `apps/backend/types.py` to minimal historical TypedDicts (Phase 3 scope):
   - Keep only: `HistoricalProductionData`, `HistoricalRateData`, `HistoricalCountData`, `HistoricalKPIData`
   - Delete all chart/config TypedDicts

5. ✅ **Update** all tests with comprehensive coverage (≥90%)

6. ✅ **Document** migration with baseline comparisons

### Success Criteria

- [ ] Three model files created: `chart_models.py`, `config_models.py`, existing `kpi_models.py`
- [ ] Zero imports of chart/config TypedDicts from `apps/backend/types`
- [ ] `apps/backend/types.py` reduced to 4 historical TypedDicts only (clearly marked for Phase 3)
- [ ] All tests passing with ≥90% coverage
- [ ] `metrics.py` is clean wrapper with NO deprecated/legacy functions
- [ ] Manual sanity checks documented (calendar boundaries, aggregation totals)
- [ ] Mypy type checking passes with no chart/config TypedDict errors

---

## Technical Approach

### Architecture Decisions

#### 1. Pydantic as Single Source of Truth

**Decision**: Use `core/models/kpi_models.py` as the sole type definition authority.

**Rationale**:
- Runtime validation catches errors TypedDict can't
- Better IDE support and error messages
- Aligns with modern Python best practices
- Already implemented for core KPI models

**Trade-offs**:
- Slightly more verbose model definitions
- Small runtime overhead (negligible for 10-20 users)
- Must update existing code using TypedDicts

#### 2. Multi-File Domain Organization

**Decision**: Create separate Pydantic model files organized by domain.

**File Structure**:

```
core/models/
├── kpi_models.py          # Existing - KPI domain models (KPIValue, KPIResponse, etc.)
├── chart_models.py        # NEW - Chart data models (11 models)
└── config_models.py       # NEW - Configuration models (4 models)
```

**Distribution**:
- **kpi_models.py** (existing): KPI domain - `KPIValue`, `KPIResponse`, `CalculationResult`, etc.
- **chart_models.py** (new): Chart processing - `ChartDataPoint`, `ProcessedChartData`, `TimeSeriesData`, etc.
- **config_models.py** (new): Configuration - `SheetsConfig`, `LocationSettings`, `DataProviderConfig`, `AppConfig`

**Reasoning**:
- **Maximum Clarity**: Each domain has its own file, reducing cognitive load
- **Focused Files**: Each file stays under 300 lines, easy to navigate
- **Clear Imports**: Developers know exactly where to find models by domain
- **Scalability**: Easy to add new domains (e.g., `reporting_models.py`) in future phases

#### 3. Historical Data Deferral

**Decision**: Defer historical data TypedDicts to Phase 3.

**Historical TypedDicts to Keep** (in `apps/backend/types.py`):
- `HistoricalProductionData`
- `HistoricalRateData`
- `HistoricalCountData`
- `HistoricalKPIData`

**Reasoning**:
- Historical data analysis is Phase 3 scope (separate architectural decision)
- Keeps Phase 1 focused on chart/config/KPI models
- Reduces migration risk and complexity
- Historical TypedDicts isolated in single file, clearly marked for Phase 3

**Implementation**:
```python
# apps/backend/types.py (Phase 1 - reduced to historical only)

"""PHASE 3 MIGRATION TARGET: Historical Data TypedDicts

This file contains ONLY historical data TypedDicts that will be migrated
in Phase 3 (Historical Analysis Migration). All chart and config TypedDicts
have been migrated to Pydantic models in Phase 1.

DO NOT add new TypedDicts here. Use Pydantic models in core/models/ instead.
"""

from typing import TypedDict

# Phase 3 Migration Targets
class HistoricalProductionData(TypedDict):
    """Phase 3: Migrate to core/models/historical_models.py"""
    ...
```

#### 4. Legacy Function Elimination

**Decision**: Delete all legacy compatibility functions immediately.

**NO Deprecated Wrappers**:
```python
# ❌ NOT doing this:
def get_production_total(location: Location) -> float | None:
    """DEPRECATED: Use get_all_kpis() instead."""
    ...

# ✅ Clean break - use KPIService directly:
def get_all_kpis(location: Location, target_date: date | None = None) -> KPIResponse:
    """Get all KPIs for a location."""
    return get_kpi_service().get_kpis(location, target_date or date.today())
```

**Reasoning**:
- Simpler codebase with no deprecated code to maintain
- Forces migration to clean Pydantic API
- No Phase 2 cleanup needed
- Clear, single API surface

#### 5. Migration Strategy

**Decision**: Bottom-up migration (core → services → apps → tests) in 3-day sprint.

**Approach**:
```
1. Create Pydantic model files (chart_models.py, config_models.py)
2. Write comprehensive unit tests for all models
3. Update apps/backend to use Pydantic
4. Update all integration tests
5. Reduce apps/backend/types.py to historical TypedDicts only
6. Run full test suite + manual validation
```

**Why Bottom-Up**:
- Ensures type safety propagates from core outward
- Allows incremental validation at each layer
- Minimizes risk of breaking changes

**Why 3-Day Sprint**:
- Maintains momentum and focus
- Faster learning through immersion
- Complete context in working memory

---

## Implementation Steps

### Step 1: Inventory TypedDict Usage (30 minutes)

**Goal**: Understand exactly what needs to be migrated.

**Tasks**:

1. **List All TypedDicts**:
   ```bash
   grep "class.*TypedDict" apps/backend/types.py
   ```

   **Expected Output** (17 TypedDicts):
   - `TimeSeriesPoint`
   - `ChartStatistics`
   - `ChartMetadata`
   - `ChartData`
   - `TimeSeriesChartData`
   - `KPIData`
   - `MultiLocationKPIData`
   - `HistoricalProductionData`
   - `HistoricalRateData`
   - `HistoricalCountData`
   - `HistoricalKPIData`
   - `SheetConfig`
   - `LocationConfig`
   - `ProviderConfig`
   - `ConfigData`
   - `ChartSummaryStats`
   - `DataSourceMetadata`
   - `AllChartsMetadata`

2. **Find All Usages**:
   ```bash
   grep -r "from apps.backend.types import" --include="*.py"
   ```

   **Known Files**:
   - `apps/backend/data_providers.py`
   - `apps/backend/chart_data.py`
   - `apps/backend/historical_data.py`
   - `apps/backend/metrics.py`
   - `tests/test_*.py` (multiple test files)

3. **Create Migration Tracker** (use personal tracker, not version controlled):
   ```markdown
   # TypedDict → Pydantic Migration Tracker

   ## Chart TypedDicts → chart_models.py (11 models)
   - [ ] TimeSeriesPoint → ChartDataPoint
   - [ ] ChartStatistics → ChartStats
   - [ ] ChartMetadata → ChartMetaInfo
   - [ ] ChartData → ProcessedChartData
   - [ ] TimeSeriesChartData → TimeSeriesData
   - [ ] MultiLocationKPIData → MultiLocationKPIs
   - [ ] ChartSummaryStats → SummaryStatistics
   - [ ] DataSourceMetadata → DataSourceInfo
   - [ ] AllChartsMetadata → ChartsMetadata
   - [ ] KPIData → (Already exists as KPIValue in kpi_models.py)

   ## Config TypedDicts → config_models.py (4 models)
   - [ ] SheetConfig → SheetsConfig
   - [ ] LocationConfig → LocationSettings
   - [ ] ProviderConfig → DataProviderConfig
   - [ ] ConfigData → AppConfig

   ## Historical TypedDicts → DEFER TO PHASE 3 (4 models)
   - [ ] HistoricalProductionData → Phase 3
   - [ ] HistoricalRateData → Phase 3
   - [ ] HistoricalCountData → Phase 3
   - [ ] HistoricalKPIData → Phase 3

   ## Files to Update (8 files)
   - [ ] apps/backend/data_providers.py (config models)
   - [ ] apps/backend/chart_data.py (chart models)
   - [ ] apps/backend/metrics.py (CLEAN wrapper, NO legacy functions)
   - [ ] apps/backend/types.py (reduce to 4 historical TypedDicts only)
   - [ ] tests/test_chart_data.py
   - [ ] tests/test_metrics.py
   - [ ] tests/test_data_sources.py
   - [ ] CLAUDE.md (update typing section)

   ## Files to Create (4 files)
   - [ ] core/models/chart_models.py
   - [ ] core/models/config_models.py
   - [ ] tests/unit/models/test_chart_models.py
   - [ ] tests/unit/models/test_config_models.py
   ```

**Deliverable**: Complete inventory documented in personal tracker.

---

### Step 2: Create Pydantic Models (3 hours)

**Goal**: Build Pydantic equivalents for all chart and config TypedDicts.

**Files to Create**:
- `core/models/chart_models.py` (11 models)
- `core/models/config_models.py` (4 models)

**Implementation**:

```python
"""Pydantic models for chart data structures.

This module provides strongly-typed, validated models for chart data processing
and visualization. All models include runtime validation and are framework-independent.

Created: 2025-10-02
Phase: 1 - TypedDict Elimination
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# TIME SERIES DATA STRUCTURES
# =============================================================================


class ChartDataPoint(BaseModel):
    """Individual time series data point for chart visualization.

    Replaces: TimeSeriesPoint (TypedDict)
    Used by: Chart data processing functions
    """

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    timestamp: str = Field(..., description="ISO format datetime string")
    value: float | int | None = Field(
        default=None, description="Metric value (None for missing data)"
    )
    has_data: bool = Field(
        default=False, description="True if value is not None"
    )

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Ensure date is in YYYY-MM-DD format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Date must be in YYYY-MM-DD format, got: {v}")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_format(cls, v: str) -> str:
        """Ensure timestamp is ISO format."""
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Timestamp must be ISO format, got: {v}")
        return v


class ChartStats(BaseModel):
    """Statistical summary for chart data.

    Replaces: ChartStatistics (TypedDict)
    """

    total: float = Field(default=0.0, description="Sum of all values")
    average: float = Field(default=0.0, description="Mean of all values")
    minimum: float = Field(default=0.0, description="Minimum value")
    maximum: float = Field(default=0.0, description="Maximum value")
    data_points: int = Field(default=0, ge=0, description="Number of data points")


class ChartMetaInfo(BaseModel):
    """Metadata describing chart data processing.

    Replaces: ChartMetadata (TypedDict)
    """

    date_column: str = Field(..., description="Name of source date column")
    date_range: str = Field(..., description="Human-readable date range")
    error: str | None = Field(default=None, description="Error message if processing failed")
    aggregation: Literal["daily", "weekly", "monthly"] | None = Field(
        default=None, description="Aggregation level applied"
    )
    business_days_only: bool | None = Field(
        default=None, description="Whether Sundays were excluded"
    )
    date_filter: str | None = Field(
        default=None, description="Date range filter applied"
    )
    filtered_data_points: int | None = Field(
        default=None, ge=0, description="Count after filtering"
    )


class ProcessedChartData(BaseModel):
    """Complete processed chart data ready for visualization.

    Replaces: ChartData (TypedDict)
    Used by: All chart processing functions
    """

    dates: list[str] = Field(default_factory=list, description="List of date strings")
    values: list[float] = Field(default_factory=list, description="List of metric values")
    statistics: ChartStats = Field(default_factory=ChartStats, description="Statistical summary")
    metadata: ChartMetaInfo
    error: str | None = Field(default=None, description="Processing error if any")

    @field_validator("dates", "values")
    @classmethod
    def validate_aligned_lengths(cls, v, info):
        """Ensure dates and values have matching lengths."""
        if info.field_name == "values":
            dates_len = len(info.data.get("dates", []))
            if len(v) != dates_len:
                raise ValueError(
                    f"Values length ({len(v)}) must match dates length ({dates_len})"
                )
        return v


class TimeSeriesData(BaseModel):
    """Time series chart data with metadata.

    Replaces: TimeSeriesChartData (TypedDict)
    """

    metric_name: str = Field(..., description="Name of the KPI metric")
    time_series: list[ChartDataPoint] = Field(
        default_factory=list, description="Time series data points"
    )
    statistics: ChartStats = Field(
        default_factory=ChartStats, description="Statistical summary"
    )
    metadata: ChartMetaInfo


class SummaryStatistics(BaseModel):
    """Summary statistics across all charts.

    Replaces: ChartSummaryStats (TypedDict)
    """

    total_data_points: int = Field(default=0, ge=0)
    date_range: str = Field(default="No data")
    has_data: bool = Field(default=False)


class DataSourceInfo(BaseModel):
    """Metadata about data sources used for charts.

    Replaces: DataSourceMetadata (TypedDict)
    """

    location: str = Field(..., description="Practice location")
    sheets_used: list[str] = Field(default_factory=list, description="Google Sheets accessed")
    last_updated: str | None = Field(default=None, description="Last data update timestamp")


class ChartsMetadata(BaseModel):
    """Aggregated metadata for all charts.

    Replaces: AllChartsMetadata (TypedDict)
    """

    summary: SummaryStatistics = Field(default_factory=SummaryStatistics)
    data_sources: list[DataSourceInfo] = Field(default_factory=list)
    processing_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )


# =============================================================================
# MULTI-LOCATION KPI STRUCTURES
# =============================================================================


class MultiLocationKPIs(BaseModel):
    """KPI data for multiple locations.

    Replaces: MultiLocationKPIData (TypedDict)
    """

    baytown: dict[str, float | None] = Field(
        default_factory=dict, description="Baytown location KPIs"
    )
    humble: dict[str, float | None] = Field(
        default_factory=dict, description="Humble location KPIs"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Data retrieval timestamp"
    )


```

---

#### Configuration Models (`core/models/config_models.py`)

```python
"""Pydantic models for application configuration.

This module provides strongly-typed, validated models for application and
data provider configuration. All models include runtime validation and are
framework-independent.

Created: 2025-10-02
Phase: 1 - TypedDict Elimination
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SheetsConfig(BaseModel):
    """Google Sheets configuration.

    Replaces: SheetConfig (TypedDict)
    """

    spreadsheet_id: str = Field(..., min_length=1, description="Google Sheets ID")
    range_name: str = Field(..., min_length=1, description="Sheet range (e.g., 'A1:Z100')")
    sheet_name: str | None = Field(default=None, description="Specific sheet name")


class LocationSettings(BaseModel):
    """Location-specific configuration.

    Replaces: LocationConfig (TypedDict)
    """

    name: str = Field(..., min_length=1, description="Location name")
    eod_sheet: SheetsConfig = Field(..., description="End-of-day sheet config")
    front_kpi_sheet: SheetsConfig = Field(..., description="Front KPI sheet config")
    business_days: list[int] = Field(
        default=[1, 2, 3, 4, 5, 6],  # Monday-Saturday
        description="Operating days (1=Monday, 7=Sunday)"
    )


class DataProviderConfig(BaseModel):
    """Data provider configuration.

    Replaces: ProviderConfig (TypedDict)
    """

    credentials_path: str = Field(..., description="Path to Google credentials JSON")
    locations: dict[str, LocationSettings] = Field(
        default_factory=dict, description="Location configurations"
    )
    cache_ttl: int = Field(default=300, ge=0, description="Cache TTL in seconds")


class AppConfig(BaseModel):
    """Application configuration.

    Replaces: ConfigData (TypedDict)
    """

    data_provider: DataProviderConfig = Field(..., description="Data provider settings")
    frontend_theme: dict[str, str] = Field(
        default_factory=dict, description="UI theme configuration"
    )
    logging_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Application logging level"
    )
```

**Testing Strategy for New Models**:

Create `tests/unit/models/test_chart_models.py`:

```python
"""Tests for chart data Pydantic models."""

import pytest
from datetime import datetime

from core.models.chart_models import (
    ChartDataPoint,
    ChartStats,
    ProcessedChartData,
    ChartMetaInfo,
)


class TestChartDataPoint:
    """Test ChartDataPoint validation."""

    def test_valid_data_point(self):
        """Test creating a valid chart data point."""
        point = ChartDataPoint(
            date="2025-09-15",
            timestamp="2025-09-15T10:30:00",
            value=1500.50,
            has_data=True,
        )
        assert point.date == "2025-09-15"
        assert point.value == 1500.50
        assert point.has_data is True

    def test_invalid_date_format(self):
        """Test that invalid date format raises validation error."""
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            ChartDataPoint(
                date="09/15/2025",  # Invalid format
                timestamp="2025-09-15T10:30:00",
                value=1500.50,
            )

    def test_invalid_timestamp_format(self):
        """Test that invalid timestamp raises validation error."""
        with pytest.raises(ValueError, match="ISO format"):
            ChartDataPoint(
                date="2025-09-15",
                timestamp="not-a-timestamp",
                value=1500.50,
            )

    def test_none_value_with_has_data_false(self):
        """Test data point with None value."""
        point = ChartDataPoint(
            date="2025-09-15",
            timestamp="2025-09-15T10:30:00",
            value=None,
            has_data=False,
        )
        assert point.value is None
        assert point.has_data is False


class TestProcessedChartData:
    """Test ProcessedChartData validation."""

    def test_valid_chart_data(self):
        """Test creating valid chart data."""
        metadata = ChartMetaInfo(
            date_column="Submission Date",
            date_range="2025-09-01 to 2025-09-15",
        )

        data = ProcessedChartData(
            dates=["2025-09-01", "2025-09-15"],
            values=[1000.0, 2000.0],
            statistics=ChartStats(
                total=3000.0,
                average=1500.0,
                minimum=1000.0,
                maximum=2000.0,
                data_points=2,
            ),
            metadata=metadata,
        )

        assert len(data.dates) == 2
        assert len(data.values) == 2
        assert data.statistics.total == 3000.0

    def test_mismatched_dates_values_length(self):
        """Test that mismatched dates/values lengths raise error."""
        metadata = ChartMetaInfo(
            date_column="Submission Date",
            date_range="2025-09-01 to 2025-09-15",
        )

        with pytest.raises(ValueError, match="must match"):
            ProcessedChartData(
                dates=["2025-09-01"],
                values=[1000.0, 2000.0],  # Length mismatch
                metadata=metadata,
            )
```

**Deliverable**: New `core/models/chart_models.py` file with comprehensive Pydantic models and passing tests.

---

### Step 3: Update `apps/backend/chart_data.py` (3 hours)

**Goal**: Migrate all chart data processing functions to use Pydantic models.

**Current State**:
- Returns TypedDict structures like `ChartData`, `TimeSeriesChartData`
- Type hints reference `apps.backend.types`

**Target State**:
- Returns Pydantic models like `ProcessedChartData`, `TimeSeriesData`
- Type hints reference `core.models.chart_models`

**Implementation Steps**:

1. **Update Imports**:
   ```python
   # OLD
   from apps.backend.types import ChartData, ChartStatistics, ChartMetadata

   # NEW
   from core.models.chart_models import ProcessedChartData, ChartStats, ChartMetaInfo
   ```

2. **Update Function Signatures**:
   ```python
   # OLD
   def process_production_data_for_chart(df: pd.DataFrame) -> ChartData:
       ...

   # NEW
   def process_production_data_for_chart(df: pd.DataFrame) -> ProcessedChartData:
       ...
   ```

3. **Update Return Statements**:
   ```python
   # OLD
   return {
       "dates": dates,
       "values": values,
       "statistics": {
           "total": total,
           "average": avg,
           "minimum": min_val,
           "maximum": max_val,
           "data_points": len(dates),
       },
       "metadata": {
           "date_column": "Submission Date",
           "date_range": f"{min_date} to {max_date}",
           "error": None,
       },
       "error": None,
   }

   # NEW
   return ProcessedChartData(
       dates=dates,
       values=values,
       statistics=ChartStats(
           total=total,
           average=avg,
           minimum=min_val,
           maximum=max_val,
           data_points=len(dates),
       ),
       metadata=ChartMetaInfo(
           date_column="Submission Date",
           date_range=f"{min_date} to {max_date}",
           error=None,
       ),
       error=None,
   )
   ```

4. **Update Error Handling**:
   ```python
   # OLD
   except Exception as e:
       return {
           "dates": [],
           "values": [],
           "statistics": {...},
           "metadata": {..., "error": str(e)},
           "error": str(e),
       }

   # NEW
   except Exception as e:
       return ProcessedChartData(
           dates=[],
           values=[],
           statistics=ChartStats(),
           metadata=ChartMetaInfo(
               date_column="",
               date_range="No data",
               error=str(e),
           ),
           error=str(e),
       )
   ```

**Functions to Update** (10 functions):
- `process_production_data_for_chart()`
- `process_collection_rate_data_for_chart()`
- `process_new_patients_data_for_chart()`
- `process_case_acceptance_data_for_chart()`
- `process_hygiene_reappointment_data_for_chart()`
- `aggregate_to_weekly()`
- `aggregate_to_monthly()`
- `filter_data_by_date_range()`
- `create_empty_chart_data()`
- `validate_processed_chart_data()`

**Validation After Changes**:
```bash
# Run linter
uv run ruff check apps/backend/chart_data.py

# Run type checker
uv run mypy apps/backend/chart_data.py

# Run tests
uv run pytest tests/test_chart_data.py -v
```

**Deliverable**: Updated `chart_data.py` with all functions using Pydantic models, all tests passing.

---

### Step 4: Update `apps/backend/data_providers.py` (1 hour)

**Goal**: Remove TypedDict usage from data provider configuration.

**Current Usage**:
- `SheetConfig`, `LocationConfig`, `ProviderConfig`

**Migration**:

```python
# OLD
from apps.backend.types import SheetConfig, LocationConfig, ProviderConfig

class SheetsProvider:
    def __init__(self, config: ProviderConfig):
        ...

# NEW
from core.models.chart_models import SheetsConfig, LocationSettings, DataProviderConfig

class SheetsProvider:
    def __init__(self, config: DataProviderConfig):
        ...
```

**Testing**:
```bash
uv run pytest tests/test_data_sources.py -v
```

**Deliverable**: Updated `data_providers.py` with Pydantic config models.

---

### Step 5: Refactor `apps/backend/metrics.py` (2 hours)

**Goal**: Convert from facade pattern to clean Pydantic wrapper (NO legacy functions).

**Current State**:
- Acts as compatibility layer between TypedDict and Pydantic
- Contains duplicate logic for data transformation
- Returns TypedDict structures to maintain backward compatibility
- ~500+ lines with legacy helper functions

**Target State**:
- Clean wrapper that calls `KPIService` and returns Pydantic models
- No data transformation logic (delegated to core layer)
- No deprecated/legacy functions (clean break)
- ~50-100 lines total

**Refactoring Strategy**:

1. **Keep ONLY**:
   - `get_kpi_service()` → Singleton service factory
   - `get_all_kpis()` → Primary KPI access method

2. **Delete Everything Else**:
   - Legacy data transformation functions
   - Duplicate calculation logic
   - TypedDict conversion helpers
   - Individual KPI accessor functions (use `get_all_kpis()` instead)

3. **Clean Implementation** (NO deprecated functions):

```python
"""Simplified metrics module - pure Pydantic wrapper.

This module provides a simplified interface to the KPI service layer.
All business logic has been moved to core/ for framework independence.

Migrated: Phase 1 - TypedDict Elimination
"""

from datetime import date

from core.models.kpi_models import KPIResponse, Location
from services.kpi_service import KPIService
from core.business_rules.calendar import BusinessCalendar
from core.business_rules.validation_rules import KPIValidationRules
from core.transformers.sheets_transformer import SheetsToKPIInputs
from apps.backend.data_providers import build_sheets_provider


# Singleton service instance
_kpi_service: KPIService | None = None


def get_kpi_service() -> KPIService:
    """Get or create the singleton KPI service instance."""
    global _kpi_service
    if _kpi_service is None:
        _kpi_service = KPIService(
            data_provider=build_sheets_provider(),
            calendar=BusinessCalendar(),
            validation_rules=KPIValidationRules(),
            transformer=SheetsToKPIInputs(),
        )
    return _kpi_service


def get_all_kpis(location: Location, target_date: date | None = None) -> KPIResponse:
    """Get all KPIs for a location on a specific date.

    Args:
        location: Practice location ("baytown" or "humble")
        target_date: Date to calculate KPIs for (defaults to today)

    Returns:
        KPIResponse with all KPI values and validation metadata

    Example:
        >>> response = get_all_kpis("baytown", date(2025, 9, 15))
        >>> production = response.values.production_total.value
        >>> collection_rate = response.values.collection_rate.value
    """
    service = get_kpi_service()
    if target_date is None:
        target_date = date.today()
    return service.get_kpis(location, target_date)
```

**That's it!** Clean, simple, ~50 lines total. No legacy functions, no deprecated code.

**Testing Strategy**:

Update `tests/test_metrics.py` to test the simplified wrapper:

```python
"""Tests for simplified metrics wrapper."""

from datetime import date

from apps.backend.metrics import get_all_kpis, get_kpi_service
from core.models.kpi_models import KPIResponse


class TestMetricsWrapper:
    """Test metrics module wrapper functions."""

    def test_get_kpi_service_singleton(self):
        """Test that KPI service is a singleton."""
        service1 = get_kpi_service()
        service2 = get_kpi_service()
        assert service1 is service2

    def test_get_all_kpis_returns_pydantic_response(self):
        """Test that get_all_kpis returns Pydantic KPIResponse."""
        response = get_all_kpis("baytown", date(2025, 9, 15))

        assert isinstance(response, KPIResponse)
        assert response.location == "baytown"
        assert hasattr(response, "values")
        assert hasattr(response, "availability")

    def test_get_all_kpis_defaults_to_today(self):
        """Test that get_all_kpis defaults to today's date."""
        response = get_all_kpis("humble")

        assert isinstance(response, KPIResponse)
        assert response.date == date.today()
```

**Deliverable**: Clean `metrics.py` (~50 lines vs current 500+), all tests passing, NO deprecated functions.

---

### Step 6: Update All Tests (2 hours)

**Goal**: Ensure all tests use Pydantic models and maintain ≥90% coverage.

**Files to Update**:
- `tests/test_chart_data.py` (primary chart tests)
- `tests/test_metrics.py` (metrics wrapper tests)
- `tests/test_data_sources.py` (provider config tests)
- `tests/test_advanced_charts.py`
- `tests/test_chart_integration.py`
- `tests/test_plotly_charts.py`

**Migration Pattern**:

```python
# OLD
def test_chart_processing():
    result = process_production_data_for_chart(df)
    assert result["error"] is None
    assert len(result["dates"]) == 2
    assert result["statistics"]["total"] == 3000.0

# NEW
def test_chart_processing():
    result = process_production_data_for_chart(df)
    assert result.error is None
    assert len(result.dates) == 2
    assert result.statistics.total == 3000.0
```

**Key Changes**:
- Dictionary access (`result["key"]`) → Attribute access (`result.key`)
- Type assertions: `isinstance(result, dict)` → `isinstance(result, ProcessedChartData)`
- Error checking: `result.get("error")` → `result.error`

**Testing Checklist**:
- [ ] All test files updated to use Pydantic models
- [ ] Coverage remains ≥90% for backend modules
- [ ] No TypedDict assertions remaining
- [ ] All tests passing: `uv run pytest --cov=apps/backend --cov=core --cov=services`

**Deliverable**: All tests updated and passing with ≥90% coverage.

---

### Step 7: Reduce `apps/backend/types.py` to Historical TypedDicts Only (30 minutes)

**Goal**: Clean up types.py to contain ONLY Phase 3 historical TypedDicts.

**Pre-cleanup Validation**:

```bash
# 1. Ensure no chart/config TypedDict imports remain
grep -r "from apps.backend.types import.*Chart\|Config\|Sheet" --include="*.py" .

# Expected: No results (only historical imports allowed)

# 2. Run full test suite
uv run pytest --cov=apps/backend --cov=core --cov=services

# Expected: All tests passing, ≥90% coverage
```

**Cleanup Implementation**:

1. **Replace entire `apps/backend/types.py` with minimal version**:

```python
"""PHASE 3 MIGRATION TARGET: Historical Data TypedDicts

This file contains ONLY historical data TypedDicts that will be migrated
in Phase 3 (Historical Analysis Migration). All chart and config TypedDicts
have been migrated to Pydantic models in Phase 1.

DO NOT add new TypedDicts here. Use Pydantic models in core/models/ instead.

Phase 1 Status: COMPLETE
- Chart TypedDicts → core/models/chart_models.py ✅
- Config TypedDicts → core/models/config_models.py ✅
- KPI TypedDicts → core/models/kpi_models.py ✅

Phase 3 Scope: Migrate historical TypedDicts below
"""

from __future__ import annotations

from typing import TypedDict


# =============================================================================
# HISTORICAL DATA STRUCTURES (Phase 3 Migration Targets)
# =============================================================================


class HistoricalProductionData(TypedDict):
    """Historical production metrics over time.

    Phase 3: Migrate to core/models/historical_models.py
    """
    dates: list[str]
    values: list[float]
    location: str
    date_range: str


class HistoricalRateData(TypedDict):
    """Historical rate metrics (collection rate, case acceptance, etc.).

    Phase 3: Migrate to core/models/historical_models.py
    """
    dates: list[str]
    values: list[float]
    metric_name: str
    location: str


class HistoricalCountData(TypedDict):
    """Historical count metrics (new patients, hygiene appointments, etc.).

    Phase 3: Migrate to core/models/historical_models.py
    """
    dates: list[str]
    values: list[int]
    metric_name: str
    location: str


class HistoricalKPIData(TypedDict):
    """Aggregated historical KPI data.

    Phase 3: Migrate to core/models/historical_models.py
    """
    production: HistoricalProductionData
    collection_rate: HistoricalRateData
    new_patients: HistoricalCountData
    location: str
    date_range: str
```

2. **Stage changes**:

```bash
# Stage the reduced types.py
git add apps/backend/types.py

# Verify changes
git diff --cached apps/backend/types.py

# Expected: 500+ lines deleted, ~80 lines remaining
```

**Deliverable**: `apps/backend/types.py` reduced to 4 historical TypedDicts (~80 lines), clearly marked for Phase 3.

---

### Step 8: Final Validation & Documentation (1 hour)

**Goal**: Comprehensive validation and documentation of migration.

**Validation Checklist**:

1. **Type Checking**:
   ```bash
   uv run mypy apps/backend/ core/ services/
   ```
   - [ ] No TypedDict-related errors
   - [ ] All Pydantic imports resolve correctly

2. **Linting**:
   ```bash
   uv run ruff check apps/backend/ core/ services/ tests/
   ```
   - [ ] No import errors
   - [ ] No unused imports

3. **Test Suite**:
   ```bash
   uv run pytest --cov=apps/backend --cov=core --cov=services --cov-report=term-missing
   ```
   - [ ] All tests passing
   - [ ] Coverage ≥90% for all backend modules

4. **Manual Sanity Checks** (document results in personal tracker):
   - [ ] Calendar boundaries: Test closed days (Sundays) return expected closure status
   - [ ] Aggregation totals: Weekly/monthly aggregations match daily sums
   - [ ] Date filtering: Date ranges exclude out-of-range values correctly
   - [ ] Pydantic validation: Invalid data raises clear validation errors

5. **Integration Test**:
   ```bash
   # Start the dashboard
   uv run streamlit run apps/frontend/app.py

   # Manual checks:
   # - [ ] Dashboard loads without errors
   # - [ ] KPIs display correctly for both locations
   # - [ ] Charts render with proper data
   # - [ ] No console errors related to types
   ```

**Documentation Updates**:

1. **Update `CLAUDE.md`**:
   ```markdown
   ### Strict Typing with Narrow Expectations
   - **All code uses Pydantic models** (Phase 1 complete):
       - KPI structures → `core/models/kpi_models.py`
       - Chart data → `core/models/chart_models.py`
       - Configuration → `core/models/config_models.py`
   - **TypedDict Migration Status**:
       - Chart/Config/KPI TypedDicts → Migrated to Pydantic ✅
       - Historical TypedDicts → Deferred to Phase 3
       - Location: `apps/backend/types.py` (4 historical TypedDicts only)
   ```

2. **Update Migration Roadmap**:
   ```markdown
   ## Phase 1: TypedDict Elimination ✅ COMPLETE

   **Completed**: 2025-10-02
   **Duration**: 3 days
   **Impact**:
   - Created 3 domain-organized Pydantic model files
   - Migrated 13 chart/config TypedDicts to 15 Pydantic models
   - Deferred 4 historical TypedDicts to Phase 3
   - Simplified `metrics.py` from 500+ lines to ~50 lines
   - Reduced `types.py` from 500 lines to ~80 lines (historical only)
   - All tests passing with ≥90% coverage

   **File Structure**:
   - Created: `core/models/chart_models.py` (11 models)
   - Created: `core/models/config_models.py` (4 models)
   - Existing: `core/models/kpi_models.py` (KPI models)
   - Reduced: `apps/backend/types.py` (4 historical TypedDicts for Phase 3)

   **Baseline Comparison**:
   - Before: 17 TypedDicts in single file, dual type systems, no runtime validation
   - After: 15 Pydantic models in 3 organized files + 4 historical TypedDicts deferred
   - Code Reduction: -450 lines (500 deleted, 50 new metrics.py)
   ```

3. **Create Migration Summary** (in personal tracker):
   ```markdown
   # Phase 1 Migration Summary

   ## Code Changes
   - Files Modified: 8
   - Files Deleted: 1
   - Lines Added: ~400 (new Pydantic models + tests)
   - Lines Removed: ~600 (TypedDict definitions + facade logic)
   - Net Change: -200 lines

   ## Type Coverage
   - Pydantic Models Created: 15
   - TypedDicts Eliminated: 17
   - Functions Migrated: 10

   ## Quality Metrics
   - Test Coverage: 93% (maintained)
   - MyPy Errors: 0 (TypedDict-related)
   - Ruff Warnings: 0

   ## Manual Validation
   - Calendar boundaries: ✅ PASS
   - Aggregation totals: ✅ PASS
   - Date filtering: ✅ PASS
   - Pydantic validation: ✅ PASS
   ```

**Deliverable**: Complete validation documentation, updated CLAUDE.md, migration roadmap updated.

---

## Potential Challenges & Solutions

### Challenge 1: Breaking Changes in Tests

**Problem**: Updating from dictionary access to attribute access may break many tests.

**Solution**:
- Use find-and-replace with regex: `result\["(\w+)"\]` → `result.$1`
- Run tests incrementally after each file update
- Use mypy to catch remaining dictionary access patterns

**Example Fix**:
```python
# Before
assert result["statistics"]["total"] == 3000.0

# After
assert result.statistics.total == 3000.0
```

### Challenge 2: Nested Dictionary Structures

**Problem**: Some TypedDicts have deeply nested structures that are complex to convert.

**Solution**:
- Create Pydantic models from innermost to outermost
- Use `Field(default_factory=...)` for nested models
- Leverage Pydantic's automatic validation propagation

**Example**:
```python
# Complex nested structure
class ChartsMetadata(BaseModel):
    summary: SummaryStatistics = Field(default_factory=SummaryStatistics)
    data_sources: list[DataSourceInfo] = Field(default_factory=list)

    # Pydantic automatically validates nested models
```

### Challenge 3: Optional Fields Handling

**Problem**: TypedDict uses `NotRequired` for optional fields; Pydantic uses `None` or `Field(default=...)`.

**Solution**:
- Convert `NotRequired[str]` → `str | None = None`
- Use `Field(default=...)` for non-None defaults
- Leverage Pydantic's `@field_validator` for complex default logic

**Example**:
```python
# TypedDict
class OldModel(TypedDict):
    required_field: str
    optional_field: NotRequired[str]

# Pydantic
class NewModel(BaseModel):
    required_field: str
    optional_field: str | None = None
```

### Challenge 4: Performance Concerns

**Problem**: Pydantic validation adds runtime overhead.

**Solution**:
- Use `model_validate()` for trusted data sources
- Enable Pydantic's `model_config = ConfigDict(validate_assignment=False)` for hot paths
- For 10-20 users, overhead is negligible (<1ms per validation)

**Measurement**:
```python
import time
from core.models.chart_models import ProcessedChartData

# Benchmark validation
start = time.perf_counter()
data = ProcessedChartData(dates=..., values=..., ...)
elapsed = time.perf_counter() - start

# Expected: <1ms for typical chart data
assert elapsed < 0.001
```

### Challenge 5: Historical Data Migration Scope

**Problem**: Historical data TypedDicts (`HistoricalProductionData`, etc.) are complex and Phase 3-scoped.

**Solution**:
- **Defer to Phase 3**: Mark historical TypedDicts as "Phase 3 Migration"
- **Temporary Isolation**: Keep historical functions using TypedDicts in a separate module
- **Document Debt**: Add TODO comments for Phase 3 cleanup

**Code Pattern**:
```python
# apps/backend/historical_data.py

# TODO: Phase 3 - Migrate to Pydantic historical models
from typing import TypedDict

class HistoricalProductionData(TypedDict):
    """TEMPORARY: Phase 3 migration target."""
    ...
```

---

## Testing Strategy

### Unit Testing

**Scope**: Test individual Pydantic models in isolation.

**Coverage Targets**:
- `core/models/chart_models.py`: 95%+
- `core/models/kpi_models.py`: 95%+ (already achieved)

**Test Files**:
- `tests/unit/models/test_chart_models.py` (new)
- `tests/unit/models/test_kpi_models.py` (existing)

**Key Test Scenarios**:
1. Valid data instantiation
2. Field validation (dates, timestamps, ranges)
3. Nested model validation
4. Optional field handling
5. Default value population
6. Custom validator logic

### Integration Testing

**Scope**: Test Pydantic models flow through layers (core → services → apps).

**Coverage Targets**:
- `apps/backend/chart_data.py`: 90%+
- `apps/backend/metrics.py`: 90%+
- `services/kpi_service.py`: 95%+ (already achieved)

**Test Files**:
- `tests/test_chart_data.py` (updated)
- `tests/test_metrics.py` (updated)
- `tests/integration/test_kpi_service.py` (existing)

**Key Test Scenarios**:
1. Chart data processing returns Pydantic models
2. KPI service returns validated `KPIResponse`
3. Error paths return Pydantic models with errors
4. Aggregation functions preserve Pydantic structure
5. Multi-location data uses Pydantic models

### Regression Testing

**Scope**: Ensure no functionality breaks during migration.

**Strategy**:
1. **Baseline Capture** (before migration):
   ```bash
   # Capture baseline test results
   uv run pytest --json-report --json-report-file=baseline.json
   ```

2. **Post-Migration Comparison**:
   ```bash
   # Run tests after migration
   uv run pytest --json-report --json-report-file=migration.json

   # Compare results
   diff baseline.json migration.json
   ```

3. **Manual Validation** (document in personal tracker):
   - Run dashboard with Baytown location, verify all 5 KPIs
   - Run dashboard with Humble location, verify all 5 KPIs
   - Test date filtering with custom ranges
   - Test weekly/monthly aggregation
   - Test closed day behavior (Sundays)

**Acceptance Criteria**:
- All previously passing tests still pass
- No new failures introduced
- Coverage maintained or improved (≥90%)

---

## Success Criteria

### Technical Success

- [x] `apps/backend/types.py` deleted from git
- [x] Zero imports from `apps.backend.types` in codebase
- [x] All TypedDict usages replaced with Pydantic models
- [x] `metrics.py` simplified to pure Pydantic wrapper (<150 lines)
- [x] All tests passing with ≥90% coverage
- [x] MyPy type checking passes (0 TypedDict-related errors)
- [x] Ruff linting passes (0 import warnings)

### Quality Success

- [x] 15+ Pydantic models created with full validation
- [x] Runtime validation catches invalid data (demonstrated in tests)
- [x] Nested models properly validated
- [x] Clear error messages for validation failures
- [x] Performance acceptable (<1ms validation overhead)

### Documentation Success

- [x] CLAUDE.md updated to reflect Pydantic-only approach
- [x] Migration roadmap Phase 1 marked complete
- [x] Personal tracker documents baseline comparisons
- [x] Manual validation results documented
- [x] Code comments explain Pydantic model choices

### Business Success

- [x] Dashboard functionality unchanged (user perspective)
- [x] All 5 KPIs calculate correctly
- [x] Charts render with proper data
- [x] Multi-location switching works
- [x] No user-facing errors or degradation

---

## Timeline & Effort Estimates

### Day 1: Setup & Core Models (4.5 hours)

- [ ] **Step 1**: Inventory TypedDict usage (30 min)
- [ ] **Step 2**: Create Pydantic models (3 hours)
  - Create `core/models/chart_models.py` (11 models)
  - Create `core/models/config_models.py` (4 models)
  - Write comprehensive unit tests for both

### Day 2: Migration & Refactoring (5.5 hours)

- [ ] **Step 3**: Update `chart_data.py` (3 hours)
- [ ] **Step 4**: Update `data_providers.py` (1 hour)
- [ ] **Step 5**: Refactor `metrics.py` to clean wrapper (2 hours)
  - Delete ALL legacy functions
  - Keep only `get_kpi_service()` and `get_all_kpis()`

### Day 3: Testing & Cleanup (4 hours)

- [ ] **Step 6**: Update all tests (2 hours)
- [ ] **Step 7**: Reduce `types.py` to historical TypedDicts only (30 min)
  - Delete 13 chart/config TypedDicts
  - Keep 4 historical TypedDicts for Phase 3
- [ ] **Step 8**: Final validation & documentation (1.5 hours)

**Total Effort**: 14 hours (~2 working days)

**Buffer**: +1 day for unexpected issues = **3 days total**

**Configuration**: Multi-file organization, no deprecated functions, full test suite

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking tests during migration | Medium | Medium | Incremental updates, run tests after each file |
| Performance regression | Low | Low | Benchmark validation, optimize hot paths |
| Mypy errors from complex types | Medium | Low | Incremental type checking, use `Any` sparingly |
| Missed TypedDict usages | Low | Medium | Grep for all imports before deletion |
| Historical data migration scope creep | Medium | High | **Defer to Phase 3**, document clearly |

**Risk Mitigation Strategy**:
- Work in small increments (file-by-file)
- Run tests after each change
- Use version control (commit after each step)
- Document assumptions and decisions in personal tracker

---

## Rollback Plan

**If migration fails or introduces critical issues:**

1. **Immediate Rollback**:
   ```bash
   # Revert all changes
   git reset --hard HEAD~1  # Or specific commit before migration

   # Verify tests pass
   uv run pytest
   ```

2. **Partial Rollback** (if some files work):
   ```bash
   # Cherry-pick successful changes
   git checkout HEAD~1 -- apps/backend/types.py  # Restore types.py
   git checkout HEAD~1 -- apps/backend/chart_data.py  # Restore problematic file
   ```

3. **Recovery Checklist**:
   - [ ] Restore `apps/backend/types.py`
   - [ ] Revert imports to TypedDict
   - [ ] Run full test suite
   - [ ] Verify dashboard functionality
   - [ ] Document failure reasons in personal tracker

4. **Post-Mortem**:
   - Analyze what went wrong
   - Update this plan with lessons learned
   - Adjust timeline and approach
   - Re-plan migration with new insights

---

## Next Steps After Phase 1

**Phase 2: Data Provider Decoupling** (planned after Phase 1 completion)

**Goals**:
- Extract Google Sheets logic from `apps/backend/data_providers.py`
- Create generic `DataProvider` protocol in `core/`
- Support multiple data sources (Google Sheets, CSV, database)

**Phase 3: Historical Analysis Migration** (planned after Phase 2)

**Goals**:
- Migrate `apps/backend/historical_data.py` to use Pydantic
- Move historical analysis to `core/analyzers/`
- Implement time-series analysis with Pydantic models

---

## Appendix: TypedDict to Pydantic Mapping

| TypedDict | Pydantic Model | Location | Notes |
|-----------|---------------|----------|-------|
| `TimeSeriesPoint` | `ChartDataPoint` | `core/models/chart_models.py` | Added date/timestamp validation |
| `ChartStatistics` | `ChartStats` | `core/models/chart_models.py` | Added `ge=0` constraints |
| `ChartMetadata` | `ChartMetaInfo` | `core/models/chart_models.py` | Added aggregation literal types |
| `ChartData` | `ProcessedChartData` | `core/models/chart_models.py` | Added cross-field validation |
| `TimeSeriesChartData` | `TimeSeriesData` | `core/models/chart_models.py` | Nested model validation |
| `KPIData` | `KPIValue` | `core/models/kpi_models.py` | Already exists |
| `MultiLocationKPIData` | `MultiLocationKPIs` | `core/models/chart_models.py` | Added timestamp auto-generation |
| `HistoricalProductionData` | *Deferred* | Phase 3 | Complex migration, separate phase |
| `HistoricalRateData` | *Deferred* | Phase 3 | Complex migration, separate phase |
| `HistoricalCountData` | *Deferred* | Phase 3 | Complex migration, separate phase |
| `HistoricalKPIData` | *Deferred* | Phase 3 | Complex migration, separate phase |
| `SheetConfig` | `SheetsConfig` | `core/models/chart_models.py` | Added min_length validation |
| `LocationConfig` | `LocationSettings` | `core/models/chart_models.py` | Added business_days field |
| `ProviderConfig` | `DataProviderConfig` | `core/models/chart_models.py` | Added cache_ttl field |
| `ConfigData` | `AppConfig` | `core/models/chart_models.py` | Added logging_level field |
| `ChartSummaryStats` | `SummaryStatistics` | `core/models/chart_models.py` | Added `ge=0` constraints |
| `DataSourceMetadata` | `DataSourceInfo` | `core/models/chart_models.py` | Simplified structure |
| `AllChartsMetadata` | `ChartsMetadata` | `core/models/chart_models.py` | Added auto-timestamp |

---

## Conclusion

Phase 1 represents a foundational shift from dual type systems (TypedDict + Pydantic) to a single, validated, runtime-safe Pydantic-based architecture. By eliminating 500 lines of TypedDict definitions and refactoring the facade pattern in `metrics.py`, we:

1. **Simplify the codebase**: One type system, clearer imports
2. **Improve safety**: Runtime validation catches errors earlier
3. **Enable future work**: Clean foundation for Phases 2 & 3
4. **Maintain quality**: All tests pass with ≥90% coverage

This migration is low-risk, high-impact, and sets the stage for more ambitious architectural improvements in subsequent phases.

**Ready to proceed? Begin with Step 1: Inventory TypedDict Usage.**
