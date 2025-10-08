"""Pydantic models for chart data structures.

This module provides strongly-typed, validated models for chart data processing
and visualization. All models include runtime validation and are framework-independent.

Created: 2025-10-02
Phase: 1 - TypedDict Elimination
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ChartDataPoint(BaseModel):
    """Individual time series data point for chart visualization.

    Replaces: TimeSeriesPoint (TypedDict in apps/backend/types.py)

    Attributes
    ----------
    date:
        Date in YYYY-MM-DD format representing the data point timestamp.
    timestamp:
        ISO format datetime string for precise temporal tracking.
    value:
        Metric value (production, rate, count). None indicates missing data.
    has_data:
        Flag indicating whether value is present and valid.
    """

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    timestamp: str = Field(..., description="ISO format datetime string")
    value: float | int | None = Field(default=None, description="Metric value")
    has_data: bool = Field(default=False, description="Data availability flag")

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Ensure date follows YYYY-MM-DD format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Date must be in YYYY-MM-DD format, got: {v}") from e
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_format(cls, v: str) -> str:
        """Ensure timestamp follows ISO format."""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError(f"Timestamp must be in ISO format, got: {v}") from e
        return v


class ChartStats(BaseModel):
    """Statistical summary for chart data.

    Replaces: ChartStatistics (TypedDict in apps/backend/types.py)

    Attributes
    ----------
    total:
        Sum of all values (production, count, etc.)
    average:
        Mean value across time period.
    minimum:
        Lowest value in dataset.
    maximum:
        Highest value in dataset.
    data_points:
        Number of valid data points included in calculations.
    """

    total: float = Field(default=0.0, description="Sum of all values")
    average: float = Field(default=0.0, description="Mean value")
    minimum: float = Field(default=0.0, description="Lowest value")
    maximum: float = Field(default=0.0, description="Highest value")
    data_points: int = Field(default=0, ge=0, description="Valid data point count")


class ChartMetaInfo(BaseModel):
    """Metadata about chart data source and processing.

    Replaces: ChartMetadata (TypedDict in apps/backend/types.py)

    Attributes
    ----------
    date_column:
        Source column name for dates (e.g., "Submission Date").
    date_range:
        Human-readable date range (e.g., "2025-01-01 to 2025-01-31").
    error:
        Error message if processing failed, None otherwise.
    aggregation:
        Aggregation level: "daily", "weekly", or "monthly".
    business_days_only:
        Whether Sunday data was excluded from calculations.
    date_filter:
        Applied date filter range specification.
    filtered_data_points:
        Number of data points remaining after filtering.
    """

    date_column: str = Field(..., description="Source date column name")
    date_range: str = Field(..., description="Human-readable date range")
    error: str | None = Field(default=None, description="Processing error message")
    aggregation: Literal["daily", "weekly", "monthly"] | None = Field(
        default=None, description="Aggregation level"
    )
    business_days_only: bool | None = Field(
        default=None, description="Sunday exclusion flag"
    )
    date_filter: str | None = Field(default=None, description="Applied date filter")
    filtered_data_points: int | None = Field(
        default=None, ge=0, description="Post-filter data point count"
    )


class ProcessedChartData(BaseModel):
    """Complete chart data structure for frontend visualization.

    Replaces: ChartData (TypedDict in apps/backend/types.py)

    This is the primary data structure passed from backend to frontend charts.
    Contains all information needed for Plotly chart generation.

    Attributes
    ----------
    dates:
        List of dates in YYYY-MM-DD format.
    values:
        Corresponding metric values (same length as dates).
    statistics:
        Aggregated statistical summary.
    metadata:
        Data source and processing information.
    error:
        Error message if processing failed, None otherwise.
    """

    dates: list[str] = Field(default_factory=list, description="Date list (YYYY-MM-DD)")
    values: list[float] = Field(default_factory=list, description="Metric values")
    statistics: ChartStats = Field(
        default_factory=ChartStats, description="Statistical summary"
    )
    metadata: ChartMetaInfo
    error: str | None = Field(default=None, description="Processing error message")

    @model_validator(mode="after")
    def validate_dates_values_alignment(self) -> ProcessedChartData:
        """Ensure dates and values lists have matching lengths."""
        if len(self.dates) != len(self.values):
            raise ValueError(
                f"Mismatched list lengths: {len(self.dates)} dates "
                f"vs {len(self.values)} values"
            )
        return self


class TimeSeriesData(BaseModel):
    """Time series chart data with advanced metadata.

    Replaces: TimeSeriesChartData (TypedDict in apps/backend/types.py)

    Extends ProcessedChartData with additional metadata for specific chart types
    and formatting preferences (currency symbols, decimal places, etc.)

    Attributes
    ----------
    metric_name:
        Display name (e.g., "Production Total", "Collection Rate").
    chart_type:
        Chart visualization type: "line", "bar", or "area".
    data_type:
        Data type for formatting: "currency", "percentage", "count", or "float".
    time_series:
        List of time series data points with metadata.
    statistics:
        Statistical summary or dict of aggregated metrics.
    format_options:
        Display formatting configuration (symbols, decimals, etc.).
    error:
        Error message if processing failed, None otherwise.
    """

    metric_name: str = Field(..., description="Display metric name")
    chart_type: Literal["line", "bar", "area"] = Field(..., description="Chart type")
    data_type: Literal["currency", "percentage", "count", "float"] = Field(
        ..., description="Data formatting type"
    )
    time_series: list[ChartDataPoint] = Field(
        default_factory=list, description="Time series data points"
    )
    statistics: dict[str, float | int] | SummaryStatistics | None = Field(
        default=None, description="Statistical summary"
    )
    format_options: dict[str, str | float | bool | dict[str, float]] = Field(
        default_factory=dict, description="Display formatting options"
    )
    error: str | None = Field(default=None, description="Processing error message")


class SummaryStatistics(BaseModel):
    """Advanced statistical summary for chart data validation.

    Replaces: ChartSummaryStats (TypedDict in apps/backend/types.py)

    Provides detailed statistics for time series data quality assessment,
    including coverage metrics and date range information.

    Attributes
    ----------
    total_points:
        Total number of data points expected in time range.
    valid_points:
        Number of points with valid (non-null) data.
    missing_points:
        Number of points with missing or null data.
    coverage_percentage:
        Percentage of valid data points (valid_points / total_points × 100).
    date_range:
        Start and end dates in YYYY-MM-DD format, None if no data.
    min_value:
        Minimum value across all valid points (if any exist).
    max_value:
        Maximum value across all valid points (if any exist).
    average_value:
        Mean value across all valid points (if any exist).
    """

    total_points: int = Field(default=0, ge=0, description="Total expected points")
    valid_points: int = Field(default=0, ge=0, description="Valid data point count")
    missing_points: int = Field(default=0, ge=0, description="Missing data point count")
    coverage_percentage: float = Field(
        default=0.0, ge=0, le=100, description="Data coverage percentage"
    )
    date_range: dict[str, str] | None = Field(
        default=None, description="Date range (start/end)"
    )
    min_value: float | int | None = Field(default=None, description="Minimum value")
    max_value: float | int | None = Field(default=None, description="Maximum value")
    average_value: float | None = Field(default=None, description="Mean value")


class DataSourceInfo(BaseModel):
    """Metadata about data source availability.

    Replaces: DataSourceMetadata (TypedDict in apps/backend/types.py)

    Tracks which data sources were available during chart data processing,
    useful for debugging and data quality monitoring.

    Attributes
    ----------
    eod_available:
        Whether EOD (End of Day) billing data was available.
    front_kpi_available:
        Whether Front KPI form data was available.
    """

    eod_available: bool = Field(default=False, description="EOD data availability")
    front_kpi_available: bool = Field(
        default=False, description="Front KPI data availability"
    )


class ChartsMetadata(BaseModel):
    """Metadata for complete chart data collection.

    Replaces: AllChartsMetadata (TypedDict in apps/backend/types.py)

    Provides generation timestamp and data source status for all charts
    processed in a single request.

    Attributes
    ----------
    generated_at:
        ISO timestamp of data generation.
    data_sources:
        Data source availability flags.
    total_metrics:
        Number of KPI metrics processed in this batch.
    """

    generated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Generation timestamp",
    )
    data_sources: DataSourceInfo = Field(
        default_factory=DataSourceInfo, description="Data source status"
    )
    total_metrics: int = Field(default=0, ge=0, description="Processed metric count")


class MultiLocationKPIs(BaseModel):
    """KPI data for multiple practice locations.

    Replaces: MultiLocationKPIData (TypedDict in apps/backend/types.py)

    Combines KPI dictionaries from Baytown and Humble locations with
    automatic timestamp generation for tracking data freshness.

    Attributes
    ----------
    baytown:
        Dictionary of Baytown KPI values (metric_name -> value).
    humble:
        Dictionary of Humble KPI values (metric_name -> value).
    timestamp:
        ISO timestamp when this data snapshot was created.
    """

    baytown: dict[str, float | int | None] = Field(
        default_factory=dict, description="Baytown KPI values"
    )
    humble: dict[str, float | int | None] = Field(
        default_factory=dict, description="Humble KPI values"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Data snapshot timestamp",
    )
