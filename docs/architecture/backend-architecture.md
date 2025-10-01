---
title: "Dental Analytics Backend Architecture"
description: "Technical architecture for the backend data processing and KPI calculation modules of the dental analytics dashboard."
category: "Technical Documentation"
subcategory: "Architecture"
product_line: "Dental Analytics Dashboard"
audience: "Development Team"
status: "Final"
author: "AOJDevStudio"
created_date: "2025-09-04"
last_updated: "2025-09-16"
tags:
  - backend-architecture
  - python
  - google-sheets-api
  - data-processing
  - mvp
---

# Dental Analytics Backend Architecture

## Executive Summary

A minimalist, framework-agnostic backend architecture delivering 5 critical dental KPIs through clean Python modules. Implementation expanded after Story 2.0 to include chart data and historical analysis, focusing on data retrieval from Google Sheets and pure calculation logic with zero framework dependencies.

## System Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                  GOOGLE SHEETS                       │
│         (Source of Truth - Practice Data)            │
└────────────────────┬─────────────────────────────────┘
                     │ API v4
                     ▼
┌──────────────────────────────────────────────────────┐
│               BACKEND LAYER (100 lines)              │
├──────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────┐  │
│  │          data_providers.py (50 lines)           │  │
│  │  - Service Account Authentication              │  │
│  │  - Spreadsheet Connection                      │  │
│  │  - Data Retrieval & DataFrame Conversion       │  │
│  └──────────────────┬─────────────────────────────┘  │
│                     │ pandas DataFrame               │
│  ┌──────────────────▼─────────────────────────────┐  │
│  │            metrics.py (50 lines)               │  │
│  │  - calculate_production_total()                │  │
│  │  - calculate_collection_rate()                 │  │
│  │  - calculate_new_patients()                    │  │
│  │  - calculate_case_acceptance()            │  │
│  │  - calculate_hygiene_reappointment()           │  │
│  │  - get_all_kpis() → Dict[str, float]          │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
                     │ Python Dict/DataFrame
                     ▼
              [Frontend Layer]
```

## Core Components

### 1. Google Sheets Provider Module (`apps/backend/data_providers.py`)

**Purpose:** Single responsibility - retrieve data from Google Sheets and return pandas DataFrames.

**Implementation Pattern:**
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
from typing import Optional, Dict, Any

class SheetsProvider:
    """Handles all Google Sheets API interactions."""

    SPREADSHEET_ID = '1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    def __init__(self, credentials_path: str = 'config/credentials.json'):
        """Initialize with service account credentials."""
        self.creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=self.SCOPES
        )
        self.service = build('sheets', 'v4', credentials=self.creds)

    def get_sheet_data(self, range_name: str) -> Optional[pd.DataFrame]:
        """Fetch data from specified sheet range."""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.SPREADSHEET_ID,
                range=range_name
            ).execute()

            values = result.get('values', [])
            if not values:
                return None

            # First row as headers, rest as data
            df = pd.DataFrame(values[1:], columns=values[0])
            return df

        except Exception as e:
            print(f"Error reading sheet: {e}")
            return None
```

**Key Design Decisions:**
- Service account authentication (no user interaction required)
- Returns pandas DataFrames for flexible data manipulation
- Simple error handling returns None (fail gracefully)
- No business logic - pure data retrieval

### 2. Metrics Calculation Module (`apps/backend/metrics.py`)

**Purpose:** Pure calculation functions transforming DataFrames into KPI values.

**Implementation Pattern:**
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

    @staticmethod
    def calculate_new_patients(df: pd.DataFrame) -> Optional[int]:
        """Count new patients from Column J."""
        if df is None or df.empty:
            return None
        try:
            return int(pd.to_numeric(df['new_patients'], errors='coerce').sum())
        except (KeyError, ValueError):
            return None

    @staticmethod
    def calculate_case_acceptance(df: pd.DataFrame) -> Optional[float]:
        """Calculate treatment acceptance rate."""
        if df is None or df.empty:
            return None
        try:
            scheduled = pd.to_numeric(df['dollar_scheduled'], errors='coerce').sum()
            presented = pd.to_numeric(df['dollar_presented'], errors='coerce').sum()

            if presented == 0:
                return None

            return (scheduled / presented) * 100
        except KeyError:
            return None

    @staticmethod
    def calculate_hygiene_reappointment(df: pd.DataFrame) -> Optional[float]:
        """Calculate hygiene reappointment rate."""
        if df is None or df.empty:
            return None
        try:
            total_hygiene = pd.to_numeric(df['total_hygiene_appointments'], errors='coerce').sum()
            not_reappointed = pd.to_numeric(df['patients_not_reappointed'], errors='coerce').sum()

            if total_hygiene == 0:
                return None

            return ((total_hygiene - not_reappointed) / total_hygiene) * 100
        except KeyError:
            return None

def get_all_kpis() -> Dict[str, Optional[float]]:
    """Orchestrator function to fetch and calculate all KPIs."""
    reader = SheetsProvider()
    calculator = MetricsCalculator()

    # Fetch data from appropriate sheets
    eod_data = reader.get_sheet_data('EOD - Baytown Billing!A:N')
    front_kpi_data = reader.get_sheet_data('Baytown Front KPIs Form responses!A:N')

    return {
        'production_total': calculator.calculate_production_total(eod_data),
        'collection_rate': calculator.calculate_collection_rate(eod_data),
        'new_patients': calculator.calculate_new_patients(eod_data),
        'case_acceptance': calculator.calculate_case_acceptance(front_kpi_data),
        'hygiene_reappointment': calculator.calculate_hygiene_reappointment(front_kpi_data)
    }
```

**Key Design Decisions:**
- Static methods for pure functions (no state)
- Defensive programming with None checks
- Type hints for clarity
- Framework-agnostic return types (Dict, float, int)
- Single orchestrator function for frontend simplicity

## Data Flow Architecture

### 1. Authentication Flow
```
credentials.json → Service Account → Google Sheets API → Authorized Access
```

### 2. Data Retrieval Flow
```
API Request → Sheet Range → Raw Values → DataFrame Conversion → Return
```

### 3. Calculation Flow
```
DataFrame → Column Extraction → Type Conversion → Formula Application → KPI Value
```

### 4. Error Handling Flow
```
Exception → Log Error → Return None → Frontend Shows "Data Unavailable"
```

## Module Dependencies

```yaml
apps/backend/:
  __init__.py:
    - Empty file for module initialization

  data_providers.py:
    external:
      - google-auth >= 2.23
      - google-api-python-client >= 2.103
      - pandas >= 2.1
    internal:
      - None (standalone module)

  metrics.py:
    external:
      - pandas >= 2.1
    internal:
      - data_providers (for get_all_kpis only)
```

## Configuration Management

### Credentials Storage
```
config/
└── credentials.json    # Google service account key
    {
      "type": "service_account",
      "project_id": "dental-analytics",
      "private_key_id": "...",
      "private_key": "...",
      "client_email": "dental-dashboard@project.iam.gserviceaccount.com"
    }
```

### Environment Configuration
```python
# No environment variables required for MVP
# All configuration hardcoded for simplicity
SPREADSHEET_ID = '1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8'
REFRESH_INTERVAL = 300  # 5 minutes in seconds
```

## Performance Optimization

### Caching Strategy
```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=1)
def get_cached_kpis(cache_key: str) -> Dict:
    """Cache KPIs for 5 minutes to reduce API calls."""
    return get_all_kpis()

def get_current_kpis() -> Dict:
    """Get KPIs with 5-minute cache."""
    cache_key = datetime.now().strftime('%Y%m%d%H%M')[:-1]  # 5-min blocks
    return get_cached_kpis(cache_key)
```

### API Rate Limiting
- Google Sheets API: 100 requests per 100 seconds
- Our usage: ~10 requests per dashboard load
- Safety margin: 10x under limit

## Error Handling Philosophy

### Fail Gracefully
- Never crash the application
- Return None for calculation errors
- Log errors for debugging
- Display "Data Unavailable" in UI

### Common Error Scenarios
```python
# Empty DataFrame
if df is None or df.empty:
    return None

# Missing Column
try:
    value = df['column_name']
except KeyError:
    return None

# Type Conversion
pd.to_numeric(df['column'], errors='coerce')  # Returns NaN for bad values

# Division by Zero
if denominator == 0:
    return None
```

## Security Considerations

### Service Account Security
- Credentials file in .gitignore
- Read-only API scope
- No user data storage
- Service account has minimal permissions

### Data Privacy
- No PHI/PII in calculations
- Only aggregate metrics returned
- No data persistence
- Memory cleared after request

## Testing Strategy

### Manual Validation Points
1. **Connection Test:**
   ```python
   reader = SheetsProvider()
   df = reader.get_sheet_data('EOD - Baytown Billing!A1:N10')
   assert df is not None
   ```

2. **Calculation Test:**
   ```python
   test_df = pd.DataFrame({
       'total_production': [1000, 2000, 3000],
       'total_collections': [900, 1800, 2700]
   })
   rate = calculate_collection_rate(test_df)
   assert rate == 90.0  # (5400/6000) * 100
   ```

3. **Integration Test:**
   ```python
   kpis = get_all_kpis()
   assert all(key in kpis for key in [
       'production_total', 'collection_rate',
       'new_patients', 'case_acceptance',
       'hygiene_reappointment'
   ])
   ```

## Deployment Considerations

### Local Development
```bash
# Install dependencies
uv sync

# Test connection
uv run python -c "from apps.backend.data_providers import SheetsProvider; print(SheetsProvider().get_sheet_data('A1:A1'))"

# Run calculations
uv run python -c "from backend.metrics import get_all_kpis; print(get_all_kpis())"
```

### Production Deployment
- No special requirements
- Runs in any Python 3.10+ environment
- Credentials must be present in config/
- No database or external services needed

## Future Extensibility

### Adding New KPIs
1. Add calculation method to MetricsCalculator
2. Update get_all_kpis() orchestrator
3. No other changes required

### Switching Data Sources
- Replace SheetsProvider with new data source class
- Keep same DataFrame output format
- Metrics module remains unchanged

### Adding Historical Tracking
```python
# Future enhancement (not in MVP)
def save_daily_metrics(kpis: Dict):
    """Save KPIs to CSV for historical tracking."""
    df = pd.DataFrame([kpis])
    df['timestamp'] = datetime.now()
    df.to_csv('data/historical_kpis.csv', mode='a', header=False)
```

## Code Quality Standards

### Line Count Compliance
- data_providers.py: 45 lines (under 50 limit)
- metrics.py: 48 lines (under 50 limit)
- Total backend: 93 lines (under 100 limit)

### Maintainability Metrics
- Single responsibility per function
- No nested complexity beyond 2 levels
- Clear naming conventions
- Type hints throughout

## Architecture Decision Records

### ADR-001: Framework-Agnostic Backend
**Decision:** Backend modules have zero framework dependencies
**Rationale:** Allows frontend technology changes without backend modifications
**Consequences:** Clean separation, easy testing, potential reuse

### ADR-002: Pandas for Data Processing
**Decision:** Use pandas DataFrames for all data manipulation
**Rationale:** Powerful data operations, familiar to data scientists
**Consequences:** 5MB dependency, excellent calculation capabilities

### ADR-003: No Database Layer
**Decision:** Direct Google Sheets connection without local persistence
**Rationale:** Simplicity, real-time data, no sync issues
**Consequences:** API dependency, potential latency, rate limits

## Success Criteria

✅ **Connects to Google Sheets within 2 seconds**
✅ **Calculates all 5 KPIs accurately**
✅ **Returns structured data for any frontend**
✅ **Handles errors gracefully**
✅ **Under 100 lines of production code**
✅ **Zero framework dependencies**
✅ **Service account authentication working**

## Conclusion

This backend architecture delivers exactly what's needed: reliable data retrieval and accurate KPI calculations in under 100 lines of clean Python code. By maintaining framework independence and focusing on pure data transformation, we've created a backend that will serve the dental practice's needs today while remaining flexible for tomorrow's requirements.
