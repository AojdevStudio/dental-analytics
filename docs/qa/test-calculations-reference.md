---
title: "Test Calculations Reference"
description: "Manual calculation reference for validating KPI formulas and expected values."
category: "Quality Assurance"
subcategory: "Calculation Validation"
product_line: "Dental Analytics Dashboard"
audience: "QA Team"
status: "Active"
author: "AOJDevStudio"
created_date: "2025-09-05"
last_updated: "2025-09-05"
tags:
  - calculations
  - validation
  - formulas
  - manual-testing
---

# Test Calculations Reference

## Overview

This document provides step-by-step manual calculation procedures for validating all 5 KPI formulas against the Sprint Change implementation.

## Google Sheets Data Sources

### Baytown Location
- **EOD Data**: "EOD - Baytown Billing!A:S"
- **Front KPI Data**: "Baytown Front KPIs Form responses!A:S"

### Humble Location
- **EOD Data**: "EOD - Humble Billing!A:S"
- **Front KPI Data**: "Humble Front KPIs Form responses!A:S"

## Manual Calculation Procedures

### 1. Production Total (Daily)

**Data Source**: EOD - [Location] Billing sheet
**Formula**: Column I + Column J + Column K (Latest Date Only)

**Manual Steps**:
1. Open the EOD sheet for the location being tested
2. Identify the most recent date in the data
3. Find the row(s) for that specific date
4. Locate these columns:
   - **Column I**: "Total Production Today"
   - **Column J**: "Adjustments Today"
   - **Column K**: "Write-offs Today"
5. Add the three values: I + J + K
6. Compare result to dashboard "DAILY PRODUCTION" value

**Example Calculation** (9/4/2025):
- Column I (Production): $6,200
- Column J (Adjustments): $150
- Column K (Write-offs): $100
- **Expected Result**: $6,450

**Validation Criteria**:
- Dashboard value matches manual calculation exactly
- Value represents single day, not cumulative total
- Range check: $5,000 - $15,000 typical for daily production

### 2. Collection Rate (Daily)

**Data Source**: EOD - [Location] Billing sheet
**Formula**: (Column L + Column M + Column N) / (Column I + Column J + Column K) × 100

**Manual Steps**:
1. Use the same latest date identified for Production Total
2. Calculate Collections (Numerator):
   - **Column L**: "Patient Income Today"
   - **Column M**: "Insurance Income Today"
   - **Column N**: "Adjustment Offset Today"
   - Total Collections = L + M + N
3. Calculate Production (Denominator):
   - Use same I + J + K from Production Total calculation
4. Calculate percentage: (Collections / Production) × 100
5. Compare result to dashboard "COLLECTION RATE" value

**Example Calculation** (9/4/2025):
- Collections: $2,800 + $2,400 + $50 = $5,250
- Production: $6,450 (from previous calculation)
- Collection Rate: ($5,250 / $6,450) × 100 = 81.4%
- **Expected Result**: 81.4%

**Validation Criteria**:
- Dashboard percentage matches manual calculation within 0.1%
- Uses same-day values for both numerator and denominator
- Range check: 75% - 95% typical for collection rates

### 3. New Patients (Monthly Total)

**Data Source**: EOD - [Location] Billing sheet
**Formula**: Column S (Latest Entry)

**Manual Steps**:
1. Use the same latest date identified for other calculations
2. Find **Column S**: "New Patients - Total Month to Date"
3. Read the value directly (no calculation needed)
4. Compare result to dashboard "NEW PATIENTS" value

**Example Calculation** (9/4/2025):
- Column S value: 23
- **Expected Result**: 23

**Validation Criteria**:
- Dashboard value matches Column S exactly
- Value is an integer (whole number)
- Range check: 5 - 50 typical for monthly new patients

### 4. Treatment Acceptance (Percentage)

**Data Source**: [Location] Front KPIs Form responses sheet
**Formula**: Column R (Latest Entry)

**Manual Steps**:
1. Open the Front KPIs Form responses sheet for the location
2. Identify the most recent date/entry in this sheet
3. Find **Column R**: "Cases Accepted (Percentage)"
4. Read the percentage value directly (pre-calculated)
5. Compare result to dashboard "TREATMENT ACCEPTANCE" value

**Example Calculation** (Latest form entry):
- Column R value: 76.3%
- **Expected Result**: 76.3%

**Validation Criteria**:
- Dashboard percentage matches Column R exactly
- Value comes from latest form submission
- Range check: 60% - 85% typical for treatment acceptance

### 5. Hygiene Reappointment (Percentage)

**Data Source**: [Location] Front KPIs Form responses sheet
**Formula**: ((Total Hygiene - Not Reappointed) / Total Hygiene) × 100

**Manual Steps**:
1. Use the same latest entry from Front KPIs sheet
2. Find these columns:
   - **Total Hygiene**: "Total hygiene Appointments"
   - **Not Reappointed**: "Number of patients NOT reappointed?"
3. Calculate: ((Total - Not Reappointed) / Total) × 100
4. Compare result to dashboard "HYGIENE REAPPOINTMENT" value

**Example Calculation** (Latest form entry):
- Total Hygiene Appointments: 45
- Patients NOT reappointed: 3
- Reappointment Rate: ((45 - 3) / 45) × 100 = (42 / 45) × 100 = 93.3%
- **Expected Result**: 93.3%

**Validation Criteria**:
- Dashboard percentage matches manual calculation within 0.1%
- Uses latest form submission data
- Range check: 85% - 95% typical for hygiene reappointment

## Latest Date Identification

### For EOD Sheets
**Steps**:
1. Look for date columns (typically Column A or B)
2. Scroll to the bottom of the data
3. Identify the most recent date entry
4. Note: Multiple rows may exist for the same date (different procedures/patients)
5. Use ALL data from the latest date for calculations

### For Front KPI Form Responses
**Steps**:
1. Look for timestamp column (typically Column A)
2. Find the most recent form submission
3. Use only that single row for Treatment Acceptance and Hygiene Reappointment

## Validation Tolerances

| KPI Type | Tolerance | Reason |
|----------|-----------|--------|
| Production Total | Exact match | Simple addition, no rounding |
| Collection Rate | ±0.1% | Rounding differences in percentage calculation |
| New Patients | Exact match | Integer value, no calculation |
| Treatment Acceptance | ±0.1% | Pre-calculated percentage, minimal variance |
| Hygiene Reappointment | ±0.1% | Division and percentage calculation |

## Common Validation Issues

### Issue: Large Production Values
**Problem**: Production shows $50,000+ instead of daily amount
**Cause**: Aggregating multiple dates instead of latest date only
**Expected Fix**: Should show single day amount (e.g., $6,450)

### Issue: Zero Collection Rate
**Problem**: Collection rate shows 0% when data exists
**Cause**: Division by zero or missing data handling
**Expected Fix**: Should calculate from same-day production and collections

### Issue: Mismatched Dates
**Problem**: KPIs using different dates for calculations
**Cause**: Inconsistent date filtering across functions
**Expected Fix**: All KPIs should use the same latest date

### Issue: Old Form Data
**Problem**: Treatment Acceptance/Hygiene using outdated form responses
**Cause**: Not filtering to latest form submission
**Expected Fix**: Should use most recent form entry only

## Quick Validation Checklist

**Before Starting**:
- [ ] Dashboard accessible and loading
- [ ] Google Sheets accessible with current data
- [ ] Calculator ready for manual calculations
- [ ] Notebook ready for recording results

**For Each Location (Baytown, Humble)**:
- [ ] Identify latest date in EOD sheet
- [ ] Calculate Production Total manually
- [ ] Calculate Collection Rate manually
- [ ] Record New Patients value
- [ ] Identify latest Front KPI form entry
- [ ] Record Treatment Acceptance value
- [ ] Calculate Hygiene Reappointment manually
- [ ] Compare all 5 values to dashboard
- [ ] Document any discrepancies

**Final Validation**:
- [ ] All calculations within tolerance
- [ ] Both locations validated independently
- [ ] Error scenarios tested ("Data Unavailable")
- [ ] Tab switching working correctly
- [ ] Performance acceptable (< 5 seconds load time)

## Expected Value Ranges

### Baytown Location (Typical)
- **Production**: $8,000 - $12,000 daily
- **Collection Rate**: 80% - 90%
- **New Patients**: 15 - 30 monthly
- **Treatment Acceptance**: 70% - 80%
- **Hygiene Reappointment**: 90% - 95%

### Humble Location (Typical)
- **Production**: $6,000 - $10,000 daily
- **Collection Rate**: 75% - 85%
- **New Patients**: 10 - 25 monthly
- **Treatment Acceptance**: 65% - 75%
- **Hygiene Reappointment**: 85% - 92%

*Note: These are typical ranges. Actual values may vary based on practice volume and seasonal factors.*

---

**Usage**: Use this reference during QA validation to manually verify all KPI calculations match the dashboard values within specified tolerances.