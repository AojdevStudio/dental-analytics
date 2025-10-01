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
from datetime import date, datetime

try:
    from config.data_sources import COLUMN_MAPPINGS
except (
    ImportError
):  # pragma: no cover - configuration module should exist in app runtime
    COLUMN_MAPPINGS = {}

import pandas as pd
import structlog

from core.business_rules.calendar import BusinessCalendar
from core.business_rules.validation_rules import KPIValidationRules
from core.calculators import kpi_calculator
from core.models.kpi_models import CalculationResult, KPIValue, Location
from core.transformers.sheets_transformer import SheetsToKPIInputs
from services.kpi_service import KPIService

from .data_providers import build_sheets_provider
from .types import (
    HistoricalCountData,
    HistoricalKPIData,
    HistoricalMetricData,
    HistoricalProductionData,
    HistoricalRateData,
    KPIData,
    MultiLocationKPIData,
)

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

_TRANSFORMER = SheetsToKPIInputs()
_CALENDAR = BusinessCalendar()
_VALIDATION_RULES = KPIValidationRules()


def _build_kpi_service() -> KPIService:
    """Create a KPIService instance wired to the Sheets provider."""

    provider = build_sheets_provider()
    return KPIService(
        data_provider=provider,
        calendar=_CALENDAR,
        validation_rules=_VALIDATION_RULES,
        transformer=_TRANSFORMER,
    )


def _result_value(result: CalculationResult) -> float | int | None:
    """Return the numeric value from a CalculationResult when available."""

    if not result.can_calculate or result.value is None:
        return None
    return result.value


def clean_currency_string(value: object) -> object:
    """Normalize currency-formatted strings for historical calculations."""

    if isinstance(value, str):
        raw = value.strip()
        is_accounting_negative = raw.startswith("(") and raw.endswith(")")
        if is_accounting_negative:
            raw = raw[1:-1]

        cleaned = raw.replace("$", "").replace(",", "")
        if cleaned in {"", "-"}:
            return 0.0
        if is_accounting_negative and cleaned:
            return f"-{cleaned}"
        return cleaned

    return value


def _kpi_value_to_number(kpi_value: KPIValue) -> float | int | None:
    """Convert a KPIValue into a primitive numeric value for legacy callers."""

    if not kpi_value.available or kpi_value.value is None:
        return None
    return kpi_value.value


def safe_numeric_conversion(
    df: pd.DataFrame, column: str, default: float = 0.0
) -> float:
    """Legacy helper retained for historical tests via transformer extraction."""

    if df is None or df.empty:
        return default

    value = _TRANSFORMER._safe_extract(df, column, default=default)  # noqa: SLF001
    if value is None:
        return default
    return float(value)


def calculate_production_total(df: pd.DataFrame | None) -> float | None:
    """Calculate total production for the day using the decoupled core."""

    if df is None or df.empty:
        return None

    production, adjustments, writeoffs = _TRANSFORMER.extract_production_inputs(df)
    result = kpi_calculator.compute_production_total(production, adjustments, writeoffs)
    value = _result_value(result)

    if value is None:
        logger.warning("Production total unavailable via new calculator")
    else:
        logger.info(
            "metrics.production_total",
            extra={
                "production": production,
                "adjustments": adjustments,
                "writeoffs": writeoffs,
                "total": value,
            },
        )

    return float(value) if value is not None else None


def calculate_collection_rate(df: pd.DataFrame | None) -> float | None:
    """Calculate collection rate percentage using the decoupled core."""

    if df is None or df.empty:
        return None

    (
        production,
        adjustments,
        writeoffs,
        patient_income,
        unearned_income,
        insurance_income,
    ) = _TRANSFORMER.extract_collection_inputs(df)

    result = kpi_calculator.compute_collection_rate(
        production,
        adjustments,
        writeoffs,
        patient_income,
        unearned_income,
        insurance_income,
    )

    value = _result_value(result)
    if value is None:
        logger.warning("Collection rate unavailable via new calculator")
        return None

    logger.info(
        "metrics.collection_rate",
        extra={
            "production": production,
            "adjustments": adjustments,
            "writeoffs": writeoffs,
            "patient_income": patient_income,
            "unearned_income": unearned_income,
            "insurance_income": insurance_income,
            "rate": value,
        },
    )

    return float(value)


def calculate_new_patients(df: pd.DataFrame | None) -> int | None:
    """Calculate new patient count using the core calculator."""

    if df is None or df.empty:
        return None

    (new_patients_mtd,) = _TRANSFORMER.extract_new_patients_inputs(df)
    result = kpi_calculator.compute_new_patients(new_patients_mtd)
    value = _result_value(result)

    if value is None:
        logger.warning("New patients unavailable via new calculator")
        return None

    logger.info("metrics.new_patients", extra={"total": value})
    return int(value)


def calculate_case_acceptance(df: pd.DataFrame | None) -> float | None:
    """Calculate case acceptance percentage using the decoupled core."""

    if df is None or df.empty:
        return None

    presented, scheduled, same_day = _TRANSFORMER.extract_case_acceptance_inputs(df)
    result = kpi_calculator.compute_case_acceptance(presented, scheduled, same_day)
    value = _result_value(result)

    if value is None:
        logger.warning("Case acceptance unavailable via new calculator")
        return None

    logger.info(
        "metrics.case_acceptance",
        extra={
            "presented": presented,
            "scheduled": scheduled,
            "same_day": same_day,
            "rate": value,
        },
    )

    return float(value)


def calculate_hygiene_reappointment(df: pd.DataFrame | None) -> float | None:
    """Calculate hygiene reappointment percentage using the decoupled core."""

    if df is None or df.empty:
        return None

    total_hygiene, not_reappointed = _TRANSFORMER.extract_hygiene_inputs(df)
    result = kpi_calculator.compute_hygiene_reappointment(
        total_hygiene, not_reappointed
    )
    value = _result_value(result)

    if value is None:
        logger.warning("Hygiene reappointment unavailable via new calculator")
        return None

    logger.info(
        "metrics.hygiene_reappointment",
        extra={
            "total_hygiene": total_hygiene,
            "not_reappointed": not_reappointed,
            "rate": value,
        },
    )

    return float(value)


def get_all_kpis(location: Location = "baytown") -> KPIData:
    """Return legacy KPI dictionary output backed by the new KPI service."""

    try:
        service = _build_kpi_service()
        response = service.get_kpis(location, date.today())
        values = response.values

        new_patients_value = _kpi_value_to_number(values.new_patients)
        new_patients_int = (
            int(new_patients_value) if new_patients_value is not None else None
        )
        return {
            "production_total": _kpi_value_to_number(values.production_total),
            "collection_rate": _kpi_value_to_number(values.collection_rate),
            "new_patients": new_patients_int,
            "case_acceptance": _kpi_value_to_number(values.case_acceptance),
            "hygiene_reappointment": _kpi_value_to_number(values.hygiene_reappointment),
        }

    except Exception as exc:
        logger.error("Error calculating %s KPIs via service", location, exc_info=exc)
        return {
            "production_total": None,
            "collection_rate": None,
            "new_patients": None,
            "case_acceptance": None,
            "hygiene_reappointment": None,
        }


def get_combined_kpis() -> MultiLocationKPIData:
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

    def _parse_date(value: object) -> datetime | None:
        """Parse raw date inputs using known formats before falling back."""

        if value in (None, ""):
            return None

        text_value = str(value).strip()
        if text_value == "":
            return None

        known_formats = ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d")
        for date_format in known_formats:
            try:
                return datetime.strptime(text_value, date_format)
            except ValueError:
                continue

        parsed = pd.to_datetime(text_value, errors="coerce")
        if pd.isna(parsed):
            return None
        result = parsed.to_pydatetime()
        return result if isinstance(result, datetime) else None

    try:
        # Create a copy to avoid modifying original
        df_copy = df.copy()

        # Convert date column to datetime
        df_copy[date_column] = df_copy[date_column].apply(_parse_date)

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
) -> HistoricalProductionData:
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

    result: HistoricalProductionData = {
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
) -> HistoricalRateData:
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
            # Get adjustments and writeoffs columns for adjusted production
            adjustments_col = EOD_MAPPING.get("adjustments", "Adjustments Today")
            writeoffs_col = EOD_MAPPING.get("writeoffs", "Write-offs Today")

            # Clean currency formatting before conversion
            df_copy[production_col] = df_copy[production_col].apply(
                clean_currency_string
            )
            df_copy[production_col] = pd.to_numeric(
                df_copy[production_col], errors="coerce"
            ).fillna(0.0)

            # Calculate adjusted production
            if adjustments_col in df_copy.columns and writeoffs_col in df_copy.columns:
                df_copy[adjustments_col] = df_copy[adjustments_col].apply(
                    clean_currency_string
                )
                df_copy[writeoffs_col] = df_copy[writeoffs_col].apply(
                    clean_currency_string
                )
                df_copy[adjustments_col] = pd.to_numeric(
                    df_copy[adjustments_col], errors="coerce"
                ).fillna(0.0)
                df_copy[writeoffs_col] = pd.to_numeric(
                    df_copy[writeoffs_col], errors="coerce"
                ).fillna(0.0)

                # Adjusted Production = Gross - |Adjustments| - |Write-offs|
                df_copy["_adjusted_production"] = (
                    df_copy[production_col]
                    - df_copy[adjustments_col].abs()
                    - df_copy[writeoffs_col].abs()
                )
            else:
                # If no adjustments/writeoffs columns, use gross production (fallback)
                df_copy["_adjusted_production"] = df_copy[production_col]

            total_collections = pd.Series([0.0] * len(df_copy), index=df_copy.index)
            for col in income_columns:
                # Clean currency formatting before conversion
                df_copy[col] = df_copy[col].apply(clean_currency_string)
                df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce").fillna(0.0)
                total_collections = total_collections + df_copy[col]

            df_copy["_total_collections"] = total_collections
            # Use adjusted production for collection rate calculation
            df_copy["collection_rate"] = (
                df_copy["_total_collections"] / df_copy["_adjusted_production"] * 100
            ).where(df_copy["_adjusted_production"] > 0)

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

        result: HistoricalRateData = {
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
) -> HistoricalCountData:
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

    result: HistoricalCountData = {
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


def calculate_historical_case_acceptance(
    df: pd.DataFrame | None,
    days: int = 30,
) -> HistoricalRateData:
    """
    Calculate historical case acceptance rate with time-series data.
    """
    log.info("metrics.historical_case_acceptance_start", days=days)

    if df is None or df.empty:
        return {
            "time_series": [],
            "average_rate": 0.0,
            "latest_value": None,
            "data_points": 0,
        }

    # Identify date column
    date_cols = ["Submission Date", "submission_date", "Date", "date"]
    date_col = None
    for col in date_cols:
        if col in df.columns:
            date_col = col
            break

    if not date_col:
        return {
            "time_series": [],
            "average_rate": 0.0,
            "latest_value": None,
            "data_points": 0,
        }

    # Get column names from mapping or use defaults
    presented_col = FRONT_MAPPING.get("treatments_presented", "treatments_presented")
    scheduled_col = FRONT_MAPPING.get("treatments_scheduled", "treatments_scheduled")
    same_day_col = FRONT_MAPPING.get("same_day_treatment", "$ Same Day Treatment")

    # Check required columns exist
    required_cols = [presented_col, scheduled_col, same_day_col]
    if not all(col in df.columns for col in required_cols):
        log.warning(
            "metrics.historical_case_acceptance_missing_columns",
            missing=[c for c in required_cols if c not in df.columns],
        )
        return {
            "time_series": [],
            "average_rate": 0.0,
            "latest_value": None,
            "data_points": 0,
        }

    try:
        df_copy = df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors="coerce")
        df_copy = df_copy.dropna(subset=[date_col])

        # Calculate case acceptance per row INCLUDING Same Day Treatment
        df_copy["_case_acceptance_rate"] = (
            (
                pd.to_numeric(df_copy[scheduled_col], errors="coerce")
                + pd.to_numeric(df_copy[same_day_col], errors="coerce")
            )
            / pd.to_numeric(df_copy[presented_col], errors="coerce")
        ) * 100

        # Filter to recent days
        if days > 0:
            cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
            df_copy = df_copy[df_copy[date_col] >= cutoff_date]

        # Sort by date
        df_copy = df_copy.sort_values(date_col)

        # Create time series using safe helper function
        time_series = safe_time_series_conversion(
            df_copy, "_case_acceptance_rate", date_col
        )

        # Calculate aggregates

        latest_value = time_series[-1][1] if time_series else None

        result: HistoricalRateData = {
            "time_series": time_series,
            "average_rate": (
                float(df_copy["_case_acceptance_rate"].mean())
                if not df_copy["_case_acceptance_rate"].isna().all()
                else 0.0
            ),
            "latest_value": latest_value,
            "data_points": len(time_series),
        }

        log.info(
            "metrics.historical_case_acceptance_success",
            data_points=result["data_points"],
        )
        return result

    except Exception as e:
        log.error("metrics.historical_case_acceptance_failed", error=str(e))
        return {
            "time_series": [],
            "average_rate": 0.0,
            "latest_value": None,
            "data_points": 0,
        }


def calculate_historical_hygiene_reappointment(
    df: pd.DataFrame | None, days: int = 30
) -> HistoricalRateData:
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

        result: HistoricalRateData = {
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


def get_all_historical_kpis(days: int = 30) -> HistoricalKPIData:
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
        historical_kpis: dict[str, HistoricalMetricData] = {
            "production_total": calculate_historical_production_total(eod_data, days),
            "collection_rate": calculate_historical_collection_rate(eod_data, days),
            "new_patients": calculate_historical_new_patients(eod_data, days),
            "case_acceptance": calculate_historical_case_acceptance(
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

        current_kpis: KPIData = {
            "production_total": calculate_production_total(eod_data_df),
            "collection_rate": calculate_collection_rate(eod_data_df),
            "new_patients": calculate_new_patients(eod_data_df),
            "case_acceptance": calculate_case_acceptance(front_kpi_data_df),
            "hygiene_reappointment": calculate_hygiene_reappointment(front_kpi_data_df),
        }

        result: HistoricalKPIData = {
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
                "case_acceptance": None,
                "hygiene_reappointment": None,
            },
            "period_days": days,
            "data_date": None,
        }
