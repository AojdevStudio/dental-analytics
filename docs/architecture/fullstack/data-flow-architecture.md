# Data Flow Architecture

## Request Lifecycle

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant Streamlit
    participant Metrics
    participant SheetsReader
    participant GoogleAPI

    User->>Browser: Open Dashboard
    Browser->>Streamlit: HTTP Request
    Streamlit->>Metrics: get_all_kpis()
    Metrics->>SheetsReader: get_sheet_data("EOD")
    SheetsReader->>GoogleAPI: Authenticate & Fetch
    GoogleAPI-->>SheetsReader: Raw Data
    SheetsReader-->>Metrics: DataFrame
    Metrics->>SheetsReader: get_sheet_data("Front KPI")
    SheetsReader->>GoogleAPI: Fetch
    GoogleAPI-->>SheetsReader: Raw Data
    SheetsReader-->>Metrics: DataFrame
    Metrics-->>Streamlit: KPI Dictionary
    Streamlit-->>Browser: Rendered HTML
    Browser-->>User: Display Dashboard
```

## Data Transformation Pipeline

```
Google Sheets → API Response → JSON → DataFrame → Calculations → Dict → UI Components
```

**Stage 1: Data Retrieval**
- Google Sheets API returns nested arrays
- Convert to pandas DataFrame with headers

**Stage 2: Data Processing**
- Type conversion (strings to numbers)
- Null handling (coerce errors)
- Aggregation (sum, count)

**Stage 3: KPI Calculation**
- Apply business formulas
- Handle edge cases (division by zero)
- Return typed results

**Stage 4: UI Rendering**
- Format numbers (currency, percentage)
- Apply conditional styling
- Display in metric cards
