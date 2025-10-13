"""Data provider implementations for dental analytics.

Provides abstracted data access through configurable providers.
Supports Google Sheets with alias-based configuration and prepares
interface for future SQLite provider integration.
"""

import logging
from pathlib import Path
from typing import Any, Protocol, cast

import pandas as pd
import yaml
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.models.config_models import (
    AppConfig,
    DataProviderConfig,
    LocationSettings,
    SheetsConfig,
)

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

    def _load_config(self, config_path: Path | str | None) -> DataProviderConfig:
        """Load and validate sheets configuration into Pydantic models."""
        if config_path is None:
            config_path = "config/sheets.yml"

        config_file = Path(config_path)
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with config_file.open() as f:
                # YAML ingestion - OK to use dict[str, Any] for external source
                raw_config: dict[str, Any] = yaml.safe_load(f)

            # Build Pydantic models from YAML structure
            locations: dict[str, LocationSettings] = {}

            for loc_name, loc_data in raw_config.get("locations", {}).items():
                # Each location has eod and front sheet references
                eod_alias = loc_data.get("eod")
                front_alias = loc_data.get("front")

                # Get sheet configs from sheets section
                sheets_section = raw_config.get("sheets", {})
                eod_sheet_data = sheets_section.get(eod_alias, {})
                front_sheet_data = sheets_section.get(front_alias, {})

                locations[loc_name] = LocationSettings(
                    eod_sheet=SheetsConfig(
                        spreadsheet_id=eod_sheet_data.get("spreadsheet_id", ""),
                        range_name=eod_sheet_data.get("range", ""),
                        sheet_name=eod_alias,
                    ),
                    front_sheet=SheetsConfig(
                        spreadsheet_id=front_sheet_data.get("spreadsheet_id", ""),
                        range_name=front_sheet_data.get("range", ""),
                        sheet_name=front_alias,
                    ),
                )

            provider_section = raw_config.get("provider_config", {})
            config = DataProviderConfig(
                locations=locations,
                credentials_path=provider_section.get(
                    "credentials_path", "config/credentials.json"
                ),
                scopes=provider_section.get(
                    "scopes",
                    ["https://www.googleapis.com/auth/spreadsheets.readonly"],
                ),
            )

            logger.info(
                f"Loaded Pydantic configuration with {len(locations)} locations"
            )
            return config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML configuration: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to parse configuration: {e}") from e

    def _init_google_service(self) -> Any:
        """Initialize Google Sheets API service."""
        # Access Pydantic model attributes directly
        credentials_path = self.config.credentials_path
        scopes = self.config.scopes

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
        """Validate all location configurations are properly set up."""
        # Pydantic models are self-validating at instantiation
        # This method now just logs successful configuration
        location_count = len(self.config.locations)
        logger.info(
            f"Configuration validation passed for {location_count} locations "
            f"(Pydantic models validated at construction)"
        )

    def fetch(self, alias: str) -> pd.DataFrame | None:
        """Fetch data by alias (location_datatype format).

        Args:
            alias: Sheet alias (e.g., 'baytown_eod', 'humble_front')
                   Format: {location}_{datatype}

        Returns:
            DataFrame with sheet data or None if fetch fails
        """
        # Parse alias into location and data type
        parts = alias.split("_")
        if len(parts) != 2:
            logger.error(f"Invalid alias format: {alias}. Expected 'location_datatype'")
            return None

        location, data_type = parts[0], parts[1]

        if location not in self.config.locations:
            logger.error(f"Unknown location: {location}")
            return None

        location_config = self.config.locations[location]

        # Get appropriate sheet config based on data type
        if data_type == "eod":
            sheet_config = location_config.eod_sheet
        elif data_type == "front":
            sheet_config = location_config.front_sheet
        else:
            logger.error(f"Unknown data type: {data_type}")
            return None

        try:
            result = (
                self.service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=sheet_config.spreadsheet_id,
                    range=sheet_config.range_name,
                )
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
        """Get list of available sheet aliases in location_datatype format."""
        aliases = []
        for location in self.config.locations:
            aliases.append(f"{location}_eod")
            aliases.append(f"{location}_front")
        return aliases

    def validate_alias(self, alias: str) -> bool:
        """Check if alias exists in configuration (location_datatype format)."""
        parts = alias.split("_")
        if len(parts) != 2:
            return False

        location, data_type = parts[0], parts[1]
        return location in self.config.locations and data_type in ["eod", "front"]

    def get_location_aliases(self, location: str, data_type: str) -> str | None:
        """Get alias for location and data type combination.

        Args:
            location: Location name ('baytown' or 'humble')
            data_type: Data type ('eod' or 'front')

        Returns:
            Alias string (location_datatype format) or None if not found
        """
        if location.lower() not in self.config.locations:
            logger.warning(f"Location not configured: {location}")
            return None

        if data_type not in ["eod", "front"]:
            logger.warning(f"Invalid data type: {data_type}")
            return None

        return f"{location.lower()}_{data_type}"

    def get_location_info(self, location: str) -> LocationSettings | None:
        """Get location configuration details.

        Args:
            location: Location name

        Returns:
            LocationSettings Pydantic model or None if not found
        """
        return self.config.locations.get(location.lower())

    def get_spreadsheet_info(self, alias: str) -> SheetsConfig | None:
        """Get spreadsheet details for an alias.

        Args:
            alias: Sheet alias (location_datatype format)

        Returns:
            SheetsConfig Pydantic model or None if not found
        """
        if not self.validate_alias(alias):
            return None

        parts = alias.split("_")
        location, data_type = parts[0], parts[1]

        location_config = self.config.locations.get(location)
        if not location_config:
            return None

        if data_type == "eod":
            return location_config.eod_sheet
        elif data_type == "front":
            return location_config.front_sheet
        else:
            return None


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
