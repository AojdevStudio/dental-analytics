# Unit tests for simplified metrics module (Story 3.3).
# Tests the Pydantic wrapper interface to KPIService.

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from apps.backend.metrics import get_all_kpis, get_kpi_service
from core.models.kpi_models import (
    DataAvailabilityStatus,
    KPIResponse,
    KPIValue,
    KPIValues,
)


class TestMetricsWrapper:
    """Test simplified metrics wrapper (Story 3.3)."""

    @pytest.mark.unit
    @patch("apps.backend.metrics.build_sheets_provider")
    def test_get_kpi_service_singleton(self, mock_build_provider: MagicMock) -> None:
        """Test that KPI service is a singleton."""
        # Mock the provider builder
        mock_build_provider.return_value = MagicMock()

        # Reset singleton
        import apps.backend.metrics

        apps.backend.metrics._kpi_service = None

        service1 = get_kpi_service()
        service2 = get_kpi_service()
        assert service1 is service2

        # Restore singleton for other tests
        apps.backend.metrics._kpi_service = None

    @pytest.mark.unit
    @patch("apps.backend.metrics.build_sheets_provider")
    def test_get_kpi_service_returns_configured_instance(
        self, mock_build_provider: MagicMock
    ) -> None:
        """Test that get_kpi_service returns configured KPIService."""
        # Mock the provider builder
        mock_build_provider.return_value = MagicMock()

        # Reset singleton
        import apps.backend.metrics

        apps.backend.metrics._kpi_service = None

        service = get_kpi_service()

        # Verify service has required components
        assert service is not None
        assert hasattr(service, "get_kpis")
        assert hasattr(service, "data_provider")
        assert hasattr(service, "calendar")
        assert hasattr(service, "validation_rules")
        assert hasattr(service, "transformer")

        # Restore singleton
        apps.backend.metrics._kpi_service = None

    @pytest.mark.unit
    @patch("apps.backend.metrics.get_kpi_service")
    def test_get_all_kpis_returns_pydantic_response(
        self, mock_get_service: MagicMock
    ) -> None:
        """Test that get_all_kpis returns Pydantic KPIResponse."""
        # Create a mock KPIResponse with proper structure
        mock_response = KPIResponse(
            location="baytown",
            business_date=date(2025, 9, 15),
            availability=DataAvailabilityStatus.AVAILABLE,
            values=KPIValues(
                production_total=KPIValue(
                    value=15000.0,
                    available=True,
                    availability_status=DataAvailabilityStatus.AVAILABLE,
                ),
                collection_rate=KPIValue(
                    value=92.5,
                    available=True,
                    availability_status=DataAvailabilityStatus.AVAILABLE,
                ),
                new_patients=KPIValue(
                    value=12,
                    available=True,
                    availability_status=DataAvailabilityStatus.AVAILABLE,
                ),
                case_acceptance=KPIValue(
                    value=75.0,
                    available=True,
                    availability_status=DataAvailabilityStatus.AVAILABLE,
                ),
                hygiene_reappointment=KPIValue(
                    value=88.0,
                    available=True,
                    availability_status=DataAvailabilityStatus.AVAILABLE,
                ),
            ),
        )

        # Configure mock service
        mock_service = MagicMock()
        mock_service.get_kpis.return_value = mock_response
        mock_get_service.return_value = mock_service

        # Call wrapper
        response = get_all_kpis("baytown", date(2025, 9, 15))

        # Verify Pydantic response
        assert isinstance(response, KPIResponse)
        assert response.location == "baytown"
        assert response.values.production_total.value == 15000.0
        assert response.values.collection_rate.value == 92.5
        assert response.values.new_patients.value == 12
        assert response.availability == DataAvailabilityStatus.AVAILABLE

    @pytest.mark.unit
    @patch("apps.backend.metrics.get_kpi_service")
    def test_get_all_kpis_defaults_to_today(self, mock_get_service: MagicMock) -> None:
        """Test that get_all_kpis defaults business_date to today."""
        mock_response = KPIResponse(
            location="humble",
            business_date=date.today(),
            availability=DataAvailabilityStatus.AVAILABLE,
            values=KPIValues(
                production_total=KPIValue(
                    value=10000.0,
                    available=True,
                    availability_status=DataAvailabilityStatus.AVAILABLE,
                ),
                collection_rate=KPIValue(
                    value=85.0,
                    available=True,
                    availability_status=DataAvailabilityStatus.AVAILABLE,
                ),
                new_patients=KPIValue(
                    value=8,
                    available=True,
                    availability_status=DataAvailabilityStatus.AVAILABLE,
                ),
                case_acceptance=KPIValue(
                    value=70.0,
                    available=True,
                    availability_status=DataAvailabilityStatus.AVAILABLE,
                ),
                hygiene_reappointment=KPIValue(
                    value=80.0,
                    available=True,
                    availability_status=DataAvailabilityStatus.AVAILABLE,
                ),
            ),
        )

        mock_service = MagicMock()
        mock_service.get_kpis.return_value = mock_response
        mock_get_service.return_value = mock_service

        # Call without date
        get_all_kpis("humble")

        # Verify service was called with today's date
        mock_service.get_kpis.assert_called_once()
        call_args = mock_service.get_kpis.call_args
        assert call_args[0][0] == "humble"
        assert call_args[0][1] == date.today()

    @pytest.mark.unit
    @patch("apps.backend.metrics.get_kpi_service")
    def test_get_all_kpis_handles_partial_data(
        self, mock_get_service: MagicMock
    ) -> None:
        """Test that get_all_kpis handles partial data responses."""
        mock_response = KPIResponse(
            location="baytown",
            business_date=date(2025, 9, 15),
            availability=DataAvailabilityStatus.PARTIAL,
            values=KPIValues(
                production_total=KPIValue(
                    value=None,
                    available=False,
                    availability_status=DataAvailabilityStatus.DATA_NOT_READY,
                    unavailable_reason="EOD data unavailable",
                ),
                collection_rate=KPIValue(
                    value=None,
                    available=False,
                    availability_status=DataAvailabilityStatus.DATA_NOT_READY,
                    unavailable_reason="EOD data unavailable",
                ),
                new_patients=KPIValue(
                    value=12,
                    available=True,
                    availability_status=DataAvailabilityStatus.AVAILABLE,
                ),
                case_acceptance=KPIValue(
                    value=75.0,
                    available=True,
                    availability_status=DataAvailabilityStatus.AVAILABLE,
                ),
                hygiene_reappointment=KPIValue(
                    value=None,
                    available=False,
                    availability_status=DataAvailabilityStatus.DATA_NOT_READY,
                ),
            ),
        )

        mock_service = MagicMock()
        mock_service.get_kpis.return_value = mock_response
        mock_get_service.return_value = mock_service

        response = get_all_kpis("baytown", date(2025, 9, 15))

        # Verify partial data handling
        assert response.availability == DataAvailabilityStatus.PARTIAL
        assert response.values.production_total.value is None
        assert response.values.production_total.available is False
        assert response.values.new_patients.value == 12
        assert response.values.new_patients.available is True
