"""Base configuration and styling for Plotly charts.

Contains brand colors, chart configurations, and base figure creation.
Keeps all chart foundation elements under 150 lines.
"""

import plotly.graph_objects as go
from plotly.graph_objects import Figure, layout

# KamDental Brand Colors with all required keys
BRAND_COLORS = {
    "primary_navy": "#142D54",
    "teal_accent": "#007E9E",
    "emergency_red": "#BB0A0A",
    "light_gray": "#F8F9FA",
    "medium_gray": "#6C757D",
    "success_green": "#28A745",
    "border": "#E9ECEF",  # Light border color for annotations
    "warning": "#FFC107",  # Yellow warning color for underperforming
    "accent": "#17A2B8",  # Cyan accent color for highlights
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
BASE_LAYOUT = go.Layout(
    font=layout.Font(
        family="Arial, sans-serif",
        size=12,
        color=BRAND_COLORS["primary_navy"],
    ),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=layout.Margin(l=60, r=20, t=60, b=60),
    showlegend=False,  # Single series charts don't need legends
    hovermode="x unified",
    dragmode="zoom",  # Enable zoom by default
)

# Grid and axis styling
GRID_CONFIG: dict[str, bool | float | str] = {
    "showgrid": True,
    "gridcolor": "#E9ECEF",
    "gridwidth": 1,
    "zeroline": True,
    "zerolinecolor": "#CED4DA",
    "zerolinewidth": 1,
}


def _build_axis_configs(show_grid: bool) -> tuple[layout.XAxis, layout.YAxis]:
    """Create consistent x/y axis objects with shared styling."""

    if show_grid:
        axis_overrides = GRID_CONFIG
    else:
        axis_overrides = {"showgrid": False, "zeroline": False}

    x_axis = layout.XAxis(
        linecolor=BRAND_COLORS["medium_gray"],
        linewidth=1,
        ticks="outside",
        tickcolor=BRAND_COLORS["medium_gray"],
        tickfont=layout.xaxis.Tickfont(
            color=BRAND_COLORS["primary_navy"],
            size=10,
        ),
        title=layout.xaxis.Title(
            font=layout.xaxis.title.Font(
                color=BRAND_COLORS["primary_navy"],
                size=12,
            )
        ),
        **axis_overrides,
    )

    y_axis = layout.YAxis(
        linecolor=BRAND_COLORS["medium_gray"],
        linewidth=1,
        ticks="outside",
        tickcolor=BRAND_COLORS["medium_gray"],
        tickfont=layout.yaxis.Tickfont(
            color=BRAND_COLORS["primary_navy"],
            size=10,
        ),
        title=layout.yaxis.Title(
            font=layout.yaxis.title.Font(
                color=BRAND_COLORS["primary_navy"],
                size=12,
            )
        ),
        **axis_overrides,
    )

    return x_axis, y_axis


def create_base_figure() -> Figure:
    """Create base Plotly figure with KamDental branding.

    Returns:
        Configured base figure with brand styling
    """
    fig = go.Figure()
    fig.update_layout(BASE_LAYOUT)
    return fig


def apply_axis_styling(fig: Figure, show_grid: bool = True) -> None:
    """Apply consistent axis styling to figure.

    Args:
        fig: Plotly figure to style
        show_grid: Whether to show grid lines
    """
    x_axis, y_axis = _build_axis_configs(show_grid)

    fig.update_xaxes(x_axis)
    fig.update_yaxes(y_axis)


def get_range_selector_buttons() -> list[layout.xaxis.rangeselector.Button]:
    """Get standard range selector buttons for time series charts.

    Returns:
        List of range selector button configurations
    """
    return [
        layout.xaxis.rangeselector.Button(
            count=7,
            label="1w",
            step="day",
            stepmode="backward",
        ),
        layout.xaxis.rangeselector.Button(
            count=14,
            label="2w",
            step="day",
            stepmode="backward",
        ),
        layout.xaxis.rangeselector.Button(
            count=1,
            label="1m",
            step="month",
            stepmode="backward",
        ),
        layout.xaxis.rangeselector.Button(step="all", label="All"),
    ]


def apply_range_selector(fig: Figure) -> None:
    """Apply range selector buttons to a figure.

    Args:
        fig: Plotly figure to add range selector to
    """
    fig.update_xaxes(
        rangeselector=layout.xaxis.Rangeselector(
            buttons=get_range_selector_buttons(),
            bgcolor="rgba(255,255,255,0.7)",
            activecolor=BRAND_COLORS["teal_accent"],
            x=0,
            y=1.1,
        ),
        rangeslider=layout.xaxis.Rangeslider(visible=False),
    )
