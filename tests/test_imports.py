"""Test that all critical imports work correctly."""


def test_chart_utils_imports():
    """Verify all chart_utils functions can be imported."""
    from apps.frontend.chart_utils import (
        add_pattern_annotation,
        add_trend_line_to_figure,
        add_trend_pattern_annotation,
        apply_alpha_to_color,
        calculate_trend_line,
        format_currency_hover,
        handle_empty_data,
        parse_currency_string,
        safe_float_conversion,
    )

    assert callable(add_trend_line_to_figure)
    assert callable(calculate_trend_line)
    assert callable(format_currency_hover)
    assert callable(handle_empty_data)
    assert callable(parse_currency_string)
    assert callable(safe_float_conversion)
    assert callable(add_pattern_annotation)
    assert callable(add_trend_pattern_annotation)
    assert callable(apply_alpha_to_color)


def test_chart_kpis_imports():
    """Verify chart_kpis can import all dependencies."""
    from apps.frontend.chart_kpis import (
        create_case_acceptance_chart,
        create_chart_from_data,
        create_collection_rate_chart,
        create_hygiene_reappointment_chart,
        create_new_patients_chart,
    )

    assert callable(create_collection_rate_chart)
    assert callable(create_new_patients_chart)
    assert callable(create_case_acceptance_chart)
    assert callable(create_hygiene_reappointment_chart)
    assert callable(create_chart_from_data)


def test_chart_production_imports():
    """Verify chart_production can import all dependencies."""
    from apps.frontend.chart_production import create_production_chart

    assert callable(create_production_chart)


def test_backend_metrics_imports():
    """Verify backend metrics can be imported (Story 3.3 - Pydantic wrapper)."""
    from apps.backend.metrics import get_all_kpis, get_kpi_service

    # Story 3.3: Individual calculator functions removed, replaced with get_all_kpis()
    assert callable(get_all_kpis)
    assert callable(get_kpi_service)


def test_data_sources_imports():
    """Verify data sources can be imported."""
    from apps.backend.data_sources import SheetsProvider

    assert callable(SheetsProvider)

# type: ignore-file
