# Unit tests for metrics calculations


import pandas as pd
import pytest

from backend.metrics import MetricsCalculator


class TestMetricsCalculator:
    """Test suite for MetricsCalculator class."""

    def test_calculate_production_total_success(self) -> None:
        """Test successful production total calculation."""
        # Arrange
        test_data = pd.DataFrame({"total_production": [1000, 2000, 1500]})

        # Act
        result = MetricsCalculator.calculate_production_total(test_data)

        # Assert
        assert result == 4500.0
        assert isinstance(result, float)

    def test_calculate_production_total_with_decimals(self) -> None:
        """Test production calculation with decimal values."""
        # Arrange
        test_data = pd.DataFrame({"total_production": [1000.50, 2000.25, 1500.75]})

        # Act
        result = MetricsCalculator.calculate_production_total(test_data)

        # Assert
        assert result == 4501.5

    def test_calculate_production_total_empty_dataframe(self) -> None:
        """Test production calculation with empty DataFrame."""
        # Arrange
        empty_df = pd.DataFrame()

        # Act
        result = MetricsCalculator.calculate_production_total(empty_df)

        # Assert
        assert result is None

    def test_calculate_production_total_none_input(self) -> None:
        """Test production calculation with None input."""
        # Act
        result = MetricsCalculator.calculate_production_total(None)  # type: ignore[arg-type]

        # Assert
        assert result is None

    def test_calculate_production_total_missing_column(self) -> None:
        """Test production calculation with missing column."""
        # Arrange
        test_data = pd.DataFrame({"other_column": [1, 2, 3]})

        # Act
        result = MetricsCalculator.calculate_production_total(test_data)

        # Assert
        assert result is None

    def test_calculate_production_total_invalid_values(self) -> None:
        """Test production calculation with invalid string values."""
        # Arrange
        test_data = pd.DataFrame({"total_production": ["invalid", "data", "values"]})

        # Act
        result = MetricsCalculator.calculate_production_total(test_data)

        # Assert
        assert (
            result == 0.0
        )  # pd.to_numeric with errors='coerce' converts to NaN, sum is 0

    def test_calculate_production_total_mixed_values(self) -> None:
        """Test production calculation with mix of valid and invalid values."""
        # Arrange
        test_data = pd.DataFrame({"total_production": [1000, "invalid", 2000, None]})

        # Act
        result = MetricsCalculator.calculate_production_total(test_data)

        # Assert
        assert result == 3000.0  # Only valid numbers are summed

    def test_calculate_collection_rate_success(self) -> None:
        """Test successful collection rate calculation."""
        # Arrange
        test_data = pd.DataFrame(
            {"total_production": [1000, 2000], "total_collections": [900, 1800]}
        )

        # Act
        result = MetricsCalculator.calculate_collection_rate(test_data)

        # Assert
        assert result == 90.0  # (2700/3000) * 100
        assert isinstance(result, float)

    def test_calculate_collection_rate_perfect_collection(self) -> None:
        """Test collection rate with 100% collection."""
        # Arrange
        test_data = pd.DataFrame(
            {"total_production": [1000, 2000], "total_collections": [1000, 2000]}
        )

        # Act
        result = MetricsCalculator.calculate_collection_rate(test_data)

        # Assert
        assert result == 100.0

    def test_calculate_collection_rate_zero_production(self) -> None:
        """Test collection rate with zero production (division by zero)."""
        # Arrange
        test_data = pd.DataFrame(
            {"total_production": [0, 0, 0], "total_collections": [100, 200, 300]}
        )

        # Act
        result = MetricsCalculator.calculate_collection_rate(test_data)

        # Assert
        assert result is None

    def test_calculate_collection_rate_empty_dataframe(self) -> None:
        """Test collection rate calculation with empty DataFrame."""
        # Arrange
        empty_df = pd.DataFrame()

        # Act
        result = MetricsCalculator.calculate_collection_rate(empty_df)

        # Assert
        assert result is None

    def test_calculate_collection_rate_none_input(self) -> None:
        """Test collection rate calculation with None input."""
        # Act
        result = MetricsCalculator.calculate_collection_rate(None)  # type: ignore[arg-type]

        # Assert
        assert result is None

    def test_calculate_collection_rate_missing_production_column(self) -> None:
        """Test collection rate with missing production column."""
        # Arrange
        test_data = pd.DataFrame({"total_collections": [100, 200, 300]})

        # Act
        result = MetricsCalculator.calculate_collection_rate(test_data)

        # Assert
        assert result is None

    def test_calculate_collection_rate_missing_collections_column(self) -> None:
        """Test collection rate with missing collections column."""
        # Arrange
        test_data = pd.DataFrame({"total_production": [1000, 2000, 1500]})

        # Act
        result = MetricsCalculator.calculate_collection_rate(test_data)

        # Assert
        assert result is None

    def test_calculate_collection_rate_invalid_values(self) -> None:
        """Test collection rate with invalid string values."""
        # Arrange
        test_data = pd.DataFrame(
            {
                "total_production": ["invalid", "data"],
                "total_collections": ["invalid", "data"],
            }
        )

        # Act
        result = MetricsCalculator.calculate_collection_rate(test_data)

        # Assert
        assert result is None  # Division by zero when both convert to 0

    def test_calculate_collection_rate_decimal_precision(self) -> None:
        """Test collection rate with decimal precision."""
        # Arrange
        test_data = pd.DataFrame(
            {
                "total_production": [1000.33, 2000.67],
                "total_collections": [950.30, 1850.60],
            }
        )

        # Act
        result = MetricsCalculator.calculate_collection_rate(test_data)

        # Assert
        assert result is not None  # Guard clause for type safety
        expected = (2800.9 / 3001.0) * 100  # approximately 93.33%
        assert abs(result - expected) < 0.01

    @pytest.mark.parametrize(
        "production,collections,expected",
        [
            ([1000], [1000], 100.0),
            ([2000], [1000], 50.0),
            ([500, 500], [300, 200], 50.0),
            ([1000, 0], [800, 0], 80.0),
        ],
    )
    def test_calculate_collection_rate_parametrized(
        self, production: list[int], collections: list[int], expected: float
    ) -> None:
        """Test collection rate with various parameter combinations."""
        # Arrange
        test_data = pd.DataFrame(
            {"total_production": production, "total_collections": collections}
        )

        # Act
        result = MetricsCalculator.calculate_collection_rate(test_data)

        # Assert
        assert result is not None  # Guard clause for type safety
        assert abs(result - expected) < 0.01
