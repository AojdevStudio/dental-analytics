"""
Kam Dental Analytics Dashboard - 5 KPIs from Google Sheets with
Dual Location Support.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

import streamlit as st

# Add project root to Python path for proper import resolution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from apps.backend.chart_data import format_all_chart_data  # noqa: E402
from apps.backend.data_providers import SheetsProvider  # noqa: E402
from apps.backend.metrics import get_all_kpis  # noqa: E402
from apps.frontend.chart_components import create_chart_from_data  # noqa: E402

# Configure Streamlit page settings
st.set_page_config(
    page_title="KamDental Analytics",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Location Selector (Task 1 & 2: Location UI and State Management)
location = st.radio(
    "📍 **Select Location:**",
    options=["baytown", "humble"],
    format_func=lambda x: x.title(),
    horizontal=True,
    key="location_selector",
    help="Choose which practice location to view KPI data for",
)

# Custom CSS for KamDental branding with location-specific accents
location_colors = {
    "baytown": {
        "primary": "#142D54",
        "accent": "#00556B",
        "bg": "rgba(20, 45, 84, 0.05)",
    },
    "humble": {
        "primary": "#007E9E",
        "accent": "#FF6642",
        "bg": "rgba(0, 126, 158, 0.05)",
    },
}

current_colors = location_colors[location]

st.markdown(
    f"""
<style>
    .main > div {{
        padding-top: 2rem;
        background: {current_colors['bg']};
        border-radius: 0.5rem;
    }}
    .metric-container {{
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid {current_colors['primary']};
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    .stMetric > label {{
        color: {current_colors['primary']} !important;
        font-weight: 600;
    }}
    .stMetric > div {{
        color: {current_colors['accent']} !important;
    }}
    .stRadio > div {{
        border: 2px solid {current_colors['primary']};
        border-radius: 0.5rem;
        padding: 0.5rem;
        background: white;
    }}
    .location-indicator {{
        background: {current_colors['primary']};
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-left: 0.5rem;
    }}
</style>
""",
    unsafe_allow_html=True,
)

# Header section with location indicator
st.markdown(
    f"""
    # 🦷 KamDental Analytics Dashboard
    <span class="location-indicator">{location.title()}</span>
    """,
    unsafe_allow_html=True,
)
st.markdown(f"**Daily KPI Report** • {datetime.now().strftime('%B %d, %Y')}")
st.markdown("---")

# Load KPI data and chart data (Task 3: Location-aware data calls)
with st.spinner(f"Loading {location.title()} KPI data from Google Sheets..."):
    try:
        kpis = get_all_kpis(location=location)

        # Load chart data for interactive visualizations
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

        chart_data = format_all_chart_data(eod_df, front_df)

        st.success(f"✅ {location.title()} data loaded successfully")
    except Exception as e:
        st.error(f"❌ Failed to load {location.title()} data: {str(e)}")
        kpis = {}
        chart_data = {}

# Primary metrics row (2 columns)
col1, col2 = st.columns(2)

with col1:
    if kpis.get("production_total") is not None:
        st.metric(
            label="💰 DAILY PRODUCTION",
            value=f"${kpis['production_total']:,.0f}",
            help="Total Production + Adjustments + Write-offs",
        )
    else:
        st.metric(label="💰 DAILY PRODUCTION", value="Data Unavailable")

with col2:
    if kpis.get("collection_rate") is not None:
        rate = kpis["collection_rate"]
        rate_delta_color: Literal["normal", "inverse"] = (
            "normal" if rate is not None and rate >= 95 else "inverse"
        )
        st.metric(
            label="📊 COLLECTION RATE",
            value=f"{rate:.1f}%",
            delta="Target: 95%",
            delta_color=rate_delta_color,
            help="(Collections ÷ Production) × 100",
        )
    else:
        st.metric(label="📊 COLLECTION RATE", value="Data Unavailable")

st.markdown("---")

# Secondary metrics row (3 columns)
col3, col4, col5 = st.columns(3)

with col3:
    if kpis.get("new_patients") is not None:
        st.metric(
            label="👥 NEW PATIENTS",
            value=f"{kpis['new_patients']:,}",
            help="Count of new patients today",
        )
    else:
        st.metric(label="👥 NEW PATIENTS", value="Data Unavailable")

with col4:
    if kpis.get("case_acceptance") is not None:
        acceptance = kpis["case_acceptance"]
        acceptance_delta_color: Literal["normal", "inverse"] = (
            "normal" if acceptance is not None and acceptance >= 85 else "inverse"
        )
        st.metric(
            label="✅ CASE ACCEPTANCE",
            value=f"{acceptance:.1f}%",
            delta="Target: 85%",
            delta_color=acceptance_delta_color,
            help="((Scheduled $ + Same Day $) ÷ Presented $) × 100",
        )
    else:
        st.metric(label="✅ CASE ACCEPTANCE", value="Data Unavailable")

with col5:
    if kpis.get("hygiene_reappointment") is not None:
        reappointment = kpis["hygiene_reappointment"]
        reappointment_delta_color: Literal["normal", "inverse"] = (
            "normal" if reappointment is not None and reappointment >= 90 else "inverse"
        )
        st.metric(
            label="🔄 HYGIENE REAPPOINTMENT",
            value=f"{reappointment:.1f}%",
            delta="Target: 90%",
            delta_color=reappointment_delta_color,
            help="((Total Hygiene - Not Reappointed) ÷ Total Hygiene) × 100",
        )
    else:
        st.metric(label="🔄 HYGIENE REAPPOINTMENT", value="Data Unavailable")

# Interactive Charts Section (Story 2.2: Plotly Charts)
st.markdown("---")
st.markdown("## 📊 **Interactive KPI Charts**")
st.markdown("Explore your data with interactive charts featuring zoom, hover, and pan.")

# Chart display with tabs for organized viewing
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "💰 Production",
        "📊 Collection Rate",
        "👥 New Patients",
        "✅ Case Acceptance",
        "🔄 Hygiene Reappointment",
    ]
)

with tab1:
    if chart_data and "production_total" in chart_data:
        production_chart = create_chart_from_data(chart_data["production_total"])
        st.plotly_chart(production_chart, use_container_width=True)
    else:
        st.info("📈 Production chart data unavailable for selected location")

with tab2:
    if chart_data and "collection_rate" in chart_data:
        collection_chart = create_chart_from_data(chart_data["collection_rate"])
        st.plotly_chart(collection_chart, use_container_width=True)
    else:
        st.info("📈 Collection rate chart data unavailable for selected location")

with tab3:
    if chart_data and "new_patients" in chart_data:
        new_patients_chart = create_chart_from_data(chart_data["new_patients"])
        st.plotly_chart(new_patients_chart, use_container_width=True)
    else:
        st.info("📈 New patients chart data unavailable for selected location")

with tab4:
    if chart_data and "case_acceptance" in chart_data:
        treatment_chart = create_chart_from_data(chart_data["case_acceptance"])
        st.plotly_chart(treatment_chart, use_container_width=True)
    else:
        st.info("📈 Treatment acceptance chart data unavailable for selected location")

with tab5:
    if chart_data and "hygiene_reappointment" in chart_data:
        hygiene_chart = create_chart_from_data(chart_data["hygiene_reappointment"])
        st.plotly_chart(hygiene_chart, use_container_width=True)
    else:
        st.info("📈 Hygiene reappointment chart data unavailable for selected location")

# Footer (Task 5: Location-specific footer)
st.markdown("---")
st.markdown(
    f"**Data Source:** Google Sheets • **Updated:** Real-time • "
    f"**Current Location:** {location.title()}"
)
