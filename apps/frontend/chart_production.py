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
    add_pattern_annotation,
    add_trend_line_to_figure,
    format_currency_hover,
    handle_empty_data,
)

log = structlog.get_logger()


def create_production_chart(
    chart_data: dict[str, Any], show_trend: bool = True, timeframe: str = "daily"
) -> Figure:
    """Create interactive production total chart with trend analysis.

    Args:
        chart_data: Formatted chart data from format_production_chart_data()
        show_trend: Whether to display trend line
        timeframe: Time aggregation level (daily, weekly, monthly)

    Returns:
        Configured Plotly figure for production data
    """
    if not chart_data.get("time_series"):
        return handle_empty_data("Production Total")

    # Import aggregation function
    from apps.backend.chart_data import aggregate_chart_data

    # Aggregate data based on timeframe
    aggregated_data = aggregate_chart_data(chart_data, timeframe)
    time_series = aggregated_data.get("time_series", chart_data["time_series"])
    format_options = aggregated_data.get("format_options", {})

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
    add_pattern_annotation(fig, values)

    # Update layout with timeframe info
    title_text = f"{timeframe.capitalize()} Production Total"
    if aggregated_data.get("aggregation"):
        title_text += f" ({aggregated_data.get('data_points', 0)} data points)"

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
