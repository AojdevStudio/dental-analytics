"""Data provider implementations for dental analytics.

Provides abstracted data access through configurable providers.
Supports Google Sheets with alias-based configuration and prepares
interface for future SQLite provider integration.
"""

import logging
from pathlib import Path
from typing import Any, Protocol

import pandas as pd
import yaml
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when provider configuration is invalid."""

    pass


class DataProvider(Protocol):
    """Protocol for data access providers."""

    def fetch(self, alias: str) -> pd.DataFrame | None:
        """Fetch data by alias.

        Args:
            alias: Data source alias (e.g., 'baytown_eod', 'humble_front')

        Returns:
            DataFrame with data or None if fetch fails
        """
        ...

    def list_available_aliases(self) -> list[str]:
        """Get list of available data aliases."""
        ...

    def validate_alias(self, alias: str) -> bool:
        """Check if alias is valid and accessible."""
        ...

    def get_location_aliases(self, location: str, data_type: str) -> str | None:
        """Resolve a location/data_type to an alias."""
        ...


class SheetsProvider:
    """Google Sheets data provider with alias-based configuration.

    Replaces legacy SheetsReader with configurable multi-sheet support.
    Uses aliases to map logical data sources to specific spreadsheet
    IDs and ranges, enabling clean separation of concerns.
    """

    def __init__(self, config_path: Path | str | None = None):
        """Initialize provider with configuration.

        Args:
            config_path: Path to sheets configuration YAML file

        Raises:
            ConfigurationError: If config is invalid or missing
        """
        self.config = self._load_config(config_path)
        self.service = self._init_google_service()

        # Validate all aliases on startup
        self._validate_configuration()

    def _load_config(self, config_path: Path | str | None) -> dict[str, Any]:
        """Load and validate sheets configuration."""
        if config_path is None:
            config_path = "config/sheets.yml"

        config_file = Path(config_path)
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            config = yaml.safe_load(config_file.read_text())

            if not isinstance(config, dict):
                raise ConfigurationError(
                    "Invalid YAML configuration: expected a mapping at document root"
                )

            # Validate required sections
            required_sections = ["sheets", "locations", "provider_config"]
            for section in required_sections:
                if section not in config:
                    raise ConfigurationError(f"Missing required section: {section}")

            logger.info(
                f"Loaded configuration with {len(config['sheets'])} sheet aliases"
            )
            return config  # type: ignore[no-any-return]

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML configuration: {e}") from e

    def _init_google_service(self) -> Any:
        """Initialize Google Sheets API service."""
        provider_config = self.config["provider_config"]
        credentials_path = provider_config["credentials_path"]
        scopes = provider_config["scopes"]

        if not Path(credentials_path).exists():
            raise ConfigurationError(f"Credentials file not found: {credentials_path}")

        try:
            creds = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=scopes
            )
            service = build("sheets", "v4", credentials=creds)
            logger.info("Google Sheets service initialized successfully")
            return service

        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Google service: {e}") from e

    def _validate_configuration(self) -> None:
        """Validate all sheet aliases are properly configured."""
        sheets_config = self.config["sheets"]

        for alias, sheet_config in sheets_config.items():
            required_fields = ["spreadsheet_id", "range"]
            for field in required_fields:
                if field not in sheet_config:
                    raise ConfigurationError(
                        f"Sheet alias '{alias}' missing required field: {field}"
                    )

        logger.info(f"Configuration validation passed for {len(sheets_config)} aliases")

    def fetch(self, alias: str) -> pd.DataFrame | None:
        """Fetch data by alias.

        Args:
            alias: Sheet alias (e.g., 'baytown_eod', 'humble_front')

        Returns:
            DataFrame with sheet data or None if fetch fails
        """
        if not self.validate_alias(alias):
            logger.error(f"Invalid alias: {alias}")
            return None

        sheet_config = self.config["sheets"][alias]
        spreadsheet_id = sheet_config["spreadsheet_id"]
        range_name = sheet_config["range"]

        try:
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )

            values = result.get("values", [])
            if not values:
                logger.warning(f"No data found for alias: {alias}")
                return None

            # Convert to DataFrame using first row as headers
            if len(values) > 1:
                df = pd.DataFrame(values[1:], columns=values[0])
                logger.info(f"Retrieved {len(df)} rows for alias: {alias}")
                return df
            else:
                logger.warning(f"Only headers found for alias: {alias}")
                return None

        except HttpError as e:
            logger.error(f"Google Sheets API error for alias {alias}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching alias {alias}: {e}")
            return None

    def list_available_aliases(self) -> list[str]:
        """Get list of available sheet aliases."""
        return list(self.config["sheets"].keys())

    def validate_alias(self, alias: str) -> bool:
        """Check if alias exists in configuration."""
        return alias in self.config["sheets"]

    def get_location_aliases(self, location: str, data_type: str) -> str | None:
        """Get alias for location and data type combination.

        Args:
            location: Location name ('baytown' or 'humble')
            data_type: Data type ('eod' or 'front')

        Returns:
            Alias string or None if not found
        """
        locations_config = self.config.get("locations", {})
        location_config = locations_config.get(location.lower())

        if not location_config:
            logger.warning(f"Location not configured: {location}")
            return None

        alias = location_config.get(data_type)
        if not alias:
            logger.warning(
                f"Data type '{data_type}' not configured for location '{location}'"
            )
            return None

        return alias  # type: ignore[no-any-return]


def build_sheets_provider(config_path: Path | str | None = None) -> SheetsProvider:
    """Factory function to create and configure SheetsProvider.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Configured SheetsProvider instance

    Raises:
        ConfigurationError: If provider cannot be initialized
    """
    try:
        provider = SheetsProvider(config_path)
        logger.info("SheetsProvider factory initialization successful")
        return provider
    except Exception as e:
        logger.error(f"Failed to build SheetsProvider: {e}")
        raise
