"""Pydantic models for application configuration structures.

This module provides strongly-typed, validated models for configuration data
including Google Sheets connections, location settings, and application config.
All models include runtime validation and are framework-independent.

Created: 2025-10-02
Phase: 1 - TypedDict Elimination
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SheetsConfig(BaseModel):
    """Configuration for a single Google Sheets data source.

    Replaces: SheetConfig (TypedDict in apps/backend/types.py)

    Defines the spreadsheet ID and range specification for retrieving
    data from Google Sheets API.

    Attributes
    ----------
    spreadsheet_id:
        Google Sheets spreadsheet ID (from URL).
    range_name:
        Sheet name and cell range (e.g., "EOD - Baytown Billing!A:N").
    sheet_name:
        Optional human-readable sheet identifier for logging/debugging.
    """

    spreadsheet_id: str = Field(
        ..., min_length=1, description="Google Sheets spreadsheet ID"
    )
    range_name: str = Field(
        ..., min_length=1, description="Sheet name and range specification"
    )
    sheet_name: str | None = Field(
        default=None, description="Human-readable sheet identifier"
    )


class LocationSettings(BaseModel):
    """Configuration for a practice location's data sources.

    Replaces: LocationConfig (TypedDict in apps/backend/types.py)

    Maps a practice location (Baytown/Humble) to its EOD billing sheet
    and Front KPI sheet configurations, with optional business day rules.

    Attributes
    ----------
    eod_sheet:
        Configuration for End of Day billing data sheet.
    front_sheet:
        Configuration for Front KPI form responses sheet.
    business_days:
        List of operating weekdays (1=Monday through 7=Sunday).
        Default: [1,2,3,4,5,6] (Monday-Saturday).
    """

    eod_sheet: SheetsConfig = Field(..., description="EOD billing sheet config")
    front_sheet: SheetsConfig = Field(..., description="Front KPI sheet config")
    business_days: list[int] = Field(
        default=[1, 2, 3, 4, 5, 6],
        description="Operating weekdays (1=Mon, 7=Sun)",
    )

    @field_validator("business_days")
    @classmethod
    def validate_business_days(cls, v: list[int]) -> list[int]:
        """Ensure business days are valid weekday integers (1-7)."""
        if not all(1 <= day <= 7 for day in v):
            raise ValueError(
                "Business days must be integers between 1 (Mon) and 7 (Sun)"
            )
        return v


class DataProviderConfig(BaseModel):
    """Google Sheets API data provider configuration.

    Replaces: ProviderConfig (TypedDict in apps/backend/types.py)

    Stores configuration for all practice locations, API credentials,
    and optional caching settings.

    Attributes
    ----------
    locations:
        Dictionary mapping location names to their settings.
        Keys: "baytown", "humble"
        Values: LocationSettings with sheet configs
    credentials_path:
        Path to Google service account credentials JSON file.
    scopes:
        List of Google API OAuth scopes required for access.
    cache_ttl:
        Optional cache time-to-live in seconds (default: 300).
        Must be >= 0.
    """

    locations: dict[str, LocationSettings] = Field(
        default_factory=dict, description="Location-specific sheet configurations"
    )
    credentials_path: str = Field(
        default="config/credentials.json",
        description="Service account credentials path",
    )
    scopes: list[str] = Field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        ],
        description="Google API OAuth scopes",
    )
    cache_ttl: int = Field(
        default=300, ge=0, description="Cache time-to-live in seconds"
    )


class AppConfig(BaseModel):
    """Complete application configuration structure.

    Replaces: ConfigData (TypedDict in apps/backend/types.py)

    Top-level configuration model loaded from YAML that aggregates
    all provider settings, location configs, and application preferences.

    Attributes
    ----------
    data_provider:
        Google Sheets data provider configuration with all locations.
    logging_level:
        Application logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    debug_mode:
        Enable debug features and verbose logging.
    """

    data_provider: DataProviderConfig = Field(
        default_factory=DataProviderConfig, description="Data provider configuration"
    )
    logging_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Application logging level"
    )
    debug_mode: bool = Field(default=False, description="Debug mode flag")
