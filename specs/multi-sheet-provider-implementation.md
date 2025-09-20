---
title: "Multi-Sheet Provider Implementation Plan"
description: "Comprehensive plan to refactor single-sheet Google Sheets reader to support multiple sheets via aliases and prepare for SQLite migration."
category: "Implementation"
subcategory: "Backend Architecture"
product_line: "Dental Analytics"
audience: "Engineering"
status: "Ready for Development"
author: "AOJDevStudio"
created_date: "2025-09-20"
last_updated: "2025-09-20"
tags:
  - google-sheets
  - data-provider
  - architecture-refactor
  - sqlite-preparation
  - alias-configuration
---

# Multi-Sheet Provider Implementation Plan

## Executive Summary

This document provides a comprehensive implementation plan to refactor the current hard-coded single-sheet Google Sheets reader into a flexible multi-sheet provider system. The new architecture will use alias-based configuration to support multiple spreadsheets and locations while preparing the interface for future SQLite migration.

## Problem Analysis

### Current Architecture Issues

1. **Hard-coded Spreadsheet ID**: Module-level `SPREADSHEET_ID` constant forces all data access through a single spreadsheet
2. **Location-specific Hardcoding**: `get_eod_data()` and `get_front_kpi_data()` methods contain hardcoded range strings with conditional logic
3. **Tight Coupling**: All consumers directly instantiate `SheetsReader` and call location-specific methods
4. **No Provider Abstraction**: No interface for swapping Google Sheets with SQLite or other data sources
5. **Scattered Configuration**: Spreadsheet IDs, ranges, and column mappings spread across multiple files

### Current Call Sites Analysis

**Primary Usage Points:**
- `apps/backend/metrics.py:416` - `reader = SheetsReader()`
- `apps/backend/metrics.py:419` - `eod_data = reader.get_eod_data(location)`
- `apps/backend/metrics.py:420` - `front_kpi_data = reader.get_front_kpi_data(location)`
- `apps/frontend/app.py:111` - `kpis = get_all_kpis(location=location)`

**Current Range Hardcoding:**
```python
# In sheets_reader.py:78-82
if location.lower() == "humble":
    range_name = "EOD - Humble Billing!A:AG"
else:  # Default to baytown
    range_name = "EOD - Baytown Billing!A:AG"
```

## Solution Architecture

### 1. Data Provider Interface

**Core Interface Definition:**
```python
from abc import ABC, abstractmethod
from typing import Protocol
import pandas as pd

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
```

### 2. Configuration Schema

**New File: `config/sheets.yml`**
```yaml
# Multi-sheet configuration for dental analytics
provider_type: "sheets"  # Prepare for 'sqlite' option

# Core spreadsheet definitions
sheets:
  baytown_eod:
    spreadsheet_id: "1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8"
    range: "EOD - Baytown Billing!A:N"
    description: "Baytown end-of-day billing data"

  humble_eod:
    spreadsheet_id: "1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8"
    range: "EOD - Humble Billing!A:N"
    description: "Humble end-of-day billing data"

  baytown_front:
    spreadsheet_id: "1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8"
    range: "Baytown Front KPIs Form responses!A:Z"
    description: "Baytown front office KPI data"

  humble_front:
    spreadsheet_id: "1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8"
    range: "Humble Front KPIs Form responses!A:Z"
    description: "Humble front office KPI data"

# Location-to-alias mapping for backward compatibility
locations:
  baytown:
    eod: "baytown_eod"
    front: "baytown_front"
  humble:
    eod: "humble_eod"
    front: "humble_front"

# Provider configuration
provider_config:
  credentials_path: "config/credentials.json"
  scopes:
    - "https://www.googleapis.com/auth/spreadsheets.readonly"
  timeout_seconds: 30
  retry_attempts: 3
  cache_duration_minutes: 5

# Future SQLite preparation
# sqlite:
#   database_path: "data/dental_analytics.db"
#   connection_pool_size: 5
#   query_timeout_seconds: 10
```

### 3. New SheetsProvider Implementation

**New File: `apps/backend/data_providers.py`**
```python
"""Data provider implementations for dental analytics.

Provides abstracted data access through configurable providers.
Supports Google Sheets with alias-based configuration and prepares
interface for future SQLite provider integration.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when provider configuration is invalid."""
    pass


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

    def _load_config(self, config_path: Path | str | None) -> Dict[str, Any]:
        """Load and validate sheets configuration."""
        if config_path is None:
            config_path = "config/sheets.yml"

        config_file = Path(config_path)
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            # Validate required sections
            required_sections = ['sheets', 'locations', 'provider_config']
            for section in required_sections:
                if section not in config:
                    raise ConfigurationError(f"Missing required section: {section}")

            logger.info(f"Loaded configuration with {len(config['sheets'])} sheet aliases")
            return config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML configuration: {e}")

    def _init_google_service(self) -> Any:
        """Initialize Google Sheets API service."""
        provider_config = self.config['provider_config']
        credentials_path = provider_config['credentials_path']
        scopes = provider_config['scopes']

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
            raise ConfigurationError(f"Failed to initialize Google service: {e}")

    def _validate_configuration(self) -> None:
        """Validate all sheet aliases are properly configured."""
        sheets_config = self.config['sheets']

        for alias, sheet_config in sheets_config.items():
            required_fields = ['spreadsheet_id', 'range']
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

        sheet_config = self.config['sheets'][alias]
        spreadsheet_id = sheet_config['spreadsheet_id']
        range_name = sheet_config['range']

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

    def list_available_aliases(self) -> List[str]:
        """Get list of available sheet aliases."""
        return list(self.config['sheets'].keys())

    def validate_alias(self, alias: str) -> bool:
        """Check if alias exists in configuration."""
        return alias in self.config['sheets']

    def get_location_aliases(self, location: str, data_type: str) -> str | None:
        """Get alias for location and data type combination.

        Args:
            location: Location name ('baytown' or 'humble')
            data_type: Data type ('eod' or 'front')

        Returns:
            Alias string or None if not found
        """
        locations_config = self.config.get('locations', {})
        location_config = locations_config.get(location.lower())

        if not location_config:
            logger.warning(f"Location not configured: {location}")
            return None

        alias = location_config.get(data_type)
        if not alias:
            logger.warning(f"Data type '{data_type}' not configured for location '{location}'")
            return None

        return alias


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


# Note: Legacy SheetsReader class completely removed
# No backward compatibility provided - this is a breaking architectural change
```

## Implementation Plan

### Phase 1: Configuration Setup (Sprint N - Week 1)

**Step 1.1: Create Configuration File**
- [ ] Create `config/sheets.yml` with alias definitions
- [ ] Validate YAML syntax and required sections
- [ ] Test configuration loading with error handling

**Step 1.2: Implement Configuration Loader**
- [ ] Add `pyyaml` dependency to `pyproject.toml`
- [ ] Create configuration validation functions
- [ ] Add unit tests for config loading edge cases

### Phase 2: Provider Implementation (Sprint N - Week 1-2)

**Step 2.1: Create DataProvider Interface**
- [ ] Implement `DataProvider` protocol in `apps/backend/data_providers.py`
- [ ] Define clear method signatures and documentation
- [ ] Add type hints for all methods

**Step 2.2: Implement SheetsProvider**
- [ ] Create `SheetsProvider` class implementing `DataProvider`
- [ ] Add alias-based fetch method
- [ ] Implement configuration validation on startup
- [ ] Add factory function for dependency injection

**Step 2.3: Remove Legacy Code**
- [ ] Delete `SheetsReader` class entirely from `sheets_reader.py`
- [ ] Remove module-level `SPREADSHEET_ID` constant
- [ ] Delete `get_eod_data()` and `get_front_kpi_data()` methods

### Phase 3: Consumer Migration (Sprint N - Week 2)

**Step 3.1: Update Metrics Module**
```python
# Before (apps/backend/metrics.py:414-420)
reader = SheetsReader()
eod_data = reader.get_eod_data(location)
front_kpi_data = reader.get_front_kpi_data(location)

# After
from .data_providers import build_sheets_provider

provider = build_sheets_provider()
eod_alias = provider.get_location_aliases(location, "eod")
front_alias = provider.get_location_aliases(location, "front")

eod_data = provider.fetch(eod_alias) if eod_alias else None
front_kpi_data = provider.fetch(front_alias) if front_alias else None
```

**Step 3.2: Update Historical Data Module**
- [ ] Replace `SheetsReader` usage in `historical_data.py`
- [ ] Use alias resolution for data fetching
- [ ] Update all internal APIs to use new provider system

**Step 3.3: Update CLI Scripts**
- [ ] Modify `scripts/print_kpis.py` to use alias system
- [ ] Add alias selection flags for CLI usage
- [ ] Remove dependency on legacy hardcoded constants

### Phase 4: Testing & Validation (Sprint N - Week 3)

**Step 4.1: Unit Tests**
```python
# Test file: tests/test_data_providers.py
import pytest
from unittest.mock import Mock, patch
from apps.backend.data_providers import SheetsProvider, ConfigurationError

class TestSheetsProvider:
    def test_valid_configuration_loading(self):
        """Test provider loads valid configuration."""
        # Create mock config file
        # Test successful initialization
        pass

    def test_invalid_configuration_raises_error(self):
        """Test provider raises error for invalid config."""
        with pytest.raises(ConfigurationError):
            SheetsProvider("invalid_config.yml")

    def test_fetch_with_valid_alias(self):
        """Test successful data fetch with valid alias."""
        # Mock Google Sheets API response
        # Test DataFrame creation
        pass

    def test_fetch_with_invalid_alias(self):
        """Test fetch returns None for invalid alias."""
        # Test error handling
        pass

    def test_location_alias_resolution(self):
        """Test location-to-alias mapping works correctly."""
        # Test baytown/humble mapping to correct aliases
        pass
```

**Step 4.2: Integration Tests**
- [ ] Test end-to-end KPI calculation with new provider
- [ ] Validate all functionality works with alias-based system
- [ ] Test error handling and configuration validation scenarios

**Step 4.3: Performance Validation**
- [ ] Benchmark new provider performance characteristics
- [ ] Ensure efficient configuration loading and caching
- [ ] Test configuration validation startup time

### Phase 5: Documentation & Cleanup (Sprint N - Week 3)

**Step 5.1: Update Documentation**
- [ ] Update README with new provider usage examples
- [ ] Document alias configuration format
- [ ] Create migration guide for developers

**Step 5.2: Code Cleanup**
- [ ] Verify complete removal of legacy `SheetsReader` references
- [ ] Clean up unused imports and dead code
- [ ] Ensure all hardcoded ranges and IDs are eliminated
- [ ] Remove any remaining location-specific conditional logic

**Step 5.3: Final Testing**
- [ ] Run full test suite with new architecture
- [ ] Test dashboard functionality with both locations using aliases
- [ ] Validate error messages are helpful and actionable

## Testing Strategy

### Unit Testing Approach

**Configuration Testing:**
```python
def test_configuration_validation():
    """Test comprehensive configuration validation."""
    # Test missing sections
    # Test invalid YAML syntax
    # Test missing required fields
    # Test invalid credential paths
```

**Provider Testing:**
```python
def test_sheets_provider_fetch():
    """Test data fetching with mocked Google API."""
    with patch('googleapiclient.discovery.build') as mock_build:
        # Mock successful API response
        # Test DataFrame creation
        # Test error handling
```

**Alias Resolution Testing:**
```python
def test_location_alias_mapping():
    """Test location-to-alias resolution."""
    provider = SheetsProvider("test_config.yml")

    # Test valid combinations
    assert provider.get_location_aliases("baytown", "eod") == "baytown_eod"
    assert provider.get_location_aliases("humble", "front") == "humble_front"

    # Test invalid combinations
    assert provider.get_location_aliases("invalid", "eod") is None
```

### Integration Testing Approach

**End-to-End KPI Testing:**
```python
def test_kpi_calculation_with_new_provider():
    """Test complete KPI calculation pipeline."""
    # Use real configuration with test data
    # Verify all 5 KPIs calculate correctly
    # Validate new alias-based approach works end-to-end
```

**Error Handling Testing:**
```python
def test_provider_error_scenarios():
    """Test graceful handling of API failures."""
    # Test network timeouts
    # Test invalid spreadsheet IDs
    # Test malformed data responses
```

## Migration Strategy

### Breaking Change Implementation

**Complete API Replacement:**
- `SheetsReader` class completely removed
- Module-level `SPREADSHEET_ID` constant eliminated
- Location-specific methods (`get_eod_data`, `get_front_kpi_data`) deleted
- All consumers must use new alias-based provider system

**New Consumer Pattern:**
1. Use `build_sheets_provider()` factory for provider instantiation
2. Use explicit alias resolution: `provider.get_location_aliases(location, data_type)`
3. Fetch data via `provider.fetch(alias)` with clear error handling

## Risk Assessment & Mitigation

### High-Risk Areas

**Configuration Management:**
- **Risk:** Invalid YAML breaks entire system
- **Mitigation:** Comprehensive validation on startup with clear error messages

**API Compatibility:**
- **Risk:** Google Sheets API changes break provider
- **Mitigation:** Robust error handling and fallback mechanisms

**Data Consistency:**
- **Risk:** Alias mapping errors lead to wrong data
- **Mitigation:** Extensive testing and validation during migration

### Medium-Risk Areas

**Performance Impact:**
- **Risk:** Configuration loading adds startup overhead
- **Mitigation:** Configuration caching and lazy loading

**Development Complexity:**
- **Risk:** New abstraction layer adds complexity
- **Mitigation:** Clear documentation and simple factory patterns

## Future SQLite Preparation

### Interface Compatibility

The new `DataProvider` protocol is designed to support future SQLite implementation:

```python
class SQLiteProvider:
    """Future SQLite data provider implementation."""

    def fetch(self, alias: str) -> pd.DataFrame | None:
        """Fetch data from SQLite using alias-to-query mapping."""
        # Will implement SQL query execution
        # Return DataFrame from database results
        pass
```

### Configuration Extension

Future `config/sheets.yml` will support provider selection:

```yaml
# Future multi-provider configuration
provider_type: "sqlite"  # or "sheets" or "hybrid"

sqlite:
  database_path: "data/dental_analytics.db"
  tables:
    baytown_eod:
      table: "eod_data"
      where: "location = 'baytown'"
    humble_eod:
      table: "eod_data"
      where: "location = 'humble'"
```

## Success Criteria

### Functional Requirements Met

- [ ] All KPI calculations work with new alias-based provider
- [ ] Both Baytown and Humble locations supported
- [ ] Configuration-driven sheet access implemented
- [ ] Legacy API completely removed
- [ ] Clear error messages for invalid configurations

### Non-Functional Requirements Met

- [ ] Performance meets or exceeds previous implementation
- [ ] Startup time increase < 500ms
- [ ] All unit tests passing with >90% coverage
- [ ] Integration tests validate end-to-end functionality
- [ ] Documentation complete and accurate

### Quality Gates

**Code Quality:**
- [ ] All linting rules pass (ruff, black, mypy)
- [ ] No TODO or FIXME comments in production code
- [ ] All functions have type hints and docstrings

**Architecture Quality:**
- [ ] Clean separation between provider interface and implementation
- [ ] Configuration loading is robust and well-tested
- [ ] Error handling provides actionable feedback

## Implementation Timeline

### Sprint N (3 weeks)

**Week 1: Foundation**
- Days 1-2: Configuration setup and validation
- Days 3-5: Provider interface and implementation

**Week 2: Migration**
- Days 1-3: Consumer module updates
- Days 4-5: Testing and validation

**Week 3: Finalization**
- Days 1-2: Documentation and cleanup
- Days 3-5: Final testing and deployment preparation

### Key Milestones

1. **M1 (End of Week 1):** New provider successfully fetches data via aliases
2. **M2 (End of Week 2):** All consumers migrated, legacy code removed
3. **M3 (End of Week 3):** Full test coverage, documentation complete

## Conclusion

This implementation plan provides a comprehensive approach to refactoring the dental analytics system from a single-sheet Google Sheets reader to a flexible, alias-based multi-provider architecture. The new system will:

1. **Eliminate hardcoded dependencies** through configuration-driven design
2. **Support multiple spreadsheets and locations** via alias mapping
3. **Prepare for future SQLite migration** with provider abstraction
4. **Maintain backward compatibility** through location-based convenience methods
5. **Improve testability** with dependency injection and clear interfaces

The phased approach ensures minimal risk while delivering immediate value through improved flexibility and maintainability. The architecture is designed to scale beyond the current two-location, five-KPI system to support future growth and data source diversification.
