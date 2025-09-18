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

        production_sum = safe_numeric_conversion(df["Production"]).sum()
        collections_sum = safe_numeric_conversion(df["Collections"]).sum()
        adjustments_sum = safe_numeric_conversion(df["Adjustments"]).sum()

        assert production_sum == 3669.0
        assert collections_sum == 2450.5
        assert adjustments_sum == -100.0

    @pytest.mark.unit
    def test_safe_float_conversion_chart_data(self) -> None:
        """Test safe float conversion for chart data."""
        assert safe_float_conversion("$1,234.56") == 1234.56
        assert safe_float_conversion("-$100.00") == -100.0
        assert safe_float_conversion("") == 0.0
        assert safe_float_conversion(None) == 0.0
        assert safe_float_conversion(1234.56) == 1234.56


class TestRealDataScenarios:
    """Test with real-world Google Sheets data patterns."""

    @pytest.mark.integration
    def test_production_calculation_with_currency_format(self) -> None:
        """Test production calculation with currency-formatted data."""
        # Real data pattern from Google Sheets
        df = pd.DataFrame(
            {
                "total_production": ["$3,669.00", "$2,450.50", "$1,234.56"],
                "total_collections": ["$3,000.00", "$2,200.00", "$1,100.00"],
            }
        )

        production_total = calculate_production_total(df)
        collection_rate = calculate_collection_rate(df)

        assert production_total == 7354.06  # 3669 + 2450.5 + 1234.56
        assert collection_rate == pytest.approx(85.33, rel=1e-2)  # (6300/7354.06)*100

    @pytest.mark.integration
    def test_historical_production_with_mixed_formats(self) -> None:
        """Test historical production with mixed data formats."""
        df = pd.DataFrame(
            {
                "total_production": ["$1,000.00", "500", "-$100.00", "$2,500.50"],
                "Date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
            }
        )

        total = calculate_historical_production_total(df)
        assert total == 3900.5  # 1000 + 500 - 100 + 2500.5

    @pytest.mark.integration
    def test_chart_data_formatting_with_currency(self) -> None:
        """Test chart data formatting with currency values."""
        df = pd.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-02"],
                "total_production": ["$1,000.00", "$2,000.00"],
            }
        )

        chart_data = format_production_chart_data(df)

        assert len(chart_data) == 2
        assert chart_data[0]["Date"] == "2023-01-01"
        assert chart_data[0]["Production"] == 1000.0
        assert chart_data[1]["Date"] == "2023-01-02"
        assert chart_data[1]["Production"] == 2000.0
