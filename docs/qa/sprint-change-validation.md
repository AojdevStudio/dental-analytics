---
title: "Sprint Change QA Validation Guide"
description: "Comprehensive QA validation guide for daily KPI calculations and dual-location support fixes."
category: "Quality Assurance"
subcategory: "Sprint Validation"
product_line: "Dental Analytics Dashboard"
audience: "QA Team"
status: "Active"
author: "AOJDevStudio"
created_date: "2025-09-05"
last_updated: "2025-09-05"
tags:
  - qa-validation
  - sprint-change
  - kpi-calculations
  - dual-location
---

# Sprint Change QA Validation Guide

## Overview

This document provides comprehensive QA validation procedures for the Sprint Change that implemented:
1. **Daily KPI Calculations**: Fixed aggregated totals to show daily values only
2. **Dual-Location Support**: Added Baytown and Humble location tabs
3. **Latest Date Filtering**: All KPIs now use most recent date's data

## Critical Changes Made

### 1. Daily vs Aggregated KPI Calculations

**BEFORE (Incorrect)**: KPIs showed aggregated totals across all dates
**AFTER (Correct)**: KPIs show daily values from the most recent date only

**Implementation**: Added `_get_latest_entry()` helper function that:
- Identifies the most recent date in the dataset
- Filters all calculations to use only that date's data
- Returns single-day values instead of cumulative totals

### 2. Dual-Location Architecture

**BEFORE**: Single location (Baytown only)
**AFTER**: Dual location support with tabbed interface

**Implementation**:
- `get_baytown_kpis()` function for Baytown location
- `get_humble_kpis()` function for Humble location
- `get_all_kpis()` wrapper returning nested location structure
- Frontend tabs for "📍 Baytown" and "📍 Humble"

### 3. Enhanced Data Source Mapping

**Baytown Data Sources**:
- EOD Data: "EOD - Baytown Billing!A:S"
- Front KPI Data: "Baytown Front KPIs Form responses!A:S"

**Humble Data Sources**:
- EOD Data: "EOD - Humble Billing!A:S"
- Front KPI Data: "Humble Front KPIs Form responses!A:S"

## Expected KPI Values and Formulas

### Production Total (Daily)
**Formula**: `I + J + K` (Latest Date Only)
- **Column I**: Total Production Today
- **Column J**: Adjustments Today  
- **Column K**: Write-offs Today
- **Expected Range**: $5,000 - $15,000 daily
- **Validation**: Should show single day value (e.g., $6,450 for 9/4), not cumulative

### Collection Rate (Daily)
**Formula**: `(L + M + N) / (I + J + K) × 100` (Latest Date Only)
- **Numerator**: Patient Income + Insurance Income + Adjustment Offset
- **Denominator**: Total Production + Adjustments + Write-offs
- **Expected Range**: 75% - 95%
- **Validation**: Should calculate from same-day values only

### New Patients (Monthly Total)
**Formula**: `Column S` (Latest Date Only)
- **Column S**: New Patients - Total Month to Date
- **Expected Range**: 5 - 50 per month
- **Validation**: Should show month-to-date total from latest entry

### Treatment Acceptance (Percentage)
**Formula**: `Column R` (Latest Date Only)
- **Column R**: Cases Accepted (Percentage)
- **Expected Range**: 60% - 85%
- **Validation**: Pre-calculated percentage from latest form response

### Hygiene Reappointment (Percentage)
**Formula**: `((Total - Not Reappointed) / Total) × 100` (Latest Date Only)
- **Total**: Total hygiene Appointments (Column)
- **Not Reappointed**: Number of patients NOT reappointed
- **Expected Range**: 85% - 95%
- **Validation**: Should calculate from latest date's data only

## QA Test Scenarios

### Test Scenario 1: Daily Production Validation
**Purpose**: Verify production shows daily values, not aggregated totals

**Steps**:
1. Access dashboard at http://localhost:8501
2. Select Baytown tab
3. Check Daily Production value
4. Manually verify against Google Sheets latest date entry
5. Switch to Humble tab and repeat

**Expected Results**:
- Production value matches latest date's I+J+K columns
- Value is reasonable daily amount ($5K-$15K)
- Value is NOT a large cumulative total ($50K+)

**Pass Criteria**: ✅ Daily production matches manual calculation from latest date
**Fail Criteria**: ❌ Production shows aggregated total or incorrect calculation

### Test Scenario 2: Latest Date Filtering
**Purpose**: Ensure all KPIs use most recent date's data

**Steps**:
1. Identify the latest date in Google Sheets data
2. Manually calculate all 5 KPIs for that specific date
3. Compare dashboard values to manual calculations
4. Verify no data from previous dates is included

**Expected Results**:
- All KPIs reflect latest date only
- Collection rate uses same-day production and collections
- Treatment acceptance from latest form submission
- Hygiene reappointment from latest date's data

**Pass Criteria**: ✅ All KPIs match manual calculations from latest date
**Fail Criteria**: ❌ Any KPI includes data from multiple dates

### Test Scenario 3: Dual-Location Display
**Purpose**: Verify both locations display correctly with independent data

**Steps**:
1. Load dashboard
2. Verify both "📍 Baytown" and "📍 Humble" tabs are present
3. Click Baytown tab, record all KPI values
4. Click Humble tab, record all KPI values
5. Verify values are different (independent calculations)
6. Verify both locations show all 5 KPIs or "Data Unavailable"

**Expected Results**:
- Two distinct tabs with location-specific icons
- Different KPI values between locations (unless coincidentally same)
- All 5 KPIs displayed in both tabs
- Consistent layout and formatting

**Pass Criteria**: ✅ Both locations display independently with correct data
**Fail Criteria**: ❌ Missing tabs, identical data, or layout inconsistencies

### Test Scenario 4: Error Handling Validation
**Purpose**: Verify graceful handling of missing or invalid data

**Steps**:
1. Test with valid credentials and data access
2. Test behavior when Google Sheets is temporarily unavailable
3. Verify "Data Unavailable" displays for failed metrics
4. Ensure application doesn't crash on data errors

**Expected Results**:
- Successful metrics display actual values
- Failed metrics show "Data Unavailable" text
- No application crashes or error popups
- User-friendly error messages

**Pass Criteria**: ✅ Graceful error handling with "Data Unavailable" display
**Fail Criteria**: ❌ Application crashes, blank displays, or technical error messages

### Test Scenario 5: Formula Accuracy Validation
**Purpose**: Verify each KPI calculation matches business requirements

**Manual Calculation Steps**:

**Production Total**:
1. Find latest date in "EOD - Baytown Billing" sheet
2. Add: Column I + Column J + Column K for that date
3. Compare to dashboard value

**Collection Rate**:
1. Find latest date in EOD sheet
2. Calculate: (Column L + Column M + Column N) / (Column I + Column J + Column K) × 100
3. Compare to dashboard percentage

**New Patients**:
1. Find latest entry in EOD sheet
2. Read Column S value directly
3. Compare to dashboard integer

**Treatment Acceptance**:
1. Find latest entry in "Baytown Front KPIs Form responses"
2. Read Column R percentage directly
3. Compare to dashboard percentage

**Hygiene Reappointment**:
1. Find latest entry in Front KPIs sheet
2. Calculate: ((Total Hygiene - Not Reappointed) / Total Hygiene) × 100
3. Compare to dashboard percentage

**Pass Criteria**: ✅ All formulas match manual calculations within 0.1%
**Fail Criteria**: ❌ Any calculation differs from manual verification

## Acceptance Criteria Validation

### Sprint Change Acceptance Criteria

| Criterion | Status | Validation Method |
|-----------|--------|------------------|
| Daily production shows single day value (e.g., $6,450) | 🔍 | Test Scenario 1 |
| All KPIs use latest date filtering | 🔍 | Test Scenario 2 |
| Baytown tab displays correctly | 🔍 | Test Scenario 3 |
| Humble tab displays correctly | 🔍 | Test Scenario 3 |
| Formulas match business requirements | 🔍 | Test Scenario 5 |
| Error handling shows "Data Unavailable" | 🔍 | Test Scenario 4 |
| No aggregated totals in daily metrics | 🔍 | Test Scenario 1 |
| Independent location calculations | 🔍 | Test Scenario 3 |

### Gate Validation Checklist

#### Pre-Test Setup
- [ ] Dashboard accessible at http://localhost:8501
- [ ] Google Sheets credentials configured
- [ ] Both location data sheets accessible
- [ ] Manual calculation spreadsheet prepared

#### Core Functionality
- [ ] Daily production displays single day amount
- [ ] Collection rate calculates from same-day values
- [ ] New patients shows month-to-date from latest entry
- [ ] Treatment acceptance from latest form response
- [ ] Hygiene reappointment from latest date data

#### Dual-Location Features
- [ ] Baytown tab loads and displays 5 KPIs
- [ ] Humble tab loads and displays 5 KPIs
- [ ] Values differ between locations (independent calculations)
- [ ] Tab switching works smoothly
- [ ] Both locations use correct data sources

#### Error Scenarios
- [ ] "Data Unavailable" shown for failed metrics
- [ ] Application doesn't crash on data errors
- [ ] User-friendly error messages displayed
- [ ] Graceful degradation when some data unavailable

#### Performance & UX
- [ ] Dashboard loads in under 5 seconds
- [ ] Tab switching is instantaneous
- [ ] All metrics visible without scrolling
- [ ] Consistent formatting across locations

## Known Issues and Workarounds

### Issue: Empty Data Sets
**Symptom**: "Data Unavailable" for all metrics in one location
**Cause**: No data entries for that location in recent dates
**Workaround**: Verify data exists in Google Sheets for that location
**Resolution**: Ensure both locations have current data entries

### Issue: Inconsistent Date Formats
**Symptom**: Latest date filtering not working correctly
**Cause**: Date column formatting varies between sheets
**Workaround**: `_get_latest_entry()` handles common date column names
**Resolution**: Standardize date column naming across all sheets

### Issue: Calculation Precision
**Symptom**: Minor differences in percentage calculations
**Cause**: Rounding differences between manual and automated calculations
**Workaround**: Allow 0.1% tolerance in validation
**Resolution**: Document expected precision levels

## Success Metrics

### Quantitative Metrics
- **Formula Accuracy**: 100% of KPIs match manual calculations within tolerance
- **Error Handling**: 100% of error scenarios display "Data Unavailable" gracefully
- **Performance**: Dashboard loads in < 5 seconds consistently
- **Data Freshness**: All KPIs reflect most recent date's data

### Qualitative Metrics
- **User Experience**: Intuitive tab navigation between locations
- **Data Clarity**: Clear distinction between daily and monthly values
- **Error Communication**: User-friendly messages for data issues
- **Visual Consistency**: Uniform layout and formatting across locations

## Post-Validation Actions

### If All Tests Pass ✅
1. Update gate status to "APPROVED"
2. Document successful validation in QA log
3. Notify stakeholders of successful Sprint Change
4. Archive validation artifacts

### If Tests Fail ❌
1. Document specific failures with screenshots
2. Create detailed bug reports with reproduction steps
3. Set gate status to "BLOCKED" with failure reasons
4. Coordinate with development team for fixes
5. Schedule re-validation after fixes applied

## Validation Sign-off

**QA Validation Completed By**: _______________________  
**Date**: _______________________  
**Overall Status**: [ ] PASS [ ] FAIL [ ] CONDITIONAL PASS  
**Notes**: _______________________________________

**Stakeholder Approval**: _______________________  
**Date**: _______________________

---

*This validation guide ensures the Sprint Change correctly implements daily KPI calculations and dual-location support according to business requirements.*