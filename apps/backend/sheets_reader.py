import logging
from pathlib import Path
from typing import Any

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SPREADSHEET_ID = "1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class SheetsReader:
    """Google Sheets API interface for dental analytics."""

    def __init__(self, credentials_path: str = "config/credentials.json"):
        """Initialize with service account credentials."""
        self.service = self._init_service(credentials_path)

    def _init_service(self, credentials_path: str) -> Any | None:
        """Initialize Google Sheets service."""
        if not Path(credentials_path).exists():
            logger.error(f"Credentials file not found: {credentials_path}")
            return None
        try:
            creds = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=SCOPES
            )
            return build("sheets", "v4", credentials=creds)
        except Exception as e:
            logger.error(f"Failed to initialize service: {e}")
            return None

    def get_sheet_data(self, range_name: str) -> pd.DataFrame | None:
        """Fetch data from Google Sheets and return as DataFrame."""
        if not self.service:
            logger.error("Sheets service not initialized")
            return None

        try:
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=SPREADSHEET_ID, range=range_name)
                .execute()
            )

            values = result.get("values", [])
            if not values:
                logger.warning(f"No data found in range: {range_name}")
                return None

            # Convert to DataFrame using first row as headers
            if len(values) > 1:
                df = pd.DataFrame(values[1:], columns=values[0])
                logger.info(f"Retrieved {len(df)} rows from {range_name}")
                return df
            else:
                logger.warning(f"Only headers found in {range_name}")
                return None

        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading {range_name}: {e}")
            return None

    def get_eod_data(self) -> pd.DataFrame | None:
        """Get EOD (End of Day) billing data from Baytown sheet."""
        range_name = "EOD - Baytown Billing!A:N"
        return self.get_sheet_data(range_name)

    def get_front_kpi_data(self) -> pd.DataFrame | None:
        """Get Front KPI data from Baytown sheet."""
        range_name = "Front KPI - Baytown!A:N"
        return self.get_sheet_data(range_name)
