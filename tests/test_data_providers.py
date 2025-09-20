"""Test suite for data providers module.

Tests the new alias-based SheetsProvider implementation that replaces
the legacy SheetsReader with configurable multi-sheet support.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml

import pandas as pd
from googleapiclient.errors import HttpError

from apps.backend.data_providers import (
    SheetsProvider,
    ConfigurationError,
    build_sheets_provider,
)


class TestSheetsProviderConfiguration:
    """Test configuration loading and validation."""

    def test_valid_configuration_loading(self, tmp_path):
        """Test provider loads valid configuration."""
        # Create valid test configuration
        config_content = {
            "provider_type": "sheets",
            "sheets": {
                "test_alias": {
                    "spreadsheet_id": "test_id_123",
                    "range": "Sheet1!A:Z",
                    "description": "Test sheet",
                }
            },
            "locations": {"test": {"eod": "test_alias"}},
            "provider_config": {
                "credentials_path": "test_creds.json",
                "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"],
            },
        }

        config_path = tmp_path / "test_config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        # Create mock credentials file
        creds_path = tmp_path / "test_creds.json"
        creds_path.write_text("{}")

        # Patch the credentials path in config
        config_content["provider_config"]["credentials_path"] = str(creds_path)
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        # Test successful initialization with mocked Google service
        with patch("apps.backend.data_providers.service_account.Credentials"):
            with patch("apps.backend.data_providers.build") as mock_build:
                provider = SheetsProvider(config_path)

                assert "test_alias" in provider.list_available_aliases()
                assert provider.validate_alias("test_alias")
                assert not provider.validate_alias("invalid_alias")

    def test_missing_configuration_file(self):
        """Test provider raises error for missing config file."""
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            SheetsProvider("nonexistent_config.yml")

    def test_invalid_yaml_configuration(self, tmp_path):
        """Test provider raises error for invalid YAML."""
        config_path = tmp_path / "invalid.yml"
        config_path.write_text("invalid: yaml: {content")

        with pytest.raises(ConfigurationError, match="Invalid YAML configuration"):
            SheetsProvider(config_path)

    def test_missing_required_sections(self, tmp_path):
        """Test provider raises error when required sections are missing."""
        # Test missing 'sheets' section
        config_content = {
            "locations": {},
            "provider_config": {"credentials_path": "test.json", "scopes": []},
        }

        config_path = tmp_path / "incomplete.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        with pytest.raises(ConfigurationError, match="Missing required section: sheets"):
            SheetsProvider(config_path)

    def test_missing_credentials_file(self, tmp_path):
        """Test provider raises error when credentials file is missing."""
        config_content = {
            "sheets": {"test": {"spreadsheet_id": "id", "range": "A:Z"}},
            "locations": {},
            "provider_config": {
                "credentials_path": "nonexistent_creds.json",
                "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"],
            },
        }

        config_path = tmp_path / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        with pytest.raises(ConfigurationError, match="Credentials file not found"):
            SheetsProvider(config_path)

    def test_default_config_path(self):
        """Test provider uses default config path when none provided."""
        with patch("apps.backend.data_providers.Path.exists", return_value=False):
            with pytest.raises(ConfigurationError, match="config/sheets.yml"):
                SheetsProvider()  # Should look for default config/sheets.yml


class TestSheetsProviderFetch:
    """Test data fetching functionality."""

    def test_fetch_with_valid_alias(self, tmp_path):
        """Test successful data fetch with valid alias."""
        # Setup test configuration
        config_content = {
            "sheets": {
                "test_alias": {"spreadsheet_id": "test_id", "range": "Sheet1!A:B"}
            },
            "locations": {},
            "provider_config": {
                "credentials_path": str(tmp_path / "creds.json"),
                "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"],
            },
        }

        config_path = tmp_path / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        # Create mock credentials file
        (tmp_path / "creds.json").write_text("{}")

        # Mock Google Sheets API response
        mock_service = Mock()
        mock_response = {
            "values": [["Column1", "Column2"], ["Value1", "Value2"], ["Value3", "Value4"]]
        }
        mock_service.spreadsheets().values().get().execute.return_value = mock_response

        with patch("apps.backend.data_providers.service_account.Credentials"):
            with patch("apps.backend.data_providers.build", return_value=mock_service):
                provider = SheetsProvider(config_path)
                df = provider.fetch("test_alias")

                assert df is not None
                assert len(df) == 2
                assert list(df.columns) == ["Column1", "Column2"]
                assert df.iloc[0]["Column1"] == "Value1"

    def test_fetch_with_invalid_alias(self, tmp_path):
        """Test fetch returns None for invalid alias."""
        # Setup minimal valid configuration
        config_content = {
            "sheets": {"valid_alias": {"spreadsheet_id": "id", "range": "A:B"}},
            "locations": {},
            "provider_config": {
                "credentials_path": str(tmp_path / "creds.json"),
                "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"],
            },
        }

        config_path = tmp_path / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        (tmp_path / "creds.json").write_text("{}")

        with patch("apps.backend.data_providers.service_account.Credentials"):
            with patch("apps.backend.data_providers.build"):
                provider = SheetsProvider(config_path)
                result = provider.fetch("invalid_alias")

                assert result is None

    def test_fetch_handles_api_errors(self, tmp_path):
        """Test fetch handles Google Sheets API errors gracefully."""
        # Setup configuration
        config_content = {
            "sheets": {"test_alias": {"spreadsheet_id": "id", "range": "A:B"}},
            "locations": {},
            "provider_config": {
                "credentials_path": str(tmp_path / "creds.json"),
                "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"],
            },
        }

        config_path = tmp_path / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        (tmp_path / "creds.json").write_text("{}")

        # Mock API error
        mock_service = Mock()
        mock_service.spreadsheets().values().get().execute.side_effect = HttpError(
            Mock(status=404), b"Not found"
        )

        with patch("apps.backend.data_providers.service_account.Credentials"):
            with patch("apps.backend.data_providers.build", return_value=mock_service):
                provider = SheetsProvider(config_path)
                result = provider.fetch("test_alias")

                assert result is None

    def test_fetch_with_empty_data(self, tmp_path):
        """Test fetch handles empty sheet data."""
        # Setup configuration
        config_content = {
            "sheets": {"test_alias": {"spreadsheet_id": "id", "range": "A:B"}},
            "locations": {},
            "provider_config": {
                "credentials_path": str(tmp_path / "creds.json"),
                "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"],
            },
        }

        config_path = tmp_path / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        (tmp_path / "creds.json").write_text("{}")

        # Mock empty response
        mock_service = Mock()
        mock_service.spreadsheets().values().get().execute.return_value = {"values": []}

        with patch("apps.backend.data_providers.service_account.Credentials"):
            with patch("apps.backend.data_providers.build", return_value=mock_service):
                provider = SheetsProvider(config_path)
                result = provider.fetch("test_alias")

                assert result is None

    def test_fetch_with_headers_only(self, tmp_path):
        """Test fetch handles headers-only data."""
        # Setup configuration
        config_content = {
            "sheets": {"test_alias": {"spreadsheet_id": "id", "range": "A:B"}},
            "locations": {},
            "provider_config": {
                "credentials_path": str(tmp_path / "creds.json"),
                "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"],
            },
        }

        config_path = tmp_path / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        (tmp_path / "creds.json").write_text("{}")

        # Mock headers-only response
        mock_service = Mock()
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [["Column1", "Column2"]]  # Only headers, no data rows
        }

        with patch("apps.backend.data_providers.service_account.Credentials"):
            with patch("apps.backend.data_providers.build", return_value=mock_service):
                provider = SheetsProvider(config_path)
                result = provider.fetch("test_alias")

                assert result is None


class TestLocationAliasMapping:
    """Test location-to-alias resolution."""

    def test_valid_location_alias_mapping(self, tmp_path):
        """Test successful location-to-alias resolution."""
        config_content = {
            "sheets": {
                "baytown_eod": {"spreadsheet_id": "id", "range": "A:B"},
                "humble_front": {"spreadsheet_id": "id", "range": "C:D"},
            },
            "locations": {
                "baytown": {"eod": "baytown_eod"},
                "humble": {"front": "humble_front"},
            },
            "provider_config": {
                "credentials_path": str(tmp_path / "creds.json"),
                "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"],
            },
        }

        config_path = tmp_path / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        (tmp_path / "creds.json").write_text("{}")

        with patch("apps.backend.data_providers.service_account.Credentials"):
            with patch("apps.backend.data_providers.build"):
                provider = SheetsProvider(config_path)

                assert provider.get_location_aliases("baytown", "eod") == "baytown_eod"
                assert provider.get_location_aliases("humble", "front") == "humble_front"
                assert provider.get_location_aliases("invalid", "eod") is None
                assert provider.get_location_aliases("baytown", "invalid") is None

    def test_case_insensitive_location(self, tmp_path):
        """Test location names are case-insensitive."""
        config_content = {
            "sheets": {"test_alias": {"spreadsheet_id": "id", "range": "A:B"}},
            "locations": {"baytown": {"eod": "test_alias"}},
            "provider_config": {
                "credentials_path": str(tmp_path / "creds.json"),
                "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"],
            },
        }

        config_path = tmp_path / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        (tmp_path / "creds.json").write_text("{}")

        with patch("apps.backend.data_providers.service_account.Credentials"):
            with patch("apps.backend.data_providers.build"):
                provider = SheetsProvider(config_path)

                assert provider.get_location_aliases("BAYTOWN", "eod") == "test_alias"
                assert provider.get_location_aliases("Baytown", "eod") == "test_alias"
                assert provider.get_location_aliases("baytown", "eod") == "test_alias"


class TestBuildSheetsProvider:
    """Test factory function."""

    def test_build_sheets_provider_success(self, tmp_path):
        """Test successful provider creation via factory."""
        config_content = {
            "sheets": {},
            "locations": {},
            "provider_config": {
                "credentials_path": str(tmp_path / "creds.json"),
                "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"],
            },
        }

        config_path = tmp_path / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        (tmp_path / "creds.json").write_text("{}")

        with patch("apps.backend.data_providers.service_account.Credentials"):
            with patch("apps.backend.data_providers.build"):
                provider = build_sheets_provider(config_path)
                assert isinstance(provider, SheetsProvider)

    def test_build_sheets_provider_failure(self):
        """Test factory raises error on initialization failure."""
        with pytest.raises(ConfigurationError):
            build_sheets_provider("nonexistent.yml")


class TestConfigurationValidation:
    """Test configuration validation."""

    def test_missing_sheet_fields(self, tmp_path):
        """Test validation catches missing required fields in sheet config."""
        config_content = {
            "sheets": {"incomplete_alias": {"spreadsheet_id": "id"}},  # Missing 'range'
            "locations": {},
            "provider_config": {
                "credentials_path": str(tmp_path / "creds.json"),
                "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"],
            },
        }

        config_path = tmp_path / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        (tmp_path / "creds.json").write_text("{}")

        with patch("apps.backend.data_providers.service_account.Credentials"):
            with patch("apps.backend.data_providers.build"):
                with pytest.raises(
                    ConfigurationError, match="missing required field: range"
                ):
                    SheetsProvider(config_path)