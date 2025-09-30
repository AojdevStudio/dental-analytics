"""Production chart creation with enhanced features.

Specialized chart for production metrics with trend analysis and interactivity.
"""

from typing import Any

import plotly.graph_objects as go
import structlog
from plotly.graph_objects import Figure

from apps.frontend.chart_base import (
    BRAND_COLORS,
    apply_axis_styling,
    apply_range_selector,
    create_base_figure,
)
from apps.frontend.chart_utils import (
    add_trend_line_to_figure,
    add_trend_pattern_annotation,
    format_currency_hover,
    handle_empty_data,
)

log = structlog.get_logger()


def create_production_chart(
    chart_data: dict[str, Any] | None,
    show_trend: bool = True,
    timeframe: str = "daily",
) -> Figure:
    """Create interactive production total chart with trend analysis.

    Args:
        chart_data: Formatted chart data from format_production_chart_data()
        show_trend: Whether to display trend line
        timeframe: Time aggregation level (daily, weekly, monthly)

    Returns:
        Configured Plotly figure for production data
    """
    if chart_data is None:
        return handle_empty_data("Production Total")

    if not isinstance(chart_data, dict):
        raise TypeError("chart_data must be a dictionary or None")

    metadata = chart_data.get("metadata", {})
    format_options = chart_data.get("format_options", {})
    time_series = chart_data.get("time_series")

    # Fallback for legacy data shape that uses separate lists
    if not time_series and chart_data.get("dates") and chart_data.get("values"):
        time_series = [
            {"date": date, "value": value}
            for date, value in zip(
                chart_data["dates"],
                chart_data["values"],
                strict=False,
            )
        ]

    if not time_series:
        return handle_empty_data("Production Total")

    aggregation_value = chart_data.get("aggregation") or metadata.get("aggregation")

    if timeframe != "daily" and not aggregation_value:
        log.warning(
            "chart.production_aggregation_unavailable",
            timeframe=timeframe,
        )

    # Extract dates and values
    dates = [point["date"] for point in time_series]
    values = [point["value"] for point in time_series]

    # Create line chart
    fig = create_base_figure()

    # Main data trace with enhanced interactivity
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            line={
                "color": format_options.get("line_color", BRAND_COLORS["teal_accent"]),
                "width": 3,
                "shape": "spline",  # Smooth lines
            },
            marker={
                "size": 8,
                "color": format_options.get("line_color", BRAND_COLORS["teal_accent"]),
                "line": {"color": "white", "width": 2},
            },
            hovertemplate="<b>%{x}</b><br>"
            + f"Production ({timeframe}): %{{customdata}}<br>"
            + "<extra></extra>",
            customdata=[format_currency_hover(v) for v in values],
            name="Production",
        )
    )

    # Add trend line if requested
    if show_trend and len(values) > 3:
        add_trend_line_to_figure(
            fig,
            dates,
            values,
            name="Trend",
            color=(
                BRAND_COLORS["emergency_red"]
                if any(v < 0 for v in values if v)
                else BRAND_COLORS["success_green"]
            ),
        )

    # Add pattern identification annotation
    add_trend_pattern_annotation(fig, values)

    # Update layout with timeframe info
    title_text = f"{timeframe.capitalize()} Production Total"
    if aggregation_value:
        title_text += (
            f" ({chart_data.get('data_points', len(time_series))} data points)"
        )

    fig.update_layout(
        title={
            "text": title_text,
            "x": 0.5,
            "font": {"size": 16, "color": BRAND_COLORS["primary_navy"]},
        },
        xaxis_title="Date",
        yaxis_title="Production Amount ($)",
        height=450,  # Slightly taller for annotations
        dragmode="zoom",  # Enable zoom by default
        hovermode="x unified",  # Better hover experience
    )

    # Apply consistent styling
    apply_axis_styling(fig, format_options.get("show_grid", True))

    # Format y-axis for currency
    fig.update_yaxes(tickformat="$,.0f")

    # Add range selector buttons for better interaction
    apply_range_selector(fig)

    log.info(
        "chart.production_created", data_points=len(time_series), timeframe=timeframe
    )
    return fig
