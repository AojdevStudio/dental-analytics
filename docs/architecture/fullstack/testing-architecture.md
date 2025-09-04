# Testing Architecture

## Testing Pyramid

```
         /\
        /  \  E2E Tests (Manual)
       /    \  - Full dashboard load
      /──────\  - All KPIs display
     /        \  - Error states
    /──────────\  Integration Tests
   /            \  - API connection
  /──────────────\  - Data flow
 /                \  Unit Tests
/──────────────────\  - Calculations
                      - Type conversions
```

## Test Scenarios

**Unit Tests:**
```python
def test_collection_rate_calculation():
    df = pd.DataFrame({
        'total_collections': [900, 1800],
        'total_production': [1000, 2000]
    })
    assert calculate_collection_rate(df) == 90.0
```

**Integration Tests:**
```python
def test_google_sheets_connection():
    reader = SheetsReader()
    data = reader.get_sheet_data('A1:A1')
    assert data is not None
```

**E2E Tests:**
```python
def test_dashboard_loads():
    response = requests.get('http://localhost:8501')
    assert response.status_code == 200
    assert 'KAM DENTAL ANALYTICS' in response.text
```
