"""Enhanced chart creation functions with trend lines and advanced features for Story 2.3."""

import logging
from typing import Any

import plotly.graph_objects as go
from plotly.graph_objects import Figure

log = logging.getLogger(__name__)

# Import base functions from chart_components
from apps.frontend.chart_components import (
    BRAND_COLORS,
    add_target_range_annotation,
    add_trend_line_to_figure,
    apply_axis_styling,
    create_base_figure,
    format_count_hover,
    format_percentage_hover,
    handle_empty_data,
    identify_pattern,
)


def create_enhanced_collection_rate_chart(
    chart_data: dict[str, Any], show_trend: bool = True, timeframe: str = "daily"
) -> Figure:
    """Create interactive collection rate chart with trend analysis."""
    if not chart_data.get("time_series"):
        return handle_empty_data("Collection Rate")

    # Import aggregation function
    from apps.backend.chart_data import aggregate_chart_data

    # Aggregate data based on timeframe
    aggregated_data = aggregate_chart_data(chart_data, timeframe)
    time_series = aggregated_data.get("time_series", chart_data["time_series"])
    format_options = aggregated_data.get("format_options", {})

    # Extract dates and values
    dates = [point["date"] for point in time_series]
    values = [point["value"] for point in time_series]

    # Create area chart for percentage data
    fig = create_base_figure()

    # Main data trace
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            fill="tozeroy",
            fillcolor="rgba(0, 126, 158, 0.2)",
            line={
                "color": format_options.get("line_color", BRAND_COLORS["teal_accent"]),
                "width": 3,
                "shape": "spline",
            },
            marker={
                "size": 8,
                "color": format_options.get("line_color", BRAND_COLORS["teal_accent"]),
                "line": {"color": "white", "width": 2},
            },
            hovertemplate="<b>%{x}</b><br>"
            + f"Collection Rate ({timeframe}): %{{customdata}}<br>"
            + "<extra></extra>",
            customdata=[format_percentage_hover(v) for v in values],
            name="Collection Rate",
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
                BRAND_COLORS["success_green"]
                if any(v >= 98 for v in values if v)
                else BRAND_COLORS["warning"]
            ),
        )

    # Add target range (98-100%)
    add_target_range_annotation(fig, 98, 100, "Target Range")

    # Add pattern identification
    pattern = identify_pattern(values)
    fig.add_annotation(
        text=pattern,
        xref="paper",
        yref="paper",
        x=0.5,
        y=1.15,
        showarrow=False,
        font=dict(size=12, color=BRAND_COLORS["primary_navy"]),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=BRAND_COLORS["border"],
        borderwidth=1,
        borderpad=4,
    )

    # Update layout
    title_text = f"{timeframe.capitalize()} Collection Rate"
    if aggregated_data.get("aggregation"):
        title_text += f" ({aggregated_data.get('data_points', 0)} data points)"

    fig.update_layout(
        title={
            "text": title_text,
            "x": 0.5,
            "font": {"size": 16, "color": BRAND_COLORS["primary_navy"]},
        },
        xaxis_title="Date",
        yaxis_title="Collection Rate (%)",
        height=450,
        dragmode="zoom",
        hovermode="x unified",
        yaxis=dict(range=[0, 120]),  # Cap at 120% for better visualization
    )

    # Apply consistent styling
    apply_axis_styling(fig, format_options.get("show_grid", True))

    # Format y-axis for percentage
    fig.update_yaxes(tickformat=".1f", ticksuffix="%")

    # Add range selector
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=14, label="2w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(step="all", label="All"),
                ]
            ),
            bgcolor="rgba(255,255,255,0.7)",
            activecolor=BRAND_COLORS["teal_accent"],
            x=0,
            y=1.1,
        ),
        rangeslider=dict(visible=False),
    )

    log.info(
        "chart.collection_rate_created",
        data_points=len(time_series),
        timeframe=timeframe,
    )
    return fig


def create_enhanced_new_patients_chart(
    chart_data: dict[str, Any], show_trend: bool = True, timeframe: str = "daily"
) -> Figure:
    """Create interactive new patients chart with trend analysis."""
    if not chart_data.get("time_series"):
        return handle_empty_data("New Patients")

    # Import aggregation function
    from apps.backend.chart_data import aggregate_chart_data

    # Aggregate data based on timeframe
    aggregated_data = aggregate_chart_data(chart_data, timeframe)
    time_series = aggregated_data.get("time_series", chart_data["time_series"])
    format_options = aggregated_data.get("format_options", {})

    # Extract dates and values
    dates = [point["date"] for point in time_series]
    values = [point["value"] for point in time_series]

    # Create bar chart for count data
    fig = create_base_figure()

    # Main data trace
    fig.add_trace(
        go.Bar(
            x=dates,
            y=values,
            marker={
                "color": format_options.get("bar_color", BRAND_COLORS["teal_accent"]),
                "line": {"color": BRAND_COLORS["primary_navy"], "width": 1},
            },
            hovertemplate="<b>%{x}</b><br>"
            + f"New Patients ({timeframe}): %{{customdata}}<br>"
            + "<extra></extra>",
            customdata=[format_count_hover(v) for v in values],
            name="New Patients",
        )
    )

    # Add trend line if requested
    if show_trend and len(values) > 3:
        add_trend_line_to_figure(
            fig, dates, values, name="Trend", color=BRAND_COLORS["success_green"]
        )

    # Add pattern identification
    pattern = identify_pattern(values, window=7 if timeframe == "daily" else 3)
    fig.add_annotation(
        text=pattern,
        xref="paper",
        yref="paper",
        x=0.5,
        y=1.15,
        showarrow=False,
        font=dict(size=12, color=BRAND_COLORS["primary_navy"]),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=BRAND_COLORS["border"],
        borderwidth=1,
        borderpad=4,
    )

    # Update layout
    title_text = f"{timeframe.capitalize()} New Patients"
    if aggregated_data.get("aggregation"):
        title_text += f" ({aggregated_data.get('data_points', 0)} data points)"

    fig.update_layout(
        title={
            "text": title_text,
            "x": 0.5,
            "font": {"size": 16, "color": BRAND_COLORS["primary_navy"]},
        },
        xaxis_title="Date",
        yaxis_title="Number of New Patients",
        height=450,
        dragmode="zoom",
        hovermode="x unified",
    )

    # Apply consistent styling
    apply_axis_styling(fig, format_options.get("show_grid", True))

    # Add range selector
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=14, label="2w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(step="all", label="All"),
                ]
            ),
            bgcolor="rgba(255,255,255,0.7)",
            activecolor=BRAND_COLORS["teal_accent"],
            x=0,
            y=1.1,
        ),
        rangeslider=dict(visible=False),
    )

    log.info(
        "chart.new_patients_created", data_points=len(time_series), timeframe=timeframe
    )
    return fig


def create_enhanced_case_acceptance_chart(
    chart_data: dict[str, Any], show_trend: bool = True, timeframe: str = "daily"
) -> Figure:
    """Create interactive case acceptance chart with trend analysis."""
    if not chart_data.get("time_series"):
        return handle_empty_data("Case Acceptance")

    from apps.backend.chart_data import aggregate_chart_data

    aggregated_data = aggregate_chart_data(chart_data, timeframe)
    time_series = aggregated_data.get("time_series", chart_data["time_series"])
    format_options = aggregated_data.get("format_options", {})

    dates = [point["date"] for point in time_series]
    values = [point["value"] for point in time_series]

    fig = create_base_figure()

    # Main trace with gradient fill
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            fill="tozeroy",
            fillcolor="rgba(0, 126, 158, 0.15)",
            line={
                "color": format_options.get("line_color", BRAND_COLORS["teal_accent"]),
                "width": 3,
                "shape": "spline",
            },
            marker={
                "size": 8,
                "color": format_options.get("line_color", BRAND_COLORS["teal_accent"]),
                "line": {"color": "white", "width": 2},
            },
            hovertemplate="<b>%{x}</b><br>"
            + f"Case Acceptance ({timeframe}): %{{customdata}}<br>"
            + "<extra></extra>",
            customdata=[format_percentage_hover(v) for v in values],
            name="Case Acceptance",
        )
    )

    if show_trend and len(values) > 3:
        add_trend_line_to_figure(
            fig, dates, values, name="Trend", color=BRAND_COLORS["accent"]
        )

    # Add target range (85-95%)
    add_target_range_annotation(fig, 85, 95, "Target Range")

    # Pattern identification
    pattern = identify_pattern(values)
    fig.add_annotation(
        text=pattern,
        xref="paper",
        yref="paper",
        x=0.5,
        y=1.15,
        showarrow=False,
        font=dict(size=12, color=BRAND_COLORS["primary_navy"]),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=BRAND_COLORS["border"],
        borderwidth=1,
        borderpad=4,
    )

    title_text = f"{timeframe.capitalize()} Case Acceptance Rate"
    if aggregated_data.get("aggregation"):
        title_text += f" ({aggregated_data.get('data_points', 0)} data points)"

    fig.update_layout(
        title={
            "text": title_text,
            "x": 0.5,
            "font": {"size": 16, "color": BRAND_COLORS["primary_navy"]},
        },
        xaxis_title="Date",
        yaxis_title="Case Acceptance Rate (%)",
        height=450,
        dragmode="zoom",
        hovermode="x unified",
        yaxis=dict(range=[0, 110]),
    )

    apply_axis_styling(fig, format_options.get("show_grid", True))
    fig.update_yaxes(tickformat=".1f", ticksuffix="%")

    # Range selector
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=14, label="2w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(step="all", label="All"),
                ]
            ),
            bgcolor="rgba(255,255,255,0.7)",
            activecolor=BRAND_COLORS["teal_accent"],
            x=0,
            y=1.1,
        ),
        rangeslider=dict(visible=False),
    )

    log.info(
        "chart.case_acceptance_created",
        data_points=len(time_series),
        timeframe=timeframe,
    )
    return fig


def create_enhanced_hygiene_reappointment_chart(
    chart_data: dict[str, Any], show_trend: bool = True, timeframe: str = "daily"
) -> Figure:
    """Create interactive hygiene reappointment chart with trend analysis."""
    if not chart_data.get("time_series"):
        return handle_empty_data("Hygiene Reappointment")

    from apps.backend.chart_data import aggregate_chart_data

    aggregated_data = aggregate_chart_data(chart_data, timeframe)
    time_series = aggregated_data.get("time_series", chart_data["time_series"])
    format_options = aggregated_data.get("format_options", {})

    dates = [point["date"] for point in time_series]
    values = [point["value"] for point in time_series]

    fig = create_base_figure()

    # Main trace with gradient
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            fill="tozeroy",
            fillcolor="rgba(0, 126, 158, 0.15)",
            line={
                "color": format_options.get("line_color", BRAND_COLORS["teal_accent"]),
                "width": 3,
                "shape": "spline",
            },
            marker={
                "size": 8,
                "color": format_options.get("line_color", BRAND_COLORS["teal_accent"]),
                "line": {"color": "white", "width": 2},
            },
            hovertemplate="<b>%{x}</b><br>"
            + f"Hygiene Reappointment ({timeframe}): %{{customdata}}<br>"
            + "<extra></extra>",
            customdata=[format_percentage_hover(v) for v in values],
            name="Hygiene Reappointment",
        )
    )

    if show_trend and len(values) > 3:
        add_trend_line_to_figure(
            fig,
            dates,
            values,
            name="Trend",
            color=(
                BRAND_COLORS["success_green"]
                if any(v >= 90 for v in values if v)
                else BRAND_COLORS["warning"]
            ),
        )

    # Add target range (90-95%)
    add_target_range_annotation(fig, 90, 95, "Target Range")

    # Pattern identification
    pattern = identify_pattern(values)
    fig.add_annotation(
        text=pattern,
        xref="paper",
        yref="paper",
        x=0.5,
        y=1.15,
        showarrow=False,
        font=dict(size=12, color=BRAND_COLORS["primary_navy"]),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=BRAND_COLORS["border"],
        borderwidth=1,
        borderpad=4,
    )

    title_text = f"{timeframe.capitalize()} Hygiene Reappointment Rate"
    if aggregated_data.get("aggregation"):
        title_text += f" ({aggregated_data.get('data_points', 0)} data points)"

    fig.update_layout(
        title={
            "text": title_text,
            "x": 0.5,
            "font": {"size": 16, "color": BRAND_COLORS["primary_navy"]},
        },
        xaxis_title="Date",
        yaxis_title="Reappointment Rate (%)",
        height=450,
        dragmode="zoom",
        hovermode="x unified",
        yaxis=dict(range=[0, 110]),
    )

    apply_axis_styling(fig, format_options.get("show_grid", True))
    fig.update_yaxes(tickformat=".1f", ticksuffix="%")

    # Range selector
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=14, label="2w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(step="all", label="All"),
                ]
            ),
            bgcolor="rgba(255,255,255,0.7)",
            activecolor=BRAND_COLORS["teal_accent"],
            x=0,
            y=1.1,
        ),
        rangeslider=dict(visible=False),
    )

    log.info(
        "chart.hygiene_reappointment_created",
        data_points=len(time_series),
        timeframe=timeframe,
    )
    return fig
