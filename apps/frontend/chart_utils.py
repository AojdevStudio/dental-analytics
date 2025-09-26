"""Chart utilities for enhanced visualizations.

Provides common chart features: trend lines, statistical annotations,
pattern detection, and data validation across all chart types.
"""

from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import structlog
from plotly.graph_objects import Figure

from .chart_base import BRAND_COLORS

# Configure structured logging
log = structlog.get_logger()


def format_currency(value: float) -> str:
    """Format currency values for display.

    Args:
        value: Numeric value to format

    Returns:
        Formatted currency string
    """
    if value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    else:
        return f"${value:,.0f}"


def format_percentage(value: float) -> str:
    """Format percentage values for display.

    Args:
        value: Numeric percentage value

    Returns:
        Formatted percentage string
    """
    return f"{value:.1f}%"


def calculate_moving_average(values: list[float], window: int = 7) -> list[float]:
    """Calculate moving average for trend smoothing.

    Args:
        values: List of numeric values
        window: Window size for moving average

    Returns:
        List of moving average values
    """
    if len(values) < window:
        return values

    # Use pandas for efficient moving average calculation
    series = pd.Series(values)
    moving_avg = series.rolling(window=window, min_periods=1).mean()
    return moving_avg.tolist()


def detect_trend_pattern(values: list[float]) -> str:
    """Detect trend pattern in time series data.

    Args:
        values: List of numeric values

    Returns:
        String describing the trend pattern
    """
    if len(values) < 3:
        return "Insufficient data"

    # Calculate slope using linear regression
    x = np.arange(len(values))
    y = np.array(values)

    # Remove any NaN values
    valid_indices = ~np.isnan(y)
    if np.sum(valid_indices) < 3:
        return "Insufficient valid data"

    x_valid = x[valid_indices]
    y_valid = y[valid_indices]

    # Simple linear regression
    if len(x_valid) > 1:
        slope = np.polyfit(x_valid, y_valid, 1)[0]

        # Calculate relative change
        first_value = y_valid[0]
        last_value = y_valid[-1]

        if first_value != 0:
            relative_change = abs((last_value - first_value) / first_value)
        else:
            relative_change = 0

        # Determine trend strength and direction
        if abs(slope) < 0.1 and relative_change < 0.05:
            return "📊 Stable"
        elif slope > 0:
            if relative_change > 0.2:
                return "📈 Strong upward trend"
            else:
                return "🔼 Upward trend"
        else:
            if relative_change > 0.2:
                return "📉 Strong downward trend"
            else:
                return "🔽 Downward trend"

    return "📊 Stable"


def calculate_trend_line(
    dates: list[str], values: list[float]
) -> tuple[list[float], float, float]:
    """Calculate trend line using linear regression.

    Args:
        dates: List of date strings
        values: List of numeric values

    Returns:
        Tuple of (trend_values, slope, r_squared)
    """
    try:
        if not dates or not values or len(dates) != len(values):
            return [], 0, 0

        # Convert dates to numeric values - sort by date to ensure
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
        x_all_norm = (pd.to_numeric(date_objs) - date_nums.min()) / (
            date_nums.max() - date_nums.min()
        )
        trend_values = (slope * x_all_norm + intercept).tolist()

        return trend_values, slope, r_squared

    except Exception as e:
        log.error("chart_utils.trend_calculation_error", error=str(e))
        return [], 0, 0


def add_trend_line(
    fig: Figure,
    dates: list[str],
    values: list[float],
    name: str = "Trend",
    color: str | None = None,
) -> None:
    """Add trend line to existing figure.

    Args:
        fig: Plotly figure to add trend line to
        dates: List of date strings
        values: List of numeric values
        name: Name for the trend line
        color: Color for trend line (optional)
    """
    try:
        trend_values, slope, r_squared = calculate_trend_line(dates, values)

        if not trend_values:
            log.warning("chart_utils.no_trend_calculated")
            return

        # Set default color if not provided
        if color is None:
            color = BRAND_COLORS["medium_gray"]

        # Determine line style based on trend strength
        if r_squared > 0.7:
            dash_style = "solid"
            opacity = 0.8
        elif r_squared > 0.4:
            dash_style = "dash"
            opacity = 0.6
        else:
            dash_style = "dot"
            opacity = 0.5

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=trend_values,
                mode="lines",
                name=name,
                line={"color": color, "width": 2, "dash": dash_style},
                opacity=opacity,
                hovertemplate="Trend: %{y:.2f}<extra></extra>",
                showlegend=True,
            )
        )

        # Add R² annotation if significant
        if r_squared > 0.5:
            fig.add_annotation(
                text=f"R² = {r_squared:.3f}",
                xref="paper",
                yref="paper",
                x=0.02,
                y=0.98,
                showarrow=False,
                font={"size": 10, "color": "#666"},
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#ddd",
                borderwidth=1,
            )

    except Exception as e:
        log.error("chart_utils.trend_line_error", error=str(e))


def validate_chart_data_structure(chart_data: dict[str, Any]) -> bool:
    """Validate chart data structure for compatibility.

    Args:
        chart_data: Dictionary containing chart data

    Returns:
        True if data structure is valid
    """
    required_keys = {"dates", "values"}
    if not isinstance(chart_data, dict):
        return False

    if not all(key in chart_data for key in required_keys):
        return False

    dates = chart_data["dates"]
    values = chart_data["values"]

    if not isinstance(dates, list) or not isinstance(values, list):
        return False

    return len(dates) == len(values)


def add_target_line(
    fig: Figure,
    target_value: float,
    label: str = "Target",
    color: str | None = None,
) -> None:
    """Add horizontal target line to chart.

    Args:
        fig: Plotly figure to add target line to
        target_value: Y-value for target line
        label: Label for target line
        color: Color for target line
    """
    if color is None:
        color = BRAND_COLORS["medium_gray"]

    fig.add_hline(
        y=target_value,
        line_dash="dot",
        line_color=color,
        annotation_text=label,
        annotation_position="bottom right",
    )


def add_trend_pattern_annotation(fig: Figure, values: list[float]) -> None:
    """Add trend pattern annotation to chart.

    Args:
        fig: Plotly figure to add annotation to
        values: List of values to analyze
    """
    try:
        pattern = detect_trend_pattern(values)

        fig.add_annotation(
            text=pattern,
            xref="paper",
            yref="paper",
            x=0.35,
            y=1.08,  # Adjusted from 1.15 to avoid overlap with title
            xanchor="center",  # Ensure horizontal centering
            yanchor="bottom",  # Anchor to bottom of annotation box
            showarrow=False,
            font={
                "size": 11,
                "color": BRAND_COLORS["primary_navy"],
            },  # Slightly smaller font
            bgcolor="rgba(255,255,255,0.95)",  # Slightly more opaque
            bordercolor=BRAND_COLORS["border"],
            borderwidth=1,
            borderpad=4,
        )

    except Exception as e:
        log.error("chart_utils.pattern_annotation_error", error=str(e))


def apply_alpha_to_color(color: str, alpha: float = 0.2) -> str:
    """Convert a hex color to rgba with the provided alpha.

    Args:
        color: Hex (`#RRGGBB` or `#RRGGBBAA`) or rgba string.
        alpha: Alpha component between 0 and 1.

    Returns:
        Color string in rgba format when conversion is possible.
    """

    if not color:
        return color

    normalized_alpha = min(max(alpha, 0.0), 1.0)

    if color.startswith("rgba"):
        return color

    if color.startswith("#"):
        hex_value = color.lstrip("#")

        # Remove trailing alpha channel if present
        if len(hex_value) == 8:
            hex_value = hex_value[:6]

        if len(hex_value) == 6:
            try:
                r = int(hex_value[0:2], 16)
                g = int(hex_value[2:4], 16)
                b = int(hex_value[4:6], 16)
            except ValueError:
                return color

            return f"rgba({r}, {g}, {b}, {normalized_alpha:.3f})"

    return color

