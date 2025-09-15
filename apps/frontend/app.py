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

from apps.backend.metrics import get_all_kpis  # noqa: E402

# Configure Streamlit page settings
st.set_page_config(
    page_title="KamDental Analytics",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for KamDental branding
st.markdown(
    """
<style>
    .main > div {
        padding-top: 2rem;
    }
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007E9E;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric > label {
        color: #142D54 !important;
        font-weight: 600;
    }
    .stMetric > div {
        color: #007E9E !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Header section
st.markdown("# 🦷 KamDental Analytics Dashboard")
st.markdown(f"**Daily KPI Report** • {datetime.now().strftime('%B %d, %Y')}")
st.markdown("---")

# Load KPI data
with st.spinner("Loading KPI data from Google Sheets..."):
    try:
        kpis = get_all_kpis()
        st.success("✅ Data loaded successfully")
    except Exception as e:
        st.error(f"❌ Failed to load data: {str(e)}")
        kpis = {}

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
    if kpis.get("treatment_acceptance") is not None:
        acceptance = kpis["treatment_acceptance"]
        acceptance_delta_color: Literal["normal", "inverse"] = (
            "normal" if acceptance is not None and acceptance >= 85 else "inverse"
        )
        st.metric(
            label="✅ TREATMENT ACCEPTANCE",
            value=f"{acceptance:.1f}%",
            delta="Target: 85%",
            delta_color=acceptance_delta_color,
            help="(Treatments Scheduled ÷ Treatments Presented) × 100",
        )
    else:
        st.metric(label="✅ TREATMENT ACCEPTANCE", value="Data Unavailable")

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

# Footer
st.markdown("---")
st.markdown(
    "**Data Source:** Google Sheets • **Updated:** Real-time • "
    "**Locations:** Baytown & Humble"
)
