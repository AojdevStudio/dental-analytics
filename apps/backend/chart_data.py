"""Chart Data Processor for Frontend-Agnostic Data Formatting.

Processes time-series data from Google Sheets into JSON-serializable
formats optimized for chart visualization. Handles missing data points,
gaps in time series, and operational day logic.
"""

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


def validate_chart_data(data: dict[str, Any]) -> bool:
    """Validate that chart data has the required structure.

    Args:
        data: Dictionary with keys 'dates', 'values', and optional metadata

    Returns:
        bool: True if data is valid for chart rendering
    """
    if not isinstance(data, dict):
        return False

    required_keys = {"dates", "values"}
    if not required_keys.issubset(data.keys()):
        return False

    dates = data["dates"]
    values = data["values"]

    if not isinstance(dates, list) or not isinstance(values, list):
        return False

    return len(dates) == len(values)


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


def calculate_chart_statistics(time_series: list[dict[str, Any]]) -> dict[str, float]:
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

            statistics = calculate_chart_statistics(time_series)
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

            statistics = calculate_chart_statistics(time_series)
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

        statistics = calculate_chart_statistics(time_series)

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
