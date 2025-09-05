# Manual verification script for metrics calculations
import pandas as pd

from backend.metrics import MetricsCalculator


def test_production_calculation() -> None:
    """Test production total calculation with known data."""
    print("🧪 Testing production total calculation...")
    test_data = pd.DataFrame({"total_production": [1000, 2000, 1500]})
    result = MetricsCalculator.calculate_production_total(test_data)
    expected = 4500
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"✅ Production calculation test passed: {result}")


def test_collection_rate_calculation() -> None:
    """Test collection rate calculation with known data."""
    print("🧪 Testing collection rate calculation...")
    test_data = pd.DataFrame(
        {"total_production": [1000, 2000], "total_collections": [900, 1800]}
    )
    result = MetricsCalculator.calculate_collection_rate(test_data)
    expected = 90.0  # (2700/3000) * 100
    assert (
        result is not None and abs(result - expected) < 0.01
    ), f"Expected {expected}, got {result}"
    print(f"✅ Collection rate calculation test passed: {result}%")


def test_error_conditions() -> None:
    """Test error handling for edge cases."""
    print("🧪 Testing error conditions...")

    # Test empty DataFrame
    empty_df = pd.DataFrame()
    assert MetricsCalculator.calculate_production_total(empty_df) is None
    assert MetricsCalculator.calculate_collection_rate(empty_df) is None
    print("✅ Empty DataFrame handling works")

    # Test None DataFrame
    assert MetricsCalculator.calculate_production_total(None) is None
    assert MetricsCalculator.calculate_collection_rate(None) is None
    print("✅ None DataFrame handling works")

    # Test missing columns
    incomplete_df = pd.DataFrame({"other_column": [1, 2, 3]})
    assert MetricsCalculator.calculate_production_total(incomplete_df) is None
    assert MetricsCalculator.calculate_collection_rate(incomplete_df) is None
    print("✅ Missing columns handling works")

    # Test division by zero
    zero_production_df = pd.DataFrame(
        {"total_production": [0, 0, 0], "total_collections": [100, 200, 300]}
    )
    assert MetricsCalculator.calculate_collection_rate(zero_production_df) is None
    print("✅ Division by zero handling works")


if __name__ == "__main__":
    print("🎯 Starting manual verification of metrics calculations...\n")

    test_production_calculation()
    print()

    test_collection_rate_calculation()
    print()

    test_error_conditions()
    print()

    print("🎉 All manual tests passed!")
    print("📊 Metrics calculations are working correctly.")
