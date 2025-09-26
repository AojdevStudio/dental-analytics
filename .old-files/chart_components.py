"""Interactive Plotly Chart Components for Dental Analytics Dashboard.

Provides reusable, branded chart components that integrate with existing
chart data functions from Story 2.1. Includes KamDental brand styling,
responsive layouts, and comprehensive error handling.

Brand Colors:
- Primary Navy: #142D54
- Teal Accent: #007E9E
- Emergency Red: #BB0A0A
"""

import sys
from typing import Any

import plotly.graph_objects as go
import structlog
from plotly.graph_objects import Figure

# Configure structured logging to stderr
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)

log = structlog.get_logger()

# KamDental Brand Colors
BRAND_COLORS = {
    "primary_navy": "#142D54",
    "teal_accent": "#007E9E",
    "emergency_red": "#BB0A0A",
    "light_gray": "#F8F9FA",
    "medium_gray": "#6C757D",
    "success_green": "#28A745",
}

# Chart Type Configurations
CHART_TYPE_CONFIG = {
    "line": {
        "mode": "lines+markers",
        "line_width": 3,
        "marker_size": 8,
        "fill": None,
    },
    "bar": {
        "marker_line_width": 1,
        "marker_line_color": "white",
    },
    "area": {
        "mode": "lines",
        "fill": "tonexty",
        "line_width": 2,
    },
}

# Base layout configuration for all charts
BASE_LAYOUT = {
    "font": {
        "family": "Arial, sans-serif",
        "size": 12,
        "color": BRAND_COLORS["primary_navy"],
    },
    "plot_bgcolor": "white",
    "paper_bgcolor": "white",
    "margin": {"l": 60, "r": 20, "t": 60, "b": 60},
    "showlegend": False,  # Single series charts don't need legends
    "hovermode": "x unified",
    "dragmode": "zoom",  # Enable zoom by default
}

# Grid and axis styling
GRID_CONFIG = {
    "showgrid": True,
    "gridcolor": "#E9ECEF",
    "gridwidth": 1,
    "zeroline": True,
    "zerolinecolor": "#CED4DA",
    "zerolinewidth": 1,
}


def create_base_figure() -> Figure:
    """Create base Plotly figure with KamDental branding.

    Returns:
        Configured base figure with brand styling
    """
    fig = go.Figure()
    fig.update_layout(**BASE_LAYOUT)
    return fig


def apply_axis_styling(fig: Figure, show_grid: bool = True) -> None:
    """Apply consistent axis styling to figure.

    Args:
        fig: Plotly figure to style
        show_grid: Whether to show grid lines
    """
    axis_config = {
        "linecolor": BRAND_COLORS["medium_gray"],
        "linewidth": 1,
        "ticks": "outside",
        "tickcolor": BRAND_COLORS["medium_gray"],
        "tickfont": {"color": BRAND_COLORS["primary_navy"], "size": 10},
        "title_font": {"color": BRAND_COLORS["primary_navy"], "size": 12},
    }

    if show_grid:
        axis_config.update(GRID_CONFIG)
    else:
        axis_config.update({"showgrid": False, "zeroline": False})

    fig.update_xaxes(**axis_config)
    fig.update_yaxes(**axis_config)


def format_currency_hover(value: float | None) -> str:
    """Format currency values for hover tooltips.

    Args:
        value: Currency value to format

    Returns:
        Formatted currency string
    """
    if value is None:
        return "No Data"
    return f"${value:,.0f}"


def format_percentage_hover(value: float | None) -> str:
    """Format percentage values for hover tooltips.

    Args:
        value: Percentage value to format

    Returns:
        Formatted percentage string
    """
    if value is None:
        return "No Data"
    return f"{value:.1f}%"


def format_count_hover(value: int | None) -> str:
    """Format count values for hover tooltips.

    Args:
        value: Count value to format

    Returns:
        Formatted count string
    """
    if value is None:
        return "No Data"
    return f"{int(value):,}"


def add_target_range_annotation(fig: Figure, target_range: dict[str, float]) -> None:
    """Add target range visualization to chart.

    Args:
        fig: Plotly figure to add annotation to
        target_range: Dictionary with 'min' and 'max' target values
    """
    if not target_range or "min" not in target_range or "max" not in target_range:
        return

    min_target = target_range["min"]
    max_target = target_range["max"]

    # Add target range as filled area
    fig.add_hrect(
        y0=min_target,
        y1=max_target,
        fillcolor=BRAND_COLORS["success_green"],
        opacity=0.1,
        layer="below",
        line_width=0,
        annotation_text=f"Target: {min_target:.1f}%-{max_target:.1f}%",
        annotation_position="top right",
        annotation_font_size=10,
        annotation_font_color=BRAND_COLORS["medium_gray"],
    )


def handle_empty_data(metric_name: str) -> Figure:
    """Create placeholder figure for empty data.

    Args:
        metric_name: Name of the metric with no data

    Returns:
        Figure with no data message
    """
    fig = create_base_figure()

    # Add centered text annotation
    fig.add_annotation(
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        text=f"No {metric_name} Data Available",
        showarrow=False,
        font={
            "size": 16,
            "color": BRAND_COLORS["medium_gray"],
        },
        xanchor="center",
        yanchor="middle",
    )

    # Remove axis ticks and labels for empty state
    fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False)
    fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False)

    log.warning("chart.empty_data", metric=metric_name)
    return fig


def calculate_trend_line(dates: list, values: list) -> tuple:
    """Calculate linear trend line for time series data.

    Args:
        dates: List of date strings
        values: List of numeric values

    Returns:
        Tuple of (trend_values, slope, r_squared)
    """
    try:
        import numpy as np
        from datetime import datetime
        import pandas as pd

        if not dates or not values or len(dates) != len(values):
            return [], 0, 0

        # Convert dates to numeric values (days from first date)
        date_objs = pd.to_datetime(dates)
        x = (date_objs - date_objs.min()).days.values
        y = np.array(values)

        # Remove NaN values
        mask = ~np.isnan(y)
        x = x[mask]
        y = y[mask]

        if len(x) < 2:
            return [], 0, 0

        # Calculate linear regression
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
        intercept = coeffs[1]

        # Calculate trend line values
        trend_values = [slope * xi + intercept for xi in x]

        # Calculate R-squared
        y_mean = np.mean(y)
        ss_tot = np.sum((y - y_mean) ** 2)
        ss_res = np.sum((y - trend_values) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # Map back to full date range
        full_trend = []
        trend_idx = 0
        for i, date in enumerate(dates):
            if mask[i]:
                full_trend.append(trend_values[trend_idx])
                trend_idx += 1
            else:
                full_trend.append(None)

        return full_trend, slope, r_squared

    except Exception as e:
        log.error(f"Error calculating trend line: {e}")
        return [], 0, 0


def identify_pattern(values: list, window: int = 7) -> str:
    """Identify patterns in time series data.

    Args:
        values: List of numeric values
        window: Rolling window size for pattern detection

    Returns:
        Pattern description string
    """
    try:
        import numpy as np

        if not values or len(values) < window:
            return "Insufficient data"

        # Remove None/NaN values
        clean_values = [v for v in values if v is not None and not np.isnan(v)]
        if len(clean_values) < window:
            return "Insufficient data"

        values_array = np.array(clean_values)

        # Calculate rolling statistics
        recent = values_array[-window:]
        older = values_array[:-window] if len(values_array) > window else []

        # Determine trend
        if len(older) > 0:
            recent_mean = np.mean(recent)
            older_mean = np.mean(older)
            change_pct = (
                ((recent_mean - older_mean) / older_mean * 100)
                if older_mean != 0
                else 0
            )

            if change_pct > 10:
                return f"📈 Strong upward trend (+{change_pct:.1f}%)"
            elif change_pct > 3:
                return f"📊 Moderate growth (+{change_pct:.1f}%)"
            elif change_pct < -10:
                return f"📉 Declining trend ({change_pct:.1f}%)"
            elif change_pct < -3:
                return f"⚠️ Slight decline ({change_pct:.1f}%)"
            else:
                return f"➡️ Stable (±{abs(change_pct):.1f}%)"
        else:
            return "📊 Establishing baseline"

    except Exception as e:
        log.error(f"Error identifying pattern: {e}")
        return "Pattern analysis unavailable"


def add_trend_line_to_figure(
    fig, dates: list, values: list, name: str = "Trend", color: str = "#FF6B6B"
) -> None:
    """Add trend line to existing plotly figure.

    Args:
        fig: Plotly figure object
        dates: List of date strings
        values: List of numeric values
        name: Name for the trend line
        color: Color for the trend line
    """
    trend_values, slope, r_squared = calculate_trend_line(dates, values)

    if trend_values:
        import plotly.graph_objects as go

        # Determine trend direction for styling
        if slope > 0:
            dash_style = "dot"
            opacity = 0.7
        else:
            dash_style = "dash"
            opacity = 0.5

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=trend_values,
                mode="lines",
                name=name,
                line=dict(color=color, width=2, dash=dash_style),
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
                font=dict(size=10, color="#666"),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#ddd",
                borderwidth=1,
            )


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
        return handle_empty_data("Production")

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
        rangeslider=dict(visible=False),  # Hide range slider for cleaner look
    )

    log.info(
        "chart.production_created", data_points=len(time_series), timeframe=timeframe
    )
    return fig


def create_collection_rate_chart(
    chart_data: dict[str, Any], show_trend: bool = True, timeframe: str = "daily"
) -> Figure:
    """Create interactive collection rate chart.

    Args:
        chart_data: Formatted chart data from format_collection_rate_chart_data()

    Returns:
        Configured Plotly figure for collection rate data
    """
    if not chart_data.get("time_series"):
        return handle_empty_data("Collection Rate")

    time_series = chart_data["time_series"]
    format_options = chart_data.get("format_options", {})

    # Extract dates and values
    dates = [point["date"] for point in time_series]
    values = [point["value"] for point in time_series]

    # Create line chart
    fig = create_base_figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            line={
                "color": format_options.get("line_color", BRAND_COLORS["primary_navy"]),
                "width": 3,
            },
            marker={
                "size": 8,
                "color": format_options.get("line_color", BRAND_COLORS["primary_navy"]),
                "line": {"color": "white", "width": 2},
            },
            hovertemplate="<b>%{x}</b><br>"
            + "Collection Rate: %{customdata}<br>"
            + "<extra></extra>",
            customdata=[format_percentage_hover(v) for v in values],
            name="Collection Rate",
        )
    )

    # Add target range if specified
    target_range = format_options.get("target_range")
    if target_range:
        add_target_range_annotation(fig, target_range)

    # Update layout
    fig.update_layout(
        title={
            "text": "Daily Collection Rate",
            "x": 0.5,
            "font": {"size": 16, "color": BRAND_COLORS["primary_navy"]},
        },
        xaxis_title="Date",
        yaxis_title="Collection Rate (%)",
        height=400,
    )

    # Apply consistent styling
    apply_axis_styling(fig, format_options.get("show_grid", True))

    # Format y-axis for percentage
    fig.update_yaxes(tickformat=".1f", ticksuffix="%")

    log.info("chart.collection_rate_created", data_points=len(time_series))
    return fig


def create_new_patients_chart(
    chart_data: dict[str, Any], show_trend: bool = True, timeframe: str = "daily"
) -> Figure:
    """Create interactive new patients chart.

    Args:
        chart_data: Formatted chart data from format_new_patients_chart_data()

    Returns:
        Configured Plotly figure for new patients data
    """
    if not chart_data.get("time_series"):
        return handle_empty_data("New Patients")

    time_series = chart_data["time_series"]
    format_options = chart_data.get("format_options", {})

    # Extract dates and values
    dates = [point["date"] for point in time_series]
    values = [point["value"] for point in time_series]

    # Create bar chart
    fig = create_base_figure()

    fig.add_trace(
        go.Bar(
            x=dates,
            y=values,
            marker={
                "color": format_options.get("bar_color", BRAND_COLORS["teal_accent"]),
                "line": {"color": "white", "width": 1},
            },
            hovertemplate="<b>%{x}</b><br>"
            + "New Patients: %{customdata}<br>"
            + "<extra></extra>",
            customdata=[format_count_hover(v) for v in values],
            name="New Patients",
        )
    )

    # Update layout
    fig.update_layout(
        title={
            "text": "Daily New Patients",
            "x": 0.5,
            "font": {"size": 16, "color": BRAND_COLORS["primary_navy"]},
        },
        xaxis_title="Date",
        yaxis_title="Number of New Patients",
        height=400,
        bargap=0.2,  # Space between bars
    )

    # Apply consistent styling
    apply_axis_styling(fig, format_options.get("show_grid", True))

    # Format y-axis for counts (integer)
    fig.update_yaxes(tickformat="d")

    log.info("chart.new_patients_created", data_points=len(time_series))
    return fig


def create_case_acceptance_chart(
    chart_data: dict[str, Any], show_trend: bool = True, timeframe: str = "daily"
) -> Figure:
    """Create interactive case acceptance chart.

    Args:
        chart_data: Formatted chart data from format_case_acceptance_chart_data()

    Returns:
        Configured Plotly figure for case acceptance data
    """
    if not chart_data.get("time_series"):
        return handle_empty_data("Case Acceptance")

    time_series = chart_data["time_series"]
    format_options = chart_data.get("format_options", {})

    # Extract dates and values
    dates = [point["date"] for point in time_series]
    values = [point["value"] for point in time_series]

    # Create line chart
    fig = create_base_figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            line={
                "color": format_options.get("line_color", BRAND_COLORS["primary_navy"]),
                "width": 3,
            },
            marker={
                "size": 8,
                "color": format_options.get("line_color", BRAND_COLORS["primary_navy"]),
                "line": {"color": "white", "width": 2},
            },
            hovertemplate="<b>%{x}</b><br>"
            + "Acceptance Rate: %{customdata}<br>"
            + "<extra></extra>",
            customdata=[format_percentage_hover(v) for v in values],
            name="Case Acceptance",
        )
    )

    # Add target range if specified
    target_range = format_options.get("target_range")
    if target_range:
        add_target_range_annotation(fig, target_range)

    # Update layout
    fig.update_layout(
        title={
            "text": "Daily Case Acceptance Rate",
            "x": 0.5,
            "font": {"size": 16, "color": BRAND_COLORS["primary_navy"]},
        },
        xaxis_title="Date",
        yaxis_title="Acceptance Rate (%)",
        height=400,
    )

    # Apply consistent styling
    apply_axis_styling(fig, format_options.get("show_grid", True))

    # Format y-axis for percentage
    fig.update_yaxes(tickformat=".1f", ticksuffix="%")

    log.info("chart.case_acceptance_created", data_points=len(time_series))
    return fig


def create_hygiene_reappointment_chart(
    chart_data: dict[str, Any], show_trend: bool = True, timeframe: str = "daily"
) -> Figure:
    """Create interactive hygiene reappointment chart.

    Args:
        chart_data: Formatted chart data from format_hygiene_reappointment_chart_data()

    Returns:
        Configured Plotly figure for hygiene reappointment data
    """
    if not chart_data.get("time_series"):
        return handle_empty_data("Hygiene Reappointment")

    time_series = chart_data["time_series"]
    format_options = chart_data.get("format_options", {})

    # Extract dates and values
    dates = [point["date"] for point in time_series]
    values = [point["value"] for point in time_series]

    # Create line chart
    fig = create_base_figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            line={
                "color": format_options.get("line_color", BRAND_COLORS["teal_accent"]),
                "width": 3,
            },
            marker={
                "size": 8,
                "color": format_options.get("line_color", BRAND_COLORS["teal_accent"]),
                "line": {"color": "white", "width": 2},
            },
            hovertemplate="<b>%{x}</b><br>"
            + "Reappointment Rate: %{customdata}<br>"
            + "<extra></extra>",
            customdata=[format_percentage_hover(v) for v in values],
            name="Hygiene Reappointment",
        )
    )

    # Add target range if specified
    target_range = format_options.get("target_range")
    if target_range:
        add_target_range_annotation(fig, target_range)

    # Update layout
    fig.update_layout(
        title={
            "text": "Daily Hygiene Reappointment Rate",
            "x": 0.5,
            "font": {"size": 16, "color": BRAND_COLORS["primary_navy"]},
        },
        xaxis_title="Date",
        yaxis_title="Reappointment Rate (%)",
        height=400,
    )

    # Apply consistent styling
    apply_axis_styling(fig, format_options.get("show_grid", True))

    # Format y-axis for percentage
    fig.update_yaxes(tickformat=".1f", ticksuffix="%")

    log.info("chart.hygiene_reappointment_created", data_points=len(time_series))
    return fig


def validate_chart_data_structure(chart_data: dict[str, Any]) -> bool:
    """Validate chart data structure for compatibility.

    Args:
        chart_data: Chart data dictionary to validate

    Returns:
        True if valid structure, False otherwise
    """
    required_fields = ["metric_name", "chart_type", "data_type", "time_series"]

    try:
        # Check top-level fields
        for field in required_fields:
            if field not in chart_data:
                log.error("chart_validation.missing_field", field=field)
                return False

        # Validate time series structure
        time_series = chart_data["time_series"]
        if not isinstance(time_series, list):
            log.error("chart_validation.invalid_time_series_type")
            return False

        # Check time series points
        for i, point in enumerate(time_series[:5]):  # Check first 5 points
            if not isinstance(point, dict):
                log.error("chart_validation.invalid_point_type", index=i)
                return False
            if "date" not in point:
                log.error("chart_validation.missing_date", index=i)
                return False

        log.debug("chart_validation.passed", metric=chart_data["metric_name"])
        return True

    except Exception as e:
        log.error("chart_validation.error", error=str(e))
        return False


def create_chart_from_data(
    chart_data: dict[str, Any], show_trend: bool = True, timeframe: str = "daily"
) -> Figure:
    """Create appropriate chart based on chart data structure with advanced features.

    Args:
        chart_data: Formatted chart data from backend functions
        show_trend: Whether to display trend line
        timeframe: Time aggregation level (daily, weekly, monthly)

    Returns:
        Configured Plotly figure
    """
    # Validate data structure first
    if not validate_chart_data_structure(chart_data):
        return handle_empty_data(chart_data.get("metric_name", "Unknown"))

    metric_name = chart_data["metric_name"]

    # Route to appropriate chart creation function
    chart_creators = {
        "Production Total": create_production_chart,
        "Collection Rate": create_collection_rate_chart,
        "New Patients": create_new_patients_chart,
        "Case Acceptance": create_case_acceptance_chart,
        "Hygiene Reappointment": create_hygiene_reappointment_chart,
    }

    creator_func = chart_creators.get(metric_name)
    if not creator_func:
        log.warning("chart.unknown_metric", metric=metric_name)
        return handle_empty_data(metric_name)

    try:
        # Pass advanced parameters to chart creation functions
        return creator_func(chart_data, show_trend=show_trend, timeframe=timeframe)
    except Exception as e:
        log.error("chart.creation_error", metric=metric_name, error=str(e))
        return handle_empty_data(metric_name)
