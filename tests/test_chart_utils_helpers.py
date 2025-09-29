"""Test suite for chart utility helper functions."""

import plotly.graph_objects as go

from apps.frontend.chart_utils import (
    add_pattern_annotation,
    add_trend_line_to_figure,
    calculate_trend_line,
    format_currency_hover,
    handle_empty_data,
)


def test_format_currency_hover_positive() -> None:
    """Test formatting positive currency values for hover display."""
    assert format_currency_hover(1500) == "$1.5K"
    assert format_currency_hover(1500000) == "$1.5M"
    assert format_currency_hover(500) == "$500"
    assert format_currency_hover(0) == "$0"


def test_format_currency_hover_negative() -> None:
    """Test formatting negative currency values for hover display."""
    assert format_currency_hover(-1500) == "-$1.5K"
    assert format_currency_hover(-1500000) == "-$1.5M"
    assert format_currency_hover(-500) == "-$500"


def test_format_currency_hover_none() -> None:
    """Test handling None values in currency formatting."""
    assert format_currency_hover(None) == "N/A"


def test_handle_empty_data() -> None:
    """Test empty data chart generation."""
    fig = handle_empty_data("Test Metric")

    # Check it returns a valid figure
    assert isinstance(fig, go.Figure)

    # Check the annotation text
    assert len(fig.layout.annotations) == 1
    assert "No data available for Test Metric" in fig.layout.annotations[0].text

    # Check the title
    assert fig.layout.title.text == "Test Metric - No Data"

    # Check axes are hidden
    assert fig.layout.xaxis.visible is False
    assert fig.layout.yaxis.visible is False


def test_add_pattern_annotation() -> None:
    """Test pattern annotation addition to charts."""
    fig = go.Figure()

    # Add pattern annotation
    add_pattern_annotation(fig, "Upward trend detected", 0.1, 0.9)

    # Check annotation was added
    assert len(fig.layout.annotations) == 1
    assert fig.layout.annotations[0].text == "Upward trend detected"
    assert fig.layout.annotations[0].x == 0.1
    assert fig.layout.annotations[0].y == 0.9


def test_calculate_trend_line() -> None:
    """Test trend line calculation without figure modification."""
    # Test data
    dates: list[str] = ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]
    values: list[float] = [100.0, 110.0, 120.0, 130.0]

    # Calculate trend
    trend_values, slope, r_squared = calculate_trend_line(dates, values)

    # Check trend calculation
    assert len(trend_values) == 4
    assert slope > 0  # Should be positive for upward trend
    assert r_squared >= 0.95  # Should be high R-squared for linear data


def test_add_trend_line_to_figure() -> None:
    """Test trend line calculation and addition to figure."""
    fig = go.Figure()

    # Test data
    dates: list[str] = ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]
    values: list[float] = [100.0, 110.0, 120.0, 130.0]

    # Calculate trend and add to figure
    trend_values, slope, r_squared = add_trend_line_to_figure(fig, dates, values)

    # Check trend calculation
    assert len(trend_values) == 4
    assert slope > 0  # Should be positive for upward trend
    assert r_squared >= 0.95  # Should be high R-squared for linear data

    # Check that trend line was added to figure
    assert len(fig.data) == 1  # Should have one trace (the trend line)
    assert fig.data[0].mode == "lines"


def test_calculate_trend_line_insufficient_data() -> None:
    """Test trend line with insufficient data."""
    # Test with insufficient data
    dates: list[str] = ["2023-01-01"]
    values: list[float] = [100.0]

    trend_values, slope, r_squared = calculate_trend_line(dates, values)

    # Should return empty results
    assert trend_values == []
    assert slope == 0
    assert r_squared == 0
