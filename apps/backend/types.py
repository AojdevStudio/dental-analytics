"""TypedDict definitions for Dental Analytics Dashboard.

This module defines strongly-typed dictionary structures to replace dict[str, Any]
across the codebase. Following CLAUDE.md strict typing guidelines:
- NEVER use Any for function return types or internal data structures
- ONLY use Any for YAML ingestion (external, untyped data source)
- Use TypedDict for all structured dictionary returns
- Use Plotly-stubs types for chart configurations

Created: 2025-01-30
Phase: 3 of 4-phase TypedDict refactoring plan (fixing call sites)
"""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict

from typing_extensions import NotRequired

# =============================================================================
# TIME SERIES DATA STRUCTURES
# =============================================================================


class TimeSeriesPoint(TypedDict):
    """Individual time series data point for chart visualization.

    Used by: chart_data.py processing functions
    Purpose: Standardized format for chart data points with date and value

    Example:
        {
            "date": "2025-01-15",
            "timestamp": "2025-01-15T00:00:00",
            "value": 15000.50,
            "has_data": True
        }
    """

    date: str  # YYYY-MM-DD format
    timestamp: str  # ISO format datetime string
    value: float | int | None  # Actual metric value (None for missing data)
    has_data: bool  # True if value is not None


# =============================================================================
# CHART DATA STRUCTURES
# =============================================================================


class ChartStatistics(TypedDict):
    """Statistical summary for chart data.

    Used by: chart_data.py for aggregations and summaries
    Purpose: Provide min/max/average/total statistics for visualizations

    Note: All numeric fields use float for consistency with calculations
    """

    total: float  # Sum of all values (production, count, etc.)
    average: float  # Mean value across time period
    minimum: float  # Lowest value in dataset
    maximum: float  # Highest value in dataset
    data_points: int  # Number of valid data points


class ChartMetadata(TypedDict):
    """Metadata about chart data source and processing.

    Used by: chart_data.py processing functions
    Purpose: Track data provenance and processing information

    Optional fields use NotRequired[] for flexibility
    """

    date_column: str  # Source column name for dates
    date_range: str  # Human-readable date range (e.g., "2025-01-01 to 2025-01-31")
    error: NotRequired[str | None]  # Error message if processing failed
    aggregation: NotRequired[str | None]  # "daily", "weekly", or "monthly"
    business_days_only: NotRequired[bool | None]  # Whether Sundays were excluded
    date_filter: NotRequired[str | None]  # Applied date filter range
    filtered_data_points: NotRequired[int | None]  # Number of points after filtering


class ChartData(TypedDict):
    """Complete chart data structure for frontend visualization.

    Used by: chart_data.py processing functions, chart_kpis.py
    Purpose: Standardized chart data format for all KPI visualizations

    This is the PRIMARY data structure passed from backend to frontend charts.
    Contains all information needed for Plotly chart generation.

    Example:
        {
            "dates": ["2025-01-01", "2025-01-02", ...],
            "values": [12500.0, 13200.0, ...],
            "statistics": {"total": 250000.0, "average": 12500.0, ...},
            "metadata": {"date_column": "Submission Date", ...}
        }
    """

    dates: list[str]  # List of dates in YYYY-MM-DD format
    values: list[float]  # Corresponding metric values (same length as dates)
    statistics: ChartStatistics  # Aggregated statistics
    metadata: ChartMetadata  # Data source and processing info
    error: NotRequired[str | None]  # Error message if processing failed


class TimeSeriesChartData(TypedDict):
    """Time series chart data with advanced metadata.

    Used by: chart_data.py format_*_chart_data() functions
    Purpose: Rich chart data structure with formatting options

    This extends ChartData with additional metadata for specific chart types
    and formatting preferences (currency symbols, decimal places, etc.)
    """

    metric_name: str  # Display name (e.g., "Production Total", "Collection Rate")
    chart_type: str  # "line", "bar", or "area"
    data_type: str  # "currency", "percentage", "count", or "float"
    time_series: list[TimeSeriesPoint]  # Time series data points
    statistics: NotRequired[
        dict[str, float | int] | ChartSummaryStats
    ]  # Statistical summary
    format_options: dict[
        str, str | float | bool | dict[str, float]
    ]  # Display formatting
    error: NotRequired[str | None]  # Error message if processing failed


# =============================================================================
# KPI DATA STRUCTURES
# =============================================================================


class KPIData(TypedDict):
    """Response structure for all 5 core KPI calculations.

    Used by: metrics.py get_all_kpis() and get_combined_kpis()
    Purpose: Standardized KPI response for dashboard display

    All KPI values are optional (None) to handle missing/failed calculations.
    This structure is returned by get_all_kpis(location) for a single location.

    Example:
        {
            "production_total": 125000.0,
            "collection_rate": 97.5,
            "new_patients": 42,
            "case_acceptance": 85.2,
            "hygiene_reappointment": 92.1
        }
    """

    production_total: float | None  # Total production (revenue) in dollars
    collection_rate: float | None  # Collection rate percentage (0-100)
    new_patients: int | None  # Count of new patients (month-to-date)
    case_acceptance: float | None  # Treatment acceptance rate percentage (0-100)
    hygiene_reappointment: float | None  # Hygiene reappointment rate percentage (0-100)


class MultiLocationKPIData(TypedDict):
    """KPI data for multiple practice locations.

    Used by: metrics.py get_combined_kpis()
    Purpose: Combine KPIs from Baytown and Humble locations

    Example:
        {
            "baytown": {"production_total": 125000.0, ...},
            "humble": {"production_total": 98000.0, ...}
        }
    """

    baytown: KPIData  # Baytown practice KPIs
    humble: KPIData  # Humble practice KPIs


# =============================================================================
# HISTORICAL METRIC DATA STRUCTURES (SPECIALIZED VARIANTS)
# =============================================================================


class HistoricalProductionData(TypedDict):
    """Historical data for production-based metrics (Production Total).

    Used by: metrics.py calculate_historical_production()
    Purpose: Time series with sum and average aggregations

    Example:
        {
            "time_series": [(datetime(2025,1,1), 12500.0), ...],
            "total_sum": 250000.0,
            "daily_average": 12500.0,
            "latest_value": 13200.0,
            "data_points": 20
        }
    """

    time_series: list[tuple[datetime, float]]  # List of (date, value) tuples
    total_sum: float  # Sum of production values
    daily_average: float  # Average production per day
    latest_value: float | None  # Most recent value
    data_points: int  # Number of valid data points


class HistoricalRateData(TypedDict):
    """Historical data for rate-based metrics (Collection Rate, Hygiene Reappointment).

    Used by: metrics.py calculate_historical_collection(),
    calculate_historical_hygiene()
    Purpose: Time series with average rate calculation

    Example:
        {
            "time_series": [(datetime(2025,1,1), 97.5), ...],
            "average_rate": 96.8,
            "latest_value": 98.2,
            "data_points": 20
        }
    """

    time_series: list[tuple[datetime, float]]  # List of (date, value) tuples
    average_rate: float  # Average rate across time period
    latest_value: float | None  # Most recent value
    data_points: int  # Number of valid data points


class HistoricalCountData(TypedDict):
    """Historical data for count-based metrics (New Patients, Case Acceptance).
    Used by: metrics.py calculate_historical_new_patients(),
    calculate_historical_case_acceptance()
    Purpose: Time series with total count and average

    Example:
        {
            "time_series": [(datetime(2025,1,1), 5), ...],
            "total_count": 42,
            "daily_average": 2.1,
            "latest_value": 3,
            "data_points": 20
        }
    """

    time_series: list[tuple[datetime, float]]  # List of (date, value) tuples
    total_count: int  # Total count across time period
    daily_average: float  # Average count per day
    latest_value: int | None  # Most recent value
    data_points: int  # Number of valid data points


# Generic alias for functions that can return any historical metric type
HistoricalMetricData = (
    HistoricalProductionData | HistoricalRateData | HistoricalCountData
)


class HistoricalKPIData(TypedDict):
    """Complete historical KPI response structure.

    Used by: metrics.py get_all_historical_kpis()
    Purpose: Return historical data for all KPIs with current values

    Example:
        {
            "historical": {
                "production_total": {"time_series": [...], "total_sum": 250000.0, ...},
                "collection_rate": {"time_series": [...], "average_rate": 97.5, ...},
                ...
            },
            "current": {"production_total": 125000.0, "collection_rate": 97.5, ...},
            "data_date": "2025-01-30",
            "period_days": 30
        }
    """

    historical: dict[str, HistoricalMetricData]  # Historical data for each KPI
    current: KPIData  # Current/latest KPI values
    data_date: str | None  # Date of most recent data (YYYY-MM-DD)
    period_days: int  # Number of days in historical period


# =============================================================================
# CONFIGURATION DATA STRUCTURES
# =============================================================================


class SheetConfig(TypedDict):
    """Configuration for a single Google Sheets data source.

    Used by: data_providers.py SheetsProvider
    Purpose: Define spreadsheet ID and range for data retrieval

    Example:
        {
            "spreadsheet_id": "1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8",
            "range": "EOD - Baytown Billing!A:N"
        }
    """

    spreadsheet_id: str  # Google Sheets spreadsheet ID
    range: str  # Sheet name and range (e.g., "Sheet1!A:Z")


class LocationConfig(TypedDict):
    """Configuration for a practice location's data sources.

    Used by: data_providers.py SheetsProvider
    Purpose: Map location to EOD and Front KPI sheet aliases

    Example:
        {
            "eod": "baytown_eod",
            "front": "baytown_front"
        }
    """

    eod: str  # Alias for EOD billing sheet
    front: str  # Alias for Front KPI sheet


class ProviderConfig(TypedDict):
    """Google Sheets API provider configuration.

    Used by: data_providers.py SheetsProvider
    Purpose: Store credentials path and API scopes

    Example:
        {
            "credentials_path": "config/credentials.json",
            "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        }
    """

    credentials_path: str  # Path to service account credentials JSON
    scopes: list[str]  # Google API OAuth scopes


class ConfigData(TypedDict):
    """Complete configuration structure loaded from YAML.

    Used by: data_providers.py SheetsProvider._load_config()
    Purpose: Store all provider configuration after YAML ingestion

    NOTE: This is the ONLY place where dict[str, Any] was used in the original
    code (for YAML loading). We now define explicit structure post-ingestion.

    Example:
        {
            "sheets": {
                "baytown_eod": {"spreadsheet_id": "...", "range": "..."},
                "baytown_front": {"spreadsheet_id": "...", "range": "..."},
                ...
            },
            "locations": {
                "baytown": {"eod": "baytown_eod", "front": "baytown_front"},
                "humble": {"eod": "humble_eod", "front": "humble_front"}
            },
            "provider_config": {
                "credentials_path": "config/credentials.json",
                "scopes": ["https://..."]
            }
        }
    """

    sheets: dict[str, SheetConfig]  # Map of alias -> sheet configuration
    locations: dict[str, LocationConfig]  # Map of location name -> data aliases
    provider_config: ProviderConfig  # API credentials and configuration


# =============================================================================
# CHART SUMMARY STATISTICS (ADVANCED)
# =============================================================================


class ChartSummaryStats(TypedDict):
    """Advanced statistical summary for chart data validation.

    Used by: chart_data.py calculate_chart_statistics()
    Purpose: Provide detailed statistics for time series data quality

    Includes data coverage metrics and date range information
    for data quality assessment.

    Example:
        {
            "total_points": 30,
            "valid_points": 28,
            "missing_points": 2,
            "coverage_percentage": 93.3,
            "date_range": {"start": "2025-01-01", "end": "2025-01-30"},
            "min_value": 8500.0,
            "max_value": 15200.0,
            "average_value": 12350.0
        }
    """

    total_points: int  # Total number of data points expected
    valid_points: int  # Number of points with valid data
    missing_points: int  # Number of points with missing/null data
    coverage_percentage: float  # Percentage of valid data points
    date_range: dict[str, str] | None  # {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
    min_value: NotRequired[float | int | None]  # Minimum value (if valid_points > 0)
    max_value: NotRequired[float | int | None]  # Maximum value (if valid_points > 0)
    average_value: NotRequired[float | None]  # Mean value (if valid_points > 0)


# =============================================================================
# METADATA STRUCTURES
# =============================================================================


class DataSourceMetadata(TypedDict):
    """Metadata about data source availability.

    Used by: chart_data.py format_all_chart_data()
    Purpose: Track which data sources were available during processing

    Example:
        {
            "eod_available": True,
            "front_kpi_available": True
        }
    """

    eod_available: bool  # Whether EOD billing data was available
    front_kpi_available: bool  # Whether Front KPI data was available


class AllChartsMetadata(TypedDict):
    """Metadata for complete chart data collection.

    Used by: chart_data.py format_all_chart_data()
    Purpose: Provide generation timestamp and data source status

    Example:
        {
            "generated_at": "2025-01-30T14:30:00",
            "data_sources": {"eod_available": True, "front_kpi_available": True},
            "total_metrics": 5
        }
    """

    generated_at: str  # ISO timestamp of data generation
    data_sources: DataSourceMetadata  # Data source availability flags
    total_metrics: int  # Number of KPI metrics processed


# =============================================================================
# TYPE ALIASES FOR COMMON PATTERNS
# =============================================================================

# Type alias for chart data collection (used in format_all_chart_data)
AllChartData = dict[str, TimeSeriesChartData | AllChartsMetadata]

# Type alias for spreadsheet info (used in get_spreadsheet_info)
SpreadsheetInfo = dict[str, str]  # {"spreadsheet_id": str, "range": str}


# =============================================================================
# VALIDATION AND HELPER NOTES
# =============================================================================

"""
USAGE GUIDELINES:

1. **Function Return Types**:
   - Use specific TypedDict instead of dict[str, Any]
   - Example: def process_chart(df: pd.DataFrame) -> ChartData:

2. **Optional Fields**:
   - Use NotRequired[] for fields that may not always be present
   - Example: error: NotRequired[str]  # Only present on failure

3. **Nested Structures**:
   - Define nested TypedDicts separately for clarity
   - Example: ChartData contains ChartStatistics and ChartMetadata

4. **Type Narrowing**:
   - Use isinstance() checks before accessing NotRequired fields
   - Example: if "error" in data: handle_error(data["error"])

5. **Historical Metric Variants**:
   - Use HistoricalProductionData for production metrics
   - Use HistoricalRateData for percentage-based metrics
   - Use HistoricalCountData for count-based metrics
   - Use HistoricalMetricData union type for generic handling

6. **Migration Strategy**:
   - Phase 2: Update function signatures to use these types ✅
   - Phase 3: Fix call sites to provide all required fields (CURRENT)
   - Phase 4: Add runtime validation with validation functions

7. **YAML Exception**:
   - config: dict[str, Any] = yaml.safe_load(f)  # OK - external source
   - After validation, cast to ConfigData for type safety
"""
