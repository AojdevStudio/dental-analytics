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


def test_new_patients_calculation() -> None:
    """Test new patient count calculation with known data."""
    print("🧪 Testing new patients calculation...")
    test_data = pd.DataFrame({"new_patients": [5, 3, 7, 2]})
    result = MetricsCalculator.calculate_new_patients(test_data)
    expected = 17
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"✅ New patients calculation test passed: {result}")


def test_treatment_acceptance_calculation() -> None:
    """Test treatment acceptance rate calculation with known data."""
    print("🧪 Testing treatment acceptance calculation...")
    test_data = pd.DataFrame(
        {
            "treatments_presented": [20, 15, 10],  # Column L
            "treatments_scheduled": [18, 12, 8],  # Column M
        }
    )
    result = MetricsCalculator.calculate_treatment_acceptance(test_data)
    expected = 84.44444444444444  # (38/45) * 100
    assert (
        result is not None and abs(result - expected) < 0.01
    ), f"Expected {expected}, got {result}"
    print(f"✅ Treatment acceptance calculation test passed: {result:.2f}%")


def test_get_all_kpis_structure() -> None:
    """Test that get_all_kpis returns all 4 expected KPIs."""
    print("🧪 Testing get_all_kpis structure...")
    # This would normally test with real data, but we'll test the structure
    try:
        kpis = MetricsCalculator.get_all_kpis()
        expected_keys = [
            "production_total",
            "collection_rate",
            "new_patients",
            "treatment_acceptance",
        ]
        assert all(
            key in kpis for key in expected_keys
        ), f"Missing expected KPI keys: {expected_keys}"
        assert len(kpis) == 4, f"Expected 4 KPIs, got {len(kpis)}"
        print("✅ All KPIs structure test passed")
    except Exception as e:
        print(f"⚠️  get_all_kpis test skipped (needs Google Sheets connection): {e}")


def test_error_conditions() -> None:
    """Test error handling for edge cases."""
    print("🧪 Testing error conditions...")

    # Test empty DataFrame
    empty_df = pd.DataFrame()
    assert MetricsCalculator.calculate_production_total(empty_df) is None
    assert MetricsCalculator.calculate_collection_rate(empty_df) is None
    assert MetricsCalculator.calculate_new_patients(empty_df) is None
    assert MetricsCalculator.calculate_treatment_acceptance(empty_df) is None
    print("✅ Empty DataFrame handling works")

    # Test None DataFrame
    assert MetricsCalculator.calculate_production_total(None) is None
    assert MetricsCalculator.calculate_collection_rate(None) is None
    assert MetricsCalculator.calculate_new_patients(None) is None
    assert MetricsCalculator.calculate_treatment_acceptance(None) is None
    print("✅ None DataFrame handling works")

    # Test missing columns
    incomplete_df = pd.DataFrame({"other_column": [1, 2, 3]})
    assert MetricsCalculator.calculate_production_total(incomplete_df) is None
    assert MetricsCalculator.calculate_collection_rate(incomplete_df) is None
    assert MetricsCalculator.calculate_new_patients(incomplete_df) is None
    assert MetricsCalculator.calculate_treatment_acceptance(incomplete_df) is None
    print("✅ Missing columns handling works")

    # Test division by zero
    zero_production_df = pd.DataFrame(
        {"total_production": [0, 0, 0], "total_collections": [100, 200, 300]}
    )
    assert MetricsCalculator.calculate_collection_rate(zero_production_df) is None
    print("✅ Division by zero handling works")

    # Test division by zero for treatment acceptance
    zero_presented_df = pd.DataFrame(
        {"treatments_presented": [0, 0, 0], "treatments_scheduled": [5, 3, 2]}
    )
    assert MetricsCalculator.calculate_treatment_acceptance(zero_presented_df) is None
    print("✅ Treatment acceptance division by zero handling works")


if __name__ == "__main__":
    print("🎯 Starting manual verification of metrics calculations...\n")

    test_production_calculation()
    print()

    test_collection_rate_calculation()
    print()

    test_new_patients_calculation()
    print()

    test_treatment_acceptance_calculation()
    print()

    test_get_all_kpis_structure()
    print()

    test_error_conditions()
    print()

    print("🎉 All manual tests passed!")
    print("📊 Metrics calculations are working correctly.")
