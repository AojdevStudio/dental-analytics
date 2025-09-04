# Technical Implementation Checklist - Dental Analytics Dashboard

## 🎯 Pre-Development Setup

### Environment Configuration
- [ ] Install Python 3.10+ on development machine
- [ ] Install `uv` package manager
- [ ] Create project directory structure matching spec
- [ ] Initialize git repository on development branch

### Google Cloud Setup
- [ ] Create Google Cloud project
- [ ] Enable Google Sheets API v4
- [ ] Create service account credentials
- [ ] Download credentials.json to `config/` directory
- [ ] Set appropriate file permissions (read-only)
- [ ] Test API access with spreadsheet ID: `1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8`

## 📋 Phase 1: Google Sheets Connection (Days 1-2)

### Project Configuration
- [ ] Create `pyproject.toml` with dependencies:
  - [ ] google-auth>=2.23
  - [ ] google-api-python-client>=2.103
  - [ ] pandas>=2.1
  - [ ] streamlit>=1.30
- [ ] Run `uv sync` to install dependencies
- [ ] Create `backend/__init__.py`
- [ ] Create `backend/sheets_reader.py` (50 lines max)

### Connection Testing
- [ ] Implement Google Sheets authentication
- [ ] Connect to spreadsheet using provided ID
- [ ] Read "EOD - Baytown Billing" sheet
- [ ] Read "EOD - Humble Billing" sheet
- [ ] Print first 5 rows from each sheet
- [ ] Verify column mappings match data-structures.json

### Critical Validation
- [ ] ⚠️ Implement sheet name checking for Column N conflict
- [ ] Verify Column N in EOD sheets = calls_answered (integer)
- [ ] Verify Column N in Front KPI sheets = same_day_treatment (currency)
- [ ] Create validation function for column type checking

## 📊 Phase 2: Core Dental Metrics (Days 3-7)

### Metrics Module Setup
- [ ] Create `backend/metrics.py` (50 lines max)
- [ ] Import pandas and sheets_reader module
- [ ] Set up CSV storage directory

### KPI Implementations

#### Production Total
- [ ] Read Column E from EOD sheets (total_production)
- [ ] Alternative: Sum columns B, C, D (provider production)
- [ ] Validate against daily targets:
  - [ ] Baytown: $8,000/day
  - [ ] Humble: $7,000/day

#### Collection Rate
- [ ] Formula: `(Column F / Column E) × 100`
- [ ] Implement calculation function
- [ ] Handle division by zero cases
- [ ] Format as percentage with 1 decimal place

#### New Patient Count
- [ ] Read Column J from EOD sheets
- [ ] Implement daily counter
- [ ] Add weekly aggregation
- [ ] Add monthly aggregation

#### Treatment Acceptance Rate
- [ ] Read Front KPI sheets (NOT EOD sheets)
- [ ] Formula: `(Column M / Column L) × 100`
- [ ] Validate Column L = dollar_presented (currency)
- [ ] Validate Column M = dollar_scheduled (currency)
- [ ] Check against thresholds:
  - [ ] 60% minimum
  - [ ] 70% excellent

#### Hygiene Reappointment Rate
- [ ] Read Front KPI sheets columns C and D
- [ ] Formula: `((Column C - Column D) / Column C) × 100`
- [ ] Validate Column C = total_hygiene_appointments
- [ ] Validate Column D = patients_not_reappointed
- [ ] Check against thresholds:
  - [ ] 95% minimum
  - [ ] 98% excellent

### Data Storage
- [ ] Implement CSV writer for historical data
- [ ] Create daily metrics CSV structure
- [ ] Add timestamp to each record
- [ ] Test data persistence

## 🖥️ Phase 3: Streamlit Dashboard (Days 8-12)

### Frontend Setup
- [ ] Create `frontend/app.py` (100 lines max)
- [ ] Import streamlit and backend modules
- [ ] Set page configuration and title

### Dashboard Layout
- [ ] Create title: "Dental KPIs"
- [ ] Implement 3-column layout for top metrics:
  - [ ] Column 1: Production (currency format)
  - [ ] Column 2: Collections (currency format)
  - [ ] Column 3: New Patients (integer)
- [ ] Add second row for additional metrics:
  - [ ] Treatment Acceptance (percentage)
  - [ ] Hygiene Reappointment (percentage)
- [ ] Add basic data table showing daily values

### Visual Indicators
- [ ] Color code metrics based on performance levels:
  - [ ] Red: Needs Improvement
  - [ ] Yellow: Acceptable
  - [ ] Green: Good
  - [ ] Blue: Excellent
- [ ] Add trend arrows (up/down/neutral)
- [ ] Display location-specific targets

## 🚀 Phase 4: Local Deployment & Testing (Days 13-14)

### Local Testing
- [ ] Run `uv sync` to ensure all dependencies installed
- [ ] Execute: `uv run streamlit run frontend/app.py`
- [ ] Access http://localhost:8501
- [ ] Verify dashboard loads within 3 seconds

### Functional Testing
- [ ] Test all 5 KPIs display correctly
- [ ] Verify currency formatting ($X,XXX.XX)
- [ ] Verify percentage formatting (XX.X%)
- [ ] Test refresh functionality (5-minute intervals)
- [ ] Validate against sample data from sheets

### Code Validation
- [ ] Count total lines of production code
- [ ] Verify under 200 lines total:
  - [ ] frontend/app.py ≤ 100 lines
  - [ ] backend/sheets_reader.py ≤ 50 lines
  - [ ] backend/metrics.py ≤ 50 lines
- [ ] Remove any commented code
- [ ] Remove debug print statements

## ✅ Acceptance Criteria

### Must Have (MVP)
- [ ] Connects to Google Sheets successfully
- [ ] Displays 5 KPIs accurately
- [ ] Updates data within 5 minutes of sheet changes
- [ ] Loads in under 3 seconds
- [ ] Under 200 lines of production code
- [ ] No authentication required
- [ ] No database dependencies

### Performance Benchmarks Met
- [ ] Production tracking by location
- [ ] Collection rate calculation working
- [ ] New patient count accurate
- [ ] Treatment acceptance from Front KPI sheets
- [ ] Hygiene reappointment percentage correct

### Data Integrity
- [ ] Column N conflict handled correctly
- [ ] Location-specific schedules recognized
- [ ] CSV storage functioning
- [ ] No data type mismatches

## 🐛 Common Issues & Solutions

### Google Sheets API Issues
- **Rate Limiting**: Implement exponential backoff
- **Authentication Errors**: Verify credentials.json path
- **Permission Denied**: Check service account permissions

### Data Issues
- **Column Mismatch**: Always check sheet name first
- **Empty Cells**: Handle None/NaN values gracefully
- **Type Errors**: Validate data types before calculations

### Streamlit Issues
- **Slow Loading**: Cache data appropriately
- **Layout Breaking**: Test on different screen sizes
- **Refresh Not Working**: Check timer implementation

## 📝 Post-MVP Considerations

### Future Enhancements (NOT for MVP)
- [ ] User authentication
- [ ] Historical trending charts
- [ ] Email alerts for threshold breaches
- [ ] Multi-practice support
- [ ] Mobile responsive design
- [ ] PDF report generation

### Technical Debt to Track
- [ ] Error handling improvements
- [ ] Logging implementation
- [ ] Unit test coverage
- [ ] Documentation updates
- [ ] Performance optimization

## 🎯 Definition of Done

A task is complete when:
1. Code works as specified
2. No errors in console
3. Meets line count limits
4. Data displays correctly
5. Performance targets met
6. CSV storage verified
7. Code is clean (no comments, no debug statements)
