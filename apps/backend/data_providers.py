"""Multi-location data provider with enhanced configuration support."""

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
    """Raised when configuration is invalid or missing."""

    pass


class DataProvider(Protocol):
    """Protocol defining the interface for data providers."""

    def fetch(self, alias: str) -> pd.DataFrame | None:
        """Fetch data by alias."""
        ...

    def list_available_aliases(self) -> list[str]:
        """Get list of available aliases."""
        ...

    def validate_alias(self, alias: str) -> bool:
        """Check if alias is valid."""
        ...


class SheetsProvider:
    """Legacy alias for MultiLocationDataProvider.

    Maintained for backward compatibility during transition.
    """

    def __init__(self, config_path: str = "config/sheets.yml") -> None:
        """Initialize with legacy interface."""
        self._provider = MultiLocationDataProvider(config_path)

    def fetch(self, alias: str) -> pd.DataFrame | None:
        """Fetch data by alias."""
        return self._provider.fetch(alias)

    def list_available_aliases(self) -> list[str]:
        """Get list of available aliases."""
        return self._provider.list_available_aliases()

    def validate_alias(self, alias: str) -> bool:
        """Check if alias is valid."""
        return self._provider.validate_alias(alias)

    def get_location_aliases(self, location: str, data_type: str) -> str | None:
        """Get alias for location and data type combination."""
        return self._provider.get_location_aliases(location, data_type)


class MultiLocationDataProvider:
    """Enhanced data provider supporting multiple locations via configuration.

    Provides unified interface for fetching data from multiple Google Sheets
    across different dental office locations using alias-based configuration.

    Features:
    - Configuration-driven sheet mapping
    - Alias-based data access (e.g., 'baytown_eod', 'humble_front')
    - Robust error handling and logging
    - Location-aware data routing
    """

    def __init__(self, config_path: str = "config/sheets.yml") -> None:
        """Initialize provider with configuration file.

        Args:
            config_path: Path to YAML configuration file

        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.config_path = Path(config_path)
        self.config = self._load_configuration()
        self.service = self._init_google_service()
        self._validate_configuration()

        alias_count = len(self.config["sheets"])
        logger.info(f"MultiLocationDataProvider initialized with {alias_count} aliases")

    def _load_configuration(self) -> dict[str, Any]:
        """Load and validate YAML configuration.

        Returns:
            Loaded configuration dictionary

        Raises:
            ConfigurationError: If file missing or invalid
        """
        if not self.config_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {self.config_path}"
            )

        try:
            with self.config_path.open() as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                raise ConfigurationError("Configuration must be a dictionary")

            # Validate required top-level sections
            required_sections = ["sheets", "locations", "provider_config"]
            for section in required_sections:
                if section not in config:
                    raise ConfigurationError(f"Missing required section: {section}")

            logger.info(
                f"Loaded configuration with {len(config['sheets'])} sheet aliases"
            )
            return config

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
        # Build expected alias pattern
        expected_alias = f"{location}_{data_type}"

        if self.validate_alias(expected_alias):
            return expected_alias

        logger.warning(
            f"No alias found for location '{location}' and data type '{data_type}'"
        )
        return None

    def get_location_info(self, location: str) -> dict[str, Any] | None:
        """Get location configuration details.

        Args:
            location: Location name

        Returns:
            Location configuration or None if not found
        """
        locations_config: dict[str, Any] = self.config.get("locations", {})
        location_info = locations_config.get(location)
        return location_info if location_info is not None else None

    def get_spreadsheet_info(self, alias: str) -> dict[str, str] | None:
        """Get spreadsheet details for an alias.

        Args:
            alias: Sheet alias

        Returns:
            Dictionary with spreadsheet_id and range, or None if not found
        """
        if not self.validate_alias(alias):
            return None

        sheet_config = self.config["sheets"][alias]
        return {
            "spreadsheet_id": sheet_config["spreadsheet_id"],
            "range": sheet_config["range"],
        }


def build_sheets_provider(config_path: Path | str | None = None) -> SheetsProvider:
    """Build a configured SheetsProvider instance.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Configured SheetsProvider instance
    """
    if config_path is None:
        config_path = "config/sheets.yml"

    return SheetsProvider(str(config_path))
