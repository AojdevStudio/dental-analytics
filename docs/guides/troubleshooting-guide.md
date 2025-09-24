# Troubleshooting Guide

## Quick Diagnostics

### Check System Status
```bash
# Verify Python version
python --version  # Should be 3.10+

# Check dependencies
uv pip list | grep -E "streamlit|pandas|google"

# Test Google Sheets connection
uv run python scripts/print_kpis.py --location baytown

# Check configuration
cat config/sheets.yml | head -20
```

## Common Issues and Solutions

## 1. Case Acceptance Over 100%

### Symptom
Case acceptance showing values like 247.8% or 173.5%

### Cause
Dollar amounts in "Same Day Treatment" column exceeding "Treatments Presented"

### Solution
1. Verify data entry in Google Sheets:
```python
# Check specific dates
uv run python -c "
from apps.backend.data_providers import build_sheets_provider
df = provider.fetch('baytown_front')
print(df[['treatments_presented', 'treatments_scheduled', '$ Same Day Treatment']].head())
"
```

2. Review Column T formula in Google Sheets
3. Ensure Same Day Treatment only includes presented treatments

### Prevention
- Add data validation rules in Google Forms
- Implement warning alerts in dashboard for >100% values

## 2. Data Unavailable Errors

### Symptom
Dashboard shows "Data Unavailable" for one or more KPIs

### Possible Causes

#### A. Missing Credentials
```bash
# Check if credentials exist
ls -la config/credentials.json

# Verify JSON structure
python -m json.tool config/credentials.json | head -10
```

#### B. Incorrect Sheet Configuration
```bash
# Verify sheet aliases
grep -A 3 "baytown_eod" config/sheets.yml

# Test specific alias
uv run python -c "
from apps.backend.data_providers import build_sheets_provider
provider = build_sheets_provider()
df = provider.fetch('baytown_eod')
print('Rows:', len(df) if df is not None else 'None')
"
```

#### C. Column Name Mismatches
```python
# Check column names
uv run python -c "
from apps.backend.data_providers import build_sheets_provider
provider = build_sheets_provider()
df = provider.fetch('baytown_eod')
print('Columns:', df.columns.tolist() if df is not None else 'None')
"
```

### Solutions
1. Regenerate service account credentials
2. Update config/sheets.yml with correct ranges
3. Verify column mappings in config/data_sources.py

## 3. Slow Dashboard Loading

### Symptom
Dashboard takes >10 seconds to load

### Diagnosis
```bash
# Profile loading time
time uv run python scripts/print_kpis.py --location baytown

# Check data volume
uv run python -c "
from apps.backend.data_providers import build_sheets_provider
provider = build_sheets_provider()
for alias in ['baytown_eod', 'baytown_front']:
    df = provider.fetch(alias)
    if df is not None:
        print(f'{alias}: {len(df)} rows, {len(df.columns)} columns')
"
```

### Solutions

#### Implement Caching
```python
# Add to app.py
@st.cache_data(ttl=300)  # 5-minute cache
def get_cached_kpis(location):
    return get_all_kpis(location)
```

#### Reduce Data Range
```yaml
# config/sheets.yml - Limit range
baytown_eod:
  range: "EOD - Baytown Billing!A1:N1000"  # Last 1000 rows only
```

#### Optimize Queries
```python
# Use specific columns
REQUIRED_COLUMNS = ['Date', 'total_production', 'total_collections']
df = df[REQUIRED_COLUMNS]
```

## 4. Authentication Failures

### Symptom
```
Error: Request had insufficient authentication scopes
```

### Solution
1. Check service account permissions in Google Cloud Console
2. Verify API is enabled:
```bash
# List enabled APIs
gcloud services list --enabled --project YOUR_PROJECT_ID
```

3. Update scopes in config:
```yaml
# config/sheets.yml
provider_config:
  scopes:
    - "https://www.googleapis.com/auth/spreadsheets.readonly"
    - "https://www.googleapis.com/auth/drive.readonly"
```

## 5. Currency Parsing Issues

### Symptom
KPI values showing as 0 or NaN when data exists

### Diagnosis
```python
# Test currency parsing
uv run python -c "
from apps.backend.metrics import clean_currency_string
import pandas as pd

test_values = ['$1,234.56', '1234.56', '$1,234', '1234']
for val in test_values:
    cleaned = clean_currency_string(val)
    numeric = pd.to_numeric(cleaned, errors='coerce')
    print(f'{val} -> {cleaned} -> {numeric}')
"
```

### Solution
Ensure Google Sheets columns are formatted consistently:
- Use currency format: $X,XXX.XX
- Or use plain numbers: XXXX.XX

## 6. Location Switching Not Working

### Symptom
Selecting different location shows same data

### Diagnosis
```python
# Test location aliases
uv run python -c "
from apps.backend.data_providers import build_sheets_provider
provider = build_sheets_provider()

for location in ['baytown', 'humble']:
    eod_alias = provider.get_location_aliases(location, 'eod')
    print(f'{location} EOD: {eod_alias}')
"
```

### Solution
1. Verify location mapping in config/sheets.yml:
```yaml
locations:
  baytown:
    eod: "baytown_eod"
    front: "baytown_front"
  humble:
    eod: "humble_eod"
    front: "humble_front"
```

2. Clear Streamlit cache:
```python
# Add cache clear button to dashboard
if st.button("Clear Cache"):
    st.cache_data.clear()
    st.rerun()
```

## 7. Historical Data Issues

### Symptom
Historical charts showing gaps or incorrect dates

### Diagnosis
```python
# Check date parsing
uv run python -c "
from apps.backend.historical_data import HistoricalDataManager
import pandas as pd

manager = HistoricalDataManager()
test_dates = ['2025-09-24', '2025-09-22', '2025-09-21']  # Tue, Sun, Sat

for date_str in test_dates:
    date = pd.to_datetime(date_str)
    operational = manager.get_operational_date(date)
    print(f'{date_str} ({date.strftime('%a')}) -> {operational.strftime('%Y-%m-%d %a')}')
"
```

### Solution
- Ensure date columns are properly formatted
- Check for weekend data (Sunday fallback logic)
- Verify timezone consistency

## 8. Chart Display Problems

### Symptom
Charts not rendering or showing errors

### Diagnosis
```bash
# Check Plotly installation
uv pip show plotly

# Test chart generation
uv run python -c "
from apps.backend.chart_data import get_chart_data
chart_data = get_chart_data('baytown')
print('Charts available:', list(chart_data.keys()))
"
```

### Solution
1. Reinstall Plotly:
```bash
uv remove plotly
uv add plotly>=5.17
```

2. Check browser console for JavaScript errors
3. Try different browser or incognito mode

## Performance Monitoring

### Enable Debug Logging
```python
# Add to app.py
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add timing logs
import time
start = time.time()
kpis = get_all_kpis(location)
logger.debug(f"KPI calculation took {time.time() - start:.2f} seconds")
```

### Memory Usage
```bash
# Monitor memory during execution
while true; do
  ps aux | grep streamlit | grep -v grep
  sleep 5
done
```

## Emergency Procedures

### Complete Reset
```bash
# 1. Stop application
pkill -f streamlit

# 2. Clear cache
rm -rf ~/.streamlit/cache/

# 3. Reinstall dependencies
uv sync --reinstall

# 4. Restart
uv run streamlit run apps/frontend/app.py
```

### Rollback Changes
```bash
# View recent changes
git log --oneline -10

# Rollback to specific commit
git checkout <commit-hash>

# Or rollback last change
git checkout HEAD~1
```

## Getting Help

### Collect Diagnostic Information
```bash
# Generate diagnostic report
cat > diagnostic_report.txt << EOF
Date: $(date)
Python: $(python --version)
Directory: $(pwd)
Dependencies:
$(uv pip list | grep -E "streamlit|pandas|google|plotly")

Config Check:
$(ls -la config/)

Test Results:
$(uv run python scripts/print_kpis.py --location baytown 2>&1)
EOF
```

### Log Files
- Application logs: Check terminal output
- Google API logs: Google Cloud Console > Logging
- Browser logs: F12 > Console tab

### Support Channels
1. Check documentation: `docs/guides/`
2. Review test files: `tests/`
3. Contact development team with diagnostic report
