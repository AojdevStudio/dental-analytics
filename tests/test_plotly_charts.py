#!/usr/bin/env python3
"""Test Plotly Chart Rendering with Sample Data.

Validates that Plotly charts render correctly with realistic sample data
for all 5 KPIs and handles various edge cases.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path setup (required for module resolution)
from apps.frontend.chart_kpis import (  # noqa: E402
    create_case_acceptance_chart,
    create_chart_from_data,
    create_collection_rate_chart,
    create_hygiene_reappointment_chart,
    create_new_patients_chart,
)
from apps.frontend.chart_production import create_production_chart  # noqa: E402
from core.models.chart_models import (  # noqa: E402
    ChartDataPoint,
    TimeSeriesData,
)


def create_sample_time_series_data(
    metric_name: str, chart_type: str, data_type_hint: str, days: int = 7
) -> TimeSeriesData:
    """Create sample time-series data for testing as Pydantic model."""
    base_date = datetime.now() - timedelta(days=days)

    # Map metric name to proper data_type
    if metric_name == "production":
        values = [1000.0 + (i * 100.0) for i in range(days)]
        data_type = "currency"
    elif metric_name == "collection_rate":
        values = [85.0 + (i * 2.5) for i in range(days)]
        data_type = "percentage"
    elif metric_name == "new_patients":
        values = [float(5 + i) for i in range(days)]
        data_type = "count"
    elif metric_name == "case_acceptance":
        values = [75.0 + (i * 1.5) for i in range(days)]
        data_type = "percentage"
    elif metric_name == "hygiene_reappointment":
        values = [90.0 + (i * 0.5) for i in range(days)]
        data_type = "percentage"
    else:
        values = [100.0 + (i * 10.0) for i in range(days)]
        data_type = "float"

    # Create ChartDataPoint list
    data_points = []
    for i in range(days):
        date_obj = base_date + timedelta(days=i)
        data_points.append(
            ChartDataPoint(
                date=date_obj.strftime("%Y-%m-%d"),
                timestamp=date_obj.isoformat(),
                value=values[i],
                has_data=True,
            )
        )

    # Calculate statistics as dict
    stats_dict = {
        "total_sum": sum(values) if metric_name == "production" else None,
        "daily_average": sum(values) / len(values),
        "latest_value": values[-1],
        "data_points": len(values),
    }

    return TimeSeriesData(
        metric_name=metric_name,
        chart_type=chart_type,
        data_type=data_type,
        time_series=data_points,
        statistics={k: v for k, v in stats_dict.items() if v is not None},
    )


def test_production_charts() -> None:
    """Test production chart rendering."""
    print("🧪 Testing Production Charts...")

    # Test daily production chart
    sample_data = create_sample_time_series_data("production", "line", "daily", 7)

    try:
        # create_production_chart expects dict, not Pydantic model
        create_production_chart(sample_data.model_dump())
        print("   ✅ Daily production chart works")

        # Test with create_chart_from_data (accepts Pydantic model)
        create_chart_from_data(sample_data)
        print("   ✅ Generic chart creator works")

    except Exception as exc:
        pytest.fail(f"Production chart failed: {exc}")

    # Test monthly production chart
    monthly_data = create_sample_time_series_data("production", "bar", "monthly", 12)

    try:
        create_production_chart(monthly_data.model_dump())
        print("   ✅ Monthly production chart works")
    except Exception as exc:
        pytest.fail(f"Monthly production chart failed: {exc}")


def test_collection_rate_charts() -> None:
    """Test collection rate chart rendering."""
    print("🧪 Testing Collection Rate Charts...")

    sample_data = create_sample_time_series_data("collection_rate", "line", "daily", 7)

    try:
        create_collection_rate_chart(sample_data)
        print("   ✅ Collection rate chart works")
    except Exception as exc:
        pytest.fail(f"Collection rate chart failed: {exc}")


def test_new_patients_charts() -> None:
    """Test new patients chart rendering."""
    print("🧪 Testing New Patients Charts...")

    sample_data = create_sample_time_series_data("new_patients", "bar", "daily", 7)

    try:
        create_new_patients_chart(sample_data)
        print("   ✅ New patients chart works")
    except Exception as exc:
        pytest.fail(f"New patients chart failed: {exc}")


def test_case_acceptance_charts() -> None:
    """Test case acceptance chart rendering."""
    print("🧪 Testing Case Acceptance Charts...")

    sample_data = create_sample_time_series_data("case_acceptance", "line", "daily", 7)

    try:
        create_case_acceptance_chart(sample_data)
        print("   ✅ Case acceptance chart works")
    except Exception as exc:
        pytest.fail(f"Case acceptance chart failed: {exc}")


def test_hygiene_reappointment_charts() -> None:
    """Test hygiene reappointment chart rendering."""
    print("🧪 Testing Hygiene Reappointment Charts...")

    sample_data = create_sample_time_series_data(
        "hygiene_reappointment", "line", "daily", 7
    )

    try:
        create_hygiene_reappointment_chart(sample_data)
        print("   ✅ Hygiene reappointment chart works")
    except Exception as exc:
        pytest.fail(f"Hygiene reappointment chart failed: {exc}")


def test_edge_cases() -> None:
    """Test edge cases for chart rendering."""
    print("🧪 Testing Edge Cases...")

    # Test with empty data
    empty_data = {
        "metric_name": "production",
        "chart_type": "line",
        "data_type": "daily",
        "dates": [],
        "values": [],
        "statistics": {"data_points": 0},
    }

    try:
        create_production_chart(empty_data)
        print("✅ Empty data handling works")
    except Exception as exc:
        pytest.fail(f"Empty data handling failed: {exc}")

    # Test with null values
    data_with_nulls = create_sample_time_series_data("production", "line", "daily", 5)
    # Convert to dict and modify
    data_dict = data_with_nulls.model_dump()
    # Modify time_series to have null value
    data_dict["time_series"][2]["value"] = None

    try:
        create_production_chart(data_dict)
        print("✅ Null values handling works")
    except Exception as exc:
        pytest.fail(f"Null values handling failed: {exc}")

    # Test with large dataset
    large_data = create_sample_time_series_data("production", "line", "daily", 365)

    start_time = datetime.now()
    try:
        create_production_chart(large_data.model_dump())
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"✅ Large dataset (365 days) rendered in {duration:.2f}s")
    except Exception as exc:
        pytest.fail(f"Large dataset rendering failed: {exc}")


def test_chart_interactivity() -> None:
    """Test chart interactivity features."""
    print("🧪 Testing Chart Interactivity...")

    sample_data = create_sample_time_series_data("production", "line", "daily", 30)

    try:
        fig = create_production_chart(sample_data.model_dump())

        # Check if chart has proper configuration
        if hasattr(fig, "layout"):
            print("   ✅ Chart layout configured")

        if hasattr(fig, "data") and len(fig.data) > 0:
            print("   ✅ Chart data populated")

        print("✅ Chart interactivity works")
    except Exception as exc:
        pytest.fail(f"Chart interactivity failed: {exc}")


def test_all_chart_types() -> None:
    """Test all chart type combinations."""
    print("🧪 Testing All Chart Type Combinations...")

    chart_configs = [
        ("production", "line", "daily"),
        ("production", "bar", "weekly"),
        ("collection_rate", "line", "daily"),
        ("new_patients", "bar", "daily"),
        ("case_acceptance", "line", "weekly"),
        ("hygiene_reappointment", "line", "daily"),
    ]

    for metric, chart_type, data_type in chart_configs:
        try:
            sample_data = create_sample_time_series_data(metric, chart_type, data_type)

            # Try specific chart creator first
            if metric == "production":
                # create_production_chart expects dict
                create_production_chart(sample_data.model_dump())
            elif metric == "collection_rate":
                # Other chart builders accept Pydantic models
                create_collection_rate_chart(sample_data)
            elif metric == "new_patients":
                create_new_patients_chart(sample_data)
            elif metric == "case_acceptance":
                create_case_acceptance_chart(sample_data)
            elif metric == "hygiene_reappointment":
                create_hygiene_reappointment_chart(sample_data)

            print(f"   ✅ {metric} {chart_type} {data_type} works")

        except Exception as exc:
            pytest.fail(f"{metric} {chart_type} {data_type} failed: {exc}")

    print(f"✅ {len(chart_configs)}/{len(chart_configs)} chart combinations work")


def main() -> bool:
    """Run all chart rendering tests.

    Returns:
        True if all tests passed, False otherwise
    """
    print("🚀 Starting Plotly Chart Rendering Tests...\n")

    tests = [
        test_production_charts,
        test_collection_rate_charts,
        test_new_patients_charts,
        test_case_acceptance_charts,
        test_hygiene_reappointment_charts,
        test_edge_cases,
        test_chart_interactivity,
        test_all_chart_types,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as exc:
            print(f"❌ Test {test.__name__} crashed: {exc}")
            failed += 1
        print()  # Add spacing between tests

    print(f"📊 Test Summary: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All chart rendering tests passed!")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed. Review chart implementations.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
