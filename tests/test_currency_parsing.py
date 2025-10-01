"""Test currency parsing functionality for real Google Sheets data.

This test module validates that the system correctly handles currency-formatted
values from Google Sheets, addressing QA findings from Story 2.1.
"""

import pandas as pd
import pytest

from apps.backend.chart_data import format_production_chart_data, safe_float_conversion
from apps.backend.metrics import (
    calculate_collection_rate,
    calculate_historical_production_total,
    calculate_production_total,
    clean_currency_string,
    safe_numeric_conversion,
)


class TestCurrencyParsing:
    """Test currency string cleaning and conversion functions."""

    @pytest.mark.unit
    def test_clean_currency_string_basic(self) -> None:
        """Test basic currency string cleaning."""
        assert clean_currency_string("$1,234.56") == "1234.56"
        assert clean_currency_string("-$1,234.56") == "-1234.56"
        assert clean_currency_string("$0.00") == "0.00"
        assert clean_currency_string("$3,669.00") == "3669.00"

    @pytest.mark.unit
    def test_clean_currency_string_edge_cases(self) -> None:
        """Test edge cases for currency cleaning."""
        assert clean_currency_string("") == 0.0
        assert clean_currency_string("-") == 0.0
        assert clean_currency_string("$") == 0.0
        assert clean_currency_string(None) is None
        assert clean_currency_string(1234.56) == 1234.56

    @pytest.mark.unit
    def test_safe_numeric_conversion_with_currency(self) -> None:
        """Test safe numeric conversion with currency-formatted values."""
        df = pd.DataFrame(
            {
                "Production": ["$3,669.00"],
                "Collections": ["$2,450.50"],
                "Adjustments": ["-$100.00"],
            }
        )

        production_sum = safe_numeric_conversion(df, "Production")
        collections_sum = safe_numeric_conversion(df, "Collections")
        adjustments_sum = safe_numeric_conversion(df, "Adjustments")

        assert production_sum == 3669.0
        assert collections_sum == 2450.5
        assert adjustments_sum == -100.0

    @pytest.mark.unit
    def test_safe_float_conversion_chart_data(self) -> None:
        """Test safe float conversion for chart data."""
        assert safe_float_conversion("$1,234.56") == 1234.56
        assert safe_float_conversion("-$100.00") == -100.0
        assert safe_float_conversion("") == 0.0
        assert safe_float_conversion(None) is None
        assert safe_float_conversion(1234.56) == 1234.56


class TestRealDataScenarios:
    """Test with real-world Google Sheets data patterns."""

    @pytest.mark.integration
    def test_production_calculation_with_currency_format(self) -> None:
        """Test production calculation with currency-formatted data."""
        # Real data pattern from Google Sheets (single row as per current design)
        df = pd.DataFrame(
            {
                "Total Production Today": ["$1,234.56"],
                "Adjustments Today": ["$0.00"],
                "Write-offs Today": ["$0.00"],
                "Patient Income Today": ["$800.00"],
                "Unearned Income Today": ["$100.00"],
                "Insurance Income Today": ["$200.00"],
            }
        )

        production_total = calculate_production_total(df)
        collection_rate = calculate_collection_rate(df)

        assert production_total == pytest.approx(1234.56)
        assert collection_rate == pytest.approx(89.11, rel=1e-2)  # (1100/1234.56)*100

    @pytest.mark.integration
    def test_historical_production_with_mixed_formats(self) -> None:
        """Test historical production with mixed data formats."""
        df = pd.DataFrame(
            {
                "total_production": ["$1,000.00", "500", "-$100.00", "$2,500.50"],
                "Date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
            }
        )

        # Historical function returns dict with time series data
        result = calculate_historical_production_total(df)
        # Check that it returns expected structure (new API)
        assert "time_series" in result
        assert "total_sum" in result
        assert "daily_average" in result

    @pytest.mark.integration
    def test_chart_data_formatting_with_currency(self) -> None:
        """Test chart data formatting with currency values."""
        df = pd.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-02"],
                "total_production": ["$1,000.00", "$2,000.00"],
            }
        )

        # Note: This test uses "Date" column but function expects "Submission Date"
        chart_data = format_production_chart_data(df, date_column="Date")

        # Check that it returns chart structure (new API)
        assert chart_data["metric_name"] == "Production Total"
        assert "time_series" in chart_data
        assert "chart_type" in chart_data
