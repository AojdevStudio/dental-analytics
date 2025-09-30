#!/usr/bin/env python3
"""Verification script for chart import fixes."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def verify_imports():
    """Verify all required imports are working."""
    print("🔍 Verifying imports...")

    try:
        # Test chart_utils imports
        from apps.frontend.chart_utils import (
            add_pattern_annotation,
            add_trend_line_to_figure,
            format_currency_hover,
            handle_empty_data,
        )

        print("✅ chart_utils helper functions imported successfully")

        # Test that wrapper functions work
        import plotly.graph_objects as go

        fig = go.Figure()
        test_values = [100, 110, 120]
        test_dates = ["2025-01-01", "2025-01-02", "2025-01-03"]

        # Test wrapper functions
        add_trend_line_to_figure(fig, test_dates, test_values)
        add_pattern_annotation(fig, test_values)
        formatted = format_currency_hover(1500)
        empty_fig = handle_empty_data("Test")

        if formatted != "$1.5K":
            raise AssertionError("Unexpected currency formatting result")
        if empty_fig.layout.title.text != "Test - No Data":
            raise AssertionError("Empty figure title mismatch")

        print(f"✅ Wrapper functions executed (sample format: {formatted})")

        # Test chart_production imports
        from apps.frontend.chart_production import create_production_chart

        assert callable(create_production_chart)
        print("✅ chart_production imported successfully")

        # Test chart_kpis imports
        from apps.frontend.chart_kpis import create_chart_from_data

        assert callable(create_chart_from_data)
        print("✅ chart_kpis imported successfully")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def verify_chart_creation():
    """Verify charts can be created with empty data."""
    print("\n📊 Verifying chart creation...")

    try:
        from apps.frontend.chart_production import create_production_chart

        # Create test data
        empty_data = {
            "time_series": [],
            "format_options": {},
        }

        # Try to create a chart
        fig = create_production_chart(empty_data)
        print(f"✅ Empty production chart created: {fig.layout.title.text}")

        # Test with some data
        test_data = {
            "time_series": [
                {"date": "2025-01-01", "value": 1000},
                {"date": "2025-01-02", "value": 1500},
            ],
            "format_options": {"line_color": "#007E9E"},
        }

        fig = create_production_chart(test_data, show_trend=True)
        print(f"✅ Production chart with data created: {len(fig.data)} traces")

        return True

    except Exception as e:
        print(f"❌ Chart creation error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all verification checks."""
    print("🚀 Starting chart import fix verification...\n")

    all_passed = True

    # Check imports
    if not verify_imports():
        all_passed = False

    # Check chart creation
    if not verify_chart_creation():
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL VERIFICATIONS PASSED!")
        print("\n💡 Next steps:")
        print("1. Run: uv run streamlit run apps/frontend/app.py")
        print("2. Navigate to http://localhost:8501")
        print("3. Verify all 5 KPI tabs render correctly")
        print("4. Switch between Baytown and Humble locations")
        print("5. Check that charts display or show 'No data' gracefully")
    else:
        print("❌ Some verifications failed. Please review the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
