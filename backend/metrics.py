"""
Dental Practice KPI Metrics Calculator

This module calculates 5 core KPIs from Google Sheets data:
1. Production Total (daily revenue)
2. Collection Rate (collections/production percentage)
3. New Patient Count (daily new patients)
4. Treatment Acceptance (scheduled/presented percentage)
5. Hygiene Reappointment Rate (reappointed/total percentage)

COLUMN NAMING CONVENTION:
- Current phase: Uses unprefixed variants ("Production", "Collections")
- Future time series: Will use prefixed variants ("daily_production",
  "daily_collections", "weekly_production", "weekly_collections",
  "monthly_production", "monthly_collections", etc.)
- Functions support both naming conventions for backward compatibility

Functions handle missing data gracefully and return None for failed calculations.
"""

import logging

import pandas as pd

from .sheets_reader import SheetsReader

# Set up logging
logger = logging.getLogger(__name__)


def safe_numeric_conversion(df: pd.DataFrame, column: str) -> float:
    """
    Safely convert a DataFrame column value to numeric.

    Args:
        df: DataFrame containing the data
        column: Column name to convert

    Returns:
        Float value or 0.0 if conversion fails

    Note:
        Current implementation uses iloc[0] for single-row design.
        Future time series implementation will sum entire columns.
    """
    if df is None or df.empty or column not in df.columns:
        return 0.0

    # Handle case where value might be a pandas Series with single value
    value = df[column].iloc[0] if len(df) > 0 else 0

    # Convert to numeric, return 0 if conversion fails or is NaN
    numeric_value = pd.to_numeric(value, errors="coerce")
    return 0.0 if pd.isna(numeric_value) else float(numeric_value)


def calculate_production_total(df: pd.DataFrame | None) -> float | None:
    """
    Calculate total production for the day.

    Args:
        df: DataFrame with production data (EOD sheet format)

    Returns:
        Total production amount or None if calculation fails

    Formula:
        Production = Column I (Total Production Today) + Column J (Adjustments)
                   + Column K (Write-offs Today)
    """
    if df is None or df.empty:
        return None

    # Check if required column exists with fallback support
    # Support both prefixed (total_production) and unprefixed (Production) variants
    prod_col = "total_production" if "total_production" in df.columns else "Production"

    if prod_col not in df.columns:
        logger.warning(f"Required production column not found. Looking for: {prod_col}")
        return None

    # Column I: Total Production Today
    production = safe_numeric_conversion(df, prod_col)
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
    return float(total)


def calculate_collection_rate(df: pd.DataFrame | None) -> float | None:
    """
    Calculate collection rate percentage.

    Args:
        df: DataFrame with production and collection data

    Returns:
        Collection rate as percentage (0-100) or None if calculation fails

    Formula:
        Collection Rate = (Collections / Production) × 100
    """
    if df is None or df.empty:
        return None

    # Check required columns with fallback support
    # Support both prefixed (total_production) and unprefixed (Production) variants
    prod_col = "total_production" if "total_production" in df.columns else "Production"
    col_col = (
        "total_collections" if "total_collections" in df.columns else "Collections"
    )

    if prod_col not in df.columns or col_col not in df.columns:
        logger.warning(
            f"Required columns not found. Looking for production column: "
            f"{prod_col}, collections column: {col_col}"
        )
        return None

    # Column I: Production; Column J: Collections
    production = safe_numeric_conversion(df, prod_col)
    collections = safe_numeric_conversion(df, col_col)

    # Avoid division by zero
    if production == 0:
        logger.warning("Production is zero, cannot calculate collection rate")
        return None

    collection_rate = (collections / production) * 100
    return float(collection_rate)


def calculate_new_patients(df: pd.DataFrame | None) -> int | None:
    """
    Calculate new patient count.

    Args:
        df: DataFrame with new patient data (EOD sheet format)

    Returns:
        Number of new patients or None if calculation fails

    Formula:
        New Patients = Column J (New Patients Today)
    """
    if df is None or df.empty:
        return None

    # Check required column
    if "new_patients" not in df.columns:
        logger.warning("Required column 'new_patients' not found")
        return None

    # Column J: New Patients Today
    new_patients = safe_numeric_conversion(df, "new_patients")
    return int(new_patients)


def calculate_treatment_acceptance(df: pd.DataFrame | None) -> float | None:
    """
    Calculate treatment acceptance percentage.

    Args:
        df: DataFrame with treatment data (Front KPI sheet format)

    Returns:
        Treatment acceptance rate as percentage (0-100) or None if calculation fails

    Formula:
        Treatment Acceptance = (Treatments Scheduled / Treatments Presented) × 100
    """
    if df is None or df.empty:
        return None

    # Check required columns
    required_cols = ["treatments_presented", "treatments_scheduled"]
    if not all(col in df.columns for col in required_cols):
        logger.warning(f"Required columns not found: {required_cols}")
        return None

    # Column K: Treatments Presented; Column L: Treatments Scheduled
    presented = safe_numeric_conversion(df, "treatments_presented")
    scheduled = safe_numeric_conversion(df, "treatments_scheduled")

    # Avoid division by zero
    if presented == 0:
        logger.warning("Treatments presented is zero, cannot calculate acceptance rate")
        return None

    acceptance_rate = (scheduled / presented) * 100
    return float(acceptance_rate)


def calculate_hygiene_reappointment(df: pd.DataFrame | None) -> float | None:
    """
    Calculate hygiene reappointment percentage.

    Args:
        df: DataFrame with hygiene data (Front KPI sheet format)

    Returns:
        Hygiene reappointment rate as percentage (0-100) or None if calculation fails

    Formula:
        Hygiene Reappointment = ((Total Hygiene - Not Reappointed) /
                                Total Hygiene) × 100
    """
    if df is None or df.empty:
        return None

    # Check required columns
    required_cols = ["total_hygiene_appointments", "patients_not_reappointed"]
    if not all(col in df.columns for col in required_cols):
        logger.warning(f"Required columns not found: {required_cols}")
        return None

    # Column M: Total Hygiene Appointments; Column N: Patients Not Reappointed
    total_hygiene = safe_numeric_conversion(df, "total_hygiene_appointments")
    not_reappointed = safe_numeric_conversion(df, "patients_not_reappointed")

    # Avoid division by zero
    if total_hygiene == 0:
        logger.warning(
            "Total hygiene appointments is zero, cannot calculate reappointment rate"
        )
        return None

    reappointed = total_hygiene - not_reappointed
    reappointment_rate = (reappointed / total_hygiene) * 100
    return float(reappointment_rate)


def get_all_kpis() -> dict[str, float | int | None]:
    """
    Calculate all 5 KPIs from Google Sheets data.

    Returns:
        Dictionary containing all calculated KPIs:
        - production_total: float or None
        - collection_rate: float or None
        - new_patients: int or None
        - treatment_acceptance: float or None
        - hygiene_reappointment: float or None
    """
    try:
        # Initialize sheets reader
        reader = SheetsReader()

        # Get data from both sheets
        eod_data = reader.get_eod_data()
        front_kpi_data = reader.get_front_kpi_data()

        # Calculate all KPIs
        kpis = {
            "production_total": calculate_production_total(eod_data),
            "collection_rate": calculate_collection_rate(eod_data),
            "new_patients": calculate_new_patients(eod_data),
            "treatment_acceptance": calculate_treatment_acceptance(front_kpi_data),
            "hygiene_reappointment": calculate_hygiene_reappointment(front_kpi_data),
        }

        logger.info(f"Successfully calculated KPIs: {kpis}")
        return kpis

    except Exception as e:
        logger.error(f"Error calculating KPIs: {e}")
        return {
            "production_total": None,
            "collection_rate": None,
            "new_patients": None,
            "treatment_acceptance": None,
            "hygiene_reappointment": None,
        }
