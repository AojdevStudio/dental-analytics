"""
KPI Calculations for Dental Practice Analytics.

This module calculates 5 core KPIs from Google Sheets data:
1. Production Total (daily revenue)
2. Collection Rate (collections/production percentage)
3. New Patient Count (daily new patients)
4. Treatment Acceptance (scheduled/presented percentage)
5. Hygiene Reappointment Rate (reappointed/total percentage)

Functions handle missing data gracefully and return None for failed calculations.
"""

import logging

import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_all_kpis() -> dict[str, float | int | None]:
    """
    Get all 5 KPIs by reading from Google Sheets.

    Returns dict with keys: production_total, collection_rate, new_patients,
    treatment_acceptance, hygiene_reappointment
    """
    from backend.sheets_reader import SheetsReader

    try:
        reader = SheetsReader()

        # Get data from both sheets
        eod_data = reader.get_eod_data()
        front_kpi_data = reader.get_front_kpi_data()

        return {
            "production_total": calculate_production_total(eod_data),
            "collection_rate": calculate_collection_rate(eod_data),
            "new_patients": calculate_new_patients(eod_data),
            "treatment_acceptance": calculate_treatment_acceptance(front_kpi_data),
            "hygiene_reappointment": calculate_hygiene_reappointment(front_kpi_data),
        }
    except Exception as e:
        logger.error(f"Error retrieving KPI data: {e}")
        return {
            "production_total": None,
            "collection_rate": None,
            "new_patients": None,
            "treatment_acceptance": None,
            "hygiene_reappointment": None,
        }


def safe_numeric_conversion(df: pd.DataFrame, column: str) -> float:
    """Safely convert column values to numeric, handling errors gracefully."""
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found in DataFrame")
        return 0.0

    # Handle case where value might be a pandas Series with single value
    value = df[column].iloc[0] if len(df) > 0 else 0

    # Convert to numeric, return 0 if conversion fails or is NaN
    numeric_value = pd.to_numeric(value, errors="coerce")
    return 0.0 if pd.isna(numeric_value) else float(numeric_value)


def calculate_production_total(df: pd.DataFrame | None) -> float | None:
    """
    Calculate daily production: Column I + J + K
    (Total Production + Adjustments + Write-offs).
    """
    if df is None or df.empty:
        return None

    # Check if required column exists
    if "total_production" not in df.columns:
        return None

    # Column I: Total Production Today
    production = safe_numeric_conversion(df, "total_production")
    # Column J: Adjustments Today (optional)
    adjustments = (
        safe_numeric_conversion(df, "adjustments")
        if "adjustments" in df.columns
        else 0.0
    )
    # Column K: Write-offs Today (optional)
    writeoffs = (
        safe_numeric_conversion(df, "writeoffs") if "writeoffs" in df.columns else 0.0
    )

    total = production + adjustments + writeoffs
    logger.info(
        f"Production calculation: ${production:,.0f} + ${adjustments:,.0f} "
        f"+ ${writeoffs:,.0f} = ${total:,.0f}"
    )

    return float(total)


def calculate_collection_rate(df: pd.DataFrame | None) -> float | None:
    """
    Calculate collection rate: (Collections / Production) * 100.

    Returns percentage (0-100) or None if calculation fails.
    """
    if df is None or df.empty:
        return None

    # Check required columns
    if "total_production" not in df.columns or "total_collections" not in df.columns:
        return None

    # Column I: Production; Column J: Collections
    production = safe_numeric_conversion(df, "total_production")
    collections = safe_numeric_conversion(df, "total_collections")

    # Avoid division by zero
    if production == 0:
        logger.warning("Production is zero, cannot calculate collection rate")
        return None

    rate = (collections / production) * 100
    logger.info(
        f"Collection rate: ${collections:,.0f} / ${production:,.0f} = {rate:.1f}%"
    )

    return float(rate)


def calculate_new_patients(df: pd.DataFrame | None) -> int | None:
    """
    Calculate new patients count from Column J.

    Returns count or None if calculation fails.
    """
    if df is None or df.empty:
        return None

    # Check required column
    if "new_patients" not in df.columns:
        return None

    # Column J: New Patients Today
    count = safe_numeric_conversion(df, "new_patients")
    logger.info(f"New patients: {count}")

    return int(count)


def calculate_treatment_acceptance(df: pd.DataFrame | None) -> float | None:
    """
    Calculate treatment acceptance: (Treatments Scheduled / Treatments Presented) * 100.

    Returns percentage (0-100) or None if calculation fails.
    """
    if df is None or df.empty:
        return None

    # Check required columns exist
    if (
        "treatments_presented" not in df.columns
        or "treatments_scheduled" not in df.columns
    ):
        return None

    # Column M: Treatments Presented, Column N: Treatments Scheduled
    presented = safe_numeric_conversion(df, "treatments_presented")
    scheduled = safe_numeric_conversion(df, "treatments_scheduled")

    # Avoid division by zero
    if presented == 0:
        logger.warning("No treatments presented, cannot calculate acceptance rate")
        return None

    rate = (scheduled / presented) * 100
    logger.info(
        f"Treatment acceptance: ${scheduled:,.0f} / ${presented:,.0f} = {rate:.1f}%"
    )

    return float(rate)


def calculate_hygiene_reappointment(df: pd.DataFrame | None) -> float | None:
    """
    Calculate hygiene reappointment rate: ((Total - Not Reappointed) / Total) * 100.

    Returns percentage (0-100) or None if calculation fails.
    """
    if df is None or df.empty:
        return None

    # Check required columns exist
    if (
        "total_hygiene_appointments" not in df.columns
        or "patients_not_reappointed" not in df.columns
    ):
        return None

    # Column L: Total Hygiene, Column M: Patients Not Reappointed
    total_hygiene = safe_numeric_conversion(df, "total_hygiene_appointments")
    not_reappointed = safe_numeric_conversion(df, "patients_not_reappointed")

    # Avoid division by zero
    if total_hygiene == 0:
        logger.warning("No hygiene appointments, cannot calculate reappointment rate")
        return None

    reappointed = total_hygiene - not_reappointed
    rate = (reappointed / total_hygiene) * 100

    logger.info(f"Hygiene reappointment: {reappointed} / {total_hygiene} = {rate:.1f}%")

    return float(rate)
