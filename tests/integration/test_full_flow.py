# Integration tests for complete KPI calculation flow

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from backend.metrics import get_all_kpis
from tests.fixtures.sample_eod_data import get_simple_eod_data
from tests.fixtures.sample_front_kpi_data import get_simple_front_kpi_data


class TestFullIntegration:
    """Integration tests for complete KPI calculation flow."""

    @pytest.mark.integration
    def test_complete_kpi_flow(self) -> None:
        """Test end-to-end KPI calculation."""
        with patch("backend.sheets_reader.SheetsReader") as mock_reader:
            mock_instance = Mock()
            mock_reader.return_value = mock_instance

            # Mock the specific methods that get_all_kpis() calls
            mock_instance.get_eod_data.return_value = get_simple_eod_data()
            mock_instance.get_front_kpi_data.return_value = get_simple_front_kpi_data()

            # Execute full flow
            kpis = get_all_kpis()

            # Validate all KPIs present
            assert "production_total" in kpis
            assert "collection_rate" in kpis
            assert "new_patients" in kpis
            assert "treatment_acceptance" in kpis
            assert "hygiene_reappointment" in kpis

            # Validate values are reasonable
            assert kpis["production_total"] is not None and kpis["production_total"] > 0
            assert (
                kpis["collection_rate"] is not None
                and 0 <= kpis["collection_rate"] <= 100
            )
            assert kpis["new_patients"] is not None and kpis["new_patients"] >= 0
            assert (
                kpis["treatment_acceptance"] is not None
                and 0 <= kpis["treatment_acceptance"] <= 100
            )
            assert (
                kpis["hygiene_reappointment"] is not None
                and 0 <= kpis["hygiene_reappointment"] <= 100
            )

    @pytest.mark.integration
    def test_partial_data_failure(self) -> None:
        """Test handling when some data sources fail."""
        with patch("backend.sheets_reader.SheetsReader") as mock_reader:
            mock_instance = Mock()
            mock_reader.return_value = mock_instance

            # EOD succeeds, Front KPI fails
            mock_instance.get_eod_data.return_value = get_simple_eod_data()
            mock_instance.get_front_kpi_data.return_value = None

            kpis = get_all_kpis()

            # EOD-based KPIs should work
            assert kpis["production_total"] is not None
            assert kpis["collection_rate"] is not None
            assert kpis["new_patients"] is not None

            # Front KPI-based should be None
            assert kpis["treatment_acceptance"] is None
            assert kpis["hygiene_reappointment"] is None

    @pytest.mark.integration
    def test_all_data_sources_fail(self) -> None:
        """Test handling when all data sources fail."""
        with patch("backend.sheets_reader.SheetsReader") as mock_reader:
            mock_instance = Mock()
            mock_reader.return_value = mock_instance

            # Both data sources fail
            mock_instance.get_eod_data.return_value = None
            mock_instance.get_front_kpi_data.return_value = None

            kpis = get_all_kpis()

            # All KPIs should be None
            assert kpis["production_total"] is None
            assert kpis["collection_rate"] is None
            assert kpis["new_patients"] is None
            assert kpis["treatment_acceptance"] is None
            assert kpis["hygiene_reappointment"] is None

    @pytest.mark.integration
    @pytest.mark.slow
    def test_performance_benchmark(self) -> None:
        """Test that KPI calculation completes within 1 second."""
        import time

        with patch("backend.sheets_reader.SheetsReader") as mock_reader:
            mock_instance = Mock()
            mock_reader.return_value = mock_instance

            # Fast mock responses
            mock_instance.get_eod_data.return_value = get_simple_eod_data()
            mock_instance.get_front_kpi_data.return_value = get_simple_front_kpi_data()

            start = time.time()
            kpis = get_all_kpis()
            duration = time.time() - start

            assert duration < 1.0  # Should complete in under 1 second
            assert kpis is not None

    @pytest.mark.integration
    def test_kpi_calculation_accuracy(self) -> None:
        """Test that KPI calculations are accurate with known values."""
        with patch("backend.sheets_reader.SheetsReader") as mock_reader:
            mock_instance = Mock()
            mock_reader.return_value = mock_instance

            # Create test data with known expected results
            test_eod_data = pd.DataFrame(
                {
                    "Date": ["2025-08-16"],
                    "total_production": [10000.00],
                    "total_collections": [9000.00],
                    "new_patients": [5],
                }
            )

            test_front_data = pd.DataFrame(
                {
                    "Date": ["2025-08-16"],
                    "total_hygiene_appointments": [20],
                    "patients_not_reappointed": [2],
                    "treatments_presented": [50000],
                    "treatments_scheduled": [40000],
                }
            )

            mock_instance.get_eod_data.return_value = test_eod_data
            mock_instance.get_front_kpi_data.return_value = test_front_data

            kpis = get_all_kpis()

            # Verify exact calculations
            assert kpis["production_total"] == 10000.00
            assert kpis["collection_rate"] == 90.0  # (9000/10000) * 100
            assert kpis["new_patients"] == 5
            assert kpis["treatment_acceptance"] == 80.0  # (40000/50000) * 100
            assert kpis["hygiene_reappointment"] == 90.0  # ((20-2)/20) * 100

    @pytest.mark.integration
    def test_error_propagation(self) -> None:
        """Test that errors are properly handled and don't crash the system."""
        with patch("backend.sheets_reader.SheetsReader") as mock_reader:
            mock_instance = Mock()
            mock_reader.return_value = mock_instance

            # Simulate an exception during data retrieval
            mock_instance.get_eod_data.side_effect = Exception("Network error")
            mock_instance.get_front_kpi_data.side_effect = Exception("Network error")

            # Should not raise exception, but return None values
            kpis = get_all_kpis()

            assert kpis is not None  # Function should still return a dict
            assert all(v is None for v in kpis.values())  # All values should be None
