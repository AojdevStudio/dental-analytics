"""Kam Dental Analytics Dashboard - 5 KPIs from Google Sheets with Dual Location Support."""

from datetime import datetime
from pathlib import Path

import streamlit as st

from backend.metrics import get_all_kpis

st.set_page_config(
    page_title="Kam Dental Analytics", layout="wide", initial_sidebar_state="collapsed"
)


def display_location_kpis(kpis: dict[str, float | None], location_name: str):
    """Display KPIs for a specific location."""

    # Display location header
    st.markdown(
        f"<h2 style='text-align: center; color: #007E9E; margin-bottom: 1rem;'>"
        f"{location_name.upper()} LOCATION</h2>",
        unsafe_allow_html=True,
    )

    # Primary metrics (2 columns)
    col1, col2 = st.columns(2)

    with col1:
        if kpis.get("production_total") is not None:
            st.metric(
                label="DAILY PRODUCTION", value=f"${kpis['production_total']:,.0f}"
            )
        else:
            st.metric(label="DAILY PRODUCTION", value="Data Unavailable")

    with col2:
        if kpis.get("collection_rate") is not None:
            st.metric(label="COLLECTION RATE", value=f"{kpis['collection_rate']:.1f}%")
        else:
            st.metric(label="COLLECTION RATE", value="Data Unavailable")

    # Secondary metrics (3 columns)
    col3, col4, col5 = st.columns(3)

    with col3:
        if kpis.get("new_patients") is not None:
            st.metric(label="NEW PATIENTS", value=str(int(kpis["new_patients"])))
        else:
            st.metric(label="NEW PATIENTS", value="Data Unavailable")

    with col4:
        if kpis.get("treatment_acceptance") is not None:
            st.metric(
                label="TREATMENT ACCEPTANCE",
                value=f"{kpis['treatment_acceptance']:.1f}%",
            )
        else:
            st.metric(label="TREATMENT ACCEPTANCE", value="Data Unavailable")

    with col5:
        if kpis.get("hygiene_reappointment") is not None:
            st.metric(
                label="HYGIENE REAPPOINTMENT",
                value=f"{kpis['hygiene_reappointment']:.1f}%",
            )
        else:
            st.metric(label="HYGIENE REAPPOINTMENT", value="Data Unavailable")


def main():
    """Main dashboard application with dual location tabs."""
    # Validate credentials before proceeding
    if not Path("config/credentials.json").exists():
        st.error("⚠️ Credentials file not found. Please add config/credentials.json")
        return

    # Main header
    st.markdown(
        "<h1 style='text-align: center; color: #142D54; margin-bottom: 2rem;'>"
        "KAM DENTAL ANALYTICS</h1>",
        unsafe_allow_html=True,
    )

    # Get KPIs for both locations
    all_kpis = get_all_kpis()

    # Create tabs for each location
    baytown_tab, humble_tab = st.tabs(["📍 Baytown", "📍 Humble"])

    with baytown_tab:
        if "baytown" in all_kpis:
            display_location_kpis(all_kpis["baytown"], "Baytown")
        else:
            st.error("Unable to load Baytown data")

    with humble_tab:
        if "humble" in all_kpis:
            display_location_kpis(all_kpis["humble"], "Humble")
        else:
            st.error("Unable to load Humble data")

    # Footer
    st.caption(f"Last Updated: {datetime.now().strftime('%I:%M %p')}")


if __name__ == "__main__":
    main()
