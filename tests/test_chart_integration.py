"""Pytest-based integration checks for chart data + Plotly components."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from plotly.graph_objects import Figure

from apps.backend.chart_data import format_all_chart_data
from apps.frontend.chart_kpis import (
    create_case_acceptance_chart,
    create_chart_from_data,
    create_collection_rate_chart,
    create_hygiene_reappointment_chart,
    create_new_patients_chart,
)
from apps.frontend.chart_production import create_production_chart
from apps.frontend.chart_utils import validate_chart_data_structure
from core.models.chart_models import SummaryStatistics, TimeSeriesData


@pytest.fixture()
def empty_chart_data() -> TimeSeriesData:
    """Create empty TimeSeriesData Pydantic model for testing."""
    return TimeSeriesData(
        metric_name="Production Total",
        chart_type="line",
        data_type="float",
        time_series=[],
        statistics=SummaryStatistics(total_points=0, valid_points=0),
        format_options={},
    )


@pytest.fixture()
def empty_chart_data_dict() -> dict[str, object]:
    """Legacy dict fixture for validate_chart_data_structure compatibility."""
    return {
        "metric_name": "Production Total",
        "metric_key": "production_total",
        "chart_type": "line",
        "data_type": "float",
        "time_series": [],
        "statistics": {"total_points": 0, "valid_points": 0},
        "format_options": {},
    }


def test_validate_chart_data_structure_handles_empty(
    empty_chart_data_dict: dict[str, object],
) -> None:
    """Test validate_chart_data_structure with dict input (legacy compatibility)."""
    assert validate_chart_data_structure(empty_chart_data_dict) is True


def test_create_chart_from_data_returns_placeholder_on_empty(
    empty_chart_data: TimeSeriesData,
) -> None:
    """Test create_chart_from_data with Pydantic TimeSeriesData model."""
    figure = create_chart_from_data(empty_chart_data)
    assert len(figure.data) == 0


@pytest.mark.parametrize(
    "chart_factory",
    [
        create_collection_rate_chart,
        create_new_patients_chart,
        create_case_acceptance_chart,
        create_hygiene_reappointment_chart,
    ],
)
def test_individual_chart_factories_accept_empty_payload(
    chart_factory: Callable[..., Figure],
    empty_chart_data: TimeSeriesData,
) -> None:
    """Test individual chart factories with Pydantic TimeSeriesData models.

    Note: create_production_chart still expects dict (legacy), excluded from this test.
    Chart factories accept (chart_data: BaseModel, format_options: dict | None = None).
    """
    figure = chart_factory(empty_chart_data)
    assert len(figure.data) == 0


def test_production_chart_factory_accepts_empty_dict() -> None:
    """Test create_production_chart with legacy dict input.

    Production chart still uses dict input format (future migration).
    """
    empty_dict = {
        "dates": [],
        "values": [],
        "statistics": {"total": 0.0, "average": 0.0},
    }
    figure = create_production_chart(empty_dict)
    assert len(figure.data) == 0


def test_format_all_chart_data_produces_expected_keys() -> None:
    """Test format_all_chart_data returns dict with expected structure."""
    chart_data: dict[str, Any] = format_all_chart_data(None, None)
    expected_keys = {
        "production_total",
        "collection_rate",
        "new_patients",
        "case_acceptance",
        "hygiene_reappointment",
        "metadata",
    }
    assert expected_keys.issubset(chart_data.keys())

    # Access metadata dict (Pydantic model serialized to dict)
    metadata: Any = chart_data["metadata"]
    assert isinstance(metadata, dict)
    assert metadata.get("total_metrics") == 5

    data_sources: Any = metadata.get("data_sources")
    assert isinstance(data_sources, dict)
    assert data_sources == {
        "eod_available": False,
        "front_kpi_available": False,
    }
