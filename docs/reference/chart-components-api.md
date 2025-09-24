# Chart Components API Reference

## Overview

The chart components system provides interactive Plotly visualizations for dental KPI data.

## Chart Data Functions

### Production Chart Data

```python
def format_production_chart_data(
    eod_df: pd.DataFrame | None,
    date_column: str = "Date"
) -> dict[str, Any]
```

**Returns**:
```python
{
    "metric_name": "Production Total",
    "chart_type": "bar",
    "data_type": "currency",
    "time_series": [{
        "date": "2025-09-24",
        "value": 15000.00,
        "formatted_value": "$15,000"
    }, ...],
    "statistics": {
        "mean": 12000.00,
        "median": 11500.00,
        "min": 5000.00,
        "max": 20000.00,
        "trend": "increasing"
    }
}
```

### Collection Rate Chart Data

```python
def format_collection_rate_chart_data(
    eod_df: pd.DataFrame | None,
    date_column: str = "Date"
) -> dict[str, Any]
```

**Chart Type**: Line chart
**Data Type**: Percentage
**Y-Axis Range**: 0-100%

### New Patients Chart Data

```python
def format_new_patients_chart_data(
    eod_df: pd.DataFrame | None,
    date_column: str = "Date"
) -> dict[str, Any]
```

**Chart Type**: Bar chart
**Data Type**: Count (integer)

### Case Acceptance Chart Data

```python
def format_case_acceptance_chart_data(
    front_kpi_df: pd.DataFrame | None,
    date_column: str = "Submission Date"
) -> dict[str, Any]
```

**Chart Type**: Line chart
**Data Type**: Percentage
**Note**: Can exceed 100% when same-day treatment exceeds presented amount

### Hygiene Reappointment Chart Data

```python
def format_hygiene_reappointment_chart_data(
    front_kpi_df: pd.DataFrame | None,
    date_column: str = "Submission Date"
) -> dict[str, Any]
```

**Chart Type**: Line chart
**Data Type**: Percentage (0-100%)

## Chart Creation Functions

### Base Chart Creation

```python
def create_chart_from_data(
    chart_data: dict[str, Any],
    metric_name: str = None
) -> Figure
```

**Parameters**:
- `chart_data`: Formatted data from chart data functions
- `metric_name`: Optional override for metric name

**Returns**: Plotly Figure object

### Specific Chart Creators

```python
def create_production_chart(chart_data: dict[str, Any]) -> Figure
def create_collection_rate_chart(chart_data: dict[str, Any]) -> Figure
def create_new_patients_chart(chart_data: dict[str, Any]) -> Figure
def create_case_acceptance_chart(chart_data: dict[str, Any]) -> Figure
def create_hygiene_reappointment_chart(chart_data: dict[str, Any]) -> Figure
```

## Chart Styling

### Brand Colors

```python
BRAND_COLORS = {
    "primary_navy": "#142D54",
    "secondary_teal": "#007E9E",
    "success_green": "#28a745",
    "warning_amber": "#ffc107",
    "danger_red": "#BB0A0A",
    "neutral_gray": "#6c757d",
    "light_background": "#f8f9fa"
}
```

### Common Chart Properties

- **Height**: 400px default
- **Font**: System font stack
- **Grid**: Light gray gridlines
- **Hover**: Interactive tooltips with formatted values
- **Zoom**: Enabled for all charts
- **Pan**: Enabled for time series

## Utility Functions

### Format Currency

```python
def format_currency(value: float) -> str
```
Returns: "$X,XXX.XX" formatted string

### Format Percentage

```python
def format_percentage(value: float) -> str
```
Returns: "XX.X%" formatted string

### Calculate Statistics

```python
def calculate_chart_statistics(
    time_series: list[dict]
) -> dict[str, Any]
```

Returns statistics including mean, median, min, max, and trend

### Process Time Series

```python
def process_time_series_data(
    df: pd.DataFrame,
    date_column: str,
    value_column: str,
    data_type: str = "float"
) -> list[dict]
```

Converts DataFrame to time series format for charting

## Integration Example

```python
from apps.backend.chart_data import get_chart_data
from apps.frontend.chart_components import create_chart_from_data

# Get chart data for a location
chart_data = get_chart_data("baytown")

# Create production chart
if chart_data and "production_total" in chart_data:
    production_chart = create_chart_from_data(
        chart_data["production_total"]
    )
    st.plotly_chart(production_chart, use_container_width=True)
```

## Error Handling

- Empty data returns placeholder chart with "No data available" message
- Invalid data types are coerced safely with pandas
- Missing columns log warnings and return empty charts
- All charts gracefully degrade with informative messages

## Plotly Configuration

```python
DEFAULT_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "dental_kpi_chart",
        "scale": 2
    }
}
```

## Chart Types by KPI

| KPI | Chart Type | Primary Color | Target Line |
|-----|------------|---------------|-------------|
| Production | Bar | Navy | None |
| Collection Rate | Line | Teal | 95% |
| New Patients | Bar | Navy | None |
| Case Acceptance | Line | Navy | 85% |
| Hygiene Reappointment | Line | Teal | 90% |
