# Simple Dental Analytics Dashboard - Bare Bones Specification

## Phase 1: Google Sheets Connection (2 days)
**Goal**: Prove we can read dental KPI data from Google Sheets

### Step 1: Google API Setup (pyproject)
- Use `uv` for dependency management (no direct `pip`).
- Declare all dependencies in `pyproject.toml`.

```toml
# pyproject.toml (excerpt)
[project]
name = "dental-analytics"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
  "google-auth>=2.23",
  "google-api-python-client>=2.103",
  "pandas>=2.1",
  "streamlit>=1.30",
]
```

### Step 2: Test Connection
- Use spreadsheet ID: `1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8`
- Read these sheets first:
  - "EOD - Baytown Billing" 
  - "EOD - Humble Billing"
- Print first 5 rows to verify connection works

## Phase 2: Core Dental Metrics (5 days)
**Goal**: Calculate the 5 essential dental KPIs

### Essential Metrics Only
```python
# Core calculations
production_total = sum(provider_productions)
collection_rate = (collections / production) * 100
new_patient_count = count(new_patients)
hygiene_reappointment = ((total_hygiene - not_reappointed) / total_hygiene) * 100
treatment_acceptance = (scheduled / presented) * 100
```

### Data Pipeline
1. Read EOD sheets daily
2. Calculate metrics with pandas
3. Store in simple CSV file
4. No database, no complexity

## Phase 3: Basic Streamlit Dashboard (5 days)
**Goal**: Display metrics in simple web interface (frontend)

### Minimal Components
```python
import streamlit as st
import pandas as pd
# Data provided by backend modules
# from backend.metrics import production, collections, new_patients, daily_data

# Simple layout
st.title("Dental KPIs")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Production", f"${production:,.0f}")
with col2:
    st.metric("Collections", f"${collections:,.0f}")
with col3:
    st.metric("New Patients", new_patients)

# Basic data table
st.dataframe(daily_data)
```

### No Extras
- No user authentication
- No real-time updates
- No fancy charts
- Just numbers on screen

## Phase 4: Local Deployment (2 days)
**Goal**: Run locally for testing

### Simple Setup (uv)
```bash
# Install/sync dependencies from pyproject
uv sync

# Run locally via uv (frontend entrypoint)
uv run streamlit run frontend/app.py
```

### Access
- Local URL: http://localhost:8501
- No Docker yet
- No production deployment
- Just local testing

## File Structure
```
dental-analytics/
├── frontend/
│   └── app.py             # Streamlit app (100 lines max)
├── backend/
│   ├── __init__.py
│   ├── sheets_reader.py   # Google Sheets connection (50 lines)
│   └── metrics.py         # Calculate KPIs (50 lines)
├── config/
│   └── credentials.json   # Google API credentials
├── pyproject.toml         # uv project + dependencies
└── uv.lock                # uv lockfile
```

## Benefits of This Separation
- **Clear responsibilities**: Backend: "How do we get and process data?" Frontend: "How do we show data to users?"
- **Reusability**: Backend services can be used in other applications; Frontend components can be reused across dashboards.

## The 5 Core KPIs to Track

1. **Daily Production**: Total $ produced by all providers
2. **Collection Rate**: (Collections / Production) × 100
3. **New Patients**: Count of new patients
4. **Treatment Acceptance**: ($ Scheduled / $ Presented) × 100
5. **Hygiene Reappointment**: Percentage reappointed

## Success Criteria
- **It connects**: Can read Google Sheets data
- **It calculates**: Shows the 5 KPIs correctly
- **It displays**: Numbers visible on screen
- **It's simple**: Under 200 lines of code total

## What This Is NOT
- Not a production system
- Not using AI/Claude API
- Not sending emails
- Not real-time
- Not pretty

## Implementation Order
1. **Day 1-2**: Get Google Sheets connection working
2. **Day 3-7**: Calculate metrics with pandas
3. **Day 8-12**: Build Streamlit interface
4. **Day 13-14**: Test locally

## Next Steps After MVP
Only after basic system works:
1. Add more metrics
2. Add charts/visualizations
3. Deploy to Proxmox
4. Add historical tracking
5. Consider automation

**Bottom Line**: Get 5 numbers on screen from Google Sheets. Everything else comes later.
