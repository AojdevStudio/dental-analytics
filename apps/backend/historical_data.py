"""Historical data manager utilities for the dental analytics dashboard."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta
from typing import Any

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

# Preserve access to the real ``datetime`` class for parsing operations even when
# tests patch ``apps.backend.historical_data.datetime``.
REAL_DATETIME = datetime


class HistoricalDataManager:
    """Manages historical dental practice data with caching and date filtering."""

    def __init__(self, data_provider: Any | None = None) -> None:
        """Initialise the historical data manager with optional provider injection."""

        self.data_provider = data_provider or build_sheets_provider()
        # Maintain backward compatibility with previous attribute name
        self.provider = self.data_provider
        log.info("historical_data.manager_initialized")

    def _get_operational_date(self, reference_date: datetime) -> datetime:
        """Return the nearest operational day (Mon-Sat) for a given reference."""

        if reference_date.weekday() == 6:  # Sunday
            return reference_date - timedelta(days=1)
        return reference_date

    def get_latest_operational_date(self) -> datetime:
        """Get the latest operational day based on the current timestamp."""

        today = datetime.now()
        latest_date = self._get_operational_date(today)
        if latest_date != today:
            log.info(
                "historical_data.sunday_fallback",
                original_date=today.date().isoformat(),
                fallback_date=latest_date.date().isoformat(),
            )
        return latest_date

    def _parse_date_string(self, value: Any) -> datetime | None:
        """Parse a date string into a ``datetime`` instance if possible."""

        if value in (None, ""):
            return None

        text_value = str(value).strip()
        if text_value == "":
            return None

        formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]
        for fmt in formats:
            try:
                return REAL_DATETIME.strptime(text_value, fmt)
            except ValueError:
                continue

        parsed = pd.to_datetime(text_value, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.to_pydatetime()

    def _convert_to_datetime_column(
        self, df: pd.DataFrame, column: str
    ) -> pd.DataFrame | None:
        """Coerce a column to ``datetime`` and drop rows that cannot convert."""

        if df is None or df.empty or column not in df.columns:
            return None

        df_copy = df.copy()
        df_copy[column] = df_copy[column].apply(self._parse_date_string)
        df_copy = df_copy.dropna(subset=[column])

        if df_copy.empty:
            return None

        return df_copy

    def _calculate_aggregations(self, df: pd.DataFrame) -> dict[str, Any]:
        """Calculate summary statistics for production-oriented datasets."""

        if df is None or df.empty:
            return {
                "total_sum": None,
                "daily_average": None,
                "latest_value": None,
                "data_points": 0,
            }

        numeric_df = df.select_dtypes(include=["number", "float", "int"])
        candidate_columns = [
            "total_production",
            "production_total",
            "collections_total",
        ]
        target_column = next(
            (col for col in candidate_columns if col in df.columns),
            None,
        )

        if target_column is None:
            if numeric_df.empty:
                return {
                    "total_sum": None,
                    "daily_average": None,
                    "latest_value": None,
                    "data_points": 0,
                }
            target_column = numeric_df.columns[0]

        series = pd.to_numeric(df[target_column], errors="coerce").dropna()

        if series.empty:
            return {
                "total_sum": None,
                "daily_average": None,
                "latest_value": None,
                "data_points": 0,
            }

        return {
            "total_sum": float(series.sum()),
            "daily_average": float(series.mean()),
            "latest_value": float(series.iloc[-1]) if not series.empty else None,
            "data_points": int(series.count()),
        }

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

    def get_recent_eod_data(
        self, days: int = 30, location: str = "baytown"
    ) -> pd.DataFrame | None:
        """
        Get EOD billing data for the last N days.

        Args:
            days: Number of days to retrieve (default: 30)
            location: Location name ('baytown' or 'humble')

        Returns:
            DataFrame with EOD data or None if retrieval fails
        """
        log.info("historical_data.eod_data_start", days=days, location=location)

        try:
            # Get EOD data using new provider pattern
            eod_alias = self.data_provider.get_location_aliases(location, "eod")
            eod_df = self.data_provider.fetch(eod_alias) if eod_alias else None
            if eod_df is None or eod_df.empty:
                log.warning("historical_data.eod_data_empty", location=location)
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
                    location=location,
                )
                return filtered_data
            else:
                log.warning(
                    "historical_data.eod_no_date_column",
                    available_columns=list(eod_df.columns),
                    location=location,
                )
                return eod_df

        except Exception as e:
            log.error(
                "historical_data.eod_data_failed", error=str(e), location=location
            )
            return None

    def get_historical_front_kpi_data(
        self, days: int = 30, location: str = "baytown"
    ) -> pd.DataFrame | None:
        """
        Get Front KPI data for the last N days.

        Args:
            days: Number of days to retrieve (default: 30)
            location: Location name ('baytown' or 'humble')

        Returns:
            DataFrame with Front KPI data or None if retrieval fails
        """
        log.info("historical_data.front_kpi_data_start", days=days, location=location)

        try:
            # Get Front KPI data using new provider pattern
            front_alias = self.data_provider.get_location_aliases(location, "front")
            front_kpi_df = (
                self.data_provider.fetch(front_alias) if front_alias else None
            )
            if front_kpi_df is None or front_kpi_df.empty:
                log.warning("historical_data.front_kpi_data_empty", location=location)
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
                    location=location,
                )
                return filtered_data
            else:
                log.warning(
                    "historical_data.front_kpi_no_date_column",
                    available_columns=list(front_kpi_df.columns),
                    location=location,
                )
                return front_kpi_df

        except Exception as e:
            log.error(
                "historical_data.front_kpi_data_failed", error=str(e), location=location
            )
            return None

    def get_latest_available_data(
        self, location: str = "baytown"
    ) -> dict[str, pd.DataFrame | None]:
        """
        Get the most recent available data for all data sources.

        Returns data from the latest operational day (Monday-Saturday),
        automatically falling back from Sundays to Saturday data.

        Args:
            location: Location name ('baytown' or 'humble')

        Returns:
            Dictionary with 'eod' and 'front_kpi' DataFrames from latest
            operational day, plus 'data_date' with the target date
        """
        log.info("historical_data.get_latest_start", location=location)

        latest_date = self.get_latest_operational_date()

        result: dict[str, pd.DataFrame | None] = {
            "eod": None,
            "front_kpi": None,
        }

        try:
            # Get EOD data and filter to latest operational day
            eod_alias = self.data_provider.get_location_aliases(location, "eod")
            eod_df = self.data_provider.fetch(eod_alias) if eod_alias else None
            if (
                eod_df is not None
                and not eod_df.empty
                and "Submission Date" in eod_df.columns
            ):
                result["eod"] = self._filter_to_specific_date(
                    eod_df, "Submission Date", latest_date
                )

            # Get Front KPI data and filter to latest operational day
            front_alias = self.data_provider.get_location_aliases(location, "front")
            front_kpi_df = (
                self.data_provider.fetch(front_alias) if front_alias else None
            )
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
                location=location,
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
            log.error(
                "historical_data.get_latest_failed", error=str(e), location=location
            )

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

    def get_historical_data(
        self, sheet_alias: str, date_column: str, days: int
    ) -> dict[str, Any] | None:
        """Retrieve historical data for an arbitrary sheet alias."""

        try:
            raw_df = self.data_provider.fetch(sheet_alias)
        except Exception as error:  # pragma: no cover - defensive logging
            log.error(
                "historical_data.provider_fetch_failed",
                alias=sheet_alias,
                error=str(error),
            )
            return None

        if raw_df is None or raw_df.empty:
            log.warning(
                "historical_data.empty_dataset",
                alias=sheet_alias,
                days=days,
            )
            return None

        converted = self._convert_to_datetime_column(raw_df, date_column)
        if converted is None:
            log.warning(
                "historical_data.unusable_date_column",
                alias=sheet_alias,
                column=date_column,
            )
            return None

        filtered = self._filter_by_date_range(converted, date_column, days)
        if filtered is None:
            return None

        aggregations = self._calculate_aggregations(filtered)
        return aggregations

    def get_latest_data(
        self, sheet_alias: str, date_column: str
    ) -> pd.DataFrame | None:
        """Retrieve the records for the latest operational day."""

        try:
            raw_df = self.data_provider.fetch(sheet_alias)
        except Exception as error:  # pragma: no cover - defensive logging
            log.error(
                "historical_data.provider_fetch_failed",
                alias=sheet_alias,
                error=str(error),
            )
            return None

        converted = self._convert_to_datetime_column(raw_df, date_column)
        if converted is None:
            return None

        latest_date = self.get_latest_operational_date()
        latest_records = self._filter_to_specific_date(
            converted, date_column, latest_date
        )

        if latest_records is not None and not latest_records.empty:
            return latest_records

        # Fallback to most recent available row within a one-week window
        sorted_df = converted.sort_values(date_column)
        most_recent_date = sorted_df[date_column].max()

        if most_recent_date is None:
            return None

        if (latest_date.date() - most_recent_date.date()).days <= 7:
            return sorted_df[sorted_df[date_column] == most_recent_date]

        return None
