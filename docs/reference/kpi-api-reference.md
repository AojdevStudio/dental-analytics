# KPI API Reference

## Overview

This document provides comprehensive API reference for all KPI calculations in the dental analytics dashboard as of v2.1.0.

## Core KPI Functions

### 1. Production Total

```python
def calculate_production_total(df: pd.DataFrame | None) -> float | None
```

**Purpose**: Calculate total production from EOD billing data
**Source Column**: `total_production` (Column E)
**Formula**: Sum of all production values
**Returns**: Float value in dollars or None if calculation fails

### 2. Collection Rate

```python
def calculate_collection_rate(df: pd.DataFrame | None) -> float | None
```

**Purpose**: Calculate the percentage of production collected
**Source Columns**:
- `total_collections` (Column F)
- `total_production` (Column E)
**Formula**: `(Collections / Production) × 100`
**Returns**: Percentage (0-100) or None

### 3. New Patients

```python
def calculate_new_patients(df: pd.DataFrame | None) -> int | None
```

**Purpose**: Count total new patients
**Source Column**: `new_patients` (Column J)
**Formula**: Sum of new patient counts
**Returns**: Integer count or None

### 4. Case Acceptance

```python
def calculate_case_acceptance(df: pd.DataFrame | None) -> float | None
```

**Purpose**: Calculate percentage of treatment dollars accepted
**Source Columns**:
- `treatments_presented` (Column L) - Dollar amount presented
- `treatments_scheduled` (Column M) - Dollar amount scheduled
- `$ Same Day Treatment` (Column N) - Same day treatment dollars
**Formula**: `((Scheduled $ + Same Day $) / Presented $) × 100`
**Returns**: Percentage (can exceed 100%) or None

**Note**: Previously named "treatment_acceptance", renamed to "case_acceptance" to reflect dollar-based calculation

### 5. Hygiene Reappointment

```python
def calculate_hygiene_reappointment(df: pd.DataFrame | None) -> float | None
```

**Purpose**: Calculate hygiene reappointment rate
**Source Columns**:
- `total_hygiene_appointments` (Column C)
- `patients_not_reappointed` (Column D)
**Formula**: `((Total - Not Reappointed) / Total) × 100`
**Returns**: Percentage (0-100) or None

## Historical KPI Functions

### Historical Data Structure

All historical functions return a dictionary with:
```python
{
    "total_sum": float,      # Sum across date range
    "daily_average": float,  # Average per day
    "latest_value": float,   # Most recent value
    "data_points": int,      # Number of data points
    "time_series": list      # List of {date, value} pairs
}
```

### Historical Functions

```python
calculate_historical_production_total(df, days=30) -> dict
calculate_historical_collection_rate(df, days=30) -> dict
calculate_historical_new_patients(df, days=30) -> dict
calculate_historical_case_acceptance(df, days=30) -> dict
calculate_historical_hygiene_reappointment(df, days=30) -> dict
```

## Main API Endpoints

### Get All KPIs

```python
def get_all_kpis(location: str = "baytown") -> dict[str, float | None]
```

**Parameters**:
- `location`: "baytown" or "humble"

**Returns**:
```python
{
    "production_total": float,
    "collection_rate": float,
    "new_patients": int,
    "case_acceptance": float,
    "hygiene_reappointment": float
}
```

### Get Historical KPIs

```python
def get_historical_kpis(location: str = "baytown", days: int = 30) -> dict
```

**Returns**: Dictionary with historical data for each KPI

### Get Combined KPIs

```python
def get_combined_kpis() -> dict[str, dict[str, float | None]]
```

**Returns**: KPIs for all configured locations

## Data Provider API

### DataProvider Protocol

```python
class DataProvider(Protocol):
    def fetch(self, alias: str) -> pd.DataFrame | None
    def list_available_aliases(self) -> list[str]
    def validate_alias(self, alias: str) -> bool
    def get_location_aliases(self, location: str, sheet_type: str) -> str | None
```

### SheetsProvider

Primary implementation for Google Sheets data access:

```python
provider = build_sheets_provider()
df = provider.fetch("baytown_eod")
```

## Configuration

### Sheet Aliases (config/sheets.yml)

```yaml
sheets:
  baytown_eod:
    spreadsheet_id: "1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8"
    range: "EOD - Baytown Billing!A:N"
  baytown_front:
    spreadsheet_id: "1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8"
    range: "Baytown Front KPIs Form responses!A:Z"
  # ... additional locations

locations:
  baytown:
    eod: "baytown_eod"
    front: "baytown_front"
```

## Error Handling

All functions follow consistent error handling patterns:
- Return `None` for missing/invalid data
- Use `pd.to_numeric(errors="coerce")` for safe conversions
- Log warnings for data quality issues
- Dashboard displays "Data Unavailable" for None values

## Type Annotations

All functions use modern Python 3.10+ union syntax:
- `pd.DataFrame | None` instead of `Optional[pd.DataFrame]`
- `dict[str, float | None]` instead of `Dict[str, Optional[float]]`

## Column Mappings

EOD Sheet Columns:
- E: `total_production`
- F: `total_collections`
- J: `new_patients`

Front KPI Sheet Columns:
- C: `total_hygiene_appointments`
- D: `patients_not_reappointed`
- L: `treatments_presented` (dollars)
- M: `treatments_scheduled` (dollars)
- N: `$ Same Day Treatment` (dollars)

## Version History

- **v2.1.0**: Renamed treatment_acceptance to case_acceptance
- **v2.0.0**: Multi-location provider architecture
- **v1.5.0**: Historical data functions added
- **v1.0.0**: Initial 5 core KPIs
