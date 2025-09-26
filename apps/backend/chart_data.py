"""Chart Data Processor for Frontend-Agnostic Data Formatting.

Processes time-series data from Google Sheets into JSON-serializable
formats optimized for chart visualization. Handles missing data points,
gaps in time series, and operational day logic.
"""

from datetime import datetime
from typing import Any

import pandas as pd
import structlog

from .metrics import clean_currency_string

try:
    from config.data_sources import COLUMN_MAPPINGS
except ImportError:  # pragma: no cover - configuration module should exist in runtime
    COLUMN_MAPPINGS = {}

# Configure structured logging to stderr
log = structlog.get_logger()

EOD_MAPPING = COLUMN_MAPPINGS.get("eod_billing", {})
FRONT_MAPPING = COLUMN_MAPPINGS.get("front_kpis", {})


def safe_float_conversion(value: Any) -> float | None:
    """Safely convert value to float with None fallback."""

    if value is None or pd.isna(value):
        return None

    try:
        cleaned = clean_currency_string(value)
        if cleaned == "":
            return 0.0
        return float(cleaned)
    except (ValueError, TypeError):
        log.debug("float_conversion.failed", value=value, type=type(value).__name__)
        return None


def safe_int_conversion(value: Any) -> int | None:
    """Safely convert value to integer with None fallback."""

    if value is None or pd.isna(value):
        return None

    try:
        if isinstance(value, str):
            if value.strip() == "":
                return None
            cleaned = clean_currency_string(value)
            return int(float(cleaned))
        return int(value)
    except (ValueError, TypeError):
        log.debug("int_conversion.failed", value=value, type=type(value).__name__)
        return None


def parse_datetime_string(date_str: str | None) -> datetime | None:
    """Parse datetime string from Google Sheets format."""

    if not date_str or pd.isna(date_str):
        return None

    try:
        date_text = str(date_str).strip()
        if " " in date_text:
            return datetime.strptime(date_text, "%Y-%m-%d %H:%M:%S")
        return datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError as error:
        log.debug("datetime_parsing.failed", date_str=date_str, error=str(error))
        return None


def create_time_series_point(
    date: datetime | None, value: float | int | None
) -> dict[str, Any] | None:
    """Create standardized time-series data point."""

    if date is None:
        return None

    return {
        "date": date.strftime("%Y-%m-%d"),
        "timestamp": date.isoformat(),
        "value": value,
        "has_data": value is not None,
    }


def process_time_series_data(
    df: pd.DataFrame | None,
    date_column: str,
    value_column: str,
    data_type: str = "float",
) -> list[dict[str, Any]]:
    """Process DataFrame into time-series format for charts."""

    if df is None or df.empty:
        log.warning("time_series.empty_data", value_column=value_column)
        return []

    if date_column not in df.columns or value_column not in df.columns:
        log.warning(
            "time_series.missing_columns",
            date_column=date_column,
            value_column=value_column,
            available_columns=list(df.columns),
        )
        return []

    time_series: list[dict[str, Any]] = []
    conversion_func = safe_int_conversion if data_type == "int" else safe_float_conversion

    for _, row in df.iterrows():
        date = parse_datetime_string(row[date_column])
        value = conversion_func(row[value_column])

        if date is not None:
            point = create_time_series_point(date, value)
            if point:
                time_series.append(point)

    time_series.sort(key=lambda entry: entry["timestamp"])

    log.info(
        "time_series.processed",
        value_column=value_column,
        data_points=len(time_series),
        valid_values=sum(1 for point in time_series if point["has_data"]),
    )

    return time_series


def validate_chart_data(chart_data: dict[str, Any]) -> bool:
    """Validate chart data structure integrity."""

    required_fields = ["metric_name", "chart_type", "data_type", "time_series"]

    try:
        for field in required_fields:
            if field not in chart_data:
                log.error("chart_data.validation_failed", missing_field=field)
                return False

        time_series = chart_data.get("time_series", [])
        if not isinstance(time_series, list):
            log.error("chart_data.invalid_time_series_type")
            return False

        for point in time_series:
            if not isinstance(point, dict) or "date" not in point:
                log.error("chart_data.invalid_time_series_point", point=point)
                return False

        log.debug("chart_data.validation_passed", metric=chart_data.get("metric_name"))
        return True

    except Exception as error:
        log.error("chart_data.validation_error", error=str(error))
        return False


def process_production_data_for_chart(df: pd.DataFrame) -> dict[str, Any]:
    """Process production data for chart display.

    Args:
        df: DataFrame with production data

    Returns:
        Dictionary with chart-ready data structure
    """
    try:
        log.info("chart_data.processing_started", columns=list(df.columns))

        # Get column names from mapping or fallback to direct names
        date_col = COLUMN_MAPPINGS.get("submission_date", "Submission Date")
        production_col = COLUMN_MAPPINGS.get(
            "total_production", "Total Production Today"
        )

        # Check if required columns exist
        if date_col not in df.columns:
            available_date_cols = [col for col in df.columns if "date" in col.lower()]
            if available_date_cols:
                date_col = available_date_cols[0]
                log.warning(
                    "chart_data.date_column_fallback",
                    original=COLUMN_MAPPINGS.get("submission_date", "Submission Date"),
                    fallback=date_col,
                )
            else:
                log.error("chart_data.no_date_column", columns=list(df.columns))
                return {"dates": [], "values": [], "error": "No date column found"}

        if production_col not in df.columns:
            available_prod_cols = [
                col for col in df.columns if "production" in col.lower()
            ]
            if available_prod_cols:
                production_col = available_prod_cols[0]
                log.warning(
                    "chart_data.production_column_fallback",
                    original=COLUMN_MAPPINGS.get(
                        "total_production", "Total Production Today"
                    ),
                    fallback=production_col,
                )
            else:
                log.error("chart_data.no_production_column", columns=list(df.columns))
                return {
                    "dates": [],
                    "values": [],
                    "error": "No production column found",
                }

        # Clean and prepare data
        chart_df = df[[date_col, production_col]].copy()
        chart_df = chart_df.dropna()

        if chart_df.empty:
            log.warning("chart_data.empty_after_cleanup")
            return {"dates": [], "values": [], "error": "No valid data after cleanup"}

        # Convert dates to datetime and production to numeric
        chart_df[date_col] = pd.to_datetime(chart_df[date_col], errors="coerce")
        chart_df[production_col] = pd.to_numeric(
            chart_df[production_col].apply(clean_currency_string), errors="coerce"
        )

        # Remove any rows where conversion failed
        chart_df = chart_df.dropna()

        if chart_df.empty:
            log.warning("chart_data.empty_after_conversion")
            return {
                "dates": [],
                "values": [],
                "error": "No valid data after conversion",
            }

        # Sort by date
        chart_df = chart_df.sort_values(date_col)

        # Prepare chart data
        dates = chart_df[date_col].dt.strftime("%Y-%m-%d").tolist()
        values = chart_df[production_col].tolist()

        # Calculate basic statistics
        total_production = sum(values)
        avg_production = sum(values) / len(values) if values else 0
        min_production = min(values) if values else 0
        max_production = max(values) if values else 0

        result = {
            "dates": dates,
            "values": values,
            "statistics": {
                "total": round(total_production, 2),
                "average": round(avg_production, 2),
                "minimum": round(min_production, 2),
                "maximum": round(max_production, 2),
                "data_points": len(values),
            },
            "metadata": {
                "date_column": date_col,
                "production_column": production_col,
                "date_range": f"{dates[0]} to {dates[-1]}" if dates else "No data",
            },
        }

        log.info(
            "chart_data.processing_completed",
            data_points=len(values),
            date_range=result["metadata"]["date_range"],
            total_production=total_production,
        )

        return result

    except Exception as e:
        log.error("chart_data.processing_error", error=str(e))
        return {"dates": [], "values": [], "error": f"Processing failed: {str(e)}"}


def process_collection_rate_data_for_chart(df: pd.DataFrame) -> dict[str, Any]:
    """Process collection rate data for chart display.

    Args:
        df: DataFrame with collection and production data

    Returns:
        Dictionary with chart-ready collection rate data
    """
    try:
        log.info(
            "chart_data.collection_rate_processing_started", columns=list(df.columns)
        )

        # Get column names from mapping
        date_col = COLUMN_MAPPINGS.get("submission_date", "Submission Date")
        production_col = COLUMN_MAPPINGS.get(
            "total_production", "Total Production Today"
        )
        collections_col = COLUMN_MAPPINGS.get("patient_income", "Patient Income Today")
        insurance_col = COLUMN_MAPPINGS.get(
            "insurance_income", "Insurance Income Today"
        )

        # Check for required columns with fallback logic
        missing_cols = []
        for col_name, col_key in [
            (date_col, "date"),
            (production_col, "production"),
            (collections_col, "collections"),
        ]:
            if col_name not in df.columns:
                missing_cols.append(col_key)

        if missing_cols:
            log.error("chart_data.missing_columns", missing=missing_cols)
            return {
                "dates": [],
                "values": [],
                "error": f"Missing columns: {missing_cols}",
            }

        # Prepare data
        chart_df = df[[date_col, production_col, collections_col]].copy()

        # Add insurance collections if available
        if insurance_col in df.columns:
            chart_df[insurance_col] = pd.to_numeric(
                df[insurance_col].apply(clean_currency_string), errors="coerce"
            ).fillna(0)
        else:
            chart_df[insurance_col] = 0

        # Clean data
        chart_df = chart_df.dropna(subset=[date_col, production_col, collections_col])

        if chart_df.empty:
            return {"dates": [], "values": [], "error": "No valid data after cleanup"}

        # Convert data types
        chart_df[date_col] = pd.to_datetime(chart_df[date_col], errors="coerce")
        chart_df[production_col] = pd.to_numeric(
            chart_df[production_col].apply(clean_currency_string), errors="coerce"
        )
        chart_df[collections_col] = pd.to_numeric(
            chart_df[collections_col].apply(clean_currency_string), errors="coerce"
        )

        # Remove rows with conversion failures
        chart_df = chart_df.dropna()

        if chart_df.empty:
            return {
                "dates": [],
                "values": [],
                "error": "No valid data after conversion",
            }

        # Calculate total collections (patient + insurance)
        chart_df["total_collections"] = (
            chart_df[collections_col] + chart_df[insurance_col]
        )

        # Calculate collection rate (avoid division by zero)
        chart_df["collection_rate"] = (
            (chart_df["total_collections"] / chart_df[production_col] * 100)
            .fillna(0)
            .replace([float("inf"), -float("inf")], 0)
        )

        # Sort by date
        chart_df = chart_df.sort_values(date_col)

        # Prepare chart data
        dates = chart_df[date_col].dt.strftime("%Y-%m-%d").tolist()
        values = chart_df["collection_rate"].round(2).tolist()

        # Calculate statistics
        avg_rate = sum(values) / len(values) if values else 0
        min_rate = min(values) if values else 0
        max_rate = max(values) if values else 0

        result = {
            "dates": dates,
            "values": values,
            "statistics": {
                "average": round(avg_rate, 2),
                "minimum": round(min_rate, 2),
                "maximum": round(max_rate, 2),
                "data_points": len(values),
            },
            "metadata": {
                "date_column": date_col,
                "collections_column": collections_col,
                "production_column": production_col,
                "date_range": f"{dates[0]} to {dates[-1]}" if dates else "No data",
            },
        }

        log.info(
            "chart_data.collection_rate_completed",
            data_points=len(values),
            avg_rate=avg_rate,
        )

        return result

    except Exception as e:
        log.error("chart_data.collection_rate_error", error=str(e))
        return {
            "dates": [],
            "values": [],
            "error": f"Collection rate processing failed: {str(e)}",
        }


def process_new_patients_data_for_chart(df: pd.DataFrame) -> dict[str, Any]:
    """Process new patients data for chart display.

    Args:
        df: DataFrame with new patients data

    Returns:
        Dictionary with chart-ready new patients data
    """
    try:
        log.info("chart_data.new_patients_processing_started", columns=list(df.columns))

        # Get column names
        date_col = COLUMN_MAPPINGS.get("submission_date", "Submission Date")
        new_patients_col = COLUMN_MAPPINGS.get(
            "new_patients", "New Patients - Total Month to Date"
        )

        # Check required columns
        if date_col not in df.columns or new_patients_col not in df.columns:
            missing = []
            if date_col not in df.columns:
                missing.append("date")
            if new_patients_col not in df.columns:
                missing.append("new_patients")
            return {"dates": [], "values": [], "error": f"Missing columns: {missing}"}

        # Clean and prepare data
        chart_df = df[[date_col, new_patients_col]].copy()
        chart_df = chart_df.dropna()

        if chart_df.empty:
            return {"dates": [], "values": [], "error": "No valid data"}

        # Convert data types
        chart_df[date_col] = pd.to_datetime(chart_df[date_col], errors="coerce")
        chart_df[new_patients_col] = pd.to_numeric(
            chart_df[new_patients_col], errors="coerce"
        )

        chart_df = chart_df.dropna()

        if chart_df.empty:
            return {
                "dates": [],
                "values": [],
                "error": "No valid data after conversion",
            }

        # Sort by date
        chart_df = chart_df.sort_values(date_col)

        # Prepare chart data
        dates = chart_df[date_col].dt.strftime("%Y-%m-%d").tolist()
        values = chart_df[new_patients_col].astype(int).tolist()

        # Calculate statistics
        total_new = sum(values)
        avg_new = sum(values) / len(values) if values else 0
        min_new = min(values) if values else 0
        max_new = max(values) if values else 0

        result = {
            "dates": dates,
            "values": values,
            "statistics": {
                "total": total_new,
                "average": round(avg_new, 1),
                "minimum": min_new,
                "maximum": max_new,
                "data_points": len(values),
            },
            "metadata": {
                "date_column": date_col,
                "new_patients_column": new_patients_col,
                "date_range": f"{dates[0]} to {dates[-1]}" if dates else "No data",
            },
        }

        log.info(
            "chart_data.new_patients_completed",
            data_points=len(values),
            total=total_new,
        )

        return result

    except Exception as e:
        log.error("chart_data.new_patients_error", error=str(e))
        return {
            "dates": [],
            "values": [],
            "error": f"New patients processing failed: {str(e)}",
        }


def process_case_acceptance_data_for_chart(df: pd.DataFrame) -> dict[str, Any]:
    """Process case acceptance data for chart display.

    Args:
        df: DataFrame with case acceptance data

    Returns:
        Dictionary with chart-ready case acceptance rate data
    """
    try:
        log.info(
            "chart_data.case_acceptance_processing_started", columns=list(df.columns)
        )

        # Get column names
        date_col = COLUMN_MAPPINGS.get("timestamp", "Timestamp")
        presented_col = COLUMN_MAPPINGS.get(
            "treatments_presented", "Treatments Presented"
        )
        scheduled_col = COLUMN_MAPPINGS.get(
            "treatments_scheduled", "Treatments Scheduled"
        )
        same_day_col = COLUMN_MAPPINGS.get("same_day_starts", "Same Day Starts")

        # Check required columns
        missing_cols = []
        for col_name, col_key in [
            (date_col, "date"),
            (presented_col, "presented"),
            (scheduled_col, "scheduled"),
        ]:
            if col_name not in df.columns:
                missing_cols.append(col_key)

        if missing_cols:
            return {
                "dates": [],
                "values": [],
                "error": f"Missing columns: {missing_cols}",
            }

        # Prepare data
        chart_df = df[[date_col, presented_col, scheduled_col]].copy()

        # Add same day starts if available
        if same_day_col in df.columns:
            chart_df[same_day_col] = pd.to_numeric(
                df[same_day_col], errors="coerce"
            ).fillna(0)
        else:
            chart_df[same_day_col] = 0

        # Clean data
        chart_df = chart_df.dropna(subset=[date_col, presented_col, scheduled_col])

        if chart_df.empty:
            return {"dates": [], "values": [], "error": "No valid data"}

        # Convert data types
        chart_df[date_col] = pd.to_datetime(chart_df[date_col], errors="coerce")
        chart_df[presented_col] = pd.to_numeric(
            chart_df[presented_col], errors="coerce"
        )
        chart_df[scheduled_col] = pd.to_numeric(
            chart_df[scheduled_col], errors="coerce"
        )

        chart_df = chart_df.dropna()

        if chart_df.empty:
            return {
                "dates": [],
                "values": [],
                "error": "No valid data after conversion",
            }

        # Calculate total accepted (scheduled + same day)
        chart_df["total_accepted"] = chart_df[scheduled_col] + chart_df[same_day_col]

        # Calculate acceptance rate
        chart_df["acceptance_rate"] = (
            (chart_df["total_accepted"] / chart_df[presented_col] * 100)
            .fillna(0)
            .replace([float("inf"), -float("inf")], 0)
        )

        # Sort by date
        chart_df = chart_df.sort_values(date_col)

        # Prepare chart data
        dates = chart_df[date_col].dt.strftime("%Y-%m-%d").tolist()
        values = chart_df["acceptance_rate"].round(2).tolist()

        # Calculate statistics
        avg_rate = sum(values) / len(values) if values else 0
        min_rate = min(values) if values else 0
        max_rate = max(values) if values else 0

        result = {
            "dates": dates,
            "values": values,
            "statistics": {
                "average": round(avg_rate, 2),
                "minimum": round(min_rate, 2),
                "maximum": round(max_rate, 2),
                "data_points": len(values),
            },
            "metadata": {
                "date_column": date_col,
                "presented_column": presented_col,
                "scheduled_column": scheduled_col,
                "date_range": f"{dates[0]} to {dates[-1]}" if dates else "No data",
            },
        }

        log.info(
            "chart_data.case_acceptance_completed",
            data_points=len(values),
            avg_rate=avg_rate,
        )

        return result

    except Exception as e:
        log.error("chart_data.case_acceptance_error", error=str(e))
        return {
            "dates": [],
            "values": [],
            "error": f"Case acceptance processing failed: {str(e)}",
        }


def process_hygiene_reappointment_data_for_chart(df: pd.DataFrame) -> dict[str, Any]:
    """Process hygiene reappointment data for chart display.

    Args:
        df: DataFrame with hygiene reappointment data

    Returns:
        Dictionary with chart-ready hygiene reappointment rate data
    """
    try:
        log.info("chart_data.hygiene_processing_started", columns=list(df.columns))

        # Get column names
        date_col = COLUMN_MAPPINGS.get("timestamp", "Timestamp")
        total_hygiene_col = COLUMN_MAPPINGS.get(
            "total_hygiene_appointments", "Total Hygiene Appointments"
        )
        not_reappointed_col = COLUMN_MAPPINGS.get(
            "patients_not_reappointed", "Patients Not Reappointed"
        )

        # Check required columns
        missing_cols = []
        for col_name, col_key in [
            (date_col, "date"),
            (total_hygiene_col, "total_hygiene"),
            (not_reappointed_col, "not_reappointed"),
        ]:
            if col_name not in df.columns:
                missing_cols.append(col_key)

        if missing_cols:
            return {
                "dates": [],
                "values": [],
                "error": f"Missing columns: {missing_cols}",
            }

        # Clean and prepare data
        chart_df = df[[date_col, total_hygiene_col, not_reappointed_col]].copy()
        chart_df = chart_df.dropna()

        if chart_df.empty:
            return {"dates": [], "values": [], "error": "No valid data"}

        # Convert data types
        chart_df[date_col] = pd.to_datetime(chart_df[date_col], errors="coerce")
        chart_df[total_hygiene_col] = pd.to_numeric(
            chart_df[total_hygiene_col], errors="coerce"
        )
        chart_df[not_reappointed_col] = pd.to_numeric(
            chart_df[not_reappointed_col], errors="coerce"
        )

        chart_df = chart_df.dropna()

        if chart_df.empty:
            return {
                "dates": [],
                "values": [],
                "error": "No valid data after conversion",
            }

        # Calculate reappointment rate
        chart_df["reappointed"] = (
            chart_df[total_hygiene_col] - chart_df[not_reappointed_col]
        )
        chart_df["reappointment_rate"] = (
            (chart_df["reappointed"] / chart_df[total_hygiene_col] * 100)
            .fillna(0)
            .replace([float("inf"), -float("inf")], 0)
        )

        # Sort by date
        chart_df = chart_df.sort_values(date_col)

        # Prepare chart data
        dates = chart_df[date_col].dt.strftime("%Y-%m-%d").tolist()
        values = chart_df["reappointment_rate"].round(2).tolist()

        # Calculate statistics
        avg_rate = sum(values) / len(values) if values else 0
        min_rate = min(values) if values else 0
        max_rate = max(values) if values else 0

        result = {
            "dates": dates,
            "values": values,
            "statistics": {
                "average": round(avg_rate, 2),
                "minimum": round(min_rate, 2),
                "maximum": round(max_rate, 2),
                "data_points": len(values),
            },
            "metadata": {
                "date_column": date_col,
                "total_hygiene_column": total_hygiene_col,
                "not_reappointed_column": not_reappointed_col,
                "date_range": f"{dates[0]} to {dates[-1]}" if dates else "No data",
            },
        }

        log.info(
            "chart_data.hygiene_completed", data_points=len(values), avg_rate=avg_rate
        )

        return result

    except Exception as e:
        log.error("chart_data.hygiene_error", error=str(e))
        return {
            "dates": [],
            "values": [],
            "error": f"Hygiene reappointment processing failed: {str(e)}",
        }


def calculate_basic_statistics(time_series: list[dict[str, Any]]) -> dict[str, float]:
    """Calculate statistics for time series data.

    Args:
        time_series: List of dictionaries with 'date' and 'value' keys

    Returns:
        Dictionary with calculated statistics
    """
    if not time_series:
        return {
            "average": 0.0,
            "minimum": 0.0,
            "maximum": 0.0,
            "total": 0.0,
            "data_points": 0,
        }

    values = [entry["value"] for entry in time_series if entry.get("value") is not None]

    if not values:
        return {
            "average": 0.0,
            "minimum": 0.0,
            "maximum": 0.0,
            "total": 0.0,
            "data_points": 0,
        }

    return {
        "average": round(sum(values) / len(values), 2),
        "minimum": round(min(values), 2),
        "maximum": round(max(values), 2),
        "total": round(sum(values), 2),
        "data_points": len(values),
    }


def get_chart_data_processor(kpi_type: str):
    """Get the appropriate chart data processor function for a KPI type.

    Args:
        kpi_type: Type of KPI ('production', 'collection_rate', 'new_patients',
                  'case_acceptance', 'hygiene_reappointment')

    Returns:
        Function to process data for the specified KPI type
    """
    processors = {
        "production": process_production_data_for_chart,
        "collection_rate": process_collection_rate_data_for_chart,
        "new_patients": process_new_patients_data_for_chart,
        "case_acceptance": process_case_acceptance_data_for_chart,
        "hygiene_reappointment": process_hygiene_reappointment_data_for_chart,
    }

    processor = processors.get(kpi_type)
    if not processor:
        available_types = ", ".join(processors.keys())
        raise ValueError(
            f"Unknown KPI type: {kpi_type}. Available types: {available_types}"
        )

    return processor


def create_empty_chart_data(error_message: str = "No data available") -> dict[str, Any]:
    """Create empty chart data structure with error message.

    Args:
        error_message: Message to include in the error field

    Returns:
        Empty chart data structure
    """
    return {
        "dates": [],
        "values": [],
        "statistics": {
            "total": 0.0,
            "average": 0.0,
            "minimum": 0.0,
            "maximum": 0.0,
            "data_points": 0,
        },
        "metadata": {
            "date_range": "No data",
            "error": error_message,
        },
        "error": error_message,
    }


def validate_processed_chart_data(data: dict[str, Any]) -> bool:
    """Validate processed chart data structure.

    Args:
        data: Processed chart data

    Returns:
        bool: True if data structure is valid
    """
    try:
        required_keys = {"dates", "values", "statistics", "metadata"}
        if not required_keys.issubset(data.keys()):
            return False

        # Check that dates and values are lists of same length
        if not isinstance(data["dates"], list) or not isinstance(data["values"], list):
            return False

        if len(data["dates"]) != len(data["values"]):
            return False

        # Check statistics structure
        stats = data["statistics"]
        required_stats = {"total", "average", "minimum", "maximum", "data_points"}
        if not required_stats.issubset(stats.keys()):
            return False

        # Check metadata structure
        metadata = data["metadata"]
        return isinstance(metadata, dict)

    except Exception as e:
        log.error("chart_data.validation_error", error=str(e))
        return False


def aggregate_to_weekly(
    data: dict[str, Any], business_days_only: bool = True
) -> dict[str, Any]:
    """Aggregate daily data into weekly summaries.

    Args:
        data: Chart data with 'dates' and 'values' keys
        business_days_only: If True, excludes Sundays from aggregation
                            (Mon-Sat operational)

    Returns:
        Aggregated weekly data in same format as input
    """
    try:
        if not data["dates"] or not data["values"]:
            return data

        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(
            {"date": pd.to_datetime(data["dates"]), "value": data["values"]}
        )

        # Filter out Sundays if business_days_only is True
        if business_days_only:
            # Keep Monday (0) through Saturday (5), exclude Sunday (6)
            df = df[df["date"].dt.dayofweek < 6]

        if df.empty:
            return create_empty_chart_data("No business days data available")

        # Group by week and sum values
        weekly = (
            df.groupby(df["date"].dt.to_period("W"))
            .agg(
                {
                    "date": "last",  # Use last date of week as representative
                    "value": "sum",  # Sum values for the week
                }
            )
            .reset_index(drop=True)
        )

        # Recalculate statistics for weekly data
        if not weekly["value"].empty and weekly["value"].notna().any():
            # Convert pandas Series to time_series format expected by
            # calculate_chart_statistics
            time_series = [
                {"date": row["date"].strftime("%Y-%m-%d"), "value": row["value"]}
                for _, row in weekly.iterrows()
                if pd.notna(row["value"])
            ]

            statistics = calculate_basic_statistics(time_series)
        else:
            statistics = {
                "average": 0.0,
                "minimum": 0.0,
                "maximum": 0.0,
                "total": 0.0,
                "data_points": 0,
            }

        return {
            "dates": weekly["date"].dt.strftime("%Y-%m-%d").tolist(),
            "values": weekly["value"].round(2).tolist(),
            "statistics": statistics,
            "metadata": {
                **data.get("metadata", {}),
                "aggregation": "weekly",
                "business_days_only": business_days_only,
            },
        }

    except Exception as e:
        log.error("chart_data.weekly_aggregation_error", error=str(e))
        return create_empty_chart_data(f"Weekly aggregation failed: {str(e)}")


def aggregate_to_monthly(
    data: dict[str, Any], business_days_only: bool = True
) -> dict[str, Any]:
    """Aggregate daily data into monthly summaries.

    Args:
        data: Chart data with 'dates' and 'values' keys
        business_days_only: If True, excludes Sundays from aggregation

    Returns:
        Aggregated monthly data in same format as input
    """
    try:
        if not data["dates"] or not data["values"]:
            return data

        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(
            {"date": pd.to_datetime(data["dates"]), "value": data["values"]}
        )

        # Filter out Sundays if business_days_only is True
        if business_days_only:
            df = df[df["date"].dt.dayofweek < 6]

        if df.empty:
            return create_empty_chart_data("No business days data available")

        # Group by month and sum values
        monthly = (
            df.groupby(df["date"].dt.to_period("M"))
            .agg(
                {
                    "date": "last",  # Use last date of month as representative
                    "value": "sum",  # Sum values for the month
                }
            )
            .reset_index(drop=True)
        )

        # Recalculate statistics for monthly data
        if not monthly["value"].empty and monthly["value"].notna().any():
            # Convert pandas Series to time_series format expected by
            # calculate_chart_statistics
            time_series = [
                {"date": row["date"].strftime("%Y-%m-%d"), "value": row["value"]}
                for _, row in monthly.iterrows()
                if pd.notna(row["value"])
            ]

            statistics = calculate_basic_statistics(time_series)
        else:
            statistics = {
                "average": 0.0,
                "minimum": 0.0,
                "maximum": 0.0,
                "total": 0.0,
                "data_points": 0,
            }

        return {
            "dates": monthly["date"].dt.strftime("%Y-%m-%d").tolist(),
            "values": monthly["value"].round(2).tolist(),
            "statistics": statistics,
            "metadata": {
                **data.get("metadata", {}),
                "aggregation": "monthly",
                "business_days_only": business_days_only,
            },
        }

    except Exception as e:
        log.error("chart_data.monthly_aggregation_error", error=str(e))
        return create_empty_chart_data(f"Monthly aggregation failed: {str(e)}")


def filter_data_by_date_range(
    data: dict[str, Any], start_date: str, end_date: str
) -> dict[str, Any]:
    """Filter chart data by date range.

    Args:
        data: Chart data with 'dates' and 'values' keys
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Filtered data in same format as input
    """
    try:
        if not data["dates"] or not data["values"]:
            return data

        # Convert to DataFrame for easier filtering
        df = pd.DataFrame(
            {"date": pd.to_datetime(data["dates"]), "value": data["values"]}
        )

        # Parse filter dates
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        # Filter by date range
        mask = (df["date"] >= start_dt) & (df["date"] <= end_dt)
        filtered_df = df[mask]

        if filtered_df.empty:
            return create_empty_chart_data(
                f"No data in range {start_date} to {end_date}"
            )

        # Recalculate statistics for filtered data
        time_series = [
            {"date": row["date"].strftime("%Y-%m-%d"), "value": row["value"]}
            for _, row in filtered_df.iterrows()
            if pd.notna(row["value"])
        ]

        statistics = calculate_basic_statistics(time_series)

        return {
            "dates": filtered_df["date"].dt.strftime("%Y-%m-%d").tolist(),
            "values": filtered_df["value"].tolist(),
            "statistics": statistics,
            "metadata": {
                **data.get("metadata", {}),
                "date_filter": f"{start_date} to {end_date}",
                "filtered_data_points": len(filtered_df),
            },
        }

    except Exception as e:
        log.error("chart_data.date_filter_error", error=str(e))
        return create_empty_chart_data(f"Date filtering failed: {str(e)}")


def calculate_chart_statistics(time_series: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate summary statistics for chart data."""

    if not time_series:
        return {
            "total_points": 0,
            "valid_points": 0,
            "missing_points": 0,
            "coverage_percentage": 0.0,
            "date_range": None,
        }

    valid_values = [point["value"] for point in time_series if point["has_data"]]

    stats: dict[str, Any] = {
        "total_points": len(time_series),
        "valid_points": len(valid_values),
        "missing_points": len(time_series) - len(valid_values),
        "coverage_percentage": (len(valid_values) / len(time_series)) * 100
        if time_series
        else 0.0,
        "date_range": {
            "start": time_series[0]["date"],
            "end": time_series[-1]["date"],
        },
    }

    if valid_values:
        stats.update(
            {
                "min_value": min(valid_values),
                "max_value": max(valid_values),
                "average_value": sum(valid_values) / len(valid_values),
            }
        )

    log.debug("chart_statistics.calculated", **stats)
    return stats


def _empty_chart_data(metric_name: str) -> dict[str, Any]:
    """Create empty chart data structure for missing data."""

    return {
        "metric_name": metric_name,
        "chart_type": "line",
        "data_type": "unknown",
        "time_series": [],
        "statistics": calculate_chart_statistics([]),
        "format_options": {},
        "error": "No data available",
    }


def format_production_chart_data(
    eod_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> dict[str, Any]:
    """Format production data for chart visualization."""

    if eod_df is None or eod_df.empty:
        return _empty_chart_data("Production Total")

    resolved_date_column = EOD_MAPPING.get("date", date_column)
    production_column = EOD_MAPPING.get("production", "Total Production Today")
    adjustments_column = EOD_MAPPING.get("adjustments", "Adjustments Today")
    writeoffs_column = EOD_MAPPING.get("writeoffs", "Write-offs Today")

    if all(
        column in eod_df.columns
        for column in [production_column, adjustments_column, writeoffs_column]
    ):
        df_copy = eod_df.copy()
        for column in [production_column, adjustments_column, writeoffs_column]:
            df_copy[column] = df_copy[column].apply(clean_currency_string)
            df_copy[column] = pd.to_numeric(df_copy[column], errors="coerce").fillna(0.0)

        df_copy["_production_total_story_2_1"] = (
            df_copy[production_column]
            + df_copy[adjustments_column]
            + df_copy[writeoffs_column]
        )

        time_series = process_time_series_data(
            df_copy,
            resolved_date_column,
            "_production_total_story_2_1",
            "float",
        )
    else:
        fallback_column = (
            "total_production" if "total_production" in eod_df.columns else "Production"
        )
        time_series = process_time_series_data(
            eod_df, resolved_date_column, fallback_column, "float"
        )

    return {
        "metric_name": "Production Total",
        "chart_type": "line",
        "data_type": "currency",
        "time_series": time_series,
        "statistics": calculate_chart_statistics(time_series),
        "format_options": {
            "currency_symbol": "$",
            "decimal_places": 0,
            "show_grid": True,
            "line_color": "#007E9E",
        },
    }


def format_collection_rate_chart_data(
    eod_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> dict[str, Any]:
    """Format collection rate data for chart visualization."""

    if eod_df is None or eod_df.empty:
        return _empty_chart_data("Collection Rate")

    resolved_date_column = EOD_MAPPING.get("date", date_column)
    production_column = EOD_MAPPING.get("production", "Total Production Today")
    income_columns = [
        EOD_MAPPING.get("patient_income", "Patient Income Today"),
        EOD_MAPPING.get("unearned_income", "Unearned Income Today"),
        EOD_MAPPING.get("insurance_income", "Insurance Income Today"),
    ]

    rate_df = eod_df.copy()

    if production_column in rate_df.columns and all(
        column in rate_df.columns for column in income_columns
    ):
        rate_df[production_column] = rate_df[production_column].apply(
            clean_currency_string
        )
        rate_df[production_column] = pd.to_numeric(
            rate_df[production_column], errors="coerce"
        )

        total_collections = 0.0
        for column in income_columns:
            rate_df[column] = rate_df[column].apply(clean_currency_string)
            rate_df[column] = pd.to_numeric(rate_df[column], errors="coerce").fillna(0.0)
            total_collections += rate_df[column]

        rate_df["_total_collections_story_2_1"] = total_collections
        rate_df["collection_rate"] = (
            rate_df["_total_collections_story_2_1"] / rate_df[production_column] * 100
        ).where(rate_df[production_column] > 0)
    else:
        fallback_production = (
            "total_production"
            if "total_production" in rate_df.columns
            else "Production"
        )
        fallback_collections = (
            "total_collections"
            if "total_collections" in rate_df.columns
            else "Collections"
        )

        if (
            fallback_production not in rate_df.columns
            or fallback_collections not in rate_df.columns
        ):
            log.warning(
                "collection_rate.missing_columns",
                production_col=production_column,
                income_columns=income_columns,
                fallback_production=fallback_production,
                fallback_collections=fallback_collections,
            )
            return _empty_chart_data("Collection Rate")

        collection_rates = []
        for _, row in rate_df.iterrows():
            production = safe_float_conversion(row.get(fallback_production))
            collections = safe_float_conversion(row.get(fallback_collections))

            if production and production > 0 and collections is not None:
                rate = (collections / production) * 100
            else:
                rate = None

            collection_rates.append(rate)

        rate_df["collection_rate"] = collection_rates

    time_series = process_time_series_data(
        rate_df, resolved_date_column, "collection_rate", "float"
    )

    return {
        "metric_name": "Collection Rate",
        "chart_type": "line",
        "data_type": "percentage",
        "time_series": time_series,
        "statistics": calculate_chart_statistics(time_series),
        "format_options": {
            "percentage_symbol": "%",
            "decimal_places": 1,
            "show_grid": True,
            "line_color": "#142D54",
            "target_range": {"min": 95.0, "max": 100.0},
        },
    }


def format_new_patients_chart_data(
    eod_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> dict[str, Any]:
    """Format new patients data for chart visualization."""

    if eod_df is None or eod_df.empty:
        return _empty_chart_data("New Patients")

    resolved_date_column = EOD_MAPPING.get("date", date_column)
    mtd_column = EOD_MAPPING.get(
        "new_patients_mtd", "New Patients - Total Month to Date"
    )

    if resolved_date_column in eod_df.columns and mtd_column in eod_df.columns:
        df_copy = eod_df[[resolved_date_column, mtd_column]].copy()
        df_copy[resolved_date_column] = pd.to_datetime(
            df_copy[resolved_date_column], errors="coerce"
        )
        df_copy[mtd_column] = df_copy[mtd_column].apply(clean_currency_string)
        df_copy[mtd_column] = pd.to_numeric(df_copy[mtd_column], errors="coerce")
        df_copy = df_copy.dropna(subset=[resolved_date_column])
        df_copy = df_copy.sort_values(resolved_date_column)

        daily_counts = df_copy[mtd_column].diff()
        if not daily_counts.empty:
            daily_counts.iloc[0] = df_copy[mtd_column].iloc[0]
        daily_counts = daily_counts.where(daily_counts >= 0, df_copy[mtd_column])
        df_copy["_daily_new_patients"] = daily_counts.fillna(0.0)

        time_series = process_time_series_data(
            df_copy, resolved_date_column, "_daily_new_patients", "int"
        )
    else:
        fallback_column = "new_patients"
        time_series = process_time_series_data(
            eod_df, resolved_date_column, fallback_column, "int"
        )

    return {
        "metric_name": "New Patients",
        "chart_type": "bar",
        "data_type": "count",
        "time_series": time_series,
        "statistics": calculate_chart_statistics(time_series),
        "format_options": {
            "decimal_places": 0,
            "show_grid": True,
            "bar_color": "#007E9E",
        },
    }


def format_case_acceptance_chart_data(
    front_kpi_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> dict[str, Any]:
    """Format case acceptance data for chart visualization."""

    if front_kpi_df is None or front_kpi_df.empty:
        return _empty_chart_data("Case Acceptance")

    resolved_date_column = FRONT_MAPPING.get("date", date_column)
    presented_column = FRONT_MAPPING.get("treatments_presented", "treatments_presented")
    scheduled_column = FRONT_MAPPING.get("treatments_scheduled", "treatments_scheduled")
    same_day_column = FRONT_MAPPING.get("same_day_treatment", "$ Same Day Treatment")

    acceptance_rates = []
    for _, row in front_kpi_df.iterrows():
        presented = safe_float_conversion(row.get(presented_column))
        scheduled = safe_float_conversion(row.get(scheduled_column))
        same_day = safe_float_conversion(row.get(same_day_column))

        if (
            presented
            and presented > 0
            and scheduled is not None
            and same_day is not None
        ):
            rate = ((scheduled + same_day) / presented) * 100
        else:
            rate = None

        acceptance_rates.append(rate)

    rate_df = front_kpi_df.copy()
    rate_df["acceptance_rate"] = acceptance_rates

    time_series = process_time_series_data(
        rate_df, resolved_date_column, "acceptance_rate", "float"
    )

    return {
        "metric_name": "Case Acceptance",
        "chart_type": "line",
        "data_type": "percentage",
        "time_series": time_series,
        "statistics": calculate_chart_statistics(time_series),
        "format_options": {
            "percentage_symbol": "%",
            "decimal_places": 1,
            "show_grid": True,
            "line_color": "#142D54",
            "target_range": {"min": 80.0, "max": 100.0},
        },
    }


def format_hygiene_reappointment_chart_data(
    front_kpi_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> dict[str, Any]:
    """Format hygiene reappointment data for chart visualization."""

    if front_kpi_df is None or front_kpi_df.empty:
        return _empty_chart_data("Hygiene Reappointment")

    resolved_date_column = FRONT_MAPPING.get("date", date_column)
    hygiene_column = FRONT_MAPPING.get("hygiene_total", "Total hygiene Appointments")
    not_reappointed_column = FRONT_MAPPING.get(
        "hygiene_not_reappointed", "Number of patients NOT reappointed?"
    )

    reappointment_rates = []
    for _, row in front_kpi_df.iterrows():
        total_hygiene = safe_float_conversion(row.get(hygiene_column))
        not_reappointed = safe_float_conversion(row.get(not_reappointed_column))

        if total_hygiene and total_hygiene > 0 and not_reappointed is not None:
            kept = total_hygiene - not_reappointed
            rate = (kept / total_hygiene) * 100
        else:
            rate = None

        reappointment_rates.append(rate)

    rate_df = front_kpi_df.copy()
    rate_df["reappointment_rate"] = reappointment_rates

    time_series = process_time_series_data(
        rate_df, resolved_date_column, "reappointment_rate", "float"
    )

    return {
        "metric_name": "Hygiene Reappointment",
        "chart_type": "line",
        "data_type": "percentage",
        "time_series": time_series,
        "statistics": calculate_chart_statistics(time_series),
        "format_options": {
            "percentage_symbol": "%",
            "decimal_places": 1,
            "show_grid": True,
            "line_color": "#007E9E",
            "target_range": {"min": 85.0, "max": 100.0},
        },
    }


def format_all_chart_data(
    eod_df: pd.DataFrame | None,
    front_kpi_df: pd.DataFrame | None,
    date_column: str = "Submission Date",
) -> dict[str, dict[str, Any]]:
    """Format all KPI data for chart visualization."""

    log.info("chart_data.formatting_all_metrics")

    chart_data = {
        "production_total": format_production_chart_data(eod_df, date_column),
        "collection_rate": format_collection_rate_chart_data(eod_df, date_column),
        "new_patients": format_new_patients_chart_data(eod_df, date_column),
        "case_acceptance": format_case_acceptance_chart_data(front_kpi_df, date_column),
        "hygiene_reappointment": format_hygiene_reappointment_chart_data(
            front_kpi_df, date_column
        ),
    }

    chart_data["metadata"] = {
        "generated_at": datetime.now().isoformat(),
        "data_sources": {
            "eod_available": eod_df is not None and not eod_df.empty,
            "front_kpi_available": front_kpi_df is not None and not front_kpi_df.empty,
        },
        "total_metrics": 5,
    }

    log.info(
        "chart_data.formatting_complete",
        metrics_count=chart_data["metadata"]["total_metrics"],
        eod_available=chart_data["metadata"]["data_sources"]["eod_available"],
        front_kpi_available=chart_data["metadata"]["data_sources"]["front_kpi_available"],
    )

    return chart_data
