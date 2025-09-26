"""Base configuration and styling for Plotly charts.

Contains brand colors, chart configurations, and base figure creation.
Keeps all chart foundation elements under 150 lines.
"""

import plotly.graph_objects as go
from plotly.graph_objects import Figure

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


def get_range_selector_buttons() -> list:
    """Get standard range selector buttons for time series charts.

    Returns:
        List of range selector button configurations
    """
    return [
        {"count": 7, "label": "1w", "step": "day", "stepmode": "backward"},
        {"count": 14, "label": "2w", "step": "day", "stepmode": "backward"},
        {"count": 1, "label": "1m", "step": "month", "stepmode": "backward"},
        {"step": "all", "label": "All"},
    ]


def apply_range_selector(fig: Figure) -> None:
    """Apply range selector buttons to a figure.

    Args:
        fig: Plotly figure to add range selector to
    """
    fig.update_xaxes(
        rangeselector={
            "buttons": list(get_range_selector_buttons()),
            "bgcolor": "rgba(255,255,255,0.7)",
            "activecolor": BRAND_COLORS["teal_accent"],
            "x": 0,
            "y": 1.1,
        },
        rangeslider={"visible": False},  # Hide range slider for cleaner look
    )
