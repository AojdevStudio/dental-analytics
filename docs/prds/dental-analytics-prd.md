---
title: "Dental Analytics Dashboard PRD"
description: "Product Requirements Document for KamDental's automated KPI dashboard displaying 5 critical metrics from Google Sheets."
category: "Product Management"
subcategory: "Requirements Documentation"
product_line: "Dental Analytics Dashboard"
audience: "Development Team, Stakeholders"
status: "Draft"
author: "AOJDevStudio"
created_date: "2025-09-04"
last_updated: "2025-09-04"
tags:
  - prd
  - dental-analytics
  - mvp
  - dashboard
  - kpi-tracking
---

# Dental Analytics Dashboard Product Requirements Document (PRD)

## Goals and Background Context

### Goals
- Eliminate 90% of manual KPI calculation time for dental practice staff
- Display 5 critical dental KPIs in real-time from Google Sheets data
- Achieve zero-training deployment with immediate user adoption
- Deliver complete solution in under 200 lines of production code
- Enable same-day visibility into practice performance metrics

### Background Context

KamDental practice currently loses 1-2 hours daily to manual KPI calculations from spreadsheets, creating delays in decision-making and increasing error risk. With dental practices facing tightening margins and increased competition, real-time performance visibility has become critical. This solution leverages the practice's existing Google Sheets workflow to automate the calculation and display of five essential metrics: daily production totals, collection rates, new patient counts, treatment acceptance rates, and hygiene reappointment tracking.

Unlike expensive practice management systems that cost $500-2000/month and require extensive training, this minimalist approach focuses solely on displaying the metrics that matter most. By working directly with the practice's existing data source and maintaining radical simplicity, we avoid feature bloat while delivering immediate value.

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-09-04 | 1.0 | Initial PRD creation from Project Brief | John (PM) |

## Requirements

### Functional Requirements

**FR1:** System must authenticate and connect to Google Sheets API using service account credentials stored securely in config/credentials.json

**FR2:** System must read data from spreadsheet ID `1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8` with refresh triggered 3-4 times per 24-hour period (morning, midday, end-of-day)

**FR3:** System must calculate and display Daily Production Total by summing columns B-D (provider production) or reading Column E directly from EOD sheets

**FR4:** System must calculate and display Collection Rate using formula `(total_collections / total_production) × 100` from Column F and Column E

**FR5:** System must display New Patient Count from Column J in EOD sheets

**FR6:** System must calculate and display Treatment Acceptance Rate using formula `(dollar_scheduled / dollar_presented) × 100` from Front KPI sheets Columns M and L

**FR7:** System must calculate and display Hygiene Reappointment Rate using formula `((total_hygiene - not_reappointed) / total_hygiene) × 100` from Front KPI sheets Columns C and D

**FR8:** System must display all five KPIs on a single screen without scrolling, using Streamlit's metric components

### Non-Functional Requirements

**NFR1:** Dashboard must load completely in under 3 seconds on initial page load

**NFR2:** KPI calculations must complete in under 1 second when triggered

**NFR3:** Total production code must not exceed 200 lines across all Python files

**NFR4:** System must handle Google Sheets API rate limits gracefully, staying well within free tier quotas

**NFR5:** System must work on modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)

**NFR6:** No PHI/PII data may be stored in the application; only aggregate metrics

**NFR7:** System must require zero user training for basic dashboard viewing

**NFR8:** All dependencies must be manageable through `uv` package manager with lockfile

## User Interface Design Goals

### Overall UX Vision
A single-screen dashboard that displays five critical dental KPIs with absolute clarity. Zero navigation, zero complexity - open the browser, see your numbers, make decisions. The interface maintains Kam Dental's professional yet approachable tone while letting metrics speak directly to practice managers.

### Key Interaction Paradigms
- **Read-only display** - No interactive elements, buttons, or inputs in MVP
- **Automatic refresh** - Data updates 3-4 times daily without user action
- **Glance-able metrics** - All five KPIs visible simultaneously without scrolling
- **Clear visual hierarchy** - Most important metrics (Production, Collections) prominently positioned

### Core Screens and Views
- **Main Dashboard** - Single screen displaying all 5 KPIs in metric cards
- **Error State** - Simple "Data Unavailable" message if connection fails

### Accessibility: None
MVP focuses on functional delivery; accessibility enhancements deferred to Phase 2

### Branding
Apply Kam Dental brand colors to Streamlit components:
- **Primary Navy (#142D54)** for headers and metric labels
- **Teal Blue (#007E9E)** for positive metric indicators
- **Emergency Red (#BB0A0A)** for metrics below threshold
- **Roboto font family** for all text elements
- Clean, professional medical aesthetic maintaining brand's patient-centric, trustworthy tone

### Target Device and Platforms: Web Responsive
Desktop-first design optimized for practice office computers, with basic responsive layout for tablets. Mobile optimization not required for MVP.

## Technical Assumptions

### Repository Structure: Monorepo
Single repository containing all frontend, backend, and configuration files for the dental analytics dashboard with clear separation of concerns.

### Service Architecture
**Modular monolithic application** - Clean separation between backend logic (data fetching, KPI calculations) and frontend presentation (Streamlit UI). Backend modules are framework-agnostic, allowing future frontend swaps without touching business logic.

### Testing Requirements
**Manual testing only for MVP** - Given the 200-line constraint and read-only nature, formal test suites deferred to post-MVP. Manual verification of:
- Google Sheets connection
- KPI calculation accuracy against known values
- Dashboard display on target browsers

### Additional Technical Assumptions and Requests

- **Language:** Python 3.10+ exclusively
- **Frontend Framework:** Streamlit for MVP (replaceable - see architecture notes)
- **Data Processing:** pandas for all KPI calculations
- **API Integration:** Google Sheets API v4 with OAuth 2.0 service account
- **Package Management:** uv for all dependencies (no pip/poetry/conda)
- **Configuration:** credentials.json in config/ directory for Google API auth
- **Deployment:** Streamlit Community Cloud (free tier) or local execution
- **Data Storage:** No database; calculations performed on-demand from Google Sheets
- **Caching:** Framework-agnostic caching strategy in backend layer
- **Error Handling:** Backend returns structured error responses; frontend displays appropriately
- **Logging:** Basic console output only (no formal logging framework)
- **Version Control:** Git with .gitignore for credentials

**Critical Architecture Decision - Separation of Concerns:**
- **backend/** directory: Pure Python modules with no Streamlit dependencies
  - `data_providers.py`: Google Sheets API connection and data fetching
  - `metrics.py`: KPI calculation logic returning structured data
- **frontend/** directory: Presentation layer (Streamlit for MVP)
  - `app.py`: UI components that call backend modules
- Backend modules return standard Python dictionaries/DataFrames, making them reusable with any frontend framework (Next.js, Flask, FastAPI, etc.)

## Epic List

**Epic 1: Complete Dental Analytics Dashboard** - Establish project foundation and deliver all five KPI displays with Google Sheets integration

## Epic 1: Complete Dental Analytics Dashboard

**Epic Goal:** Establish the complete project foundation including Google Sheets integration, backend KPI calculation logic, and Streamlit dashboard display. This epic delivers a fully functional dashboard showing all five critical dental KPIs with automatic data refresh, meeting the practice's need for instant visibility into daily performance metrics.

### Story 1.1: Project Foundation and Google Sheets Connection

**As a** developer,
**I want** to set up the project structure and establish Google Sheets API connection,
**so that** the application has a solid foundation and can access practice data.

**Acceptance Criteria:**
1. Project repository initialized with proper directory structure (backend/, frontend/, config/)
2. pyproject.toml configured with all required dependencies using uv
3. Google Cloud project created with Sheets API enabled
4. Service account credentials generated and stored in config/credentials.json
5. Backend module data_providers.py successfully connects to spreadsheet ID `1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8`
6. Function can read and return raw data from "EOD - Baytown Billing" sheet as pandas DataFrame
7. Basic error handling returns None with logged error message if connection fails

### Story 1.2: Production and Collection KPI Calculations

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

### Story 1.3: Patient and Treatment KPI Calculations

**As a** practice manager,
**I want** to see new patient counts and treatment acceptance rates,
**so that** I can track patient acquisition and treatment conversion.

**Acceptance Criteria:**
1. calculate_new_patients() function extracts count from Column J in EOD sheets
2. calculate_case_acceptance() implements formula: (Column M / Column L) × 100 from Front KPI sheets
3. Functions handle sheet name differences correctly (EOD vs Front KPI sheets)
4. Treatment acceptance calculation handles division by zero cases
5. Both functions integrated into metrics.py module
6. Returns structured dictionary with metric names and values

### Story 1.4: Hygiene Reappointment KPI Calculation

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

### Story 1.5: Streamlit Dashboard Display

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

## Checklist Results Report

_To be completed after PRD review_

## Next Steps

### UX Expert Prompt
Review the Dental Analytics Dashboard PRD and create a minimal UI design that displays 5 KPIs using Kam Dental brand guidelines. Focus on single-screen visibility with zero navigation complexity.

### Architect Prompt
Create technical architecture for the Dental Analytics Dashboard based on this PRD. Implement modular backend with framework-agnostic Python modules and Streamlit frontend, staying under 200 lines total production code.
