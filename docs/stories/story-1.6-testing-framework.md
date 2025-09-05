---
title: "Story 1.6: Testing Framework Implementation"
description: "Implement pytest testing framework with comprehensive test coverage for all KPI calculations and data processing logic."
category: "Development"
subcategory: "Testing"
product_line: "Dental Analytics Dashboard"
audience: "Development Team"
status: "Ready"
author: "AOJDevStudio"
created_date: "2025-09-04"
last_updated: "2025-09-04"
tags:
  - user-story
  - testing
  - pytest
  - quality-assurance
  - mvp
---

# Story 1.6: Testing Framework Implementation

## User Story

**As a** developer,
**I want** comprehensive automated tests for all KPI calculations and data processing,
**so that** we can ensure calculation accuracy and prevent regressions during development.

## Story Points: 3

## Priority: HIGH (Must complete before Phase 3)

## Acceptance Criteria

### Test Framework Setup
1. pytest installed and configured in pyproject.toml
2. Test directory structure created with proper organization
3. pytest-cov installed for coverage reporting
4. Configuration file created with appropriate settings
5. All test files discoverable by pytest
6. Coverage report shows minimum 90% for backend modules

### KPI Calculation Tests
1. Daily Production Total calculation verified with multiple datasets
2. Collection Rate percentage calculation tested including edge cases
3. New Patient Count aggregation validated
4. Treatment Acceptance Rate formula verified with division by zero handling
5. Hygiene Reappointment Rate calculation tested with various scenarios
6. All calculations match expected values within 0.01% tolerance

### Data Processing Tests
1. DataFrame conversion from Google Sheets data tested
2. Type conversion and coercion validated
3. Missing data handling verified
4. Empty dataset scenarios covered
5. Column mapping validation implemented

### Integration Tests
1. Google Sheets connection mocked appropriately
2. End-to-end KPI calculation flow tested
3. Error propagation verified
4. Cache behavior validated

### Test Data Quality
1. Sample data represents real-world scenarios
2. Edge cases included (zero values, nulls, extremes)
3. Test fixtures properly organized
4. Mock data matches production schema

## Technical Requirements

### Dependencies to Add
```toml
# pyproject.toml
[project.optional-dependencies]
test = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "faker>=20.0.0",  # For generating test data
]
```

### Directory Structure
```
dental-analytics/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Shared fixtures
│   ├── test_metrics.py       # KPI calculation tests
│   ├── test_sheets_reader.py # Data retrieval tests
│   ├── fixtures/             # Test data files
│   │   ├── __init__.py
│   │   ├── sample_eod_data.py
│   │   ├── sample_front_kpi_data.py
│   │   └── edge_cases.py
│   └── integration/
│       ├── __init__.py
│       └── test_full_flow.py
├── pytest.ini                # pytest configuration
└── .coveragerc              # Coverage configuration
```

## Implementation Details

### Step 1: Install Testing Dependencies
```bash
# Add test dependencies
uv add --dev pytest pytest-cov pytest-mock faker

# Verify installation
uv run pytest --version
```

### Step 2: Create pytest Configuration
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --cov=backend
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=90
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Tests that take > 1 second
```

### Step 3: Create Coverage Configuration
```ini
# .coveragerc
[run]
source = backend
omit =
    tests/*
    */test_*.py
    */__pycache__/*
    */site-packages/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstract

[html]
directory = htmlcov
```

### Step 4: Create Test Fixtures
```python
# tests/conftest.py
import pytest
import pandas as pd
from datetime import datetime, timedelta

@pytest.fixture
def sample_eod_data():
    """Sample EOD billing sheet data."""
    return pd.DataFrame({
        'date': [datetime.now() - timedelta(days=i) for i in range(5)],
        'provider_1_production': [3000, 3500, 2800, 3200, 3300],
        'provider_2_production': [2500, 2800, 2600, 2900, 2700],
        'provider_3_production': [2000, 2200, 2100, 1900, 2300],
        'total_production': [7500, 8500, 7500, 8000, 8300],  # Column E
        'total_collections': [6750, 7650, 7125, 7200, 7885],  # Column F
        'new_patients': [3, 4, 2, 5, 3],  # Column J
        'calls_answered': [45, 52, 48, 50, 47],  # Column N (EOD)
    })

@pytest.fixture
def sample_front_kpi_data():
    """Sample Front KPI sheet data."""
    return pd.DataFrame({
        'date': [datetime.now() - timedelta(days=i) for i in range(5)],
        'total_hygiene_appointments': [20, 18, 22, 19, 21],  # Column C
        'patients_not_reappointed': [1, 2, 1, 1, 2],  # Column D
        'dollar_presented': [5000, 4500, 5200, 4800, 5100],  # Column L
        'dollar_scheduled': [4000, 3600, 4160, 3360, 4335],  # Column M
        'same_day_treatment': [1500, 1200, 1800, 1400, 1600],  # Column N (Front)
    })

@pytest.fixture
def empty_dataframe():
    """Empty DataFrame for edge case testing."""
    return pd.DataFrame()

@pytest.fixture
def mock_sheets_service(mocker):
    """Mock Google Sheets API service."""
    mock_service = mocker.Mock()
    mock_service.spreadsheets().values().get().execute.return_value = {
        'values': [
            ['header1', 'header2', 'header3'],
            ['value1', 'value2', 'value3']
        ]
    }
    return mock_service
```

### Step 5: Create Metrics Tests
```python
# tests/test_metrics.py
import pytest
import pandas as pd
import numpy as np
from backend.metrics import (
    MetricsCalculator,
    get_all_kpis
)

class TestMetricsCalculator:
    """Test suite for KPI calculations."""

    @pytest.mark.unit
    def test_calculate_production_total(self, sample_eod_data):
        """Test daily production total calculation."""
        result = MetricsCalculator.calculate_production_total(sample_eod_data)
        expected = 39800  # Sum of all total_production
        assert result == expected

    @pytest.mark.unit
    def test_calculate_production_total_empty(self, empty_dataframe):
        """Test production calculation with empty data."""
        result = MetricsCalculator.calculate_production_total(empty_dataframe)
        assert result is None

    @pytest.mark.unit
    def test_calculate_collection_rate(self, sample_eod_data):
        """Test collection rate percentage calculation."""
        result = MetricsCalculator.calculate_collection_rate(sample_eod_data)
        # (36610 / 39800) * 100 = 91.985...
        assert abs(result - 91.99) < 0.01

    @pytest.mark.unit
    def test_calculate_collection_rate_zero_production(self):
        """Test collection rate with zero production."""
        df = pd.DataFrame({
            'total_production': [0, 0],
            'total_collections': [0, 0]
        })
        result = MetricsCalculator.calculate_collection_rate(df)
        assert result is None

    @pytest.mark.unit
    def test_calculate_new_patients(self, sample_eod_data):
        """Test new patient count calculation."""
        result = MetricsCalculator.calculate_new_patients(sample_eod_data)
        assert result == 17  # Sum of new_patients

    @pytest.mark.unit
    def test_calculate_new_patients_with_nulls(self):
        """Test new patient count with null values."""
        df = pd.DataFrame({
            'new_patients': [3, None, 2, np.nan, 1]
        })
        result = MetricsCalculator.calculate_new_patients(df)
        assert result == 6  # Should handle nulls gracefully

    @pytest.mark.unit
    def test_calculate_treatment_acceptance(self, sample_front_kpi_data):
        """Test treatment acceptance rate calculation."""
        result = MetricsCalculator.calculate_treatment_acceptance(sample_front_kpi_data)
        # (20455 / 24600) * 100 = 83.15...
        assert abs(result - 83.15) < 0.01

    @pytest.mark.unit
    def test_calculate_treatment_acceptance_zero_presented(self):
        """Test treatment acceptance with zero presented."""
        df = pd.DataFrame({
            'dollar_presented': [0, 0],
            'dollar_scheduled': [0, 0]
        })
        result = MetricsCalculator.calculate_treatment_acceptance(df)
        assert result is None

    @pytest.mark.unit
    def test_calculate_hygiene_reappointment(self, sample_front_kpi_data):
        """Test hygiene reappointment rate calculation."""
        result = MetricsCalculator.calculate_hygiene_reappointment(sample_front_kpi_data)
        # ((100 - 7) / 100) * 100 = 93.0
        assert abs(result - 93.0) < 0.01

    @pytest.mark.unit
    def test_calculate_hygiene_reappointment_zero_appointments(self):
        """Test hygiene reappointment with zero appointments."""
        df = pd.DataFrame({
            'total_hygiene_appointments': [0, 0],
            'patients_not_reappointed': [0, 0]
        })
        result = MetricsCalculator.calculate_hygiene_reappointment(df)
        assert result is None

    @pytest.mark.unit
    def test_column_name_mismatch_handling(self):
        """Test handling of incorrect column names."""
        df = pd.DataFrame({
            'wrong_column': [100, 200]
        })
        result = MetricsCalculator.calculate_production_total(df)
        assert result is None

class TestKPIThresholds:
    """Test KPI threshold validations."""

    def test_production_threshold_categories(self):
        """Test production categorization."""
        assert self._categorize_production(28000) == "excellent"
        assert self._categorize_production(20000) == "good"
        assert self._categorize_production(14000) == "needs_improvement"

    def test_collection_rate_thresholds(self):
        """Test collection rate categorization."""
        assert self._categorize_collection_rate(96) == "excellent"
        assert self._categorize_collection_rate(90) == "good"
        assert self._categorize_collection_rate(84) == "needs_improvement"

    def test_hygiene_reappointment_thresholds(self):
        """Test hygiene reappointment categorization."""
        assert self._categorize_hygiene(95) == "excellent"
        assert self._categorize_hygiene(85) == "good"
        assert self._categorize_hygiene(79) == "needs_improvement"

    def _categorize_production(self, value):
        if value >= 25000:
            return "excellent"
        elif value >= 15000:
            return "good"
        else:
            return "needs_improvement"

    def _categorize_collection_rate(self, value):
        if value >= 95:
            return "excellent"
        elif value >= 85:
            return "good"
        else:
            return "needs_improvement"

    def _categorize_hygiene(self, value):
        if value >= 90:
            return "excellent"
        elif value >= 80:
            return "good"
        else:
            return "needs_improvement"
```

### Step 6: Create Sheets Reader Tests
```python
# tests/test_sheets_reader.py
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from backend.sheets_reader import SheetsReader

class TestSheetsReader:
    """Test suite for Google Sheets data retrieval."""

    @pytest.mark.unit
    def test_sheets_reader_initialization(self):
        """Test SheetsReader initialization."""
        with patch('backend.sheets_reader.service_account.Credentials') as mock_creds:
            reader = SheetsReader('config/credentials.json')
            assert reader.SPREADSHEET_ID == '1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8'
            mock_creds.from_service_account_file.assert_called_once()

    @pytest.mark.unit
    def test_get_sheet_data_success(self, mock_sheets_service):
        """Test successful data retrieval from sheets."""
        with patch('backend.sheets_reader.build') as mock_build:
            mock_build.return_value = mock_sheets_service

            reader = SheetsReader()
            result = reader.get_sheet_data('TestRange')

            assert isinstance(result, pd.DataFrame)
            assert not result.empty

    @pytest.mark.unit
    def test_get_sheet_data_empty_response(self):
        """Test handling of empty sheet response."""
        with patch('backend.sheets_reader.build') as mock_build:
            mock_service = Mock()
            mock_service.spreadsheets().values().get().execute.return_value = {
                'values': []
            }
            mock_build.return_value = mock_service

            reader = SheetsReader()
            result = reader.get_sheet_data('EmptyRange')
            assert result is None

    @pytest.mark.unit
    def test_get_sheet_data_api_error(self):
        """Test handling of API errors."""
        with patch('backend.sheets_reader.build') as mock_build:
            mock_service = Mock()
            mock_service.spreadsheets().values().get().execute.side_effect = Exception("API Error")
            mock_build.return_value = mock_service

            reader = SheetsReader()
            result = reader.get_sheet_data('ErrorRange')
            assert result is None

    @pytest.mark.unit
    def test_dataframe_column_headers(self, mock_sheets_service):
        """Test that first row becomes column headers."""
        test_data = {
            'values': [
                ['col1', 'col2', 'col3'],
                ['a', 'b', 'c'],
                ['d', 'e', 'f']
            ]
        }
        mock_sheets_service.spreadsheets().values().get().execute.return_value = test_data

        with patch('backend.sheets_reader.build') as mock_build:
            mock_build.return_value = mock_sheets_service

            reader = SheetsReader()
            result = reader.get_sheet_data('TestRange')

            assert list(result.columns) == ['col1', 'col2', 'col3']
            assert len(result) == 2  # Two data rows
```

### Step 7: Create Integration Tests
```python
# tests/integration/test_full_flow.py
import pytest
from unittest.mock import patch, Mock
import pandas as pd
from backend.metrics import get_all_kpis

class TestFullIntegration:
    """Integration tests for complete KPI calculation flow."""

    @pytest.mark.integration
    def test_complete_kpi_flow(self, sample_eod_data, sample_front_kpi_data):
        """Test end-to-end KPI calculation."""
        with patch('backend.sheets_reader.SheetsReader') as MockReader:
            mock_instance = Mock()
            MockReader.return_value = mock_instance

            # Mock different sheet responses
            def get_sheet_side_effect(range_name):
                if 'EOD' in range_name:
                    return sample_eod_data
                elif 'Front KPI' in range_name:
                    return sample_front_kpi_data
                return None

            mock_instance.get_sheet_data.side_effect = get_sheet_side_effect

            # Execute full flow
            kpis = get_all_kpis()

            # Validate all KPIs present
            assert 'production_total' in kpis
            assert 'collection_rate' in kpis
            assert 'new_patients' in kpis
            assert 'treatment_acceptance' in kpis
            assert 'hygiene_reappointment' in kpis

            # Validate values are reasonable
            assert kpis['production_total'] > 0
            assert 0 <= kpis['collection_rate'] <= 100
            assert kpis['new_patients'] >= 0
            assert 0 <= kpis['treatment_acceptance'] <= 100
            assert 0 <= kpis['hygiene_reappointment'] <= 100

    @pytest.mark.integration
    def test_partial_data_failure(self, sample_eod_data):
        """Test handling when some data sources fail."""
        with patch('backend.sheets_reader.SheetsReader') as MockReader:
            mock_instance = Mock()
            MockReader.return_value = mock_instance

            # EOD succeeds, Front KPI fails
            def get_sheet_side_effect(range_name):
                if 'EOD' in range_name:
                    return sample_eod_data
                return None  # Front KPI fails

            mock_instance.get_sheet_data.side_effect = get_sheet_side_effect

            kpis = get_all_kpis()

            # EOD-based KPIs should work
            assert kpis['production_total'] is not None
            assert kpis['collection_rate'] is not None
            assert kpis['new_patients'] is not None

            # Front KPI-based should be None
            assert kpis['treatment_acceptance'] is None
            assert kpis['hygiene_reappointment'] is None

    @pytest.mark.integration
    @pytest.mark.slow
    def test_performance_benchmark(self, sample_eod_data, sample_front_kpi_data):
        """Test that KPI calculation completes within 1 second."""
        import time

        with patch('backend.sheets_reader.SheetsReader') as MockReader:
            mock_instance = Mock()
            MockReader.return_value = mock_instance
            mock_instance.get_sheet_data.return_value = sample_eod_data

            start = time.time()
            kpis = get_all_kpis()
            duration = time.time() - start

            assert duration < 1.0  # Should complete in under 1 second
            assert all(kpi is not None for kpi in kpis.values())
```

### Step 8: Create Edge Case Tests
```python
# tests/fixtures/edge_cases.py
import pandas as pd
import numpy as np

def get_edge_case_data():
    """Generate edge case test data."""
    return {
        'zero_values': pd.DataFrame({
            'total_production': [0, 0, 0],
            'total_collections': [0, 0, 0],
            'new_patients': [0, 0, 0]
        }),
        'negative_values': pd.DataFrame({
            'total_production': [-100, 200, -50],
            'total_collections': [100, -200, 50]
        }),
        'very_large_values': pd.DataFrame({
            'total_production': [1e10, 1e11, 1e12],
            'total_collections': [9e9, 9e10, 9e11]
        }),
        'mixed_types': pd.DataFrame({
            'total_production': ['1000', 2000, '3000.50'],
            'total_collections': [900, '1800', '2700.25']
        }),
        'with_nulls': pd.DataFrame({
            'total_production': [1000, None, 3000, np.nan],
            'total_collections': [None, 1800, np.nan, 2500],
            'new_patients': [3, np.nan, None, 2]
        })
    }
```

## Testing Commands

### Run All Tests
```bash
# Run all tests with coverage
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_metrics.py

# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration
```

### Coverage Reports
```bash
# Generate terminal coverage report
uv run pytest --cov=backend --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=backend --cov-report=html
# Open htmlcov/index.html in browser

# Check coverage threshold (90%)
uv run pytest --cov=backend --cov-fail-under=90
```

### Continuous Testing
```bash
# Watch mode (requires pytest-watch)
uv add --dev pytest-watch
uv run ptw

# Run tests before commit
git add .
uv run pytest && git commit -m "message"
```

## Definition of Done

- [ ] All test files created and organized
- [ ] pytest configuration complete
- [ ] Coverage configuration set up
- [ ] All KPI calculations have tests
- [ ] Edge cases covered
- [ ] Integration tests passing
- [ ] 90% code coverage achieved for backend/
- [ ] No test warnings or deprecations
- [ ] Tests run in under 5 seconds total
- [ ] Documentation updated with test commands

## Notes

- Tests use mocking to avoid Google API calls
- Fixtures provide consistent test data
- Coverage focuses on business logic, not API calls
- Integration tests verify complete flows
- Edge cases ensure robustness

## Related Stories

- Depends on: Story 1.1 (Google Sheets Connection)
- Depends on: Story 1.2 (KPI Calculations)
- Blocks: Story 1.5 (Dashboard Display)
- Enables: Production deployment

## Risk Mitigation

This story addresses the critical risk of calculation errors by:
- Validating all formulas against known values
- Testing edge cases and error conditions
- Ensuring consistent results across different data sets
- Providing regression protection for future changes
