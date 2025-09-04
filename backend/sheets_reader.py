# Google Sheets API reader for dental analytics dashboard
import logging
from typing import Optional
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logger = logging.getLogger(__name__)

class SheetsReader:
    """Handles all Google Sheets API interactions."""
    
    SPREADSHEET_ID = '1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    def __init__(self, credentials_path: str = 'config/credentials.json'):
        """Initialize with service account credentials."""
        try:
            self.creds = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=self.SCOPES
            )
            self.service = build('sheets', 'v4', credentials=self.creds)
            logger.info("SheetsReader initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SheetsReader: {e}")
            self.service = None
    
    def get_sheet_data(self, range_name: str) -> Optional[pd.DataFrame]:
        """Fetch data from specified sheet range.
        
        Args:
            range_name: Sheet range in A1 notation (e.g. 'Sheet1' or 'Sheet1!A1:Z100')
            
        Returns:
            DataFrame with sheet data, or None if error occurs
        """
        if not self.service:
            logger.error("Service not initialized")
            return None
        
        if not range_name or not range_name.strip():
            logger.error("Invalid range_name: cannot be empty")
            return None
            
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.SPREADSHEET_ID,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                logger.warning(f"No data found in range: {range_name}")
                return None
            
            if len(values) == 1:
                logger.warning(f"Only headers found, no data rows in range: {range_name}")
                return pd.DataFrame(columns=values[0])
            
            # Convert to DataFrame with first row as headers
            df = pd.DataFrame(values[1:], columns=values[0])
            logger.info(f"Retrieved {len(df)} rows from {range_name}")
            return df
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to read sheet data: {e}")
            return None