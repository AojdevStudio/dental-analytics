"""Pytest-based integration checks for chart data + Plotly components."""

from __future__ import annotations

import pytest

from apps.backend.chart_data import format_all_chart_data
from apps.frontend.chart_components import (
    create_case_acceptance_chart,
    create_chart_from_data,
    create_collection_rate_chart,
    create_hygiene_reappointment_chart,
    create_new_patients_chart,
    create_production_chart,
    validate_chart_data_structure,
)


@pytest.fixture()
def empty_chart_data() -> dict[str, object]:
    return {
        "metric_name": "Test Metric",
        "chart_type": "line",
        "data_type": "float",
        "time_series": [],
        "statistics": {"total_points": 0, "valid_points": 0},
        "format_options": {},
    }


def test_validate_chart_data_structure_handles_empty(
    empty_chart_data: dict[str, object],
) -> None:
    assert validate_chart_data_structure(empty_chart_data) is True


def test_create_chart_from_data_returns_placeholder_on_empty(
    empty_chart_data: dict[str, object],
) -> None:
    figure = create_chart_from_data(empty_chart_data)
    assert len(figure.data) == 0


@pytest.mark.parametrize(
    "chart_factory",
    [
        create_production_chart,
        create_collection_rate_chart,
        create_new_patients_chart,
        create_case_acceptance_chart,
        create_hygiene_reappointment_chart,
    ],
)
def test_individual_chart_factories_accept_empty_payload(
    chart_factory, empty_chart_data: dict[str, object]
) -> None:
    figure = chart_factory(empty_chart_data)
    assert len(figure.data) == 0


def test_format_all_chart_data_produces_expected_keys() -> None:
    chart_data = format_all_chart_data(None, None)
    expected_keys = {
        "production_total",
        "collection_rate",
        "new_patients",
        "case_acceptance",
        "hygiene_reappointment",
        "metadata",
    }
    assert expected_keys.issubset(chart_data.keys())

    metadata = chart_data["metadata"]
    assert metadata["total_metrics"] == 5
    assert metadata["data_sources"] == {
        "eod_available": False,
        "front_kpi_available": False,
    }
