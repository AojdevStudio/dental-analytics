"""Chart utilities for dental analytics dashboard."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.models.chart_models import ProcessedChartData, TimeSeriesData

logger = logging.getLogger(__name__)


def format_currency_hover(value: float | None) -> str:
    """Format currency values for hover display with K/M notation."""
    if value is None:
        return "N/A"

    if abs(value) >= 1_000_000:
        return (
            f"${value / 1_000_000:.1f}M"
            if value >= 0
            else f"-${abs(value) / 1_000_000:.1f}M"
        )
    elif abs(value) >= 1_000:
        return (
            f"${value / 1_000:.1f}K" if value >= 0 else f"-${abs(value) / 1_000:.1f}K"
        )
    else:
        return f"${value:.0f}" if value >= 0 else f"-${abs(value):.0f}"


def handle_empty_data(metric_name: str) -> go.Figure:
    """Create an empty chart figure with appropriate messaging."""
    fig = go.Figure()

    # Add annotation for no data message
    fig.add_annotation(
        text=f"No data available for {metric_name}<br>Please check your data source",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        xanchor="center",
        yanchor="middle",
        showarrow=False,
        font={"size": 16, "color": "gray"},
    )

    # Update layout for empty state
    fig.update_layout(
        title=f"{metric_name} - No Data",
        xaxis={"visible": False},
        yaxis={"visible": False},
        showlegend=False,
        height=400,
        margin={"t": 60, "b": 40, "l": 40, "r": 40},
    )

    return fig


def add_pattern_annotation(
    fig: go.Figure,
    pattern_text: str,
    x_position: float = 0.02,
    y_position: float = 0.98,
) -> None:
    """Add pattern analysis annotation to chart."""
    fig.add_annotation(
        text=pattern_text,
        xref="paper",
        yref="paper",
        x=x_position,
        y=y_position,
        xanchor="left",
        yanchor="top",
        showarrow=False,
        font={"size": 10, "color": "darkblue"},
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="darkblue",
        borderwidth=1,
    )


def safe_float_conversion(value: Any) -> float | None:
    """Safely convert value to float, returning None if conversion fails."""
    if value is None or pd.isna(value):
        return None
    try:
        # Handle string values that might have currency symbols
        if isinstance(value, str):
            # Remove common currency symbols and commas
            cleaned = value.replace("$", "").replace(",", "").strip()
            if cleaned == "" or cleaned.lower() in ["n/a", "na", "null", "none"]:
                return None
            return float(cleaned)
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_currency_string(value: str | float | int | None) -> float | None:
    """Parse currency string removing $ and , symbols."""
    if value is None or pd.isna(value):
        return None

    if isinstance(value, int | float):
        return float(value)

    if isinstance(value, str):
        # Remove currency symbols and whitespace
        cleaned = value.replace("$", "").replace(",", "").strip()
        if cleaned == "" or cleaned.lower() in ["n/a", "na", "null", "none"]:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    # All type cases handled above
    return None  # type: ignore[unreachable]  # pragma: no cover


def calculate_trend_line(
    dates: list[str], values: list[float]
) -> tuple[list[float], float, float]:
    """
    Calculate trend line statistics for time series data.

    Args:
        dates: List of date strings
        values: List of numeric values

    Returns:
        Tuple of (trend_values, slope, r_squared)
    """
    try:
        if len(dates) < 2 or len(values) < 2:
            return [], 0, 0

        # Convert dates to datetime objects for numeric processing, ensuring
        # proper trend direction
        date_objs = pd.to_datetime(dates)
        y = np.array(values)

        # Remove NaN values
        valid_mask = ~np.isnan(y)
        if np.sum(valid_mask) < 2:
            return [], 0, 0

        date_nums = pd.to_numeric(date_objs[valid_mask])
        y_valid = y[valid_mask]

        # Normalize x values to avoid numerical issues
        x_norm = (date_nums - date_nums.min()) / (date_nums.max() - date_nums.min())

        # Calculate linear regression
        coeffs = np.polyfit(x_norm, y_valid, 1)
        slope, intercept = coeffs

        # Calculate R-squared
        y_pred = slope * x_norm + intercept
        ss_res = np.sum((y_valid - y_pred) ** 2)
        ss_tot = np.sum((y_valid - np.mean(y_valid)) ** 2)

        r_squared = 0 if ss_tot == 0 else 1 - (ss_res / ss_tot)

        # Generate trend line for all original dates
        # Convert the full DatetimeIndex to numeric values
        date_nums_all = pd.to_numeric(date_objs.values)
        x_all_norm = (date_nums_all - date_nums.min()) / (
            date_nums.max() - date_nums.min()
        )
        trend_values = (slope * x_all_norm + intercept).tolist()

        return trend_values, slope, r_squared

    except Exception as e:
        logger.error(f"Error calculating trend line: {e}")
        return [], 0, 0


def add_trend_line_to_figure(
    fig: go.Figure,
    dates: list[str],
    values: list[float],
    name: str = "Trend",
    *,
    color: str | None = None,
    line_style: dict[str, Any] | None = None,
    trace_kwargs: dict[str, Any] | None = None,
) -> tuple[list[float], float, float]:
    """
    Add trend line to existing figure and return trend statistics.

    Args:
        fig: Plotly figure to add trend line to
        dates: List of date strings
        values: List of numeric values
        name: Name for the trend line

    Returns:
        Tuple of (trend_values, slope, r_squared)
    """
    trend_values, slope, r_squared = calculate_trend_line(dates, values)

    if trend_values:
        # Add trend line to the figure
        line_config: dict[str, Any] = {"dash": "dash", "color": "rgba(255,0,0,0.7)"}
        if color:
            line_config["color"] = color
        if line_style:
            line_config.update(line_style)

        scatter_overrides = trace_kwargs.copy() if trace_kwargs else {}

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=trend_values,
                mode="lines",
                name=name,
                line=line_config,
                **scatter_overrides,
            )
        )

    return trend_values, slope, r_squared


def calculate_moving_average(values: list[float], window: int = 7) -> list[float]:
    """Calculate moving average for smoothing data."""
    if len(values) < window:
        return values.copy()

    result = []
    for i in range(len(values)):
        if i < window - 1:
            # For early values, use expanding window
            window_values = [v for v in values[: i + 1] if not pd.isna(v)]
        else:
            # Use full window
            window_values = [
                v for v in values[i - window + 1 : i + 1] if not pd.isna(v)
            ]

        if window_values:
            result.append(sum(window_values) / len(window_values))
        else:
            result.append(np.nan)

    return result


def detect_data_patterns(values: list[float]) -> str:
    """Detect basic patterns in the data."""
    if len(values) < 3:
        return "Insufficient data for pattern analysis"

    # Remove None/NaN values for analysis
    clean_values = [v for v in values if v is not None and not pd.isna(v)]
    if len(clean_values) < 3:
        return "Insufficient valid data for pattern analysis"

    # Calculate basic statistics
    first_third = clean_values[: len(clean_values) // 3]
    last_third = clean_values[-len(clean_values) // 3 :]

    if len(first_third) == 0 or len(last_third) == 0:
        return "Insufficient data for trend analysis"

    avg_first = sum(first_third) / len(first_third)
    avg_last = sum(last_third) / len(last_third)

    # Simple trend detection
    change_percent = ((avg_last - avg_first) / avg_first) * 100 if avg_first != 0 else 0

    if abs(change_percent) < 5:
        return "Stable trend"
    elif change_percent > 5:
        return f"Upward trend (+{change_percent:.1f}%)"
    else:
        return f"Downward trend ({change_percent:.1f}%)"


def add_trend_pattern_annotation(
    fig: go.Figure,
    values: list[float],
    *,
    x_position: float = 0.02,
    y_position: float = 0.98,
) -> str:
    """Analyse values and add an annotation describing the detected pattern."""

    pattern_text = detect_data_patterns(values)
    if pattern_text:
        add_pattern_annotation(
            fig,
            pattern_text,
            x_position=x_position,
            y_position=y_position,
        )
    return pattern_text


def format_chart_data_for_display(
    time_series: list[dict[str, Any]], chart_type: str = "line"
) -> dict[str, Any]:
    """Format time series data for chart display."""
    if not time_series:
        return {"dates": [], "values": []}

    dates = []
    values = []

    for entry in time_series:
        if "date" in entry and "value" in entry:
            dates.append(entry["date"])
            # Parse value safely
            parsed_value = safe_float_conversion(entry["value"])
            values.append(parsed_value)

    return {"dates": dates, "values": values, "chart_type": chart_type}


def validate_chart_data_structure(
    chart_data: dict[str, Any] | ProcessedChartData | TimeSeriesData,
) -> bool:
    """
    Validate chart data structure for both new and legacy formats.

    Args:
        chart_data: Dictionary, ProcessedChartData, or TimeSeriesData
            containing chart data

    Returns:
        True if data structure is valid
    """
    # Handle TimeSeriesData Pydantic model (most common for charts)
    if isinstance(chart_data, TimeSeriesData):
        time_series = chart_data.time_series
        # time_series is list of ChartDataPoint objects, always valid structure
        return isinstance(time_series, list)

    # Handle ProcessedChartData Pydantic model
    if isinstance(chart_data, ProcessedChartData):
        # ProcessedChartData has dates and values lists, not time_series
        return (
            isinstance(chart_data.dates, list)
            and isinstance(chart_data.values, list)
            and len(chart_data.dates) == len(chart_data.values)
        )

    # If not ProcessedChartData, must be dict
    if not isinstance(chart_data, dict):
        return False  # type: ignore[unreachable]  # Runtime safety check

    # Handle new format with time_series
    if "time_series" in chart_data:
        time_series = chart_data["time_series"]
        if not isinstance(time_series, list):
            return False
        # Empty time series is valid
        if len(time_series) == 0:
            return True
        # Check structure of time series entries
        for entry in time_series:
            if not isinstance(entry, dict):
                return False
            if "date" not in entry or "value" not in entry:
                return False
        return True

    # Handle legacy format with dates and values
    required_keys = {"dates", "values"}
    if not all(key in chart_data for key in required_keys):
        return False

    dates = chart_data["dates"]
    values = chart_data["values"]

    # Validate that dates and values are lists
    if not isinstance(dates, list) or not isinstance(values, list):
        return False

    # Validate that dates and values have same length
    return len(dates) == len(values)


def apply_chart_styling(
    fig: go.Figure,
    title: str,
    y_axis_title: str = "",
    show_grid: bool = True,
    color_scheme: str = "default",
) -> None:
    """Apply consistent styling to charts."""

    # Color schemes
    color_schemes = {
        "default": {"background": "white", "grid": "lightgray", "text": "black"},
        "dental": {"background": "#f8f9fa", "grid": "#e9ecef", "text": "#142D54"},
    }

    scheme = color_schemes.get(color_scheme, color_schemes["default"])

    fig.update_layout(
        title={
            "text": title,
            "font": {"size": 16, "color": scheme["text"]},
            "x": 0.5,
            "xanchor": "center",
        },
        plot_bgcolor=scheme["background"],
        paper_bgcolor=scheme["background"],
        font={"color": scheme["text"]},
        margin={"t": 60, "b": 40, "l": 60, "r": 40},
        height=400,
    )

    # Update axes
    fig.update_xaxes(
        showgrid=show_grid,
        gridcolor=scheme["grid"],
        title_font={"color": scheme["text"]},
    )

    fig.update_yaxes(
        showgrid=show_grid,
        gridcolor=scheme["grid"],
        title=y_axis_title,
        title_font={"color": scheme["text"]},
    )


def create_empty_chart_placeholder(
    title: str, message: str = "No data available"
) -> go.Figure:
    """Create a placeholder chart when no data is available."""
    fig = go.Figure()

    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        xanchor="center",
        yanchor="middle",
        showarrow=False,
        font={"size": 14, "color": "gray"},
    )

    apply_chart_styling(fig, title)

    return fig


def calculate_chart_summary_stats(values: list[float]) -> dict[str, float | int]:
    """Calculate summary statistics for chart data."""
    # Filter out None and NaN values
    clean_values = [v for v in values if v is not None and not pd.isna(v)]

    if not clean_values:
        return {"min": 0, "max": 0, "mean": 0, "median": 0, "std": 0, "count": 0}

    return {
        "min": min(clean_values),
        "max": max(clean_values),
        "mean": sum(clean_values) / len(clean_values),
        "median": sorted(clean_values)[len(clean_values) // 2],
        "std": float(np.std(clean_values)),
        "count": len(clean_values),
    }


def format_number_for_display(
    value: float | None, format_type: str = "currency", decimals: int = 0
) -> str:
    """Format numbers for display in charts."""
    if value is None or pd.isna(value):
        return "N/A"

    if format_type == "currency":
        if abs(value) >= 1_000_000:
            return f"${value/1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            return f"${value/1_000:.1f}K"
        else:
            return f"${value:,.{decimals}f}"
    elif format_type == "percentage":
        return f"{value:.{decimals}f}%"
    else:
        return f"{value:,.{decimals}f}"


def apply_alpha_to_color(color: str, alpha: float) -> str:
    """Convert a hex or rgb color into an rgba string with the given alpha."""

    try:
        normalized_alpha = max(0.0, min(1.0, float(alpha)))
    except (TypeError, ValueError):
        normalized_alpha = 1.0

    if not isinstance(color, str):
        logger.warning("Invalid color type supplied to apply_alpha_to_color")  # type: ignore[unreachable]
        return f"rgba(0,0,0,{normalized_alpha:.3f})"

    stripped = color.strip()

    if stripped.startswith("#"):
        hex_value = stripped[1:]
        if len(hex_value) == 3:
            hex_value = "".join(ch * 2 for ch in hex_value)
        if len(hex_value) == 6:
            try:
                r = int(hex_value[0:2], 16)
                g = int(hex_value[2:4], 16)
                b = int(hex_value[4:6], 16)
                return f"rgba({r},{g},{b},{normalized_alpha:.3f})"
            except ValueError:
                logger.warning("Unable to parse hex color '%s'", color)

    if stripped.lower().startswith("rgb"):
        # Handle existing rgb/rgba strings by replacing/adding alpha component
        try:
            prefix, values = stripped.split("(", 1)
            components = values.rstrip(")").split(",")
            rgb_components = [int(float(c)) for c in components[:3]]
            return (
                f"rgba({rgb_components[0]},{rgb_components[1]},"
                f"{rgb_components[2]},{normalized_alpha:.3f})"
            )
        except (ValueError, IndexError):
            logger.warning("Unable to parse rgb color '%s'", color)

    # Fall back to supplying the original color string without modification
    return stripped


def add_chart_annotations(fig: go.Figure, annotations: list[dict[str, Any]]) -> None:
    """Add multiple annotations to a chart."""
    for annotation in annotations:
        fig.add_annotation(**annotation)


def create_comparison_chart(
    data1: dict[str, list[Any]],
    data2: dict[str, list[Any]],
    labels: tuple[str, str],
    title: str,
) -> go.Figure:
    """Create a comparison chart with two data series."""
    fig = go.Figure()

    # Add first series
    fig.add_trace(
        go.Scatter(
            x=data1.get("dates", []),
            y=data1.get("values", []),
            mode="lines+markers",
            name=labels[0],
            line={"color": "#007E9E"},
        )
    )

    # Add second series
    fig.add_trace(
        go.Scatter(
            x=data2.get("dates", []),
            y=data2.get("values", []),
            mode="lines+markers",
            name=labels[1],
            line={"color": "#142D54"},
        )
    )

    apply_chart_styling(fig, title)

    return fig
