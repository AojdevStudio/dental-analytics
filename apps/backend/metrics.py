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
import sys
from datetime import datetime
from typing import Any

try:
    from config.data_sources import COLUMN_MAPPINGS
except (
    ImportError
):  # pragma: no cover - configuration module should exist in app runtime
    COLUMN_MAPPINGS = {}

import pandas as pd
import structlog

# Configure structured logging to stderr
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.dict_tracebacks,
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.PATHNAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)

log = structlog.get_logger()
# Set up legacy logging for backward compatibility (please remove this!!!)
logger = logging.getLogger(__name__)

EOD_MAPPING = COLUMN_MAPPINGS.get("eod_billing", {})
FRONT_MAPPING = COLUMN_MAPPINGS.get("front_kpis", {})


def clean_currency_string(value: Any) -> Any:
    """Clean currency formatting from a value.

    Args:
        value: Value to clean (can be string, number, or other)

    Returns:
        Cleaned value ready for numeric conversion
    """
    if isinstance(value, str):
        # Remove currency symbols and thousands separators
        cleaned = value.replace("$", "").replace(",", "").strip()
        # Handle edge cases
        if cleaned == "" or cleaned == "-":
            return 0.0
        return cleaned
    return value


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
        Handles currency formats like '$1,234.56' and '-$1,234.56'.
    """
    if df is None or df.empty or column not in df.columns:
        return 0.0

    # Handle case where value might be a pandas Series with single value
    # Use iloc[-1] to get the LATEST/MOST RECENT entry (last row)
    value = df[column].iloc[-1] if len(df) > 0 else 0

    # Clean currency formatting: remove $, commas, and handle negative values
    cleaned_value = clean_currency_string(value)

    # Convert to numeric, return 0 if conversion fails or is NaN
    numeric_value = pd.to_numeric(cleaned_value, errors="coerce")
    result = 0.0 if pd.isna(numeric_value) else float(numeric_value)

    # Debug logging for currency conversion
    if isinstance(value, str) and ("$" in value or "," in value):
        logger.debug(f"Currency conversion: '{value}' -> {result}")

    return result


def calculate_production_total(df: pd.DataFrame | None) -> float | None:
    """
    Calculate total production for the day.

    Args:
        df: DataFrame with production data (EOD sheet format)

    Returns:
        Total production amount or None if calculation fails

    Formula:
        Production = Total Production Today + Adjustments Today + Write-offs Today
    """
    if df is None or df.empty:
        return None

    # Story 2.1 validated column names (primary)
    prod_col = "Total Production Today"
    adjustments_col = "Adjustments Today"
    writeoffs_col = "Write-offs Today"

    # Fallback to legacy column names for backward compatibility
    if prod_col not in df.columns:
        prod_col = (
            "total_production" if "total_production" in df.columns else "Production"
        )
    if adjustments_col not in df.columns:
        adjustments_col = "adjustments"
    if writeoffs_col not in df.columns:
        writeoffs_col = "writeoffs"

    if prod_col not in df.columns:
        logger.warning(
            f"Required production column not found. Available: {list(df.columns)}"
        )
        return None

    # Calculate total with validated column names
    production = safe_numeric_conversion(df, prod_col)
    adjustments = (
        safe_numeric_conversion(df, adjustments_col)
        if adjustments_col in df.columns
        else 0.0
    )
    writeoffs = (
        safe_numeric_conversion(df, writeoffs_col)
        if writeoffs_col in df.columns
        else 0.0
    )

    total = production + adjustments + writeoffs
    logger.info(
        f"Production: Base={production}, Adj={adjustments}, "
        f"Writeoffs={writeoffs}, Total={total}"
    )
    return float(total)


def calculate_collection_rate(df: pd.DataFrame | None) -> float | None:
    """
    Calculate collection rate percentage.

    Args:
        df: DataFrame with production and collection data

    Returns:
        Collection rate as percentage (0-100) or None if calculation fails

    Formula:
        Collection Rate = (Total Collections / Total Production) × 100
        Total Production = Production + Adjustments + Write-offs
        Total Collections = Patient Income + Unearned Income + Insurance Income
    """
    if df is None or df.empty:
        return None

    # Check required columns - updated for Story 2.1 validation
    production_col = "Total Production Today"
    adjustments_col = "Adjustments Today"
    writeoffs_col = "Write-offs Today"
    patient_income_col = "Patient Income Today"
    unearned_income_col = "Unearned Income Today"
    insurance_income_col = "Insurance Income Today"

    # Fallback to old column names for backward compatibility (please remove this!!!)
    if production_col not in df.columns:
        production_col = (
            "total_production" if "total_production" in df.columns else "Production"
        )

    # Check for production columns
    production_columns = [production_col, adjustments_col, writeoffs_col]
    income_columns = [patient_income_col, unearned_income_col, insurance_income_col]

    # Check if we have all required columns
    has_production = all(col in df.columns for col in production_columns)
    has_income = all(col in df.columns for col in income_columns)

    if not has_production or not has_income:
        # Try fallback for collections as single column
        col_col = (
            "total_collections" if "total_collections" in df.columns else "Collections"
        )
        if col_col in df.columns and production_col in df.columns:
            logger.info("Using fallback single collections column")
            production = safe_numeric_conversion(df, production_col)
            collections = safe_numeric_conversion(df, col_col)
        else:
            logger.warning(
                f"Required columns not found. " f"Available columns: {list(df.columns)}"
            )
            return None
    else:
        # Calculate total production (Story 2.1 validated formula)
        production_base = safe_numeric_conversion(df, production_col)
        adjustments = safe_numeric_conversion(df, adjustments_col)
        writeoffs = safe_numeric_conversion(df, writeoffs_col)
        production = production_base + adjustments + writeoffs

        # Calculate total collections from three components (Story 2.1 validated)
        patient_income = safe_numeric_conversion(df, patient_income_col)
        unearned_income = safe_numeric_conversion(df, unearned_income_col)
        insurance_income = safe_numeric_conversion(df, insurance_income_col)

        collections = patient_income + unearned_income + insurance_income

        logger.info(
            f"Collections breakdown: Patient={patient_income}, "
            f"Unearned={unearned_income}, Insurance={insurance_income}, "
            f"Total={collections}"
        )

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
        New Patients = New Patients - Total Month to Date (latest value)
    """
    if df is None or df.empty:
        return None

    # Story 2.1 validated column name
    new_patients_col = "New Patients - Total Month to Date"

    # Fallback to legacy column names (please remove this!!!)
    if new_patients_col not in df.columns:
        new_patients_col = "new_patients"

    if new_patients_col not in df.columns:
        logger.warning(
            f"Required new patients column not found. Available: {list(df.columns)}"
        )
        return None

    # Get the latest value (most recent entry)
    new_patients = safe_numeric_conversion(df, new_patients_col)
    logger.info(f"New patients (MTD): {new_patients}")
    return int(new_patients)


def calculate_treatment_acceptance(df: pd.DataFrame | None) -> float | None:
    """
    Calculate treatment acceptance percentage.

    Args:
        df: DataFrame with treatment data (Front KPI sheet format)

    Returns:
        Treatment acceptance rate as percentage (0-100) or None if calculation fails

    Formula:
        Treatment Acceptance = ((Treatments Scheduled + $ Same Day Treatment)
                               / Treatments Presented) × 100
    """
    if df is None or df.empty:
        return None

    # Check required columns
    presented_col = "treatments_presented"
    scheduled_col = "treatments_scheduled"
    same_day_col = "$ Same Day Treatment"

    required_cols = [presented_col, scheduled_col, same_day_col]
    if not all(col in df.columns for col in required_cols):
        logger.warning(
            "Required columns for treatment acceptance not found. Missing: %s",
            [c for c in required_cols if c not in df.columns],
        )
        return None

    # Column K: Treatments Presented; Column L: Treatments Scheduled
    presented = safe_numeric_conversion(df, presented_col)
    scheduled = safe_numeric_conversion(df, scheduled_col)
    same_day = safe_numeric_conversion(df, same_day_col)

    # Avoid division by zero
    if presented == 0:
        logger.warning("Treatments presented is zero, cannot calculate acceptance rate")
        return None

    acceptance_rate = ((scheduled + same_day) / presented) * 100
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

    # Story 2.1 validated column names
    total_hygiene_col = "Total hygiene Appointments"
    not_reappointed_col = "Number of patients NOT reappointed?"

    # Fallback to legacy column names
    if total_hygiene_col not in df.columns:
        total_hygiene_col = "total_hygiene_appointments"
    if not_reappointed_col not in df.columns:
        not_reappointed_col = "patients_not_reappointed"

    required_cols = [total_hygiene_col, not_reappointed_col]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        logger.warning(
            f"Required columns not found: {missing_cols}. "
            f"Available columns: {list(df.columns)}"
        )
        return None

    # Calculate reappointment rate with validated column names
    total_hygiene = safe_numeric_conversion(df, total_hygiene_col)
    not_reappointed = safe_numeric_conversion(df, not_reappointed_col)

    # Avoid division by zero
    if total_hygiene == 0:
        logger.warning(
            "Total hygiene appointments is zero, cannot calculate reappointment rate"
        )
        return None

    reappointed = total_hygiene - not_reappointed
    reappointment_rate = (reappointed / total_hygiene) * 100

    logger.info(
        f"Hygiene: Total={total_hygiene}, "
        f"Not Reappointed={not_reappointed}, Rate={reappointment_rate:.1f}%"
    )
    return float(reappointment_rate)


def get_all_kpis(location: str = "baytown") -> dict[str, float | int | None]:
    """
    Calculate all 5 KPIs from Google Sheets data for a specific location.

    Args:
        location: Location name ('baytown' or 'humble')

    Returns:
        Dictionary containing all calculated KPIs:
        - production_total: float or None
        - collection_rate: float or None
        - new_patients: int or None
        - treatment_acceptance: float or None
        - hygiene_reappointment: float or None
    """
    try:
        # Initialize data provider with alias-based configuration
        from .data_providers import build_sheets_provider

        provider = build_sheets_provider()

        # Get aliases for location-specific data
        eod_alias = provider.get_location_aliases(location, "eod")
        front_alias = provider.get_location_aliases(location, "front")

        # Fetch data using aliases
        eod_data = provider.fetch(eod_alias) if eod_alias else None
        front_kpi_data = provider.fetch(front_alias) if front_alias else None

        # Calculate all KPIs
        kpis = {
            "production_total": calculate_production_total(eod_data),
            "collection_rate": calculate_collection_rate(eod_data),
            "new_patients": calculate_new_patients(eod_data),
            "treatment_acceptance": calculate_treatment_acceptance(front_kpi_data),
            "hygiene_reappointment": calculate_hygiene_reappointment(front_kpi_data),
        }

        logger.info(f"Successfully calculated {location.title()} KPIs: {kpis}")
        return kpis

    except Exception as e:
        logger.error(f"Error calculating {location.title()} KPIs: {e}")
        return {
            "production_total": None,
            "collection_rate": None,
            "new_patients": None,
            "treatment_acceptance": None,
            "hygiene_reappointment": None,
        }


def get_combined_kpis() -> dict[str, dict[str, float | int | None]]:
    """
    Get KPIs for both locations.

    Returns:
        Dictionary with separate KPIs for each location:
        {
            "baytown": {KPI dict},
            "humble": {KPI dict}
        }
    """
    return {
        "baytown": get_all_kpis("baytown"),
        "humble": get_all_kpis("humble"),
    }


# =============================================================================
# HISTORICAL METRICS FUNCTIONS (New in Story 2.1)
# =============================================================================


def safe_time_series_conversion(
    df: pd.DataFrame, column: str, date_column: str = "Submission Date"
) -> list[tuple[datetime, float]]:
    """
    Safely convert DataFrame to time series format for historical data.

    Args:
        df: DataFrame containing the data
        column: Column name to convert to time series
        date_column: Name of the date column

    Returns:
        List of (datetime, value) tuples, sorted by date
    """
    if (
        df is None
        or df.empty
        or column not in df.columns
        or date_column not in df.columns
    ):
        return []

    try:
        # Create a copy to avoid modifying original
        df_copy = df.copy()

        # Convert date column to datetime
        df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors="coerce")

        # Convert value column to numeric
        df_copy[column] = pd.to_numeric(df_copy[column], errors="coerce")

        # Drop rows with invalid dates or values
        df_copy = df_copy.dropna(subset=[date_column, column])

        # Sort by date
        df_copy = df_copy.sort_values(date_column)

        # Create time series list
        time_series = [
            (row[date_column], float(row[column])) for _, row in df_copy.iterrows()
        ]

        log.info(
            "metrics.time_series_conversion", column=column, points=len(time_series)
        )
        return time_series

    except Exception as e:
        log.error("metrics.time_series_conversion_failed", column=column, error=str(e))
        return []


def calculate_historical_production_total(
    df: pd.DataFrame | None, days: int = 30
) -> dict[str, Any]:
    """
    Calculate historical production total with time-series data.

    Args:
        df: DataFrame with historical production data (EOD sheet format)
        days: Number of days for historical analysis

    Returns:
        Dictionary containing time series data, aggregations, and latest value
    """
    log.info("metrics.historical_production_start", days=days)

    if df is None or df.empty:
        return {
            "time_series": [],
            "total_sum": 0.0,
            "daily_average": 0.0,
            "latest_value": None,
            "data_points": 0,
        }

    date_col = EOD_MAPPING.get("date", "Submission Date")
    primary_columns = {
        "production": EOD_MAPPING.get("production", "Total Production Today"),
        "adjustments": EOD_MAPPING.get("adjustments", "Adjustments Today"),
        "writeoffs": EOD_MAPPING.get("writeoffs", "Write-offs Today"),
    }

    required_primary = [col for col in primary_columns.values() if col]

    if all(col in df.columns for col in required_primary):
        df_copy = df.copy()
        for col in required_primary:
            # Clean currency formatting before numeric conversion
            df_copy[col] = df_copy[col].apply(clean_currency_string)
            df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce").fillna(0.0)

        df_copy["_historical_production_total"] = (
            df_copy[primary_columns["production"]]
            + df_copy[primary_columns["adjustments"]]
            + df_copy[primary_columns["writeoffs"]]
        )

        time_series = safe_time_series_conversion(
            df_copy, "_historical_production_total", date_col
        )
    else:
        # Fallback to legacy single-column naming for backward compatibility
        prod_col = (
            "total_production" if "total_production" in df.columns else "Production"
        )

        if prod_col not in df.columns:
            log.warning(
                "metrics.historical_production_no_column",
                column=primary_columns["production"],
                fallback=prod_col,
            )
            return {
                "time_series": [],
                "total_sum": 0.0,
                "daily_average": 0.0,
                "latest_value": None,
                "data_points": 0,
            }

        time_series = safe_time_series_conversion(df, prod_col, date_col)

    if not time_series:
        return {
            "time_series": [],
            "total_sum": 0.0,
            "daily_average": 0.0,
            "latest_value": None,
            "data_points": 0,
        }

    # Calculate aggregations
    values = [value for _, value in time_series]
    total_sum = sum(values)
    daily_average = total_sum / len(values) if values else 0.0
    latest_value = values[-1] if values else None

    result = {
        "time_series": time_series,
        "total_sum": float(total_sum),
        "daily_average": float(daily_average),
        "latest_value": float(latest_value) if latest_value is not None else None,
        "data_points": len(time_series),
    }

    log.info(
        "metrics.historical_production_success",
        **{k: v for k, v in result.items() if k != "time_series"},
    )
    return result


def calculate_historical_collection_rate(
    df: pd.DataFrame | None, days: int = 30
) -> dict[str, Any]:
    """
    Calculate historical collection rate with time-series data.

    Args:
        df: DataFrame with historical production and collection data
        days: Number of days for historical analysis

    Returns:
        Dictionary containing time series data, aggregations, and latest value
    """
    log.info("metrics.historical_collection_rate_start", days=days)

    if df is None or df.empty:
        return {
            "time_series": [],
            "average_rate": 0.0,
            "latest_value": None,
            "data_points": 0,
        }

    try:
        df_copy = df.copy()
        date_col = EOD_MAPPING.get("date", "Submission Date")
        production_col = EOD_MAPPING.get("production", "Total Production Today")
        income_columns = [
            EOD_MAPPING.get("patient_income", "Patient Income Today"),
            EOD_MAPPING.get("unearned_income", "Unearned Income Today"),
            EOD_MAPPING.get("insurance_income", "Insurance Income Today"),
        ]
        fallback_production = (
            "total_production"
            if "total_production" in df_copy.columns
            else "Production"
        )
        fallback_collections = (
            "total_collections"
            if "total_collections" in df_copy.columns
            else "Collections"
        )

        if date_col not in df_copy.columns:
            log.warning("metrics.historical_collection_rate_no_date")
            return {
                "time_series": [],
                "average_rate": 0.0,
                "latest_value": None,
                "data_points": 0,
            }

        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors="coerce")

        if production_col in df_copy.columns and all(
            col in df_copy.columns for col in income_columns
        ):
            # Clean currency formatting before conversion
            df_copy[production_col] = df_copy[production_col].apply(
                clean_currency_string
            )
            df_copy[production_col] = pd.to_numeric(
                df_copy[production_col], errors="coerce"
            )
            total_collections = pd.Series([0.0] * len(df_copy), index=df_copy.index)
            for col in income_columns:
                # Clean currency formatting before conversion
                df_copy[col] = df_copy[col].apply(clean_currency_string)
                df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce").fillna(0.0)
                total_collections = total_collections + df_copy[col]

            df_copy["_total_collections"] = total_collections
            df_copy["collection_rate"] = (
                df_copy["_total_collections"] / df_copy[production_col] * 100
            ).where(df_copy[production_col] > 0)

        elif (
            fallback_production in df_copy.columns
            and fallback_collections in df_copy.columns
        ):
            df_copy[fallback_production] = pd.to_numeric(
                df_copy[fallback_production], errors="coerce"
            )
            df_copy[fallback_collections] = pd.to_numeric(
                df_copy[fallback_collections], errors="coerce"
            )
            df_copy["collection_rate"] = (
                df_copy[fallback_collections] / df_copy[fallback_production] * 100
            ).where(df_copy[fallback_production] > 0)

        else:
            log.warning(
                "metrics.historical_collection_rate_missing_columns",
                production_col=production_col,
                collections=income_columns,
                fallback_production=fallback_production,
                fallback_collections=fallback_collections,
            )
            return {
                "time_series": [],
                "average_rate": 0.0,
                "latest_value": None,
                "data_points": 0,
            }

        # Generate time series
        time_series = safe_time_series_conversion(df_copy, "collection_rate", date_col)

        if not time_series:
            return {
                "time_series": [],
                "average_rate": 0.0,
                "latest_value": None,
                "data_points": 0,
            }

        # Calculate aggregations
        rates = [rate for _, rate in time_series if rate is not None]
        average_rate = sum(rates) / len(rates) if rates else 0.0
        latest_value = rates[-1] if rates else None

        result = {
            "time_series": time_series,
            "average_rate": float(average_rate),
            "latest_value": float(latest_value) if latest_value is not None else None,
            "data_points": len(time_series),
        }

        log.info(
            "metrics.historical_collection_rate_success",
            **{k: v for k, v in result.items() if k != "time_series"},
        )
        return result

    except Exception as e:
        log.error("metrics.historical_collection_rate_failed", error=str(e))
        return {
            "time_series": [],
            "average_rate": 0.0,
            "latest_value": None,
            "data_points": 0,
        }


def calculate_historical_new_patients(
    df: pd.DataFrame | None, days: int = 30
) -> dict[str, Any]:
    """
    Calculate historical new patient count with time-series data.

    Args:
        df: DataFrame with historical new patient data (EOD sheet format)
        days: Number of days for historical analysis

    Returns:
        Dictionary containing time series data, aggregations, and latest value
    """
    log.info("metrics.historical_new_patients_start", days=days)

    if df is None or df.empty:
        return {
            "time_series": [],
            "total_count": 0,
            "daily_average": 0.0,
            "latest_value": None,
            "data_points": 0,
        }

    date_col = EOD_MAPPING.get("date", "Submission Date")
    mtd_column = EOD_MAPPING.get(
        "new_patients_mtd", "New Patients - Total Month to Date"
    )

    if date_col in df.columns and mtd_column in df.columns:
        df_copy = df[[date_col, mtd_column]].copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors="coerce")
        # Clean currency formatting before conversion
        df_copy[mtd_column] = df_copy[mtd_column].apply(clean_currency_string)
        df_copy[mtd_column] = pd.to_numeric(df_copy[mtd_column], errors="coerce")
        df_copy = df_copy.dropna(subset=[date_col])
        df_copy = df_copy.sort_values(date_col)

        daily_counts = df_copy[mtd_column].diff()
        if not daily_counts.empty:
            daily_counts.iloc[0] = df_copy[mtd_column].iloc[0]
        daily_counts = daily_counts.where(
            pd.to_numeric(daily_counts, errors="coerce") >= 0, df_copy[mtd_column]
        )
        df_copy["_daily_new_patients"] = daily_counts.fillna(0.0)

        time_series = safe_time_series_conversion(
            df_copy, "_daily_new_patients", date_col
        )
    else:
        fallback_column = "new_patients"
        if fallback_column not in df.columns:
            log.warning(
                "metrics.historical_new_patients_no_column",
                expected=mtd_column,
                fallback=fallback_column,
            )
            return {
                "time_series": [],
                "total_count": 0,
                "daily_average": 0.0,
                "latest_value": None,
                "data_points": 0,
            }

        time_series = safe_time_series_conversion(df, fallback_column, date_col)

    if not time_series:
        return {
            "time_series": [],
            "total_count": 0,
            "daily_average": 0.0,
            "latest_value": None,
            "data_points": 0,
        }

    # Calculate aggregations
    counts = [int(count) for _, count in time_series]
    total_count = sum(counts)
    daily_average = total_count / len(counts) if counts else 0.0
    latest_value = counts[-1] if counts else None

    result = {
        "time_series": time_series,
        "total_count": total_count,
        "daily_average": float(daily_average),
        "latest_value": latest_value,
        "data_points": len(time_series),
    }

    log.info(
        "metrics.historical_new_patients_success",
        **{k: v for k, v in result.items() if k != "time_series"},
    )
    return result


def calculate_historical_treatment_acceptance(
    df: pd.DataFrame | None, days: int = 30
) -> dict[str, Any]:
    """
    Calculate historical treatment acceptance rate with time-series data.
    """
    log.info("metrics.historical_treatment_acceptance_start", days=days)
    if df is None or df.empty:
        return {
            "time_series": [],
            "average_rate": 0.0,
            "latest_value": None,
            "data_points": 0,
        }

    try:
        df_copy = df.copy()
        date_col = FRONT_MAPPING.get("date", "Submission Date")
        presented_col = FRONT_MAPPING.get(
            "treatments_presented", "treatments_presented"
        )
        scheduled_col = FRONT_MAPPING.get(
            "treatments_scheduled", "treatments_scheduled"
        )
        same_day_col = FRONT_MAPPING.get("same_day_treatment", "$ Same Day Treatment")

        required_cols = [presented_col, scheduled_col, same_day_col]
        if not all(col in df_copy.columns for col in required_cols):
            log.warning(
                "metrics.historical_treatment_acceptance_missing_columns",
                missing=[c for c in required_cols if c not in df_copy.columns],
            )
            return {
                "time_series": [],
                "average_rate": 0.0,
                "latest_value": None,
                "data_points": 0,
            }

        for col in required_cols:
            df_copy[col] = df_copy[col].apply(clean_currency_string)
            df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce").fillna(0.0)

        df_copy["_treatment_acceptance_rate"] = (
            (df_copy[scheduled_col] + df_copy[same_day_col])
            / df_copy[presented_col]
            * 100
        ).where(df_copy[presented_col] > 0)

        time_series = safe_time_series_conversion(
            df_copy, "_treatment_acceptance_rate", date_col
        )
        if not time_series:
            return {
                "time_series": [],
                "average_rate": 0.0,
                "latest_value": None,
                "data_points": 0,
            }

        rates = [rate for _, rate in time_series if rate is not None]
        average_rate = sum(rates) / len(rates) if rates else 0.0
        latest_value = rates[-1] if rates else None

        result = {
            "time_series": time_series,
            "average_rate": float(average_rate),
            "latest_value": float(latest_value) if latest_value is not None else None,
            "data_points": len(time_series),
        }
        log.info(
            "metrics.historical_treatment_acceptance_success",
            **{k: v for k, v in result.items() if k != "time_series"},
        )
        return result
    except Exception as e:
        log.error("metrics.historical_treatment_acceptance_failed", error=str(e))
        return {
            "time_series": [],
            "average_rate": 0.0,
            "latest_value": None,
            "data_points": 0,
        }


def calculate_historical_hygiene_reappointment(
    df: pd.DataFrame | None, days: int = 30
) -> dict[str, Any]:
    """
    Calculate historical hygiene reappointment rate with time-series data.
    """
    log.info("metrics.historical_hygiene_reappointment_start", days=days)
    if df is None or df.empty:
        return {
            "time_series": [],
            "average_rate": 0.0,
            "latest_value": None,
            "data_points": 0,
        }

    try:
        df_copy = df.copy()
        date_col = FRONT_MAPPING.get("date", "Submission Date")
        total_col = FRONT_MAPPING.get("hygiene_total", "Total hygiene Appointments")
        not_reappointed_col = FRONT_MAPPING.get(
            "hygiene_not_reappointed", "Number of patients NOT reappointed?"
        )

        required_cols = [total_col, not_reappointed_col]
        if not all(col in df_copy.columns for col in required_cols):
            log.warning(
                "metrics.historical_hygiene_reappointment_missing_columns",
                missing=[c for c in required_cols if c not in df_copy.columns],
            )
            return {
                "time_series": [],
                "average_rate": 0.0,
                "latest_value": None,
                "data_points": 0,
            }

        for col in required_cols:
            df_copy[col] = df_copy[col].apply(clean_currency_string)
            df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce").fillna(0.0)

        df_copy["_hygiene_reappointment_rate"] = (
            (df_copy[total_col] - df_copy[not_reappointed_col])
            / df_copy[total_col]
            * 100
        ).where(df_copy[total_col] > 0)

        time_series = safe_time_series_conversion(
            df_copy, "_hygiene_reappointment_rate", date_col
        )

        if not time_series:
            return {
                "time_series": [],
                "average_rate": 0.0,
                "latest_value": None,
                "data_points": 0,
            }

        rates = [rate for _, rate in time_series if rate is not None]
        average_rate = sum(rates) / len(rates) if rates else 0.0
        latest_value = rates[-1] if rates else None

        result = {
            "time_series": time_series,
            "average_rate": float(average_rate),
            "latest_value": float(latest_value) if latest_value is not None else None,
            "data_points": len(time_series),
        }
        log.info(
            "metrics.historical_hygiene_reappointment_success",
            **{k: v for k, v in result.items() if k != "time_series"},
        )
        return result
    except Exception as e:
        log.error("metrics.historical_hygiene_reappointment_failed", error=str(e))
        return {
            "time_series": [],
            "average_rate": 0.0,
            "latest_value": None,
            "data_points": 0,
        }


def get_all_historical_kpis(days: int = 30) -> dict[str, Any]:
    """
    Calculate all historical KPIs with time-series data.

    Args:
        days: Number of days for historical analysis

    Returns:
        Dictionary containing all historical KPIs with time series and aggregations
    """
    log.info("metrics.all_historical_kpis_start", days=days)

    try:
        # Import here to avoid circular import
        from .historical_data import HistoricalDataManager

        # Initialize data manager
        historical_manager = HistoricalDataManager()

        # Get historical data
        eod_data = historical_manager.get_recent_eod_data(days)
        # Note: front_kpi_data fetched but not used in current implementation
        front_kpi_data = historical_manager.get_historical_front_kpi_data(days)

        # Get latest available data for current values
        latest_data = historical_manager.get_latest_available_data()

        # Calculate historical metrics
        historical_kpis = {
            "production_total": calculate_historical_production_total(eod_data, days),
            "collection_rate": calculate_historical_collection_rate(eod_data, days),
            "new_patients": calculate_historical_new_patients(eod_data, days),
            "treatment_acceptance": calculate_historical_treatment_acceptance(
                front_kpi_data, days
            ),
            "hygiene_reappointment": calculate_historical_hygiene_reappointment(
                front_kpi_data, days
            ),
        }

        # Calculate current values from latest available data
        # Cast to proper types to satisfy mypy
        eod_df = latest_data.get("eod")
        front_kpi_df = latest_data.get("front_kpi")

        eod_data_df = eod_df if isinstance(eod_df, pd.DataFrame) else None
        front_kpi_data_df = (
            front_kpi_df if isinstance(front_kpi_df, pd.DataFrame) else None
        )

        current_kpis = {
            "production_total": calculate_production_total(eod_data_df),
            "collection_rate": calculate_collection_rate(eod_data_df),
            "new_patients": calculate_new_patients(eod_data_df),
            "treatment_acceptance": calculate_treatment_acceptance(front_kpi_data_df),
            "hygiene_reappointment": calculate_hygiene_reappointment(front_kpi_data_df),
        }

        result = {
            "historical": historical_kpis,
            "current": current_kpis,
            "data_date": latest_data.get("data_date"),
            "period_days": days,
        }

        log.info("metrics.all_historical_kpis_success", period_days=days)
        return result

    except Exception as e:
        log.error("metrics.all_historical_kpis_failed", error=str(e))
        return {
            "historical": {},
            "current": {
                "production_total": None,
                "collection_rate": None,
                "new_patients": None,
                "treatment_acceptance": None,
                "hygiene_reappointment": None,
            },
            "period_days": days,
            "data_date": None,
        }
