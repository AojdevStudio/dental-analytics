# Epic 1: Complete Dental Analytics Dashboard

**Epic Goal:** Establish the complete project foundation including Google Sheets integration, backend KPI calculation logic, and Streamlit dashboard display. This epic delivers a fully functional dashboard showing all five critical dental KPIs with automatic data refresh, meeting the practice's need for instant visibility into daily performance metrics.

## Story 1.1: Project Foundation and Google Sheets Connection

**As a** developer,  
**I want** to set up the project structure and establish Google Sheets API connection,  
**so that** the application has a solid foundation and can access practice data.

**Acceptance Criteria:**
1. Project repository initialized with proper directory structure (backend/, frontend/, config/)
2. pyproject.toml configured with all required dependencies using uv
3. Google Cloud project created with Sheets API enabled
4. Service account credentials generated and stored in config/credentials.json
5. Backend module sheets_reader.py successfully connects to spreadsheet ID `1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8`
6. Function can read and return raw data from "EOD - Baytown Billing" sheet as pandas DataFrame
7. Basic error handling returns None with logged error message if connection fails

## Story 1.2: Production and Collection KPI Calculations

**As a** practice manager,  
**I want** to see daily production totals and collection rates calculated from EOD sheets,  
**so that** I can monitor practice financial performance.

**Acceptance Criteria:**
1. metrics.py module created with calculate_production_total() function
2. Production total correctly sums columns B-D or reads column E from EOD sheets
3. calculate_collection_rate() function implements formula: (Column F / Column E) × 100
4. Both functions handle missing or zero data gracefully
5. Functions return numeric values or None if data unavailable
6. Manual verification shows calculations match expected values from sample data

## Story 1.3: Patient and Treatment KPI Calculations

**As a** practice manager,  
**I want** to see new patient counts and treatment acceptance rates,  
**so that** I can track patient acquisition and treatment conversion.

**Acceptance Criteria:**
1. calculate_new_patients() function extracts count from Column J in EOD sheets
2. calculate_treatment_acceptance() implements formula: (Column M / Column L) × 100 from Front KPI sheets
3. Functions handle sheet name differences correctly (EOD vs Front KPI sheets)
4. Treatment acceptance calculation handles division by zero cases
5. Both functions integrated into metrics.py module
6. Returns structured dictionary with metric names and values

## Story 1.4: Hygiene Reappointment KPI Calculation

**As a** practice manager,  
**I want** to see hygiene reappointment rates,  
**so that** I can ensure patients are maintaining regular preventive care schedules.

**Acceptance Criteria:**
1. calculate_hygiene_reappointment() implements formula: ((Column C - Column D) / Column C) × 100
2. Function reads from Front KPI sheets specifically
3. Handles cases where total hygiene count is zero
4. Integrates with existing metrics.py module
5. Complete get_all_kpis() function returns all 5 metrics in single call
6. Manual verification confirms 95%+ rates flagged as good, below 90% as concerning

## Story 1.5: Streamlit Dashboard Display

**As a** practice manager,  
**I want** to view all five KPIs on a single dashboard screen,  
**so that** I can quickly assess practice performance without navigation.

**Acceptance Criteria:**
1. frontend/app.py created using Streamlit framework
2. Dashboard displays all 5 KPIs using st.metric() components
3. Kam Dental brand colors applied (Navy #142D54, Teal #007E9E)
4. All metrics visible without scrolling on 1920x1080 resolution
5. Dashboard refreshes data on page load
6. "Data Unavailable" shown for any metrics that fail to load
7. Total production code across all files remains under 200 lines
8. Dashboard loads in under 3 seconds on initial visit
