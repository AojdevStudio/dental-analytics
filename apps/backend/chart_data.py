"""Chart Data Processor for Frontend-Agnostic Data Formatting.

Processes time-series data from Google Sheets into JSON-serializable
formats optimized for chart visualization. Handles missing data points,
gaps in time series, and operational day logic.
"""

from collections.abc import Callable
from datetime import datetime
from typing import Any

import pandas as pd
import structlog
from pydantic import ValidationError

from core.models.chart_models import (
    AllChartsData,
    ChartDataPoint,
    ChartMetaInfo,
    ChartsMetadata,
    ChartStats,
    DataSourceInfo,
    ProcessedChartData,
    SummaryStatistics,
    TimeSeriesData,
)

from .metrics import clean_currency_string

try:
    from config.data_sources import COLUMN_MAPPINGS
except ImportError:  # pragma: no cover - configuration module should exist in runtime
    COLUMN_MAPPINGS = {}

# Configure structured logging to stderr
log = structlog.get_logger()

EOD_MAPPING = COLUMN_MAPPINGS.get("eod_billing", {})
FRONT_MAPPING = COLUMN_MAPPINGS.get("front_kpis", {})


def create_empty_processed_chart_data(
    error_message: str, date_column: str = ""
) -> ProcessedChartData:
    """Create empty ProcessedChartData with error message.

    Helper function to reduce code duplication in error handling.
    """
    return ProcessedChartData(
        dates=[],
        values=[],
        statistics=ChartStats(
            total=0.0,
            average=0.0,
            minimum=0.0,
            maximum=0.0,
            data_points=0,
        ),
        metadata=ChartMetaInfo(
            date_column=date_column,
            date_range="No data",
            error=error_message,
            aggregation=None,
            business_days_only=None,
            date_filter=None,
            filtered_data_points=None,
        ),
        error=error_message,
    )


def safe_float_conversion(value: Any) -> float | None:
    """Safely convert value to float with None fallback."""

    if value is None or pd.isna(value):
        return None

    try:
        cleaned = clean_currency_string(value)
        if cleaned == "":
            return 0.0
        # Cast cleaned string to ensure type safety for float conversion
        return float(str(cleaned))
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
            # Cast cleaned string to ensure type safety for float conversion
            return int(float(str(cleaned)))
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
) -> ChartDataPoint | None:
    """Create standardized time-series data point using Pydantic model."""

    if date is None:
        return None

    return ChartDataPoint(
        date=date.strftime("%Y-%m-%d"),
        timestamp=date.isoformat(),
        value=value,
        has_data=value is not None,
    )


def process_time_series_data(
    df: pd.DataFrame | None,
    date_column: str,
    value_column: str,
    data_type: str = "float",
) -> list[ChartDataPoint]:
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

    time_series: list[ChartDataPoint] = []
    conversion_func = (
        safe_int_conversion if data_type == "int" else safe_float_conversion
    )

    for _, row in df.iterrows():
        date = parse_datetime_string(row[date_column])
        value = conversion_func(row[value_column])

        if date is not None:
            point = create_time_series_point(date, value)
            if point:
                time_series.append(point)

    time_series.sort(key=lambda entry: entry.timestamp)

    log.info(
        "time_series.processed",
        value_column=value_column,
        data_points=len(time_series),
        valid_values=sum(1 for point in time_series if point.has_data),
    )

    return time_series


def validate_chart_data(chart_data: TimeSeriesData) -> bool:
    """Validate chart data structure integrity for Pydantic instances."""

    try:
        chart_data.model_validate(chart_data.model_dump())
    except ValidationError as error:
        log.error("chart_data.validation_error", errors=error.errors())
        return False
    except AttributeError:
        log.error(
            "chart_data.validation_error",
            error="Expected TimeSeriesData instance",
            received_type=type(chart_data).__name__,
        )
        return False

    log.debug("chart_data.validation_passed", metric=chart_data.metric_name)
    return True


def process_production_data_for_chart(df: pd.DataFrame) -> ProcessedChartData:
    """Process production data for chart display.

    Args:
        df: DataFrame with production data

    Returns:
        Pydantic model with chart-ready data structure
    """
    try:
        log.info("chart_data.processing_started", columns=list(df.columns))

        # Get column names from mapping or fallback to direct names
        date_col = str(COLUMN_MAPPINGS.get("submission_date", "Submission Date"))
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
                return create_empty_processed_chart_data("No date column found")

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
                return create_empty_processed_chart_data("No production column found")

        # Clean and prepare data
        chart_df = df[[date_col, production_col]].copy()
        chart_df = chart_df.dropna()

        if chart_df.empty:
            log.warning("chart_data.empty_after_cleanup")
            return create_empty_processed_chart_data(
                "No valid data after cleanup", date_col
            )

        # Convert dates to datetime and production to numeric
        chart_df[date_col] = pd.to_datetime(chart_df[date_col], errors="coerce")
        chart_df[production_col] = pd.to_numeric(
            chart_df[production_col].apply(clean_currency_string), errors="coerce"
        )

        # Remove any rows where conversion failed
        chart_df = chart_df.dropna()

        if chart_df.empty:
            log.warning("chart_data.empty_after_conversion")
            return create_empty_processed_chart_data(
                "No valid data after conversion", date_col
            )

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

        result = ProcessedChartData(
            dates=dates,
            values=values,
            statistics=ChartStats(
                total=round(total_production, 2),
                average=round(avg_production, 2),
                minimum=round(min_production, 2),
                maximum=round(max_production, 2),
                data_points=len(values),
            ),
            metadata=ChartMetaInfo(
                date_column=date_col,
                date_range=f"{dates[0]} to {dates[-1]}" if dates else "No data",
                error=None,
                aggregation=None,
                business_days_only=None,
                date_filter=None,
                filtered_data_points=None,
            ),
            error=None,
        )

        log.info(
            "chart_data.processing_completed",
            data_points=len(values),
            date_range=result.metadata.date_range,
            total_production=total_production,
        )

        return result

    except Exception as e:
        log.error("chart_data.processing_error", error=str(e))
        return create_empty_processed_chart_data(f"Processing failed: {str(e)}")


def process_collection_rate_data_for_chart(df: pd.DataFrame) -> ProcessedChartData:
    """Process collection rate data for chart display using Pydantic models."""

    try:
        log.info(
            "chart_data.collection_rate_processing_started", columns=list(df.columns)
        )

        date_col = str(COLUMN_MAPPINGS.get("submission_date", "Submission Date"))
        production_col = COLUMN_MAPPINGS.get(
            "total_production", "Total Production Today"
        )
        collections_col = COLUMN_MAPPINGS.get("patient_income", "Patient Income Today")
        insurance_col = COLUMN_MAPPINGS.get(
            "insurance_income", "Insurance Income Today"
        )

        missing_cols: list[str] = []
        for col_name, fallback_key in [
            (date_col, "date"),
            (production_col, "production"),
            (collections_col, "collections"),
        ]:
            if col_name not in df.columns:
                missing_cols.append(fallback_key)

        if missing_cols:
            message = f"Missing columns: {missing_cols}"
            log.error("chart_data.missing_columns", missing=missing_cols)
            return create_empty_processed_chart_data(message, date_col)

        chart_df = df[[date_col, production_col, collections_col]].copy()

        if insurance_col in df.columns:
            chart_df[insurance_col] = pd.to_numeric(
                df[insurance_col].apply(clean_currency_string), errors="coerce"
            ).fillna(0)
        else:
            chart_df[insurance_col] = 0

        chart_df = chart_df.dropna(subset=[date_col, production_col, collections_col])

        if chart_df.empty:
            return create_empty_processed_chart_data(
                "No valid data after cleanup", date_col
            )

        chart_df[date_col] = pd.to_datetime(chart_df[date_col], errors="coerce")
        chart_df[production_col] = pd.to_numeric(
            chart_df[production_col].apply(clean_currency_string), errors="coerce"
        )
        chart_df[collections_col] = pd.to_numeric(
            chart_df[collections_col].apply(clean_currency_string), errors="coerce"
        )

        chart_df = chart_df.dropna()

        if chart_df.empty:
            return create_empty_processed_chart_data(
                "No valid data after conversion", date_col
            )

        chart_df["total_collections"] = (
            chart_df[collections_col] + chart_df[insurance_col]
        )
        chart_df["collection_rate"] = (
            (chart_df["total_collections"] / chart_df[production_col] * 100)
            .fillna(0)
            .replace([float("inf"), -float("inf")], 0)
        )

        chart_df = chart_df.sort_values(date_col)

        dates = chart_df[date_col].dt.strftime("%Y-%m-%d").tolist()
        values = chart_df["collection_rate"].round(2).tolist()

        avg_rate = sum(values) / len(values) if values else 0.0
        min_rate = min(values) if values else 0.0
        max_rate = max(values) if values else 0.0

        result = ProcessedChartData(
            dates=dates,
            values=values,
            statistics=ChartStats(
                total=0.0,
                average=round(avg_rate, 2),
                minimum=round(min_rate, 2),
                maximum=round(max_rate, 2),
                data_points=len(values),
            ),
            metadata=ChartMetaInfo(
                date_column=date_col,
                date_range=f"{dates[0]} to {dates[-1]}" if dates else "No data",
                error=None,
                aggregation=None,
                business_days_only=None,
                date_filter=None,
                filtered_data_points=None,
            ),
            error=None,
        )

        log.info(
            "chart_data.collection_rate_completed",
            data_points=len(values),
            avg_rate=avg_rate,
        )

        return result

    except Exception as error:
        log.error("chart_data.collection_rate_error", error=str(error))
        return create_empty_processed_chart_data(
            f"Collection rate processing failed: {error}", date_col
        )


def process_new_patients_data_for_chart(df: pd.DataFrame) -> ProcessedChartData:
    """Process new patient counts into the standardized chart response."""

    try:
        log.info("chart_data.new_patients_processing_started", columns=list(df.columns))

        date_col = str(COLUMN_MAPPINGS.get("submission_date", "Submission Date"))
        new_patients_col = COLUMN_MAPPINGS.get(
            "new_patients", "New Patients - Total Month to Date"
        )

        missing_columns: list[str] = []
        if date_col not in df.columns:
            missing_columns.append("date")
        if new_patients_col not in df.columns:
            missing_columns.append("new_patients")

        if missing_columns:
            message = f"Missing columns: {missing_columns}"
            log.error("chart_data.missing_columns", missing=missing_columns)
            return create_empty_processed_chart_data(message, date_col)

        chart_df = df[[date_col, new_patients_col]].copy()
        chart_df = chart_df.dropna()

        if chart_df.empty:
            return create_empty_processed_chart_data("No valid data", date_col)

        chart_df[date_col] = pd.to_datetime(chart_df[date_col], errors="coerce")
        chart_df[new_patients_col] = pd.to_numeric(
            chart_df[new_patients_col], errors="coerce"
        )

        chart_df = chart_df.dropna()

        if chart_df.empty:
            return create_empty_processed_chart_data(
                "No valid data after conversion", date_col
            )

        chart_df = chart_df.sort_values(date_col)

        dates = chart_df[date_col].dt.strftime("%Y-%m-%d").tolist()
        values = chart_df[new_patients_col].astype(float).tolist()

        total_new = sum(values)
        avg_new = sum(values) / len(values) if values else 0.0
        min_new = min(values) if values else 0.0
        max_new = max(values) if values else 0.0

        result = ProcessedChartData(
            dates=dates,
            values=values,
            statistics=ChartStats(
                total=round(float(total_new), 2),
                average=round(avg_new, 1),
                minimum=round(float(min_new), 2),
                maximum=round(float(max_new), 2),
                data_points=len(values),
            ),
            metadata=ChartMetaInfo(
                date_column=date_col,
                date_range=f"{dates[0]} to {dates[-1]}" if dates else "No data",
                error=None,
                aggregation=None,
                business_days_only=None,
                date_filter=None,
                filtered_data_points=None,
            ),
            error=None,
        )

        log.info(
            "chart_data.new_patients_completed",
            data_points=len(values),
            total=total_new,
        )

        return result

    except Exception as error:
        log.error("chart_data.new_patients_error", error=str(error))
        return create_empty_processed_chart_data(
            f"New patients processing failed: {error}", date_col
        )


def process_case_acceptance_data_for_chart(df: pd.DataFrame) -> ProcessedChartData:
    """Transform case acceptance data into a validated chart response."""

    try:
        log.info(
            "chart_data.case_acceptance_processing_started", columns=list(df.columns)
        )

        date_col = str(COLUMN_MAPPINGS.get("timestamp", "Timestamp"))
        presented_col = COLUMN_MAPPINGS.get(
            "treatments_presented", "Treatments Presented"
        )
        scheduled_col = COLUMN_MAPPINGS.get(
            "treatments_scheduled", "Treatments Scheduled"
        )
        same_day_col = COLUMN_MAPPINGS.get("same_day_starts", "Same Day Starts")

        missing_columns: list[str] = []
        for column_name, key in [
            (date_col, "date"),
            (presented_col, "presented"),
            (scheduled_col, "scheduled"),
        ]:
            if column_name not in df.columns:
                missing_columns.append(key)

        if missing_columns:
            message = f"Missing columns: {missing_columns}"
            log.error("chart_data.missing_columns", missing=missing_columns)
            return create_empty_processed_chart_data(message, date_col)

        chart_df = df[[date_col, presented_col, scheduled_col]].copy()

        if same_day_col in df.columns:
            chart_df[same_day_col] = pd.to_numeric(
                df[same_day_col], errors="coerce"
            ).fillna(0)
        else:
            chart_df[same_day_col] = 0

        chart_df = chart_df.dropna(subset=[date_col, presented_col, scheduled_col])

        if chart_df.empty:
            return create_empty_processed_chart_data("No valid data", date_col)

        chart_df[date_col] = pd.to_datetime(chart_df[date_col], errors="coerce")
        chart_df[presented_col] = pd.to_numeric(
            chart_df[presented_col], errors="coerce"
        )
        chart_df[scheduled_col] = pd.to_numeric(
            chart_df[scheduled_col], errors="coerce"
        )

        chart_df = chart_df.dropna()

        if chart_df.empty:
            return create_empty_processed_chart_data(
                "No valid data after conversion", date_col
            )

        chart_df["total_accepted"] = chart_df[scheduled_col] + chart_df[same_day_col]
        chart_df["acceptance_rate"] = (
            (chart_df["total_accepted"] / chart_df[presented_col] * 100)
            .fillna(0)
            .replace([float("inf"), -float("inf")], 0)
        )

        chart_df = chart_df.sort_values(date_col)

        dates = chart_df[date_col].dt.strftime("%Y-%m-%d").tolist()
        values = chart_df["acceptance_rate"].round(2).tolist()

        avg_rate = sum(values) / len(values) if values else 0.0
        min_rate = min(values) if values else 0.0
        max_rate = max(values) if values else 0.0

        result = ProcessedChartData(
            dates=dates,
            values=values,
            statistics=ChartStats(
                total=0.0,
                average=round(avg_rate, 2),
                minimum=round(min_rate, 2),
                maximum=round(max_rate, 2),
                data_points=len(values),
            ),
            metadata=ChartMetaInfo(
                date_column=date_col,
                date_range=f"{dates[0]} to {dates[-1]}" if dates else "No data",
                error=None,
                aggregation=None,
                business_days_only=None,
                date_filter=None,
                filtered_data_points=None,
            ),
            error=None,
        )

        log.info(
            "chart_data.case_acceptance_completed",
            data_points=len(values),
            avg_rate=avg_rate,
        )

        return result

    except Exception as error:
        log.error("chart_data.case_acceptance_error", error=str(error))
        return create_empty_processed_chart_data(
            f"Case acceptance processing failed: {error}", date_col
        )


def process_hygiene_reappointment_data_for_chart(
    df: pd.DataFrame,
) -> ProcessedChartData:
    """Process hygiene reappointment data into a validated chart payload."""

    try:
        log.info("chart_data.hygiene_processing_started", columns=list(df.columns))

        date_col = str(COLUMN_MAPPINGS.get("timestamp", "Timestamp"))
        total_hygiene_col = COLUMN_MAPPINGS.get(
            "total_hygiene_appointments", "Total Hygiene Appointments"
        )
        not_reappointed_col = COLUMN_MAPPINGS.get(
            "patients_not_reappointed", "Patients Not Reappointed"
        )

        missing_columns: list[str] = []
        for column_name, key in [
            (date_col, "date"),
            (total_hygiene_col, "total_hygiene"),
            (not_reappointed_col, "not_reappointed"),
        ]:
            if column_name not in df.columns:
                missing_columns.append(key)

        if missing_columns:
            message = f"Missing columns: {missing_columns}"
            log.error("chart_data.missing_columns", missing=missing_columns)
            return create_empty_processed_chart_data(message, date_col)

        chart_df = df[[date_col, total_hygiene_col, not_reappointed_col]].copy()
        chart_df = chart_df.dropna(subset=[date_col, total_hygiene_col])

        if chart_df.empty:
            return create_empty_processed_chart_data("No valid data", date_col)

        chart_df[date_col] = pd.to_datetime(chart_df[date_col], errors="coerce")
        chart_df[total_hygiene_col] = pd.to_numeric(
            chart_df[total_hygiene_col], errors="coerce"
        )
        chart_df[not_reappointed_col] = pd.to_numeric(
            chart_df[not_reappointed_col], errors="coerce"
        ).fillna(0)

        chart_df = chart_df.dropna()

        if chart_df.empty:
            return create_empty_processed_chart_data(
                "No valid data after conversion", date_col
            )

        chart_df["reappointed"] = (
            chart_df[total_hygiene_col] - chart_df[not_reappointed_col]
        )
        chart_df["reappointment_rate"] = (
            (chart_df["reappointed"] / chart_df[total_hygiene_col] * 100)
            .fillna(0)
            .replace([float("inf"), -float("inf")], 0)
        )

        chart_df = chart_df.sort_values(date_col)

        dates = chart_df[date_col].dt.strftime("%Y-%m-%d").tolist()
        values = chart_df["reappointment_rate"].round(2).tolist()

        avg_rate = sum(values) / len(values) if values else 0.0
        min_rate = min(values) if values else 0.0
        max_rate = max(values) if values else 0.0

        result = ProcessedChartData(
            dates=dates,
            values=values,
            statistics=ChartStats(
                total=0.0,
                average=round(avg_rate, 2),
                minimum=round(min_rate, 2),
                maximum=round(max_rate, 2),
                data_points=len(values),
            ),
            metadata=ChartMetaInfo(
                date_column=date_col,
                date_range=f"{dates[0]} to {dates[-1]}" if dates else "No data",
                error=None,
                aggregation=None,
                business_days_only=None,
                date_filter=None,
                filtered_data_points=None,
            ),
            error=None,
        )

        log.info(
            "chart_data.hygiene_completed", data_points=len(values), avg_rate=avg_rate
        )

        return result

    except Exception as error:
        log.error("chart_data.hygiene_error", error=str(error))
        return create_empty_processed_chart_data(
            f"Hygiene reappointment processing failed: {error}", date_col
        )


def calculate_basic_statistics(time_series: list[ChartDataPoint]) -> ChartStats:
    """Calculate statistics for time series data.

    Args:
        time_series: List of chart data points containing values.

    Returns:
        ChartStats Pydantic model summarizing the series.
    """

    if not time_series:
        return ChartStats()

    valid_values = [
        point.value
        for point in time_series
        if point.has_data and point.value is not None
    ]

    if not valid_values:
        return ChartStats()

    float_values = [float(value) for value in valid_values]

    return ChartStats(
        average=round(sum(float_values) / len(float_values), 2),
        minimum=round(min(float_values), 2),
        maximum=round(max(float_values), 2),
        total=round(sum(float_values), 2),
        data_points=len(float_values),
    )


def get_chart_data_processor(
    kpi_type: str,
) -> Callable[[pd.DataFrame], ProcessedChartData]:
    """Get the appropriate chart data processor function for a KPI type.

    Args:
        kpi_type: Type of KPI ('production', 'collection_rate', 'new_patients',
                  'case_acceptance', 'hygiene_reappointment')

    Returns:
        Function to process data for the specified KPI type
    """
    processors: dict[str, Callable[[pd.DataFrame], ProcessedChartData]] = {
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


def create_empty_chart_data(
    error_message: str = "No data available", *, date_column: str = ""
) -> ProcessedChartData:
    """Create empty chart data structure with error message."""

    return create_empty_processed_chart_data(error_message, date_column)


def validate_processed_chart_data(data: ProcessedChartData) -> bool:
    """Validate processed chart data structure via Pydantic enforcement."""

    try:
        data.model_validate(data.model_dump())
    except ValidationError as error:
        log.error("chart_data.validation_error", errors=error.errors())
        return False
    except AttributeError:
        log.error(
            "chart_data.validation_error",
            error="Expected ProcessedChartData instance",
            received_type=type(data).__name__,
        )
        return False

    log.debug("chart_data.validation_passed", metric_dates=len(data.dates))
    return True


def aggregate_to_weekly(
    data: ProcessedChartData, business_days_only: bool = True
) -> ProcessedChartData:
    """Aggregate daily data into weekly summaries using Pydantic models."""

    try:
        if not data.dates or not data.values:
            return data

        df = pd.DataFrame(
            {"date": pd.to_datetime(data.dates), "value": pd.to_numeric(data.values)}
        )

        if business_days_only:
            df = df[df["date"].dt.dayofweek < 6]

        if df.empty:
            return create_empty_processed_chart_data(
                "No business days data available", data.metadata.date_column
            )

        weekly = (
            df.groupby(df["date"].dt.to_period("W"))
            .agg({"date": "last", "value": "sum"})
            .reset_index(drop=True)
        )

        if weekly.empty:
            return create_empty_processed_chart_data(
                "No weekly data available", data.metadata.date_column
            )

        weekly_values = weekly["value"].astype(float).tolist()
        weekly_dates = weekly["date"].dt.strftime("%Y-%m-%d").tolist()

        total = float(sum(weekly_values))
        average = total / len(weekly_values) if weekly_values else 0.0
        minimum = min(weekly_values) if weekly_values else 0.0
        maximum = max(weekly_values) if weekly_values else 0.0

        metadata = ChartMetaInfo(
            date_column=data.metadata.date_column,
            date_range=(
                f"{weekly_dates[0]} to {weekly_dates[-1]}"
                if weekly_dates
                else "No data"
            ),
            error=None,
            aggregation="weekly",
            business_days_only=business_days_only,
            date_filter=data.metadata.date_filter,
            filtered_data_points=len(weekly_values),
        )

        rounded_values = [round(float(value), 2) for value in weekly_values]

        return ProcessedChartData(
            dates=weekly_dates,
            values=rounded_values,
            statistics=ChartStats(
                total=round(total, 2),
                average=round(average, 2),
                minimum=round(minimum, 2),
                maximum=round(maximum, 2),
                data_points=len(rounded_values),
            ),
            metadata=metadata,
            error=None,
        )

    except Exception as error:
        log.error("chart_data.weekly_aggregation_error", error=str(error))
        return create_empty_processed_chart_data(
            f"Weekly aggregation failed: {error}", data.metadata.date_column
        )


def aggregate_to_monthly(
    data: ProcessedChartData, business_days_only: bool = True
) -> ProcessedChartData:
    """Aggregate daily data into monthly summaries using Pydantic models."""

    try:
        if not data.dates or not data.values:
            return data

        df = pd.DataFrame(
            {"date": pd.to_datetime(data.dates), "value": pd.to_numeric(data.values)}
        )

        if business_days_only:
            df = df[df["date"].dt.dayofweek < 6]

        if df.empty:
            return create_empty_processed_chart_data(
                "No business days data available", data.metadata.date_column
            )

        monthly = (
            df.groupby(df["date"].dt.to_period("M"))
            .agg({"date": "last", "value": "sum"})
            .reset_index(drop=True)
        )

        if monthly.empty:
            return create_empty_processed_chart_data(
                "No monthly data available", data.metadata.date_column
            )

        monthly_values = monthly["value"].astype(float).tolist()
        monthly_dates = monthly["date"].dt.strftime("%Y-%m-%d").tolist()

        total = float(sum(monthly_values))
        average = total / len(monthly_values) if monthly_values else 0.0
        minimum = min(monthly_values) if monthly_values else 0.0
        maximum = max(monthly_values) if monthly_values else 0.0

        metadata = ChartMetaInfo(
            date_column=data.metadata.date_column,
            date_range=(
                f"{monthly_dates[0]} to {monthly_dates[-1]}"
                if monthly_dates
                else "No data"
            ),
            error=None,
            aggregation="monthly",
            business_days_only=business_days_only,
            date_filter=data.metadata.date_filter,
            filtered_data_points=len(monthly_values),
        )

        rounded_values = [round(float(value), 2) for value in monthly_values]

        return ProcessedChartData(
            dates=monthly_dates,
            values=rounded_values,
            statistics=ChartStats(
                total=round(total, 2),
                average=round(average, 2),
                minimum=round(minimum, 2),
                maximum=round(maximum, 2),
                data_points=len(rounded_values),
            ),
            metadata=metadata,
            error=None,
        )

    except Exception as error:
        log.error("chart_data.monthly_aggregation_error", error=str(error))
        return create_empty_processed_chart_data(
            f"Monthly aggregation failed: {error}", data.metadata.date_column
        )


def filter_data_by_date_range(
    data: ProcessedChartData, start_date: str, end_date: str
) -> ProcessedChartData:
    """Filter chart data by date range using Pydantic outputs."""

    try:
        if not data.dates or not data.values:
            return data

        df = pd.DataFrame(
            {"date": pd.to_datetime(data.dates), "value": pd.to_numeric(data.values)}
        )

        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        mask = (df["date"] >= start_dt) & (df["date"] <= end_dt)
        filtered_df = df.loc[mask]

        if filtered_df.empty:
            return create_empty_processed_chart_data(
                f"No data in range {start_date} to {end_date}",
                data.metadata.date_column,
            )

        filtered_values = filtered_df["value"].astype(float).tolist()
        filtered_dates = filtered_df["date"].dt.strftime("%Y-%m-%d").tolist()

        total = float(sum(filtered_values))
        average = total / len(filtered_values) if filtered_values else 0.0
        minimum = min(filtered_values) if filtered_values else 0.0
        maximum = max(filtered_values) if filtered_values else 0.0

        metadata = ChartMetaInfo(
            date_column=data.metadata.date_column,
            date_range=(
                f"{filtered_dates[0]} to {filtered_dates[-1]}"
                if filtered_dates
                else "No data"
            ),
            error=None,
            aggregation=data.metadata.aggregation,
            business_days_only=data.metadata.business_days_only,
            date_filter=f"{start_date} to {end_date}",
            filtered_data_points=len(filtered_values),
        )

        rounded_values = [round(value, 2) for value in filtered_values]

        return ProcessedChartData(
            dates=filtered_dates,
            values=rounded_values,
            statistics=ChartStats(
                total=round(total, 2),
                average=round(average, 2),
                minimum=round(minimum, 2),
                maximum=round(maximum, 2),
                data_points=len(rounded_values),
            ),
            metadata=metadata,
            error=None,
        )

    except Exception as error:
        log.error("chart_data.date_filter_error", error=str(error))
        return create_empty_processed_chart_data(
            f"Date filtering failed: {error}", data.metadata.date_column
        )


def calculate_chart_statistics(time_series: list[ChartDataPoint]) -> SummaryStatistics:
    """Calculate summary statistics for chart data."""

    if not time_series:
        empty_stats = SummaryStatistics()
        log.debug("chart_statistics.calculated", **empty_stats.model_dump())
        return empty_stats

    valid_values = [
        point.value
        for point in time_series
        if point.has_data and point.value is not None
    ]

    total_points = len(time_series)
    valid_points = len(valid_values)
    missing_points = total_points - valid_points
    coverage_percentage = (
        (valid_points / total_points) * 100 if total_points else 0.0
    )

    stats = SummaryStatistics(
        total_points=total_points,
        valid_points=valid_points,
        missing_points=missing_points,
        coverage_percentage=round(coverage_percentage, 2),
        date_range={
            "start": time_series[0].date,
            "end": time_series[-1].date,
        },
    )

    if valid_values:
        float_values = [float(value) for value in valid_values]
        stats.min_value = min(float_values)
        stats.max_value = max(float_values)
        stats.average_value = sum(float_values) / len(float_values)

    log.debug("chart_statistics.calculated", **stats.model_dump())
    return stats


def _empty_chart_data(metric_name: str) -> TimeSeriesData:
    """Create empty chart data structure for missing data."""

    return TimeSeriesData(
        metric_name=metric_name,
        chart_type="line",
        data_type="float",
        time_series=[],
        statistics=calculate_chart_statistics([]),
        format_options={},
        error="No data available",
    )


def format_production_chart_data(
    eod_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> TimeSeriesData:
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

    return TimeSeriesData(
        metric_name="Production Total",
        chart_type="line",
        data_type="currency",
        time_series=time_series,
        statistics=calculate_chart_statistics(time_series),
        format_options={
            "currency_symbol": "$",
            "decimal_places": 0,
            "show_grid": True,
            "line_color": "#007E9E",
        },
        error=None,
    )


def format_collection_rate_chart_data(
    eod_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> TimeSeriesData:
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

    return TimeSeriesData(
        metric_name="Collection Rate",
        chart_type="line",
        data_type="percentage",
        time_series=time_series,
        statistics=calculate_chart_statistics(time_series),
        format_options={
            "percentage_symbol": "%",
            "decimal_places": 1,
            "show_grid": True,
            "line_color": "#142D54",
            "target_range": {"min": 95.0, "max": 100.0},
        },
        error=None,
    )


def format_new_patients_chart_data(
    eod_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> TimeSeriesData:
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

    return TimeSeriesData(
        metric_name="New Patients",
        chart_type="bar",
        data_type="count",
        time_series=time_series,
        statistics=calculate_chart_statistics(time_series),
        format_options={
            "decimal_places": 0,
            "show_grid": True,
            "bar_color": "#007E9E",
        },
        error=None,
    )


def format_case_acceptance_chart_data(
    front_kpi_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> TimeSeriesData:
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

    return TimeSeriesData(
        metric_name="Case Acceptance",
        chart_type="line",
        data_type="percentage",
        time_series=time_series,
        statistics=calculate_chart_statistics(time_series),
        format_options={
            "percentage_symbol": "%",
            "decimal_places": 1,
            "show_grid": True,
            "line_color": "#142D54",
            "target_range": {"min": 80.0, "max": 100.0},
        },
        error=None,
    )


def format_hygiene_reappointment_chart_data(
    front_kpi_df: pd.DataFrame | None, date_column: str = "Submission Date"
) -> TimeSeriesData:
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

    return TimeSeriesData(
        metric_name="Hygiene Reappointment",
        chart_type="line",
        data_type="percentage",
        time_series=time_series,
        statistics=calculate_chart_statistics(time_series),
        format_options={
            "percentage_symbol": "%",
            "decimal_places": 1,
            "show_grid": True,
            "line_color": "#007E9E",
            "target_range": {"min": 85.0, "max": 100.0},
        },
        error=None,
    )


def format_all_chart_data(
    eod_df: pd.DataFrame | None,
    front_kpi_df: pd.DataFrame | None,
    date_column: str = "Submission Date",
) -> AllChartsData:
    """Format all KPI data for chart visualization."""

    log.info("chart_data.formatting_all_metrics")

    chart_data = AllChartsData(
        production_total=format_production_chart_data(eod_df, date_column),
        collection_rate=format_collection_rate_chart_data(eod_df, date_column),
        new_patients=format_new_patients_chart_data(eod_df, date_column),
        case_acceptance=format_case_acceptance_chart_data(front_kpi_df, date_column),
        hygiene_reappointment=format_hygiene_reappointment_chart_data(
            front_kpi_df, date_column
        ),
        metadata=ChartsMetadata(
            generated_at=datetime.now().isoformat(),
            data_sources=DataSourceInfo(
                eod_available=eod_df is not None and not eod_df.empty,
                front_kpi_available=front_kpi_df is not None and not front_kpi_df.empty,
            ),
            total_metrics=5,
        ),
    )

    log.info(
        "chart_data.formatting_complete",
        metrics_count=chart_data.metadata.total_metrics,
        eod_available=chart_data.metadata.data_sources.eod_available,
        front_kpi_available=chart_data.metadata.data_sources.front_kpi_available,
    )

    return chart_data
