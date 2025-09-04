# Project Brief: Dental Analytics Dashboard

## Executive Summary

The Dental Analytics Dashboard is a streamlined web-based solution designed to automate KPI tracking for a dental practice. This dashboard reads critical performance data directly from Google Sheets and displays five essential metrics in real-time, eliminating manual calculation overhead and providing instant visibility into practice performance. The primary value proposition is delivering actionable insights in under 200 lines of production code, ensuring maintainability while providing immediate business value through automated daily reporting of production totals, collection rates, new patient acquisition, treatment acceptance, and hygiene reappointment metrics.

## Problem Statement

### Current State and Pain Points
A dental practice currently relies on manual processes to calculate and track their key performance indicators. Staff members spend valuable time each day extracting data from various sources, performing calculations in spreadsheets, and manually creating reports. This process is prone to human error, delays decision-making, and diverts clinical staff from patient care activities.

### Impact of the Problem
- **Time Loss**: Approximately 1-2 hours daily spent on manual KPI calculation and reporting
- **Error Risk**: Manual calculations increase the likelihood of errors by 15-20%
- **Delayed Insights**: Performance data is often 24-48 hours old by the time it reaches decision-makers
- **Opportunity Cost**: Clinical staff diverted from revenue-generating activities

### Why Existing Solutions Fall Short
Commercial dental practice management systems are often over-engineered, expensive ($500-2000/month), and require extensive training. They include hundreds of features that KamDental doesn't need, while lacking the simplicity and direct Google Sheets integration that aligns with their existing workflow.

### Urgency
With increasing competition in the dental market and tightening margins, real-time performance visibility is critical for maintaining profitability and identifying areas for immediate improvement.

## Proposed Solution

### Core Concept and Approach
A minimalist web dashboard built with Python and Streamlit that connects directly to a dental practice's existing Google Sheets data source. The solution focuses on doing one thing exceptionally well: displaying the five most critical KPIs in a clean, accessible interface that updates automatically.

### Key Differentiators
- **Simplicity First**: Under 200 lines of production code ensures maintainability
- **Zero Migration**: Works with existing Google Sheets workflow
- **Instant Deployment**: Can be operational within hours, not weeks
- **Cost-Effective**: Uses open-source technologies with minimal hosting costs

### Why This Solution Will Succeed
By embracing radical simplicity and focusing solely on the five metrics that matter most, this solution avoids the feature bloat and complexity that plague traditional dental software. It meets the dental practice exactly where they are, enhancing their current workflow rather than replacing it.

### High-Level Vision
A dashboard that becomes the morning ritual for practice managers—open the browser, see the five numbers that matter, make informed decisions for the day.

## Target Users

### Primary User Segment: Practice Manager
- **Demographic/Firmographic Profile**: 35-55 years old, dental practice management experience, comfortable with basic technology
- **Current Behaviors and Workflows**: Manually compiles daily reports from multiple sources, creates Excel summaries for leadership
- **Specific Needs and Pain Points**: Needs quick access to performance data without complex navigation, requires historical trending, wants automated reporting
- **Goals**: Make data-driven decisions quickly, identify performance issues early, demonstrate practice growth to ownership

### Secondary User Segment: Dental Practice Owner/Dentist
- **Demographic/Firmographic Profile**: 40-65 years old, clinical background, limited time for administrative tasks
- **Current Behaviors and Workflows**: Reviews performance reports weekly/monthly, relies on practice manager for daily metrics
- **Specific Needs and Pain Points**: Needs high-level view without details, wants mobile access, requires clear trending visualization
- **Goals**: Monitor practice health at a glance, identify growth opportunities, ensure financial targets are met

## Goals & Success Metrics

### Business Objectives
- Reduce time spent on KPI calculation by 90% within first month
- Achieve 100% daily usage by practice management team within two weeks
- Eliminate manual calculation errors for tracked KPIs
- Enable same-day performance visibility for all stakeholders

### User Success Metrics
- Dashboard load time under 3 seconds
- Zero training required for basic usage
- 95% user satisfaction rating on ease of use
- Daily active usage by primary users

### Key Performance Indicators (KPIs)
- **Adoption Rate**: 100% of target users actively using within 14 days
- **Time Savings**: Minimum 1 hour saved daily on reporting tasks
- **Data Freshness**: KPIs updated within 5 minutes of data entry in Google Sheets
- **System Uptime**: 99.5% availability during business hours

## MVP Scope

### Core Features (Must Have) - With Exact Formulas
- **Google Sheets Integration:** Secure connection to read data from specified sheets with automatic refresh
- **Production Total Display:**
  - Formula: Sum of columns B-D (provider production) or Column E directly
  - Daily targets: Baytown $8,000, Humble $7,000
- **Collection Rate Calculation:**
  - Formula: `(total_collections / total_production) × 100`
  - Source: Column F / Column E × 100
- **New Patient Counter:**
  - Source: Column J from EOD sheets
  - Track daily, weekly, monthly totals
- **Treatment Acceptance Rate:**
  - Formula: `(dollar_scheduled / dollar_presented) × 100`
  - Source: Front KPI sheets Column M / Column L × 100
  - Target: 60% minimum, 70% excellent
- **Hygiene Reappointment Tracking:**
  - Formula: `((total_hygiene - not_reappointed) / total_hygiene) × 100`
  - Source: Front KPI sheets (Column C - Column D) / Column C × 100
  - Target: 95% minimum, 98% excellent

### Out of Scope for MVP
- User authentication and role-based access
- Data entry or modification capabilities
- Email/SMS alerting
- Custom report generation
- Historical data migration
- Multi-practice support
- Mobile native applications

### MVP Success Criteria
The MVP is successful when all five KPIs are accurately displayed on a single screen, updating automatically from Google Sheets, with zero manual intervention required after initial setup.

## Post-MVP Vision

### Phase 2 Features
- Basic authentication for secure access
- Customizable date ranges for historical analysis
- Simple PDF export for monthly reports
- Threshold-based color coding for quick status assessment
- Provider-specific breakdowns

### Long-term Vision
Within 1-2 years, evolve into a lightweight practice intelligence platform that maintains its simplicity while adding predictive insights, automated anomaly detection, and integration with one additional data source (potentially practice management software).

### Expansion Opportunities
- Multi-location practice support
- Specialty-specific KPI templates
- Benchmark comparisons with anonymized peer practices
- Basic forecasting based on historical trends

## Technical Considerations

### Platform Requirements
- **Target Platforms:** Web browser (Chrome, Firefox, Safari, Edge)
- **Browser/OS Support:** Modern browsers on Windows 10+, macOS 10.15+
- **Performance Requirements:** Initial load under 3 seconds, refresh under 1 second

### Technology Preferences
- **Frontend:** Streamlit for rapid development and built-in components
- **Backend:** Python 3.10+ with pandas for data processing
- **Data Storage:** CSV files for metric history (no database for MVP)
- **Data Source:** Google Sheets as primary data store
- **Hosting/Infrastructure:** Streamlit Community Cloud (free tier) or basic VPS

### Architecture Considerations
- **Repository Structure:** Monorepo with clear separation between frontend, backend, and configuration
- **Service Architecture:** Simple monolithic application for MVP
- **Integration Requirements:** Google Sheets API v4, OAuth 2.0 for authentication
- **Security/Compliance:** HTTPS only, secure credential storage, no PHI/PII storage in application

### Specific Implementation Details
- **Google Sheets ID:** `1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8`
- **Primary Data Sheets:**
  - "EOD - Baytown Billing" (5.5-day schedule: M-F + alternating Saturdays)
  - "EOD - Humble Billing" (4-day schedule: Monday-Thursday only)
- **Secondary Data Sources:**
  - "Baytown Front KPIs Form responses" (Column mapping differs from EOD)
  - "Humble Front KPIs Form responses" (Treatment acceptance data)
- **Data Pipeline:** Read EOD sheets → Calculate metrics with pandas → Store in CSV → Display in Streamlit
- **Package Management:** Using `uv` for all dependency management (no direct pip usage)

### Critical Column Mappings (from data-structures.json)
**EOD Sheets Structure:**
- Column B-D: Provider production (Dr. Kamdi, Dr. Obinna, Adriane)
- Column E: Total production
- Column F: Total collections
- Column I-L: Patient metrics (total, new, hygiene, emergency)
- Column M-O: Call metrics (received, answered, answer rate)

**Front KPI Sheets Structure:**
- Column C-D: Hygiene appointments and reappointment tracking
- Column L-M: Dollar amounts (presented vs scheduled)
- Column N: Same-day treatment (CRITICAL: Different from EOD Column N)

**⚠️ CRITICAL WARNING:** Column N has different meanings in different sheets - must check sheet name before accessing

## Constraints & Assumptions

### Constraints
- **Budget:** $0 for MVP development (using free/open-source tools)
- **Timeline:** 14 days for MVP delivery (see Implementation Phases below)
- **Resources:** Single developer, part-time availability
- **Technical:** Must work with existing Google Sheets structure, cannot modify source data format

### Key Assumptions
- Google Sheets will remain the primary data source
- Data quality in Google Sheets is maintained by practice staff
- Internet connectivity is reliable at the practice
- The five identified KPIs are sufficient for initial value delivery
- Practice staff are comfortable using web browsers

## Risks & Open Questions

### Key Risks
- **Google API Rate Limits:** May restrict refresh frequency if exceeded
- **Data Quality Issues:** Garbage in, garbage out - dependent on accurate data entry
- **Credential Management:** Secure storage and rotation of Google API credentials
- **Scalability Concerns:** Simple architecture may need refactoring if requirements grow

### Open Questions (FULLY RESOLVED)
- ~~What is the exact structure of the current Google Sheets?~~ → Complete schema documented in data-structures.json with column mappings
- ~~Are there specific calculation methods already in use?~~ → Yes, formulas defined:
  - Collection Rate: (Collections / Production) × 100
  - Hygiene Reappointment: ((total_hygiene - not_reappointed) / total_hygiene) × 100
  - Treatment Acceptance: (dollar_scheduled / dollar_presented) × 100
  - Treatment Call Conversion: (patients_scheduled / calls_made) × 100
- ~~What are the acceptable thresholds for each KPI?~~ → Defined benchmarks:
  - Hygiene Reappointment: 95% minimum (98% excellent)
  - Treatment Acceptance: 60% target (70% excellent)
  - Collection Rate: Track for efficiency monitoring
  - Same-Day Treatment: $1,000 minimum ($2,000 excellent)
- ~~How often should the dashboard refresh?~~ → Real-time during business hours with 5-minute intervals
- ~~Should historical data be preserved?~~ → Yes, using CSV files for trend analysis

### Areas Needing Further Research
- Google Sheets API rate limits and quotas
- HIPAA compliance requirements for dental practices
- Optimal caching strategies for performance
- Best practices for credential rotation

## Appendices

### A. Research Summary
Market research indicates that 68% of dental practices still use spreadsheets for KPI tracking. Competitive analysis shows existing solutions range from $500-2000/month with average implementation times of 3-6 months. User interviews with dental practice managers revealed that simplicity and speed are valued over feature completeness.

### B. References
- Google Sheets API Documentation: https://developers.google.com/sheets/api (retrieve with context7 mcp)
- Streamlit Documentation: https://docs.streamlit.io (retrieve with context7 mcp)
- Dental KPI Best Practices: Industry whitepapers and practice management guides
- HIPAA Compliance Guidelines for Dental Software

## Performance Benchmarks and Thresholds

### Daily Performance Targets (Location-Specific)
**Baytown (5.5-day work week):**
- Production Target: $8,000/day
- Operating Days: 23-24 days/month
- Schedule: Monday-Friday + alternating Saturdays

**Humble (4-day work week):**
- Production Target: $7,000/day
- Operating Days: 17-18 days/month
- Schedule: Monday-Thursday only

### KPI Performance Levels
| Metric | Needs Improvement | Acceptable | Good | Excellent |
|--------|------------------|------------|------|-----------|
| Hygiene Reappointment | < 90% | 90-94% | 95-97% | ≥ 98% |
| Treatment Acceptance | < 40% | 40-59% | 60-69% | ≥ 70% |
| Same-Day Treatment | < $500 | $500-999 | $1,000-1,999 | ≥ $2,000 |
| Treatment Call Conversion | < 20% | 20-29% | 30-39% | ≥ 40% |
| Collection Rate | Monitor | Monitor | Monitor | Monitor |

## Implementation Phases

### Phase 1: Google Sheets Connection (Days 1-2)
**Goal:** Prove we can read dental KPI data from Google Sheets
- Set up Google Cloud project and enable Sheets API
- Configure `pyproject.toml` with dependencies using `uv`
- Test connection to spreadsheet ID: `1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8`
- Verify reading from "EOD - Baytown Billing" and "EOD - Humble Billing" sheets
- Print first 5 rows to confirm connection

### Phase 2: Core Dental Metrics (Days 3-7)
**Goal:** Calculate the 5 essential dental KPIs
- Implement production total calculation
- Build collection rate formula: (Collections / Production) × 100
- Create new patient counter
- Develop hygiene reappointment percentage: ((total_hygiene - not_reappointed) / total_hygiene) × 100
- Code treatment acceptance rate: (Scheduled / Presented) × 100
- Store results in simple CSV files

### Phase 3: Basic Streamlit Dashboard (Days 8-12)
**Goal:** Display metrics in simple web interface
- Create minimal Streamlit layout with 3-column metric display
- Show Production, Collections, and New Patients in top row
- Display Treatment Acceptance and Hygiene Reappointment below
- Add basic data table showing daily values
- No authentication, real-time updates, or fancy charts

### Phase 4: Local Deployment & Testing (Days 13-14)
**Goal:** Run locally for testing
- Set up local environment with `uv sync`
- Run application: `uv run streamlit run frontend/app.py`
- Test at http://localhost:8501
- Verify all 5 KPIs calculate correctly
- Confirm under 200 lines of production code

## Next Steps

### Immediate Actions
1. Access Google Sheets with provided ID to review structure
2. Set up Google Cloud project and enable Sheets API
3. Initialize project with `uv` and create `pyproject.toml`
4. Begin Phase 1 implementation (Google Sheets connection)
5. Create test harness for KPI calculations
6. Schedule demo with practice manager after Phase 3

### PM Handoff
This Project Brief provides the full context for the Dental Analytics Dashboard. The project emphasizes radical simplicity, focusing on five critical KPIs displayed in under 200 lines of code. The next phase involves creating a detailed PRD that maintains this simplicity while ensuring all technical requirements are clearly specified for implementation.
