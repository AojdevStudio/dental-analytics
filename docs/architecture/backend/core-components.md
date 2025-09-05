# Core Components

## 1. Google Sheets Reader Module (`backend/sheets_reader.py`)

**Purpose:** Single responsibility - retrieve data from Google Sheets and return pandas DataFrames.

**Implementation Pattern:**
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
from typing import Optional, Dict, Any

class SheetsReader:
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

## 2. Metrics Calculation Module (`backend/metrics.py`)

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
    def calculate_treatment_acceptance(df: pd.DataFrame) -> Optional[float]:
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
    reader = SheetsReader()
    calculator = MetricsCalculator()

    # Fetch data from appropriate sheets
    eod_data = reader.get_sheet_data('EOD - Baytown Billing!A:N')
    front_kpi_data = reader.get_sheet_data('Front KPI - Baytown!A:N')

    return {
        'production_total': calculator.calculate_production_total(eod_data),
        'collection_rate': calculator.calculate_collection_rate(eod_data),
        'new_patients': calculator.calculate_new_patients(eod_data),
        'treatment_acceptance': calculator.calculate_treatment_acceptance(front_kpi_data),
        'hygiene_reappointment': calculator.calculate_hygiene_reappointment(front_kpi_data)
    }
```

**Key Design Decisions:**
- Static methods for pure functions (no state)
- Defensive programming with None checks
- Type hints for clarity
- Framework-agnostic return types (Dict, float, int)
- Single orchestrator function for frontend simplicity
