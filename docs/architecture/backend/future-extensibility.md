# Future Extensibility

## Adding New KPIs
1. Add calculation method to MetricsCalculator
2. Update get_all_kpis() orchestrator
3. No other changes required

## Switching Data Sources
- Replace SheetsReader with new data source class
- Keep same DataFrame output format
- Metrics module remains unchanged

## Adding Historical Tracking
```python
