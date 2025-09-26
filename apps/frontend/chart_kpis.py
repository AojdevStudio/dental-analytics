"""KPI chart creation functions with enhanced features.

Contains collection rate, new patients, case acceptance, and
hygiene reappointment charts. Includes the main dispatcher function
create_chart_from_data.
"""

import structlog
from plotly.graph_objects import Figure

from .chart_base import (
    BRAND_COLORS,
    apply_axis_styling,
    apply_range_selector,
    create_base_figure,
)
from .chart_utils import (
    add_trend_line,
    add_trend_pattern_annotation,
    apply_alpha_to_color,
)

# Configure structured logging
log = structlog.get_logger()


def create_collection_rate_chart(
    chart_data: dict, format_options: dict | None = None
) -> Figure:
    """Create collection rate chart with enhanced KPI features.

    Args:
        chart_data: Dictionary with dates, values, and metadata
        format_options: Chart formatting preferences

    Returns:
        Plotly figure with collection rate visualization
    """
    if format_options is None:
        format_options = {}

    log.info(
        "chart.collection_rate_creation_started",
        data_points=len(chart_data.get("dates", [])),
    )

    fig = create_base_figure()

    # Data validation
    dates = chart_data.get("dates", [])
    values = chart_data.get("values", [])

    if not dates or not values:
        log.warning("chart.collection_rate_no_data")
        return fig

    # Configure chart style
    line_color = format_options.get("line_color", BRAND_COLORS["teal_accent"])
    fill_alpha = format_options.get("fill_opacity", 0.125)
    fill_color_setting = format_options.get("fill_color")
    fill_color = (
        apply_alpha_to_color(fill_color_setting, fill_alpha)
        if fill_color_setting
        else apply_alpha_to_color(line_color, fill_alpha)
    )
    marker_size = format_options.get("marker_size", 8)

    # Main data trace
    fig.add_scatter(
        x=dates,
        y=values,
        mode="lines+markers",
        line={"color": line_color, "width": 3},
        marker={
            "size": marker_size,
            "color": line_color,
            "line": {"width": 2, "color": "white"},
        },
        fill="tozeroy",
        fillcolor=fill_color,
        name="Collection Rate",
        hovertemplate="%{x}<br>Collection Rate: %{y:.1f}%<extra></extra>",
    )

    # Add trend line if requested
    if format_options.get("show_trend", False):
        add_trend_line(fig, dates, values, "Collection Rate Trend")

    # Add target line at 95% (industry standard)
    target_rate = format_options.get("target_rate", 95)
    if target_rate and target_rate > 0:
        fig.add_hline(
            y=target_rate,
            line_dash="dot",
            line_color=BRAND_COLORS["medium_gray"],
            annotation_text=f"Target: {target_rate}%",
            annotation_position="bottom right",
        )

    # Update layout with KPI-specific formatting
    fig.update_layout(
        title={
            "text": "Collection Rate Trends",
            "x": 0.5,
            "font": {"size": 16, "color": BRAND_COLORS["primary_navy"]},
        },
        xaxis_title="Date",
        yaxis_title="Collection Rate (%)",
        height=450,
        dragmode="zoom",
        hovermode="x unified",
        yaxis={"range": [0, 120]},  # Cap at 120% for better visualization
    )

    # Apply consistent styling
    apply_axis_styling(fig, format_options.get("show_grid", True))

    # Format y-axis for percentage
    fig.update_yaxes(tickformat=".1f", ticksuffix="%")

    # Add range selector for time-based filtering
    apply_range_selector(fig)

    # Add trend pattern annotation if enabled
    if format_options.get("show_trend_pattern", True):
        add_trend_pattern_annotation(fig, values)

    log.info(
        "chart.collection_rate_completed",
        data_points=len(dates),
        avg_rate=sum(values) / len(values) if values else 0,
    )

    return fig


def create_new_patients_chart(
    chart_data: dict, format_options: dict | None = None
) -> Figure:
    """Create new patients chart with bar visualization.

    Args:
        chart_data: Dictionary with dates, values, and metadata
        format_options: Chart formatting preferences

    Returns:
        Plotly figure with new patients visualization
    """
    if format_options is None:
        format_options = {}

    log.info(
        "chart.new_patients_creation_started",
        data_points=len(chart_data.get("dates", [])),
    )

    fig = create_base_figure()

    # Data validation
    dates = chart_data.get("dates", [])
    values = chart_data.get("values", [])

    if not dates or not values:
        log.warning("chart.new_patients_no_data")
        return fig

    # Configure chart style
    bar_color = format_options.get("bar_color", BRAND_COLORS["teal_accent"])

    # Main data trace (bar chart for count data)
    fig.add_bar(
        x=dates,
        y=values,
        marker_color=bar_color,
        marker_line={"width": 1, "color": "white"},
        name="New Patients",
        hovertemplate="%{x}<br>New Patients: %{y}<extra></extra>",
    )

    # Add trend line if requested
    if format_options.get("show_trend", False):
        add_trend_line(fig, dates, values, "New Patients Trend")

    # Add target line if specified
    target_patients = format_options.get("target_patients")
    if target_patients and target_patients > 0:
        fig.add_hline(
            y=target_patients,
            line_dash="dot",
            line_color=BRAND_COLORS["medium_gray"],
            annotation_text=f"Target: {target_patients}",
            annotation_position="bottom right",
        )

    # Update layout
    fig.update_layout(
        title={
            "text": "New Patients Over Time",
            "x": 0.5,
            "font": {"size": 16, "color": BRAND_COLORS["primary_navy"]},
        },
        xaxis_title="Date",
        yaxis_title="Number of New Patients",
        height=450,
        dragmode="zoom",
        hovermode="x unified",
    )

    # Apply styling
    apply_axis_styling(fig, format_options.get("show_grid", True))
    apply_range_selector(fig)

    # Add trend pattern annotation
    if format_options.get("show_trend_pattern", True):
        add_trend_pattern_annotation(fig, values)

    log.info(
        "chart.new_patients_completed",
        data_points=len(dates),
        total_patients=sum(values) if values else 0,
    )

    return fig


def create_case_acceptance_chart(
    chart_data: dict, format_options: dict | None = None
) -> Figure:
    """Create case acceptance rate chart.

    Args:
        chart_data: Dictionary with dates, values, and metadata
        format_options: Chart formatting preferences

    Returns:
        Plotly figure with case acceptance visualization
    """
    if format_options is None:
        format_options = {}

    log.info(
        "chart.case_acceptance_creation_started",
        data_points=len(chart_data.get("dates", [])),
    )

    fig = create_base_figure()

    # Data validation
    dates = chart_data.get("dates", [])
    values = chart_data.get("values", [])

    if not dates or not values:
        log.warning("chart.case_acceptance_no_data")
        return fig

    # Configure chart style
    line_color = format_options.get("line_color", BRAND_COLORS["success_green"])
    fill_color = format_options.get("fill_color", f"{line_color}20")

    # Main data trace
    fig.add_scatter(
        x=dates,
        y=values,
        mode="lines+markers",
        line={"color": line_color, "width": 3},
        marker={
            "size": 8,
            "color": line_color,
            "line": {"width": 2, "color": "white"},
        },
        fill="tozeroy",
        fillcolor=fill_color,
        name="Case Acceptance Rate",
        hovertemplate="%{x}<br>Acceptance Rate: %{y:.1f}%<extra></extra>",
    )

    # Add trend line if requested
    if format_options.get("show_trend", False):
        add_trend_line(fig, dates, values, "Acceptance Trend")

    # Add target line (typically 80-90% for dental practices)
    target_rate = format_options.get("target_acceptance", 85)
    if target_rate and target_rate > 0:
        fig.add_hline(
            y=target_rate,
            line_dash="dot",
            line_color=BRAND_COLORS["medium_gray"],
            annotation_text=f"Target: {target_rate}%",
            annotation_position="bottom right",
        )

    # Update layout
    fig.update_layout(
        title={
            "text": "Case Acceptance Rate Trends",
            "x": 0.5,
            "font": {"size": 16, "color": BRAND_COLORS["primary_navy"]},
        },
        xaxis_title="Date",
        yaxis_title="Case Acceptance Rate (%)",
        height=450,
        dragmode="zoom",
        hovermode="x unified",
        yaxis={"range": [0, 110]},
    )

    apply_axis_styling(fig, format_options.get("show_grid", True))
    fig.update_yaxes(tickformat=".1f", ticksuffix="%")
    apply_range_selector(fig)

    log.info(
        "chart.case_acceptance_created",
        data_points=len(dates),
        avg_rate=sum(values) / len(values) if values else 0,
    )

    return fig


def create_hygiene_reappointment_chart(
    chart_data: dict, format_options: dict | None = None
) -> Figure:
    """Create hygiene reappointment rate chart.

    Args:
        chart_data: Dictionary with dates, values, and metadata
        format_options: Chart formatting preferences

    Returns:
        Plotly figure with hygiene reappointment visualization
    """
    if format_options is None:
        format_options = {}

    log.info(
        "chart.hygiene_reappointment_creation_started",
        data_points=len(chart_data.get("dates", [])),
    )

    fig = create_base_figure()

    # Data validation
    dates = chart_data.get("dates", [])
    values = chart_data.get("values", [])

    if not dates or not values:
        log.warning("chart.hygiene_reappointment_no_data")
        return fig

    # Configure chart style
    line_color = format_options.get("line_color", BRAND_COLORS["accent"])
    fill_color = format_options.get("fill_color", f"{line_color}20")

    # Main data trace
    fig.add_scatter(
        x=dates,
        y=values,
        mode="lines+markers",
        line={"color": line_color, "width": 3},
        marker={
            "size": 8,
            "color": line_color,
            "line": {"width": 2, "color": "white"},
        },
        fill="tozeroy",
        fillcolor=fill_color,
        name="Reappointment Rate",
        hovertemplate="%{x}<br>Reappointment Rate: %{y:.1f}%<extra></extra>",
    )

    # Add trend line if requested
    if format_options.get("show_trend", False):
        add_trend_line(fig, dates, values, "Reappointment Trend")

    # Add target line (typically 90%+ for good practices)
    target_rate = format_options.get("target_reappointment", 90)
    if target_rate and target_rate > 0:
        fig.add_hline(
            y=target_rate,
            line_dash="dot",
            line_color=BRAND_COLORS["medium_gray"],
            annotation_text=f"Target: {target_rate}%",
            annotation_position="bottom right",
        )

    # Update layout
    fig.update_layout(
        title={
            "text": "Hygiene Reappointment Rate Trends",
            "x": 0.5,
            "font": {"size": 16, "color": BRAND_COLORS["primary_navy"]},
        },
        xaxis_title="Date",
        yaxis_title="Reappointment Rate (%)",
        height=450,
        dragmode="zoom",
        hovermode="x unified",
        yaxis={"range": [0, 110]},
    )

    apply_axis_styling(fig, format_options.get("show_grid", True))
    fig.update_yaxes(tickformat=".1f", ticksuffix="%")
    apply_range_selector(fig)

    log.info(
        "chart.hygiene_reappointment_created",
        data_points=len(dates),
        avg_rate=sum(values) / len(values) if values else 0,
    )

    return fig


# Chart dispatcher for dynamic chart creation
def create_chart_from_data(
    chart_data: dict, kpi_type: str, format_options: dict | None = None
) -> Figure:
    """Create appropriate chart based on KPI type.

    Args:
        chart_data: Dictionary with dates, values, and metadata
        kpi_type: Type of KPI chart to create
        format_options: Chart formatting preferences

    Returns:
        Plotly figure for the specified KPI type

    Raises:
        ValueError: If kpi_type is not supported
    """
    chart_creators = {
        "collection_rate": create_collection_rate_chart,
        "new_patients": create_new_patients_chart,
        "case_acceptance": create_case_acceptance_chart,
        "hygiene_reappointment": create_hygiene_reappointment_chart,
    }

    if kpi_type not in chart_creators:
        available_types = ", ".join(chart_creators.keys())
        raise ValueError(f"Unknown KPI type: {kpi_type}. Available: {available_types}")

    log.info("chart.dynamic_creation", kpi_type=kpi_type)
    return chart_creators[kpi_type](chart_data, format_options)
