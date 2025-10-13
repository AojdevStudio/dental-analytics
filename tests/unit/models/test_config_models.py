"""Unit tests for config_models.py Pydantic models.

Tests cover:
- Valid model instantiation
- Field validation rules
- Nested model composition
- Default values
- Error scenarios (invalid values, constraint violations)

Target: 95%+ test coverage
"""

import pytest
from pydantic import ValidationError

from core.models.config_models import (
    AppConfig,
    DataProviderConfig,
    LocationSettings,
    SheetsConfig,
)


class TestSheetsConfig:
    """Test suite for SheetsConfig model."""

    def test_valid_sheets_config(self) -> None:
        """Test creating valid sheets configuration."""
        config = SheetsConfig(
            spreadsheet_id="1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8",
            range_name="EOD - Baytown Billing!A:N",
        )
        assert config.spreadsheet_id == "1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8"
        assert config.range_name == "EOD - Baytown Billing!A:N"

    def test_empty_spreadsheet_id_rejected(self) -> None:
        """Test that empty spreadsheet_id raises ValidationError."""
        with pytest.raises(ValidationError):
            SheetsConfig(spreadsheet_id="", range_name="Sheet1!A:Z")

    def test_empty_range_name_rejected(self) -> None:
        """Test that empty range_name raises ValidationError."""
        with pytest.raises(ValidationError):
            SheetsConfig(
                spreadsheet_id="1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8",
                range_name="",
            )

    def test_optional_sheet_name_field(self) -> None:
        """Test that sheet_name is optional and defaults to None."""
        config = SheetsConfig(
            spreadsheet_id="1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8",
            range_name="Sheet1!A:Z",
        )
        assert config.sheet_name is None

    def test_sheet_name_provided(self) -> None:
        """Test sheets config with optional sheet_name provided."""
        config = SheetsConfig(
            spreadsheet_id="1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8",
            range_name="EOD!A:N",
            sheet_name="Baytown EOD Billing",
        )
        assert config.sheet_name == "Baytown EOD Billing"


class TestLocationSettings:
    """Test suite for LocationSettings model."""

    def test_valid_location_settings(self) -> None:
        """Test creating valid location settings with nested SheetsConfig."""
        eod_config = SheetsConfig(
            spreadsheet_id="1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8",
            range_name="EOD - Baytown Billing!A:N",
        )
        front_config = SheetsConfig(
            spreadsheet_id="1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8",
            range_name="Baytown Front KPIs!A:Z",
        )
        settings = LocationSettings(eod_sheet=eod_config, front_sheet=front_config)
        assert settings.eod_sheet.range_name == "EOD - Baytown Billing!A:N"
        assert settings.front_sheet.range_name == "Baytown Front KPIs!A:Z"

    def test_default_business_days(self) -> None:
        """Test that business_days defaults to Monday-Saturday [1-6]."""
        eod_config = SheetsConfig(spreadsheet_id="test_id", range_name="EOD!A:N")
        front_config = SheetsConfig(spreadsheet_id="test_id", range_name="Front!A:Z")
        settings = LocationSettings(eod_sheet=eod_config, front_sheet=front_config)
        assert settings.business_days == [1, 2, 3, 4, 5, 6]

    def test_custom_business_days(self) -> None:
        """Test location settings with custom business days."""
        eod_config = SheetsConfig(spreadsheet_id="test_id", range_name="EOD!A:N")
        front_config = SheetsConfig(spreadsheet_id="test_id", range_name="Front!A:Z")
        settings = LocationSettings(
            eod_sheet=eod_config,
            front_sheet=front_config,
            business_days=[1, 2, 3, 4, 5],  # Monday-Friday only
        )
        assert settings.business_days == [1, 2, 3, 4, 5]

    def test_invalid_business_day_rejected(self) -> None:
        """Test that business_days outside 1-7 range are rejected."""
        eod_config = SheetsConfig(spreadsheet_id="test_id", range_name="EOD!A:N")
        front_config = SheetsConfig(spreadsheet_id="test_id", range_name="Front!A:Z")
        with pytest.raises(ValidationError, match="between 1.*and 7"):
            LocationSettings(
                eod_sheet=eod_config,
                front_sheet=front_config,
                business_days=[1, 2, 3, 8],  # 8 is invalid
            )

    def test_sunday_as_business_day(self) -> None:
        """Test that Sunday (7) is valid business day."""
        eod_config = SheetsConfig(spreadsheet_id="test_id", range_name="EOD!A:N")
        front_config = SheetsConfig(spreadsheet_id="test_id", range_name="Front!A:Z")
        settings = LocationSettings(
            eod_sheet=eod_config,
            front_sheet=front_config,
            business_days=[1, 2, 3, 4, 5, 6, 7],  # All days including Sunday
        )
        assert 7 in settings.business_days


class TestDataProviderConfig:
    """Test suite for DataProviderConfig model."""

    def test_valid_data_provider_config(self) -> None:
        """Test creating valid data provider configuration."""
        eod_config = SheetsConfig(spreadsheet_id="test_id", range_name="EOD!A:N")
        front_config = SheetsConfig(spreadsheet_id="test_id", range_name="Front!A:Z")
        baytown_settings = LocationSettings(
            eod_sheet=eod_config, front_sheet=front_config
        )

        config = DataProviderConfig(
            locations={"baytown": baytown_settings},
            credentials_path="config/credentials.json",
        )
        assert "baytown" in config.locations
        assert config.credentials_path == "config/credentials.json"

    def test_default_locations_empty_dict(self) -> None:
        """Test that locations defaults to empty dict."""
        config = DataProviderConfig()
        assert config.locations == {}

    def test_default_cache_ttl(self) -> None:
        """Test that cache_ttl defaults to 300 seconds."""
        config = DataProviderConfig()
        assert config.cache_ttl == 300

    def test_default_credentials_path(self) -> None:
        """Test that credentials_path has default value."""
        config = DataProviderConfig()
        assert config.credentials_path == "config/credentials.json"

    def test_default_scopes(self) -> None:
        """Test that scopes defaults to readonly spreadsheets."""
        config = DataProviderConfig()
        assert config.scopes == [
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        ]

    def test_custom_cache_ttl(self) -> None:
        """Test data provider config with custom cache TTL."""
        config = DataProviderConfig(cache_ttl=600)
        assert config.cache_ttl == 600

    def test_negative_cache_ttl_rejected(self) -> None:
        """Test that negative cache_ttl raises ValidationError."""
        with pytest.raises(ValidationError):
            DataProviderConfig(cache_ttl=-1)

    def test_zero_cache_ttl_valid(self) -> None:
        """Test that zero cache_ttl is valid (no caching)."""
        config = DataProviderConfig(cache_ttl=0)
        assert config.cache_ttl == 0

    def test_multiple_locations(self) -> None:
        """Test data provider config with multiple locations."""
        eod_config = SheetsConfig(spreadsheet_id="test_id", range_name="EOD!A:N")
        front_config = SheetsConfig(spreadsheet_id="test_id", range_name="Front!A:Z")
        baytown_settings = LocationSettings(
            eod_sheet=eod_config, front_sheet=front_config
        )
        humble_settings = LocationSettings(
            eod_sheet=eod_config, front_sheet=front_config
        )

        config = DataProviderConfig(
            locations={"baytown": baytown_settings, "humble": humble_settings}
        )
        assert len(config.locations) == 2
        assert "baytown" in config.locations
        assert "humble" in config.locations


class TestAppConfig:
    """Test suite for AppConfig model."""

    def test_valid_app_config(self) -> None:
        """Test creating valid application configuration."""
        provider_config = DataProviderConfig()
        config = AppConfig(
            data_provider=provider_config,
            logging_level="INFO",
            debug_mode=False,
        )
        assert config.logging_level == "INFO"
        assert config.debug_mode is False

    def test_default_data_provider_created(self) -> None:
        """Test that data_provider defaults to DataProviderConfig instance."""
        config = AppConfig()
        assert isinstance(config.data_provider, DataProviderConfig)

    def test_default_logging_level(self) -> None:
        """Test that logging_level defaults to INFO."""
        config = AppConfig()
        assert config.logging_level == "INFO"

    def test_default_debug_mode_false(self) -> None:
        """Test that debug_mode defaults to False."""
        config = AppConfig()
        assert config.debug_mode is False

    def test_valid_logging_levels(self) -> None:
        """Test that all valid logging levels are accepted."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            config = AppConfig(logging_level=level)
            assert config.logging_level == level

    def test_invalid_logging_level_rejected(self) -> None:
        """Test that invalid logging_level raises ValidationError."""
        with pytest.raises(ValidationError):
            AppConfig(logging_level="INVALID")

    def test_debug_mode_enabled(self) -> None:
        """Test app config with debug mode enabled."""
        config = AppConfig(logging_level="DEBUG", debug_mode=True)
        assert config.logging_level == "DEBUG"
        assert config.debug_mode is True

    def test_nested_config_composition(self) -> None:
        """Test complete nested configuration structure."""
        eod_config = SheetsConfig(
            spreadsheet_id="1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8",
            range_name="EOD - Baytown!A:N",
        )
        front_config = SheetsConfig(
            spreadsheet_id="1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8",
            range_name="Baytown Front!A:Z",
        )
        location_settings = LocationSettings(
            eod_sheet=eod_config, front_sheet=front_config
        )
        provider_config = DataProviderConfig(
            locations={"baytown": location_settings},
            cache_ttl=600,
        )
        app_config = AppConfig(
            data_provider=provider_config,
            logging_level="WARNING",
        )

        # Verify nested structure
        assert app_config.data_provider.cache_ttl == 600
        assert "baytown" in app_config.data_provider.locations
        assert (
            app_config.data_provider.locations["baytown"].eod_sheet.range_name
            == "EOD - Baytown!A:N"
        )


class TestEdgeCases:
    """Test edge cases across multiple config models."""

    def test_sheets_config_with_whitespace_id(self) -> None:
        """Test spreadsheet_id with whitespace (caught by API)."""
        # Note: min_length=1 validates length, not content
        # Whitespace-only strings will be caught by Google Sheets API
        config = SheetsConfig(spreadsheet_id="   ", range_name="Sheet1!A:Z")
        assert config.spreadsheet_id == "   "

    def test_location_settings_with_empty_business_days(self) -> None:
        """Test location settings with empty business_days list."""
        eod_config = SheetsConfig(spreadsheet_id="test_id", range_name="EOD!A:N")
        front_config = SheetsConfig(spreadsheet_id="test_id", range_name="Front!A:Z")
        settings = LocationSettings(
            eod_sheet=eod_config, front_sheet=front_config, business_days=[]
        )
        assert settings.business_days == []

    def test_data_provider_with_custom_scopes(self) -> None:
        """Test data provider config with custom Google API scopes."""
        config = DataProviderConfig(
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.readonly",
            ]
        )
        assert len(config.scopes) == 2

    def test_app_config_minimal_instantiation(self) -> None:
        """Test app config with minimal required fields."""
        config = AppConfig()
        assert config is not None
        assert isinstance(config.data_provider, DataProviderConfig)
