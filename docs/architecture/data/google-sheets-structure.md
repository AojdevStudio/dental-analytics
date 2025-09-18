---
title: "Google Sheets Data Structure Documentation"
description: "Comprehensive documentation of the Google Sheets structure and column mappings for dental analytics KPIs."
category: "Technical Documentation"
subcategory: "Data Architecture"
product_line: "Dental Analytics Dashboard"
audience: "Development Team"
status: "Active"
author: "AOJDevStudio"
created_date: "2025-09-05"
last_updated: "2025-09-05"
tags:
  - google-sheets
  - data-structure
  - kpi-calculations
  - testing
---

# Google Sheets Data Structure Documentation

## Overview

This document provides the definitive reference for the Google Sheets data structure used by the dental analytics dashboard. All column mappings have been verified using the G-Drive MCP integration for direct spreadsheet access.

**Spreadsheet ID:** `1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8`

## Sheet List

The spreadsheet contains the following sheets:

1. **Production Analysis Logs** (Index: 0)
2. **Baytown Daily Reporting** (Index: 1)
3. **Humble Daily Reporting** (Index: 2)
4. **Humble MTD Reporting** (Index: 3)
5. **Baytown MTD Reporting** (Index: 4)
6. **Baytown Production Analysis** (Index: 5)
7. **Humble Production Analysis** (Index: 6)
8. **EOD - Humble Billing** (Index: 7) - Primary data source
9. **EOD - Baytown Billing** (Index: 8) - Primary data source
10. **Baytown Front KPIs Form responses** (Index: 9) - Primary data source
11. **Humble Front KPIs Form responses** (Index: 10) - Primary data source

## Primary Data Sheets

### EOD - Baytown Billing (Sheet Index: 8)

**Dimensions:** 1024 rows × 33 columns

#### Critical Columns for KPI Calculations:

| Column | Header | Purpose | KPI Usage |
|--------|--------|---------|-----------|
| A | Submission Date | Timestamp of data entry | Date filtering |
| B | Completed By (Team Member Name) | Data entry person | Audit trail |
| C-H | Provider Production Columns | Individual provider metrics | Not used in current KPIs |
| **I** | **Total Production Today** | Daily production amount | Production Total KPI |
| **J** | **Adjustments Today** | Daily adjustments | Production Total KPI |
| **K** | **Write-offs Today** | Daily write-offs | Production Total KPI |
| **L** | **Patient Income Today** | Patient payments | Collection Rate KPI |
| M | Unearned Income Today | Prepayments | Not currently used |
| **N** | **Insurance Income Today** | Insurance payments | Collection Rate KPI |
| O | Month to Date Production | MTD production total | Reference only |
| P | Month to Date Collection | MTD collection total | Reference only |
| Q | Cases Presented (Dollar Amount) | Treatment presented $ | Not directly used |
| **R** | **Cases Accepted (Percentage)** | Treatment acceptance % | Treatment Acceptance KPI |
| **S** | **New Patients - Total Month to Date** | New patient count | New Patients KPI |

### EOD - Humble Billing (Sheet Index: 7)

**Dimensions:** 1030 rows × 31 columns

- Same column structure as Baytown EOD sheet
- Used for Humble location KPIs

### Baytown Front KPIs Form responses (Sheet Index: 9)

**Dimensions:** 22 rows × 26 columns

#### Critical Columns for KPI Calculations:

| Column | Header | Purpose | KPI Usage |
|--------|--------|---------|-----------|
| A | Submission Date | Timestamp of data entry | Date filtering |
| B | Name | Staff member name | Audit trail |
| **C** | **Total hygiene Appointments** | Daily hygiene appointments | Hygiene Reappointment KPI |
| **D** | **Number of patients NOT reappointed?** | Not reappointed count | Hygiene Reappointment KPI |
| E-K | Various tracking metrics | Call tracking, follow-ups | Not used in current KPIs |
| **L** | **Total Dollar amount Presented for the day** | Treatment presented | Treatment Acceptance calculation |
| **M** | **$ Total Dollar amount Scheduled** | Treatment scheduled | Treatment Acceptance calculation |
| N | $ Same Day Treatment | Same-day treatment value | Reference only |

### Humble Front KPIs Form responses (Sheet Index: 10)

**Dimensions:** 18 rows × 26 columns

- Same column structure as Baytown Front KPIs sheet
- Used for Humble location KPIs

## KPI Calculation Formulas

Based on verified column mappings:

### 1. Daily Production Total
```
Production Total = Column I + Column J + Column K
                 = Total Production Today + Adjustments Today + Write-offs Today
```

### 2. Collection Rate
```
Collection Rate = ((Column L + Column N) / (Column I + Column J + Column K)) × 100
                = ((Patient Income + Insurance Income) / Production Total) × 100
```
*Note: Column M (Unearned Income) is not included in collections calculation*

### 3. New Patients Count
```
New Patients = Column S (direct value)
             = New Patients - Total Month to Date
```

### 4. Treatment Acceptance Rate
```
Treatment Acceptance = Column R (direct percentage value from EOD sheet)
                     = Cases Accepted (Percentage)
```
*Alternative calculation from Front KPI sheet:*
```
Treatment Acceptance = (Column M / Column L) × 100
                     = ($ Scheduled / $ Presented) × 100
```

### 5. Hygiene Reappointment Rate
```
Hygiene Reappointment = ((Column C - Column D) / Column C) × 100
                      = ((Total Appointments - Not Reappointed) / Total Appointments) × 100
```

## Data Type Handling

### Currency Fields
- Format: "$X,XXX.XX" (string with dollar sign and commas)
- Conversion: Remove "$" and "," then convert to float
- Negative values: "-$X,XXX.XX" format

### Percentage Fields
- Column R: Already calculated as percentage (e.g., "45.89")
- Direct numeric conversion without multiplication by 100

### Date Fields
- Column A: ISO format "YYYY-MM-DD HH:MM:SS"
- Used for finding most recent entry

## Testing Considerations

### Real Data Samples (August 2025)

**EOD Production Data Example:**
```
Date: 2025-08-16
Total Production Today: $3,669.00
Adjustments Today: $0.00
Write-offs Today: $0.00
Patient Income Today: $831.60
Insurance Income Today: $0.00
New Patients MTD: 52
Cases Accepted: 22.33%
```

**Front KPI Data Example:**
```
Date: 2025-09-04
Total hygiene Appointments: 7
Patients NOT reappointed: 0
Dollar Presented: $52,085
Dollar Scheduled: $2,715
```

### Edge Cases to Test
1. **Zero Production Days**: All production fields = $0.00
2. **Negative Adjustments**: Common pattern in real data
3. **Large Write-offs**: Can exceed daily production
4. **100% Hygiene Reappointment**: When Column D = 0
5. **Missing Data**: Empty cells or incomplete rows

## Validation Using G-Drive MCP

The G-Drive MCP integration enables:

1. **Direct Data Access**: Read actual spreadsheet values for validation
2. **Column Verification**: Confirm column headers match expected names
3. **Formula Validation**: Test calculations against known good values
4. **Test Fixture Generation**: Create realistic test data from production samples
5. **Structure Monitoring**: Detect if spreadsheet structure changes

### G-Drive MCP Commands

```python
# List all sheets in spreadsheet
mcp__gdrive__listSheets(spreadsheetId="1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8")

# Read specific range
mcp__gdrive__readSheet(
    spreadsheetId="1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8",
    range="EOD - Baytown Billing!A1:S10"
)
```

## Maintenance Notes

1. **Column Order**: Critical - formulas depend on specific column positions
2. **Header Names**: Used for DataFrame column access - must match exactly
3. **Sheet Names**: Case-sensitive, include spaces and hyphens
4. **Data Types**: Handle currency strings and percentage formats
5. **Date Filtering**: Always use most recent entry for daily KPIs

## Change History

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2025-09-05 | 1.0 | Initial documentation from G-Drive MCP verification | Scrum Master Bob |

## Related Documents

- `/docs/stories/story-1.6-testing-framework.md` - Testing implementation using this structure
- `/apps/backend/metrics.py` - KPI calculation implementation
- `/apps/backend/sheets_reader.py` - Google Sheets data retrieval
