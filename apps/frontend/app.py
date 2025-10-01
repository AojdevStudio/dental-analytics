"""
Main Streamlit dashboard application for Kam Dental Analytics.

This application displays 5 key dental practice KPIs in a clean, branded interface:
- Production Total (daily revenue)
- Collection Rate (payment efficiency)
- New Patient Count (growth metric)
- Case Acceptance (treatment conversion)
- Hygiene Reappointment Rate (patient retention)

Features:
- Multi-location support (Baytown and Humble)
- Real-time Google Sheets integration
- Interactive charts with historical data
- Responsive design with brand colors
- Performance-optimized caching
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import streamlit as st

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from apps.backend.chart_data import format_all_chart_data  # noqa: E402
from apps.backend.data_providers import SheetsProvider  # noqa: E402
from apps.frontend.chart_kpis import create_chart_from_data  # noqa: E402
from core.business_rules.calendar import BusinessCalendar  # noqa: E402
from core.business_rules.validation_rules import KPIValidationRules  # noqa: E402
from core.models.kpi_models import (  # noqa: E402
    DataAvailabilityStatus,
    KPIResponse,
)
from core.transformers.sheets_transformer import SheetsToKPIInputs  # noqa: E402

# New KPIService and dependencies (Story 3.0: Checkpoint 3)
from services.kpi_service import KPIService  # noqa: E402

# Configure Streamlit page settings
st.set_page_config(
    page_title="Kam Dental Analytics",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Location selector at the top
st.markdown("### 📍 **Practice Location**")
location = st.radio(
    "Select practice location:",
    options=["baytown", "humble"],
    format_func=lambda x: x.title(),
    horizontal=True,
    help="Choose which practice location to view KPI data for",
)

# Location selector only (Chart Time Range moved to Interactive Charts section)
col_location = st.columns([1])[0]

# Custom CSS for KamDental branding with location-specific accents
location_colors = {
    "baytown": {
        "primary": "#142D54",  # Navy blue
        "accent": "#007E9E",  # Teal
        "success": "#28a745",
        "warning": "#ffc107",
        "danger": "#dc3545",
    },
    "humble": {
        "primary": "#142D54",  # Navy blue
        "accent": "#6F42C1",  # Purple accent for differentiation
        "success": "#28a745",
        "warning": "#ffc107",
        "danger": "#dc3545",
    },
}

colors = location_colors[location]

st.markdown(
    f"""
    <style>
    .main-header {{
        color: {colors["primary"]};
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }}
    .location-badge {{
        background: linear-gradient(135deg, {colors["accent"]}, {colors["primary"]});
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }}
    .metric-container {{
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid {colors["accent"]};
        margin: 0.5rem 0;
    }}
    .metric-title {{
        color: {colors["primary"]};
        font-weight: bold;
        font-size: 1.1rem;
    }}
    .metric-value {{
        color: {colors["accent"]};
        font-size: 2rem;
        font-weight: bold;
    }}
    .subtitle {{
        color: {colors["primary"]};
        text-align: center;
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }}
    .stSelectbox > div > div {{
        background-color: {colors["accent"]};
        color: white;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Main header with location indicator
st.markdown(
    '<h1 class="main-header">🦷 KAM DENTAL ANALYTICS</h1>', unsafe_allow_html=True
)
location_badge_html = (
    f'<div style="text-align: center;">'
    f'<span class="location-badge">{location.title()} Practice</span></div>'
)
st.markdown(location_badge_html, unsafe_allow_html=True)
st.markdown('<p class="subtitle">Real-time KPI Dashboard</p>', unsafe_allow_html=True)

# Date and separator
st.markdown(f"**Daily KPI Report** • {datetime.now().strftime('%B %d, %Y')}")
st.markdown("---")


# Cache function for chart data (Story 2.3: Performance Optimization)
@st.cache_data(ttl=300)  # 5 minute cache
def load_chart_data(location: str) -> dict[str, Any] | None:
    """Load chart data with caching for performance."""
    try:
        provider = SheetsProvider()
        eod_alias = f"{location}_eod"
        front_alias = f"{location}_front"

        eod_df = (
            provider.fetch(eod_alias) if provider.validate_alias(eod_alias) else None
        )
        front_df = (
            provider.fetch(front_alias)
            if provider.validate_alias(front_alias)
            else None
        )

        if eod_df is not None and front_df is not None:
            return format_all_chart_data(eod_df, front_df)
    except Exception as e:
        st.error(f"Error loading chart data: {e}")
    return None


# Cache KPI data separately for faster updates
@st.cache_data(ttl=300)  # 5 minute cache
def load_kpi_data(location: str) -> KPIResponse:
    """Load KPI data using new KPIService with caching."""
    # Initialize dependencies
    provider = SheetsProvider()
    calendar = BusinessCalendar()
    validation_rules = KPIValidationRules()
    transformer = SheetsToKPIInputs()

    # Create service with dependency injection
    service = KPIService(
        data_provider=provider,
        calendar=calendar,
        validation_rules=validation_rules,
        transformer=transformer,
    )

    # Get KPIs for today
    from datetime import date
    from typing import cast

    from core.models.kpi_models import Location

    return service.get_kpis(cast(Location, location), date.today())


# Load KPI data and chart data (Task 3: Location-aware data calls)
with st.spinner(f"Loading {location.title()} KPI data from Google Sheets..."):
    try:
        # Use cached functions for better performance
        kpi_response = load_kpi_data(location)

        # Load chart data for interactive visualizations
        chart_data = load_chart_data(location)

        # Check if location is closed
        if kpi_response.availability == DataAvailabilityStatus.EXPECTED_CLOSURE:
            st.warning(f"⚠️ {location.title()} Practice: {kpi_response.closure_reason}")
        elif kpi_response.availability == DataAvailabilityStatus.INFRASTRUCTURE_ERROR:
            reason = kpi_response.values.production_total.unavailable_reason
            st.error(f"❌ Infrastructure error: {reason}")
        elif kpi_response.availability == DataAvailabilityStatus.DATA_NOT_READY:
            st.info("ℹ️ Data not yet available for today")
        elif kpi_response.availability == DataAvailabilityStatus.PARTIAL:
            st.warning("⚠️ Partial data available - some KPIs may be unavailable")
        else:
            st.success(f"✅ {location.title()} data loaded successfully")

        # Display data freshness information
        if kpi_response.data_freshness:
            with st.expander("📅 Data Freshness", expanded=False):
                for freshness in kpi_response.data_freshness:
                    timestamp = freshness.as_of.strftime("%Y-%m-%d %I:%M %p")
                    st.caption(f"**{freshness.source_alias}**: {timestamp}")

        # Display validation warnings if any
        if kpi_response.validation_summary:
            with st.expander("⚠️ Validation Warnings", expanded=False):
                for issue in kpi_response.validation_summary:
                    severity_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}
                    emoji = severity_emoji.get(issue.severity.value, "•")
                    st.write(f"{emoji} {issue.message}")

    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.info("Please check your internet connection and try refreshing the page.")
        # Create minimal error response
        from typing import cast

        from core.models.kpi_models import KPIValue, KPIValues, Location

        unavailable_kpi = KPIValue(
            value=None,
            available=False,
            availability_status=DataAvailabilityStatus.INFRASTRUCTURE_ERROR,
            unavailable_reason=str(e),
            validation_issues=[],
        )
        from datetime import date

        kpi_response = KPIResponse(
            location=cast(Location, location),
            business_date=date.today(),
            availability=DataAvailabilityStatus.INFRASTRUCTURE_ERROR,
            values=KPIValues(
                production_total=unavailable_kpi,
                collection_rate=unavailable_kpi,
                new_patients=unavailable_kpi,
                case_acceptance=unavailable_kpi,
                hygiene_reappointment=unavailable_kpi,
            ),
            data_freshness=[],
            closure_reason=None,
            validation_summary=[],
        )
        chart_data = None

# Primary KPIs Row (2 columns)
st.markdown("## 💰 **Primary Financial Metrics**")
col1, col2 = st.columns(2)

with col1:
    production_kpi = kpi_response.values.production_total
    if production_kpi.available and production_kpi.value is not None:
        st.metric(
            label="📈 **Production Total**",
            value=f"${production_kpi.value:,.0f}",
            help="Total production (revenue) for the selected time period",
        )
    else:
        unavailable_reason = production_kpi.unavailable_reason or "Data Unavailable"
        st.metric(label="📈 **Production Total**", value=unavailable_reason)

with col2:
    collection_kpi = kpi_response.values.collection_rate
    if collection_kpi.available and collection_kpi.value is not None:
        collection_delta_color: Literal["normal", "inverse", "off"] = (
            "normal" if collection_kpi.value >= 95 else "inverse"
        )
        st.metric(
            label="💳 **Collection Rate**",
            value=f"{collection_kpi.value:.1f}%",
            delta="Target: 95%",
            delta_color=collection_delta_color,
            help="Percentage of production successfully collected (Target: 95%+)",
        )
    else:
        unavailable_reason = collection_kpi.unavailable_reason or "Data Unavailable"
        st.metric(label="💳 **Collection Rate**", value=unavailable_reason)

# Secondary KPIs Row (3 columns)
st.markdown("---")
st.markdown("## 📊 **Operational Metrics**")
col3, col4, col5 = st.columns(3)

with col3:
    new_patients_kpi = kpi_response.values.new_patients
    if new_patients_kpi.available and new_patients_kpi.value is not None:
        st.metric(
            label="👥 **New Patients**",
            value=f"{int(new_patients_kpi.value):,}",
            help="Total new patients for the month to date",
        )
    else:
        unavailable_reason = new_patients_kpi.unavailable_reason or "Data Unavailable"
        st.metric(label="👥 **New Patients**", value=unavailable_reason)

with col4:
    case_acceptance_kpi = kpi_response.values.case_acceptance
    if case_acceptance_kpi.available and case_acceptance_kpi.value is not None:
        acceptance_delta_color: Literal["normal", "inverse", "off"] = (
            "normal" if case_acceptance_kpi.value >= 80 else "inverse"
        )
        st.metric(
            label="✅ **Case Acceptance**",
            value=f"{case_acceptance_kpi.value:.1f}%",
            delta="Target: 80%",
            delta_color=acceptance_delta_color,
            help="Percentage of presented treatments that were accepted (Target: 80%+)",
        )
    else:
        unavailable_reason = (
            case_acceptance_kpi.unavailable_reason or "Data Unavailable"
        )
        st.metric(label="✅ **Case Acceptance**", value=unavailable_reason)

with col5:
    hygiene_kpi = kpi_response.values.hygiene_reappointment
    if hygiene_kpi.available and hygiene_kpi.value is not None:
        hygiene_delta_color: Literal["normal", "inverse", "off"] = (
            "normal" if hygiene_kpi.value >= 90 else "inverse"
        )
        hygiene_help = (
            "Percentage of hygiene patients who scheduled "
            "next appointment (Target: 90%+)"
        )
        st.metric(
            label="🔄 **Hygiene Reappointment**",
            value=f"{hygiene_kpi.value:.1f}%",
            delta="Target: 90%",
            delta_color=hygiene_delta_color,
            help=hygiene_help,
        )
    else:
        unavailable_reason = hygiene_kpi.unavailable_reason or "Data Unavailable"
        st.metric(label="🔄 **Hygiene Reappointment**", value=unavailable_reason)

# Interactive Charts Section
st.markdown("---")
st.markdown("## 📊 **Interactive KPI Charts**")
st.markdown("Explore your data with interactive charts featuring zoom, hover, and pan.")

# Time Range Selector (Story 2.3) - Moved to be contextual with charts
timeframe = st.radio(
    "📊 **Chart Time Range:**",
    options=["daily", "weekly", "monthly"],
    format_func=lambda x: x.capitalize(),
    horizontal=True,
    key="timeframe_selector",
    help="Select the time aggregation for historical charts",
    index=0,  # Default to daily view
)

# Chart display with tabs for organized viewing
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📈 Production",
        "💳 Collection Rate",
        "👥 New Patients",
        "✅ Case Acceptance",
        "🔄 Hygiene Reappointment",
    ]
)

with tab1:
    if chart_data and "production_total" in chart_data:
        # Pass timeframe parameter for advanced features (Story 2.3)
        production_chart = create_chart_from_data(
            chart_data["production_total"], show_trend=True, timeframe=timeframe
        )
        st.plotly_chart(
            production_chart, use_container_width=True, key="production_chart"
        )
    else:
        st.info("📈 Production chart data unavailable for selected location")

with tab2:
    if chart_data and "collection_rate" in chart_data:
        collection_chart = create_chart_from_data(
            chart_data["collection_rate"], show_trend=True, timeframe=timeframe
        )
        st.plotly_chart(
            collection_chart, use_container_width=True, key="collection_chart"
        )
    else:
        st.info("📈 Collection rate chart data unavailable for selected location")

with tab3:
    if chart_data and "new_patients" in chart_data:
        new_patients_chart = create_chart_from_data(
            chart_data["new_patients"], show_trend=True, timeframe=timeframe
        )
        st.plotly_chart(
            new_patients_chart, use_container_width=True, key="new_patients_chart"
        )
    else:
        st.info("📈 New patients chart data unavailable for selected location")

with tab4:
    if chart_data and "case_acceptance" in chart_data:
        treatment_chart = create_chart_from_data(
            chart_data["case_acceptance"], show_trend=True, timeframe=timeframe
        )
        st.plotly_chart(
            treatment_chart, use_container_width=True, key="treatment_chart"
        )
    else:
        st.info("📈 Treatment acceptance chart data unavailable for selected location")

with tab5:
    if chart_data and "hygiene_reappointment" in chart_data:
        hygiene_chart = create_chart_from_data(
            chart_data["hygiene_reappointment"], show_trend=True, timeframe=timeframe
        )
        st.plotly_chart(hygiene_chart, use_container_width=True, key="hygiene_chart")
    else:
        st.info("📈 Hygiene reappointment chart data unavailable for selected location")

# Footer
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: {colors["primary"]}; padding: 1rem;'>
        <small>
        ⚡ Powered by Google Sheets API •
        🔄 Auto-refreshes on page reload •
        📊 Real-time data from {location.title()} Practice
        </small>
    </div>
    """,
    unsafe_allow_html=True,
)
