# Integration tests for KPI Service
"""End-to-end integration tests for the KPI orchestration service.

These tests verify the complete flow from data fetch through calculation
to validation and response assembly. They use mock DataProvider to avoid
external dependencies while testing the integration between:
- BusinessCalendar
- DataProvider
- SheetsToKPIInputs transformer
- KPI calculators
- KPIValidationRules
- KPIService orchestration
"""

from datetime import date
from unittest.mock import Mock

import pandas as pd
import pytest

from core.business_rules.calendar import BusinessCalendar
from core.business_rules.validation_rules import KPIValidationRules
from core.models.kpi_models import DataAvailabilityStatus
from core.transformers.sheets_transformer import SheetsToKPIInputs
from services.kpi_service import KPIService


@pytest.fixture
def mock_data_provider():
    """Create a mock DataProvider that returns sample data."""
    provider = Mock()

    # Default: return sample data for both EOD and Front
    def mock_fetch(alias: str):
        if "eod" in alias:
            # Return EOD data
            return pd.DataFrame(
                {
                    "Total Production Today": [7650.0],
                    "Adjustments Today": [-250.0],
                    "Write-offs Today": [-100.0],
                    "Patient Income Today": [3500.0],
                    "Unearned Income Today": [0.0],
                    "Insurance Income Today": [3700.0],
                    "New Patients - Total Month to Date": [48],
                }
            )
        elif "front" in alias:
            # Return Front KPI data
            return pd.DataFrame(
                {
                    "treatments_presented": [50000],
                    "treatments_scheduled": [35000],
                    "$ Same Day Treatment": [5000],
                    "Total hygiene Appointments": [20],
                    "Number of patients NOT reappointed?": [1],
                }
            )
        return None

    provider.fetch.side_effect = mock_fetch
    provider.list_available_aliases.return_value = [
        "baytown_eod",
        "baytown_front",
        "humble_eod",
        "humble_front",
    ]
    provider.validate_alias.return_value = True

    return provider


@pytest.fixture
def kpi_service(mock_data_provider):
    """Create KPIService with all dependencies."""
    calendar = BusinessCalendar()
    validation_rules = KPIValidationRules()
    transformer = SheetsToKPIInputs()

    return KPIService(
        data_provider=mock_data_provider,
        calendar=calendar,
        validation_rules=validation_rules,
        transformer=transformer,
    )


class TestSuccessfulKPIRetrieval:
    """Tests for successful end-to-end KPI retrieval."""

    def test_get_kpis_baytown_monday(self, kpi_service):
        """Should successfully retrieve all KPIs for Baytown on Monday."""
        monday = date(2025, 1, 6)  # Monday

        response = kpi_service.get_kpis("baytown", monday)

        # Verify response structure
        assert response.location == "baytown"
        assert response.business_date == monday
        assert response.availability == DataAvailabilityStatus.AVAILABLE
        assert response.closure_reason is None

        # Verify all 5 KPIs are available
        assert response.values.production_total.available is True
        assert response.values.collection_rate.available is True
        assert response.values.new_patients.available is True
        assert response.values.case_acceptance.available is True
        assert response.values.hygiene_reappointment.available is True

        # Verify production calculation (7650 - 250 - 100 = 7300)
        assert response.values.production_total.value == 7300.0

        # Verify collection rate calculation
        # Adjusted production: 7650 - 250 - 100 = 7300
        # Collections: 3500 + 0 + 3700 = 7200
        # Rate: (7200 / 7300) * 100 = 98.63%
        assert response.values.collection_rate.value == pytest.approx(98.63, abs=0.01)

        # Verify new patients
        assert response.values.new_patients.value == 48

        # Verify case acceptance
        # (35000 + 5000) / 50000 * 100 = 80%
        assert response.values.case_acceptance.value == pytest.approx(80.0, abs=0.1)

        # Verify hygiene reappointment
        # (20 - 1) / 20 * 100 = 95%
        assert response.values.hygiene_reappointment.value == pytest.approx(
            95.0, abs=0.1
        )

    def test_get_kpis_humble_monday(self, kpi_service):
        """Should successfully retrieve all KPIs for Humble on Monday."""
        monday = date(2025, 1, 6)  # Monday

        response = kpi_service.get_kpis("humble", monday)

        # Humble should also be open on Monday
        assert response.location == "humble"
        assert response.business_date == monday
        assert response.availability == DataAvailabilityStatus.AVAILABLE
        assert response.values.production_total.available is True

    def test_data_freshness_metadata_included(self, kpi_service):
        """Should include data freshness metadata for both sources."""
        monday = date(2025, 1, 6)

        response = kpi_service.get_kpis("baytown", monday)

        # Should have freshness data for both EOD and Front
        assert len(response.data_freshness) == 2

        aliases = {f.source_alias for f in response.data_freshness}
        assert "baytown_eod" in aliases
        assert "baytown_front" in aliases

        # All should have timezone
        for freshness in response.data_freshness:
            assert freshness.timezone == "America/Chicago"


class TestClosedDayHandling:
    """Tests for handling location closures."""

    def test_baytown_sunday_closed(self, kpi_service):
        """Should return closed response for Baytown on Sunday."""
        sunday = date(2025, 1, 12)  # Sunday

        response = kpi_service.get_kpis("baytown", sunday)

        # Verify closed response
        assert response.location == "baytown"
        assert response.business_date == sunday
        assert response.availability == DataAvailabilityStatus.EXPECTED_CLOSURE
        assert response.closure_reason == "Closed on Sundays"

        # All KPIs should be unavailable
        assert response.values.production_total.available is False
        assert response.values.collection_rate.available is False
        assert response.values.new_patients.available is False
        assert response.values.case_acceptance.available is False
        assert response.values.hygiene_reappointment.available is False

        # All should have same closure status
        for kpi in [
            response.values.production_total,
            response.values.collection_rate,
            response.values.new_patients,
            response.values.case_acceptance,
            response.values.hygiene_reappointment,
        ]:
            assert kpi.availability_status == DataAvailabilityStatus.EXPECTED_CLOSURE

    def test_humble_friday_closed(self, kpi_service):
        """Should return closed response for Humble on Friday."""
        friday = date(2025, 1, 10)  # Friday

        response = kpi_service.get_kpis("humble", friday)

        assert response.availability == DataAvailabilityStatus.EXPECTED_CLOSURE
        assert response.closure_reason == "Humble is closed on Fridays"
        assert response.values.production_total.available is False


class TestPartialDataHandling:
    """Tests for handling partial data scenarios."""

    def test_eod_only_partial_availability(self, kpi_service, mock_data_provider):
        """Should handle case when only EOD data is available."""

        # Mock to return only EOD data, no Front data
        def mock_fetch_eod_only(alias: str):
            if "eod" in alias:
                return pd.DataFrame(
                    {
                        "Total Production Today": [7650.0],
                        "Adjustments Today": [-250.0],
                        "Write-offs Today": [-100.0],
                        "Patient Income Today": [3500.0],
                        "Unearned Income Today": [0.0],
                        "Insurance Income Today": [3700.0],
                        "New Patients - Total Month to Date": [48],
                    }
                )
            return None  # No Front data

        mock_data_provider.fetch.side_effect = mock_fetch_eod_only

        monday = date(2025, 1, 6)
        response = kpi_service.get_kpis("baytown", monday)

        # Should have PARTIAL status
        assert response.availability == DataAvailabilityStatus.PARTIAL

        # EOD-based KPIs should be available
        assert response.values.production_total.available is True
        assert response.values.collection_rate.available is True
        assert response.values.new_patients.available is True

        # Front-based KPIs should be unavailable
        assert response.values.case_acceptance.available is False
        assert response.values.hygiene_reappointment.available is False
        assert (
            response.values.case_acceptance.availability_status
            == DataAvailabilityStatus.PARTIAL
        )

    def test_front_only_partial_availability(self, kpi_service, mock_data_provider):
        """Should handle case when only Front data is available."""

        # Mock to return only Front data, no EOD
        def mock_fetch_front_only(alias: str):
            if "front" in alias:
                return pd.DataFrame(
                    {
                        "treatments_presented": [50000],
                        "treatments_scheduled": [35000],
                        "$ Same Day Treatment": [5000],
                        "Total hygiene Appointments": [20],
                        "Number of patients NOT reappointed?": [1],
                    }
                )
            return None  # No EOD data

        mock_data_provider.fetch.side_effect = mock_fetch_front_only

        monday = date(2025, 1, 6)
        response = kpi_service.get_kpis("baytown", monday)

        # Should have PARTIAL status
        assert response.availability == DataAvailabilityStatus.PARTIAL

        # Front-based KPIs should be available
        assert response.values.case_acceptance.available is True
        assert response.values.hygiene_reappointment.available is True

        # EOD-based KPIs should be unavailable
        assert response.values.production_total.available is False
        assert response.values.collection_rate.available is False
        assert response.values.new_patients.available is False


class TestErrorHandling:
    """Tests for error conditions."""

    def test_no_data_available(self, kpi_service, mock_data_provider):
        """Should handle case when no data is available."""
        # Reset side_effect and set return_value to None
        mock_data_provider.fetch.side_effect = None
        mock_data_provider.fetch.return_value = None

        monday = date(2025, 1, 6)
        response = kpi_service.get_kpis("baytown", monday)

        assert response.availability == DataAvailabilityStatus.DATA_NOT_READY
        assert response.values.production_total.available is False

    def test_data_fetch_exception(self, kpi_service, mock_data_provider):
        """Should handle exceptions during data fetch."""
        mock_data_provider.fetch.side_effect = Exception("Connection timeout")

        monday = date(2025, 1, 6)
        response = kpi_service.get_kpis("baytown", monday)

        assert response.availability == DataAvailabilityStatus.INFRASTRUCTURE_ERROR
        assert (
            "Failed to fetch data"
            in response.values.production_total.unavailable_reason
        )


class TestValidationIntegration:
    """Tests for validation integration with calculation."""

    def test_production_over_goal_validation(self, kpi_service, mock_data_provider):
        """Should generate validation warning when production is over goal."""

        # Mock very high production (2x typical goal)
        def mock_fetch_high_production(alias: str):
            if "eod" in alias:
                return pd.DataFrame(
                    {
                        "Total Production Today": [15000.0],  # Very high
                        "Adjustments Today": [0.0],
                        "Write-offs Today": [0.0],
                        "Patient Income Today": [7000.0],
                        "Unearned Income Today": [0.0],
                        "Insurance Income Today": [8000.0],
                        "New Patients - Total Month to Date": [48],
                    }
                )
            elif "front" in alias:
                return pd.DataFrame(
                    {
                        "treatments_presented": [50000],
                        "treatments_scheduled": [35000],
                        "$ Same Day Treatment": [5000],
                        "Total hygiene Appointments": [20],
                        "Number of patients NOT reappointed?": [1],
                    }
                )
            return None

        mock_data_provider.fetch.side_effect = mock_fetch_high_production

        monday = date(2025, 1, 6)
        response = kpi_service.get_kpis("baytown", monday)

        # Should have validation issues
        production_issues = response.values.production_total.validation_issues
        assert len(production_issues) > 0

        # Should have over_goal warning
        codes = [issue.code for issue in production_issues]
        assert "production.over_goal" in codes

    def test_collection_rate_out_of_range_validation(
        self, kpi_service, mock_data_provider
    ):
        """Should generate validation warning for collection rate >110%."""

        # Mock collection rate > 110%
        def mock_fetch_high_collection(alias: str):
            if "eod" in alias:
                return pd.DataFrame(
                    {
                        "Total Production Today": [5000.0],
                        "Adjustments Today": [0.0],
                        "Write-offs Today": [0.0],
                        "Patient Income Today": [5500.0],  # Over production
                        "Unearned Income Today": [500.0],
                        "Insurance Income Today": [0.0],
                        "New Patients - Total Month to Date": [48],
                    }
                )
            elif "front" in alias:
                return pd.DataFrame(
                    {
                        "treatments_presented": [50000],
                        "treatments_scheduled": [35000],
                        "$ Same Day Treatment": [5000],
                        "Total hygiene Appointments": [20],
                        "Number of patients NOT reappointed?": [1],
                    }
                )
            return None

        mock_data_provider.fetch.side_effect = mock_fetch_high_collection

        monday = date(2025, 1, 6)
        response = kpi_service.get_kpis("baytown", monday)

        # Should have validation issues
        collection_issues = response.values.collection_rate.validation_issues
        assert len(collection_issues) > 0

        # Should have too_high warning
        codes = [issue.code for issue in collection_issues]
        assert "collection_rate.too_high" in codes

    def test_validation_summary_aggregates_all_issues(
        self, kpi_service, mock_data_provider
    ):
        """Should aggregate all validation issues into validation_summary."""

        # Mock case acceptance > 100%
        def mock_fetch_validation_issues(alias: str):
            if "eod" in alias:
                return pd.DataFrame(
                    {
                        "Total Production Today": [7650.0],
                        "Adjustments Today": [-250.0],
                        "Write-offs Today": [-100.0],
                        "Patient Income Today": [3500.0],
                        "Unearned Income Today": [0.0],
                        "Insurance Income Today": [3700.0],
                        "New Patients - Total Month to Date": [48],
                    }
                )
            elif "front" in alias:
                return pd.DataFrame(
                    {
                        "treatments_presented": [50000],
                        "treatments_scheduled": [45000],
                        "$ Same Day Treatment": [10000],  # > 100%
                        "Total hygiene Appointments": [20],
                        "Number of patients NOT reappointed?": [1],
                    }
                )
            return None

        mock_data_provider.fetch.side_effect = mock_fetch_validation_issues

        monday = date(2025, 1, 6)
        response = kpi_service.get_kpis("baytown", monday)

        # Validation summary should aggregate issues from all KPIs
        assert len(response.validation_summary) > 0

        # Should include case acceptance warning
        codes = [issue.code for issue in response.validation_summary]
        assert "case_acceptance.over_100" in codes


class TestCalculationAccuracy:
    """Tests to verify calculation accuracy matches expected formulas."""

    def test_production_calculation_with_adjustments(
        self, kpi_service, mock_data_provider
    ):
        """Should correctly calculate production with adjustments and writeoffs."""

        def mock_fetch_specific(alias: str):
            if "eod" in alias:
                return pd.DataFrame(
                    {
                        "Total Production Today": [10000.0],
                        "Adjustments Today": [-500.0],
                        "Write-offs Today": [-300.0],
                        "Patient Income Today": [5000.0],
                        "Unearned Income Today": [0.0],
                        "Insurance Income Today": [4200.0],
                        "New Patients - Total Month to Date": [48],
                    }
                )
            elif "front" in alias:
                return pd.DataFrame(
                    {
                        "treatments_presented": [100],
                        "treatments_scheduled": [70],
                        "$ Same Day Treatment": [10],
                        "Total hygiene Appointments": [20],
                        "Number of patients NOT reappointed?": [1],
                    }
                )
            return None

        mock_data_provider.fetch.side_effect = mock_fetch_specific

        monday = date(2025, 1, 6)
        response = kpi_service.get_kpis("baytown", monday)

        # Production: 10000 - 500 - 300 = 9200
        assert response.values.production_total.value == 9200.0

        # Collection rate: (5000 + 0 + 4200) / 9200 * 100 = 100%
        assert response.values.collection_rate.value == 100.0

        # Case acceptance: (70 + 10) / 100 * 100 = 80%
        assert response.values.case_acceptance.value == 80.0
