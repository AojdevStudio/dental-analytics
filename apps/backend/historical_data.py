"""
Historical Data Manager for Dental Practice Analytics

This module provides time-series data retrieval and operational day logic for dental
practice KPIs.
Key features:
- Time-series data collection spanning 30+ days
- Operational day logic (Monday-Saturday for dental practice)
- Sunday/holiday fallback to latest available operational day
- Framework-agnostic design for frontend flexibility

OPERATIONAL SCHEDULE:
- Dental practices typically operate Monday-Saturday
- Sundays and holidays are non-operational days
- "Latest available" data refers to the most recent operational day
"""

import logging
import sys
from datetime import datetime, timedelta

import pandas as pd
import structlog

from .sheets_reader import SheetsReader

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


class HistoricalDataManager:
    """
    Manages historical data retrieval and operational day logic for dental practice
    analytics.

    This class provides framework-agnostic methods for retrieving time-series data
    and handling operational day logic specific to dental practices.
    """

    def __init__(self, credentials_path: str = "config/credentials.json"):
        """
        Initialize the Historical Data Manager.

        Args:
            credentials_path: Path to Google Sheets service account credentials
        """
        self.sheets_reader = SheetsReader(credentials_path)
        self.operational_days = {0, 1, 2, 3, 4, 5}  # Monday=0 to Saturday=5
        log.info("historical_data.init", operational_days=list(self.operational_days))

    def is_operational_day(self, date: datetime) -> bool:
        """
        Check if a given date is an operational day for the dental practice.

        Args:
            date: Date to check

        Returns:
            True if the date is an operational day (Monday-Saturday), False otherwise
        """
        return date.weekday() in self.operational_days

    def get_latest_operational_date(
        self, reference_date: datetime | None = None
    ) -> datetime:
        """
        Get the most recent operational day from a reference date.

        Args:
            reference_date: Date to work backwards from (defaults to today)

        Returns:
            Most recent operational day (Monday-Saturday)
        """
        if reference_date is None:
            reference_date = datetime.now()

        log.info(
            "historical_data.get_latest_operational",
            reference_date=reference_date.isoformat(),
        )

        # Work backwards to find the most recent operational day
        current_date = reference_date
        max_lookback_days = 7  # Prevent infinite loops

        for _ in range(max_lookback_days):
            if self.is_operational_day(current_date):
                log.info(
                    "historical_data.latest_operational_found",
                    date=current_date.isoformat(),
                )
                return current_date
            current_date -= timedelta(days=1)

        # Fallback: return last Friday if no operational day found in the last week
        fallback_date = reference_date - timedelta(
            days=((reference_date.weekday() - 4) % 7)
        )
        log.warning(
            "historical_data.fallback_used", fallback_date=fallback_date.isoformat()
        )
        return fallback_date

    def get_date_range_for_period(self, days: int = 30) -> tuple[datetime, datetime]:
        """
        Get start and end dates for a historical period.

        Args:
            days: Number of days to include in the range

        Returns:
            Tuple of (start_date, end_date) for the historical period
        """
        end_date = self.get_latest_operational_date()
        start_date = end_date - timedelta(days=days)

        log.info(
            "historical_data.date_range_calculated",
            days=days,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        return start_date, end_date

    def get_historical_eod_data(self, days: int = 30) -> pd.DataFrame | None:
        """
        Retrieve historical EOD data spanning the specified number of days.

        Args:
            days: Number of days of historical data to retrieve

        Returns:
            DataFrame with historical EOD data or None if retrieval fails
        """
        log.info("historical_data.get_eod_start", days=days)

        try:
            df = self.sheets_reader.get_eod_data()
            if df is None or df.empty:
                log.warning("historical_data.eod_empty")
                return None

            # Filter to historical date range if date column exists
            if "Submission Date" in df.columns:
                df = self._filter_by_date_range(df, "Submission Date", days)

            log.info(
                "historical_data.eod_success", rows=len(df) if df is not None else 0
            )
            return df

        except Exception as e:
            log.error("historical_data.eod_failed", error=str(e))
            return None

    def get_historical_front_kpi_data(self, days: int = 30) -> pd.DataFrame | None:
        """
        Retrieve historical Front KPI data spanning the specified number of days.

        Args:
            days: Number of days of historical data to retrieve

        Returns:
            DataFrame with historical Front KPI data or None if retrieval fails
        """
        log.info("historical_data.get_front_kpi_start", days=days)

        try:
            df = self.sheets_reader.get_front_kpi_data()
            if df is None or df.empty:
                log.warning("historical_data.front_kpi_empty")
                return None

            # Filter to historical date range if date column exists
            if "Submission Date" in df.columns:
                df = self._filter_by_date_range(df, "Submission Date", days)

            log.info(
                "historical_data.front_kpi_success",
                rows=len(df) if df is not None else 0,
            )
            return df

        except Exception as e:
            log.error("historical_data.front_kpi_failed", error=str(e))
            return None

    def get_latest_available_data(self) -> dict[str, pd.DataFrame | None]:
        """
        Get the most recent available data for all data sources.

        Returns data from the latest operational day (Monday-Saturday),
        automatically falling back from Sundays to Saturday data.

        Returns:
            Dictionary with 'eod' and 'front_kpi' DataFrames from latest operational day
        """
        log.info("historical_data.get_latest_start")

        latest_date = self.get_latest_operational_date()

        result: dict[str, pd.DataFrame | datetime | None] = {
            "eod": None,
            "front_kpi": None,
            "data_date": latest_date,
        }

        try:
            # Get EOD data and filter to latest operational day
            eod_df = self.sheets_reader.get_eod_data()
            if (
                eod_df is not None
                and not eod_df.empty
                and "Submission Date" in eod_df.columns
            ):
                result["eod"] = self._filter_to_specific_date(
                    eod_df, "Submission Date", latest_date
                )

            # Get Front KPI data and filter to latest operational day
            front_kpi_df = self.sheets_reader.get_front_kpi_data()
            if (
                front_kpi_df is not None
                and not front_kpi_df.empty
                and "Submission Date" in front_kpi_df.columns
            ):
                result["front_kpi"] = self._filter_to_specific_date(
                    front_kpi_df, "Submission Date", latest_date
                )

            eod_df = result.get("eod")
            front_kpi_df = result.get("front_kpi")
            log.info(
                "historical_data.get_latest_success",
                data_date=latest_date.isoformat(),
                eod_rows=len(eod_df) if isinstance(eod_df, pd.DataFrame) else 0,
                front_kpi_rows=(
                    len(front_kpi_df) if isinstance(front_kpi_df, pd.DataFrame) else 0
                ),
            )

        except Exception as e:
            log.error("historical_data.get_latest_failed", error=str(e))

        return result

    def _filter_by_date_range(
        self, df: pd.DataFrame, date_column: str, days: int
    ) -> pd.DataFrame | None:
        """
        Filter DataFrame to include only data within the specified date range.

        Args:
            df: DataFrame to filter
            date_column: Name of the date column
            days: Number of days to include

        Returns:
            Filtered DataFrame or None if filtering fails
        """
        try:
            start_date, end_date = self.get_date_range_for_period(days)

            # Convert date column to datetime
            df_copy = df.copy()
            df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors="coerce")

            # Filter to date range
            mask = (df_copy[date_column] >= start_date) & (
                df_copy[date_column] <= end_date
            )
            filtered_df = df_copy[mask]

            log.info(
                "historical_data.date_filter_applied",
                original_rows=len(df),
                filtered_rows=len(filtered_df),
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            return filtered_df if not filtered_df.empty else None

        except Exception as e:
            log.error("historical_data.date_filter_failed", error=str(e))
            return None

    def _filter_to_specific_date(
        self, df: pd.DataFrame, date_column: str, target_date: datetime
    ) -> pd.DataFrame | None:
        """
        Filter DataFrame to include only data from a specific date.

        Args:
            df: DataFrame to filter
            date_column: Name of the date column
            target_date: Date to filter to

        Returns:
            Filtered DataFrame or None if no data found for the date
        """
        try:
            # Convert date column to datetime
            df_copy = df.copy()
            df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors="coerce")

            # Filter to specific date (date only, ignore time)
            target_date_only = target_date.date()
            mask = df_copy[date_column].dt.date == target_date_only
            filtered_df = df_copy[mask]

            log.info(
                "historical_data.specific_date_filter",
                target_date=target_date_only.isoformat(),
                matched_rows=len(filtered_df),
            )

            return filtered_df if not filtered_df.empty else None

        except Exception as e:
            log.error("historical_data.specific_date_filter_failed", error=str(e))
            return None
