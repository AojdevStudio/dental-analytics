"""Chart Data Processor for Frontend-Agnostic Data Formatting.

Processes time-series data from Google Sheets into JSON-serializable
formats optimized for chart visualization. Handles missing data points,
gaps in time series, and operational day logic.
"""

import sys
from datetime import datetime
from typing import Any

import pandas as pd
import structlog

try:
    from config.data_sources import COLUMN_MAPPINGS
except ImportError:  # pragma: no cover - configuration module should exist in runtime
    COLUMN_MAPPINGS = {}

# Configure structured logging to stderr
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)

log = structlog.get_logger()

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


def safe_float_conversion(value: Any) -> float | None:
    """Safely convert value to float with None fallback.

    Args:
        value: Value to convert

    Returns:
        Float value or None if conversion fails
    """
    if value is None or pd.isna(value):
        return None

    try:
        # Clean currency formatting and convert
        cleaned = clean_currency_string(value)
        return float(cleaned)
    except (ValueError, TypeError):
        log.debug("float_conversion.failed", value=value, type=type(value).__name__)
        return None


def safe_int_conversion(value: Any) -> int | None:
    """Safely convert value to integer with None fallback.

    Args:
        value: Value to convert

    Returns:
        Integer value or None if conversion fails
    """
    if value is None or pd.isna(value):
        return None

    try:
        if isinstance(value, str):
            cleaned = value.replace(",", "")
            return int(float(cleaned))  # Handle "123.0" -> 123
        return int(value)
    except (ValueError, TypeError):
        log.debug("int_conversion.failed", value=value, type=type(value).__name__)
        return None


def parse_datetime_string(date_str: str) -> datetime | None:
    """Parse datetime string from Google Sheets format.

    Args:
        date_str: Date string in format "YYYY-MM-DD HH:MM:SS"

    Returns:
        Parsed datetime or None if parsing fails
    """
    if not date_str or pd.isna(date_str):
        return None

    try:
        # Handle various datetime formats from Google Sheets
        if " " in date_str:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S")
        else:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError as e:
        log.debug("datetime_parsing.failed", date_str=date_str, error=str(e))
        return None


def create_time_series_point(
    date: datetime | None, value: float | int | None
) -> dict[str, Any] | None:
    """Create standardized time-series data point.

    Args:
        date: Data point date (optional)
        value: Metric value (can be None for missing data)

    Returns:
        Standardized data point or None if date is invalid
    """
    if date is None:
        return None

    return {
        "date": date.strftime("%Y-%m-%d"),
        "timestamp": date.isoformat(),
        "value": value,
        "has_data": value is not None,
    }


def process_time_series_data(
    df: pd.DataFrame,
    date_column: str,
    value_column: str,
    data_type: str = "float",
) -> list[dict[str, Any]]:
    """Process DataFrame into time-series format for charts.

    Args:
        df: Source DataFrame
        date_column: Name of date column
        value_column: Name of value column
        data_type: 'float' or 'int' for value conversion

    Returns:
        List of time-series data points
    """
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

    time_series = []
    conversion_func = (
        safe_int_conversion if data_type == "int" else safe_float_conversion
    )

    for _, row in df.iterrows():
        date = parse_datetime_string(str(row[date_column]))
        value = conversion_func(row[value_column])

        if date is not None:
            data_point = create_time_series_point(date, value)
            if data_point:
                time_series.append(data_point)

    # Sort by date
    time_series.sort(key=lambda x: x["timestamp"])

    log.info(
        "time_series.processed",
        value_column=value_column,
        data_points=len(time_series),
        valid_values=sum(1 for p in time_series if p["has_data"]),
    )

    return time_series


def calculate_chart_statistics(time_series: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate summary statistics for chart data.

    Args:
        time_series: List of time-series data points

    Returns:
        Dictionary with statistical summary
    """
    if not time_series:
        return {
            "total_points": 0,
            "valid_points": 0,
            "missing_points": 0,
            "coverage_percentage": 0.0,
            "date_range": None,
        }

    valid_values = [p["value"] for p in time_series if p["has_data"]]

    stats = {
        "total_points": len(time_series),
        "valid_points": len(valid_values),
        "missing_points": len(time_series) - len(valid_values),
        "coverage_percentage": (len(valid_values) / len(time_series)) * 100,
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


def format_production_chart_data(
    eod_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> dict[str, Any]:
    """Format production data for chart visualization.

    Args:
        eod_df: EOD DataFrame with production data
        date_column: Name of date column

    Returns:
        Chart-ready production data
    """
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
            # Clean currency formatting before numeric conversion
            df_copy[column] = df_copy[column].apply(clean_currency_string)
            df_copy[column] = pd.to_numeric(df_copy[column], errors="coerce").fillna(
                0.0
            )

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
            "line_color": "#007E9E",  # Teal brand color
        },
    }


def format_collection_rate_chart_data(
    eod_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> dict[str, Any]:
    """Format collection rate data for chart visualization.

    Args:
        eod_df: EOD DataFrame with production and collection data
        date_column: Name of date column

    Returns:
        Chart-ready collection rate data
    """
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
        # Clean currency formatting before conversion
        rate_df[production_column] = rate_df[production_column].apply(
            clean_currency_string
        )
        rate_df[production_column] = pd.to_numeric(
            rate_df[production_column], errors="coerce"
        )
        total_collections = 0.0
        for column in income_columns:
            # Clean currency formatting before conversion
            rate_df[column] = rate_df[column].apply(clean_currency_string)
            rate_df[column] = pd.to_numeric(rate_df[column], errors="coerce").fillna(
                0.0
            )
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
            production = safe_float_conversion(row[fallback_production])
            collections = safe_float_conversion(row[fallback_collections])

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
            "line_color": "#142D54",  # Navy brand color
            "target_range": {"min": 95.0, "max": 100.0},
        },
    }


def format_new_patients_chart_data(
    eod_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> dict[str, Any]:
    """Format new patients data for chart visualization.

    Args:
        eod_df: EOD DataFrame with new patient data
        date_column: Name of date column

    Returns:
        Chart-ready new patients data
    """
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
        # Clean currency formatting before conversion
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
            "bar_color": "#007E9E",  # Teal brand color
        },
    }


def format_treatment_acceptance_chart_data(
    front_kpi_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> dict[str, Any]:
    """Format treatment acceptance data for chart visualization.

    Args:
        front_kpi_df: Front KPI DataFrame with treatment data
        date_column: Name of date column

    Returns:
        Chart-ready treatment acceptance data
    """
    if front_kpi_df is None or front_kpi_df.empty:
        return _empty_chart_data("Treatment Acceptance")

    resolved_date_column = FRONT_MAPPING.get("date", date_column)

    presented_column = FRONT_MAPPING.get("treatments_presented", "treatments_presented")
    scheduled_column = FRONT_MAPPING.get("treatments_scheduled", "treatments_scheduled")
    same_day_column = FRONT_MAPPING.get("same_day_treatment", "$ Same Day Treatment")

    # Calculate treatment acceptance rate for each row
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

    # Create temporary DataFrame for processing
    rate_df = front_kpi_df.copy()
    rate_df["acceptance_rate"] = acceptance_rates

    time_series = process_time_series_data(
        rate_df, resolved_date_column, "acceptance_rate", "float"
    )

    return {
        "metric_name": "Treatment Acceptance",
        "chart_type": "line",
        "data_type": "percentage",
        "time_series": time_series,
        "statistics": calculate_chart_statistics(time_series),
        "format_options": {
            "percentage_symbol": "%",
            "decimal_places": 1,
            "show_grid": True,
            "line_color": "#142D54",  # Navy brand color
            "target_range": {"min": 80.0, "max": 100.0},
        },
    }


def format_hygiene_reappointment_chart_data(
    front_kpi_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> dict[str, Any]:
    """Format hygiene reappointment data for chart visualization.

    Args:
        front_kpi_df: Front KPI DataFrame with hygiene data
        date_column: Name of date column

    Returns:
        Chart-ready hygiene reappointment data
    """
    if front_kpi_df is None or front_kpi_df.empty:
        return _empty_chart_data("Hygiene Reappointment")

    resolved_date_column = FRONT_MAPPING.get("date", date_column)
    total_column = FRONT_MAPPING.get("hygiene_total", "Total hygiene Appointments")
    not_reappointed_column = FRONT_MAPPING.get(
        "hygiene_not_reappointed", "Number of patients NOT reappointed?"
    )

    # Calculate hygiene reappointment rate for each row
    reappointment_rates = []
    for _, row in front_kpi_df.iterrows():
        total = safe_int_conversion(row.get(total_column))
        not_reappointed = safe_int_conversion(row.get(not_reappointed_column))

        if total and total > 0 and not_reappointed is not None:
            reappointed = total - not_reappointed
            rate = (reappointed / total) * 100
        else:
            rate = None

        reappointment_rates.append(rate)

    # Create temporary DataFrame for processing
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
            "line_color": "#007E9E",  # Teal brand color
            "target_range": {"min": 85.0, "max": 100.0},
        },
    }


def format_all_chart_data(
    eod_df: pd.DataFrame | None,
    front_kpi_df: pd.DataFrame | None,
    date_column: str = "Submission Date",
) -> dict[str, dict[str, Any]]:
    """Format all KPI data for chart visualization.

    Args:
        eod_df: EOD DataFrame with production/collection/new patient data
        front_kpi_df: Front KPI DataFrame with treatment/hygiene data
        date_column: Name of date column

    Returns:
        Dictionary with all chart-ready data
    """
    log.info("chart_data.formatting_all_metrics")

    chart_data = {
        "production_total": format_production_chart_data(eod_df, date_column),
        "collection_rate": format_collection_rate_chart_data(eod_df, date_column),
        "new_patients": format_new_patients_chart_data(eod_df, date_column),
        "treatment_acceptance": format_treatment_acceptance_chart_data(
            front_kpi_df, date_column
        ),
        "hygiene_reappointment": format_hygiene_reappointment_chart_data(
            front_kpi_df, date_column
        ),
    }

    # Add metadata
    chart_data["metadata"] = {
        "generated_at": datetime.now().isoformat(),
        "data_sources": {
            "eod_available": eod_df is not None and not eod_df.empty,
            "front_kpi_available": front_kpi_df is not None and not front_kpi_df.empty,
        },
        "total_metrics": 5,  # Always 5 core metrics
    }

    log.info(
        "chart_data.formatting_complete",
        metrics_count=chart_data["metadata"]["total_metrics"],
        eod_available=chart_data["metadata"]["data_sources"]["eod_available"],
        front_kpi_available=chart_data["metadata"]["data_sources"][
            "front_kpi_available"
        ],
    )

    return chart_data


def _empty_chart_data(metric_name: str) -> dict[str, Any]:
    """Create empty chart data structure for missing data.

    Args:
        metric_name: Name of the metric

    Returns:
        Empty chart data structure
    """
    return {
        "metric_name": metric_name,
        "chart_type": "line",
        "data_type": "unknown",
        "time_series": [],
        "statistics": calculate_chart_statistics([]),
        "format_options": {},
        "error": "No data available",
    }


def validate_chart_data(chart_data: dict[str, Any]) -> bool:
    """Validate chart data structure integrity.

    Args:
        chart_data: Chart data to validate

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["metric_name", "chart_type", "data_type", "time_series"]

    try:
        for field in required_fields:
            if field not in chart_data:
                log.error("chart_data.validation_failed", missing_field=field)
                return False

        # Validate time series structure
        for point in chart_data["time_series"]:
            if not isinstance(point, dict) or "date" not in point:
                log.error("chart_data.invalid_time_series_point", point=point)
                return False

        log.debug("chart_data.validation_passed", metric=chart_data["metric_name"])
        return True

    except Exception as e:
        log.error("chart_data.validation_error", error=str(e))
        return False
