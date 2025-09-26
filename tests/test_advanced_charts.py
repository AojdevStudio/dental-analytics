"""Advanced Chart Testing Suite for Story 2.3.

Tests chart creation with enhanced features:
- Time-based aggregation (weekly, monthly)
- Trend analysis with R² calculations
- Performance benchmarks under 3 seconds
- Interactive controls and range selectors
"""

import time
from datetime import datetime, timedelta

import pandas as pd

# Import chart functions from the refactored modules
from apps.backend.chart_data import aggregate_to_monthly, aggregate_to_weekly
from apps.frontend.chart_production import create_production_chart


def create_test_data(days: int = 30) -> dict:
    """Create test production data for chart testing."""
    base_date = datetime.now() - timedelta(days=days)
    dates = [(base_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

    # Generate realistic production values with some variation
    # Using hash for deterministic but varied test data
    base_production = 8000
    values = [
        base_production + (hash(str(i)) % 5000) - 2000 for i in range(days)
    ]  # $6K-$11K range

    return {
        "dates": dates,
        "values": values,
        "statistics": {
            "total": sum(values),
            "average": sum(values) / len(values),
            "minimum": min(values),
            "maximum": max(values),
            "data_points": len(values),
        },
        "metadata": {"test_data": True},
    }


def test_time_aggregation():
    """Test weekly and monthly data aggregation features."""
    print("📊 Testing time-based aggregation...")

    test_data = create_test_data(30)  # 30 days of data

    # Test weekly aggregation
    weekly_data = aggregate_to_weekly(test_data)
    assert "aggregation" in weekly_data
    assert weekly_data["aggregation"] == "weekly"
    assert len(weekly_data["dates"]) < len(
        test_data["dates"]
    )  # Should have fewer data points
    print(
        f"✅ Weekly aggregation: {len(test_data['dates'])} days → "
        f"{len(weekly_data['dates'])} weeks"
    )

    # Test monthly aggregation
    monthly_data = aggregate_to_monthly(test_data)
    assert "aggregation" in monthly_data
    assert monthly_data["aggregation"] == "monthly"
    assert len(monthly_data["dates"]) <= 2  # Should have 1-2 months for 30 days
    print(
        f"✅ Monthly aggregation: {len(test_data['dates'])} days → "
        f"{len(monthly_data['dates'])} months"
    )

    return True


def test_trend_analysis():
    """Test trend line calculation and R² metrics."""
    print("📈 Testing trend analysis features...")

    # Create upward trending data
    test_data = create_test_data(21)  # 3 weeks
    for i, val in enumerate(test_data["values"]):
        test_data["values"][i] = val + (i * 100)  # Add upward trend

    # Test chart creation with trends
    chart = create_production_chart(test_data, show_trend=True)

    # Verify chart has trend trace
    trend_traces = [trace for trace in chart.data if "Trend" in trace.name]
    assert len(trend_traces) > 0, "No trend line found in chart"

    # Verify trend annotation exists
    annotations = chart.layout.annotations
    trend_annotations = [
        ann for ann in annotations if "R²" in ann.text or "trend" in ann.text.lower()
    ]
    assert len(trend_annotations) > 0, "No trend annotations found"

    print("✅ Trend analysis working: R² calculation and trend lines")
    return True


def format_production_chart_data(df: pd.DataFrame) -> dict:
    """Convert DataFrame to chart-ready format."""
    return {
        "dates": df.index.strftime("%Y-%m-%d").tolist(),
        "values": df["production"].tolist(),
        "statistics": {
            "total": df["production"].sum(),
            "average": df["production"].mean(),
            "minimum": df["production"].min(),
            "maximum": df["production"].max(),
            "data_points": len(df),
        },
        "metadata": {"source": "test_data"},
    }


def test_performance_benchmarks():
    """Test chart creation performance under 3-second requirement."""
    print("⚡ Testing performance benchmarks...")

    # Create larger dataset for performance testing
    large_dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
    large_data = pd.DataFrame(
        {"production": [8000 + (i % 100) * 50 for i in range(len(large_dates))]},
        index=large_dates,
    )

    # Format chart data
    chart_data = format_production_chart_data(large_data)

    # Time chart creation
    start_time = time.time()

    # Create chart with all advanced features
    create_production_chart(chart_data, show_trend=True, timeframe="daily")

    load_time = time.time() - start_time

    assert load_time < 3.0, f"Chart load time {load_time:.2f}s exceeds 3s requirement"
    print(f"✅ Performance test passed: Chart loaded in {load_time:.2f} seconds")

    # Test with different timeframes
    for timeframe in ["weekly", "monthly"]:
        start_time = time.time()
        create_production_chart(chart_data, show_trend=True, timeframe=timeframe)
        load_time = time.time() - start_time
        assert load_time < 3.0, f"{timeframe} chart exceeded 3s: {load_time:.2f}s"
        print(f"✅ {timeframe.capitalize()} chart loaded in {load_time:.2f} seconds")

    return True


def test_chart_interactions():
    """Test interactive chart features and controls."""
    print("🎮 Testing chart interactions...")

    test_data = create_test_data(14)  # 2 weeks

    # Create chart with all interactive features
    chart = create_production_chart(
        test_data, show_trend=True, show_range_selector=True
    )

    # Verify range selector is present
    x_axis = chart.layout.xaxis
    assert hasattr(x_axis, "rangeselector"), "Range selector not found"
    assert len(x_axis.rangeselector.buttons) > 0, "No range selector buttons"

    # Verify zoom functionality is enabled
    assert chart.layout.dragmode == "zoom", "Zoom functionality not enabled"

    # Verify hover mode is set for better UX
    assert chart.layout.hovermode == "x unified", "Hover mode not optimized"

    print("✅ Interactive features verified: range selector, zoom, hover")
    return True


def test_visual_styling():
    """Test brand compliance and visual styling."""
    print("🎨 Testing visual styling and brand compliance...")

    test_data = create_test_data(7)  # 1 week

    chart = create_production_chart(test_data)

    # Verify brand colors are used
    primary_trace = chart.data[0]
    assert primary_trace.line.color in [
        "#007E9E",
        "#142D54",
    ], "Brand colors not applied"

    # Verify layout styling
    layout = chart.layout
    assert layout.plot_bgcolor == "white", "Background color not set correctly"
    assert layout.font.family == "Arial, sans-serif", "Font family not set"

    # Verify title styling
    assert "Production" in layout.title.text, "Chart title missing or incorrect"

    print("✅ Visual styling verified: brand colors, fonts, layout")
    return True


def test_error_handling():
    """Test error handling with invalid or missing data."""
    print("🛡️ Testing error handling...")

    # Test with empty data
    empty_data = {"dates": [], "values": []}
    chart = create_production_chart(empty_data)
    assert chart is not None, "Chart creation failed with empty data"

    # Test with mismatched data lengths
    bad_data = {"dates": ["2024-01-01", "2024-01-02"], "values": [1000]}
    chart = create_production_chart(bad_data)
    assert chart is not None, "Chart creation failed with mismatched data"

    # Test with None data
    chart = create_production_chart(None)
    assert chart is not None, "Chart creation failed with None data"

    print("✅ Error handling verified: graceful degradation")
    return True


def run_all_tests():
    """Run complete test suite for Story 2.3 advanced chart features."""
    print("🚀 Starting Story 2.3 Advanced Chart Testing Suite")
    print("=" * 60)

    tests = [
        ("Time Aggregation", test_time_aggregation),
        ("Trend Analysis", test_trend_analysis),
        ("Performance Benchmarks", test_performance_benchmarks),
        ("Chart Interactions", test_chart_interactions),
        ("Visual Styling", test_visual_styling),
        ("Error Handling", test_error_handling),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n🔄 Running {test_name}...")
            result = test_func()
            if result:
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print(
            "\n🎉 All Story 2.3 tests passed! "
            "Advanced chart features working correctly."
        )
    else:
        print(f"\n⚠️ {failed} tests failed. Please review and fix issues.")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
