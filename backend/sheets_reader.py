import logging
from pathlib import Path

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

    def _init_service(self, credentials_path: str):
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

    def is_connected(self) -> bool:
        """Test Google Sheets connection."""
        return self.service is not None

    def get_sheet_data(self, range_name: str) -> pd.DataFrame | None:
        """Fetch data from sheet range."""
        if not self.service or not range_name.strip():
            return None
        try:
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=SPREADSHEET_ID, range=range_name)
                .execute()
            )
            values = result.get("values", [])
            if len(values) <= 1:
                return pd.DataFrame(columns=values[0] if values else [])
            return pd.DataFrame(values[1:], columns=values[0])
        except (HttpError, Exception) as e:
            logger.error(f"Sheet read error: {e}")
            return None
