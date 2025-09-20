"""
Historical Data Manager for Dental Analytics

Provides access to historical KPI data with caching, date range filtering,
and automatic fallback to latest operational data. Supports both EOD billing
and Front KPI data sources with robust error handling and data validation.

Key Features:
- Automatic weekend/holiday fallback to latest operational day
- Date range filtering for historical analysis
- Caching with configurable TTL for performance
- Comprehensive logging and error handling
- Data validation and type safety
"""

import logging
import sys
from datetime import datetime, timedelta

import pandas as pd
import structlog

from .data_providers import build_sheets_provider

# Configure structured logging
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


class HistoricalDataManager:
    """Manages historical dental practice data with caching and date filtering."""

    def __init__(self) -> None:
        """Initialize the historical data manager."""
        self.provider = build_sheets_provider()
        log.info("historical_data.manager_initialized")

    def get_latest_operational_date(self) -> datetime:
        """
        Get the latest operational date (Monday-Saturday).
        Automatically falls back from Sunday to Saturday.

        Returns:
            Latest operational date as datetime object
        """
        today = datetime.now()

        # If today is Sunday (6), fall back to Saturday
        if today.weekday() == 6:  # Sunday
            latest_date = today - timedelta(days=1)
            log.info(
                "historical_data.sunday_fallback",
                original_date=today.date().isoformat(),
                fallback_date=latest_date.date().isoformat(),
            )
        else:
            latest_date = today

        return latest_date

    def _filter_to_specific_date(
        self, df: pd.DataFrame, date_column: str, target_date: datetime
    ) -> pd.DataFrame | None:
        """Filter DataFrame to records from a specific date.

        Args:
            df: Source DataFrame with date column
            date_column: Name of the date column to filter on
            target_date: Date to filter for

        Returns:
            Filtered DataFrame or None if no matching records
        """
        try:
            if date_column not in df.columns:
                log.warning(
                    "historical_data.missing_date_column",
                    column=date_column,
                    available=list(df.columns),
                )
                return None

            # Convert date column to datetime, coercing errors
            df_copy = df.copy()
            df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors="coerce")

            # Filter to target date (comparing just the date part)
            target_date_only = target_date.date()
            mask = df_copy[date_column].dt.date == target_date_only
            filtered_df = df_copy[mask]

            if filtered_df.empty:
                log.warning(
                    "historical_data.no_data_for_date",
                    target_date=target_date_only.isoformat(),
                    available_dates=[
                        d.isoformat() if pd.notna(d) else None
                        for d in df_copy[date_column].dt.date.unique()
                    ],
                )
                return None

            log.info(
                "historical_data.filtered_to_date",
                target_date=target_date_only.isoformat(),
                rows=len(filtered_df),
            )
            return filtered_df

        except Exception as e:
            log.error(
                "historical_data.filter_to_date_failed",
                target_date=target_date.isoformat(),
                error=str(e),
            )
            return None

    def get_recent_eod_data(self, days: int = 30) -> pd.DataFrame | None:
        """
        Get EOD billing data for the last N days.

        Args:
            days: Number of days to retrieve (default: 30)

        Returns:
            DataFrame with EOD data or None if retrieval fails
        """
        log.info("historical_data.eod_data_start", days=days)

        try:
            # Get full EOD dataset
            # Using default location 'baytown' for backward compatibility
            eod_alias = self.provider.get_location_aliases("baytown", "eod")
            eod_df = self.provider.fetch(eod_alias) if eod_alias else None
            if eod_df is None or eod_df.empty:
                log.warning("historical_data.eod_data_empty")
                return None

            # Filter to date range if date column exists
            if "Submission Date" in eod_df.columns:
                filtered_data = self._filter_by_date_range(
                    eod_df, "Submission Date", days
                )
                log.info(
                    "historical_data.eod_data_success",
                    total_rows=len(eod_df),
                    filtered_rows=(
                        len(filtered_data) if filtered_data is not None else 0
                    ),
                    days=days,
                )
                return filtered_data
            else:
                log.warning(
                    "historical_data.eod_no_date_column",
                    available_columns=list(eod_df.columns),
                )
                return eod_df

        except Exception as e:
            log.error("historical_data.eod_data_failed", error=str(e))
            return None

    def get_historical_front_kpi_data(self, days: int = 30) -> pd.DataFrame | None:
        """
        Get Front KPI data for the last N days.

        Args:
            days: Number of days to retrieve (default: 30)

        Returns:
            DataFrame with Front KPI data or None if retrieval fails
        """
        log.info("historical_data.front_kpi_data_start", days=days)

        try:
            # Get full Front KPI dataset
            # Using default location 'baytown' for backward compatibility
            front_alias = self.provider.get_location_aliases("baytown", "front")
            front_kpi_df = self.provider.fetch(front_alias) if front_alias else None
            if front_kpi_df is None or front_kpi_df.empty:
                log.warning("historical_data.front_kpi_data_empty")
                return None

            # Filter to date range if date column exists
            if "Submission Date" in front_kpi_df.columns:
                filtered_data = self._filter_by_date_range(
                    front_kpi_df, "Submission Date", days
                )
                log.info(
                    "historical_data.front_kpi_data_success",
                    total_rows=len(front_kpi_df),
                    filtered_rows=(
                        len(filtered_data) if filtered_data is not None else 0
                    ),
                    days=days,
                )
                return filtered_data
            else:
                log.warning(
                    "historical_data.front_kpi_no_date_column",
                    available_columns=list(front_kpi_df.columns),
                )
                return front_kpi_df

        except Exception as e:
            log.error("historical_data.front_kpi_data_failed", error=str(e))
            return None

    def get_latest_available_data(self) -> dict[str, pd.DataFrame | None]:
        """
        Get the most recent available data for all data sources.

        Returns data from the latest operational day (Monday-Saturday),
        automatically falling back from Sundays to Saturday data.

        Returns:
            Dictionary with 'eod' and 'front_kpi' DataFrames from latest
            operational day, plus 'data_date' with the target date
        """
        log.info("historical_data.get_latest_start")

        latest_date = self.get_latest_operational_date()

        result: dict[str, pd.DataFrame | None] = {
            "eod": None,
            "front_kpi": None,
        }

        try:
            # Get EOD data and filter to latest operational day
            # Using default location 'baytown' for backward compatibility
            eod_alias = self.provider.get_location_aliases("baytown", "eod")
            eod_df = self.provider.fetch(eod_alias) if eod_alias else None
            if (
                eod_df is not None
                and not eod_df.empty
                and "Submission Date" in eod_df.columns
            ):
                result["eod"] = self._filter_to_specific_date(
                    eod_df, "Submission Date", latest_date
                )

            # Get Front KPI data and filter to latest operational day
            # Using default location 'baytown' for backward compatibility
            front_alias = self.provider.get_location_aliases("baytown", "front")
            front_kpi_df = self.provider.fetch(front_alias) if front_alias else None
            if (
                front_kpi_df is not None
                and not front_kpi_df.empty
                and "Submission Date" in front_kpi_df.columns
            ):
                result["front_kpi"] = self._filter_to_specific_date(
                    front_kpi_df, "Submission Date", latest_date
                )

            eod_df_result = result.get("eod")
            front_kpi_df_result = result.get("front_kpi")
            log.info(
                "historical_data.get_latest_success",
                data_date=latest_date.isoformat(),
                eod_rows=(
                    len(eod_df_result) if isinstance(eod_df_result, pd.DataFrame) else 0
                ),
                front_kpi_rows=(
                    len(front_kpi_df_result)
                    if isinstance(front_kpi_df_result, pd.DataFrame)
                    else 0
                ),
            )

        except Exception as e:
            log.error("historical_data.get_latest_failed", error=str(e))

        return result

    def _filter_by_date_range(
        self, df: pd.DataFrame, date_column: str, days: int
    ) -> pd.DataFrame | None:
        """
        Filter DataFrame to records within the last N days from today.

        Args:
            df: Source DataFrame with date column
            date_column: Name of the date column to filter on
            days: Number of days to include (working backwards from today)

        Returns:
            Filtered DataFrame or None if no matching records
        """
        try:
            if date_column not in df.columns:
                log.warning(
                    "historical_data.missing_date_column",
                    column=date_column,
                    available=list(df.columns),
                )
                return None

            # Convert date column to datetime, coercing errors
            df_copy = df.copy()
            df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors="coerce")

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Filter to date range
            mask = (
                (df_copy[date_column] >= start_date)
                & (df_copy[date_column] <= end_date)
                & (df_copy[date_column].notna())
            )
            filtered_df = df_copy[mask]

            if filtered_df.empty:
                log.warning(
                    "historical_data.no_data_in_range",
                    start_date=start_date.date().isoformat(),
                    end_date=end_date.date().isoformat(),
                    days=days,
                )
                return None

            # Sort by date
            filtered_df = filtered_df.sort_values(date_column)

            log.info(
                "historical_data.filtered_by_range",
                start_date=start_date.date().isoformat(),
                end_date=end_date.date().isoformat(),
                rows=len(filtered_df),
                days=days,
            )
            return filtered_df

        except Exception as e:
            log.error(
                "historical_data.filter_by_range_failed",
                days=days,
                error=str(e),
            )
            return None

    def get_historical_eod_data(self, days: int = 30) -> pd.DataFrame | None:
        """
        Get historical EOD data for the specified number of days.

        This is an alias for get_recent_eod_data for consistency with
        the historical metrics functions.

        Args:
            days: Number of days to retrieve (default: 30)

        Returns:
            DataFrame with EOD data or None if retrieval fails
        """
        return self.get_recent_eod_data(days)
