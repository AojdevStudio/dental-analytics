---
title: "Dental KPI Formulas Reference"
description: "Complete reference guide for dental practice KPI calculations and formulas used in the analytics dashboard."
category: "Reference"
subcategory: "Domain Knowledge"
product_line: "Dental Analytics"
audience: "Development Team, Practice Managers"
status: "Active"
author: "James (Dev Agent)"
created_date: "2025-09-24"
last_updated: "2025-09-24"
tags:
  - dental-kpis
  - formulas
  - calculations
  - domain-knowledge
  - reference
---

# Dental KPI Formulas Reference

## Overview

This document provides the definitive reference for all dental practice KPI calculations used in the analytics dashboard. These formulas represent industry-standard calculations for measuring dental practice performance.

## Core KPI Formulas

### 1. Collection Rate

```python
def calculate_collection_rate(df: pd.DataFrame) -> float:
    """Collection Rate = (Patient + Unearned + Insurance Income) / Adjusted Production × 100

    CRITICAL: Uses ADJUSTED production (net), not gross production!
    Adjusted Production = Gross Production - |Adjustments| - |Write-offs|
    Industry target: 98-100% collection rate
    """
    # Calculate adjusted production (net production after adjustments/write-offs)
    gross_production = df['Total Production Today'].sum()
    adjustments = df['Adjustments Today'].sum()
    writeoffs = df['Write-offs Today'].sum()

    # Adjusted Production = Gross - |Adjustments| - |Write-offs|
    adjusted_production = gross_production - abs(adjustments) - abs(writeoffs)

    # Calculate total collections
    collections_total = (
        df['Patient Income Today'].sum()
        + df['Unearned Income Today'].sum()  # Can be negative when applied
        + df['Insurance Income Today'].sum()
    )

    if adjusted_production == 0:
        return 0.0
    return (collections_total / adjusted_production) * 100
```

**Key Points:**
- Uses ADJUSTED production as denominator (industry standard)
- Adjustments and write-offs reduce gross production
- Unearned income can be negative when previously collected funds are applied
- Target: 98-100% (Industry average: 91%)

### 2. Case Acceptance Rate (Treatment Acceptance)

```python
def calculate_case_acceptance(df: pd.DataFrame) -> float:
    """Case Acceptance = (Scheduled + Same Day) / Presented × 100"""
    presented = df['treatments_presented'].sum()
    scheduled = df['treatments_scheduled'].sum()
    same_day = df['$ Same Day Treatment'].sum()
    if presented == 0:
        return 0.0
    return ((scheduled + same_day) / presented) * 100
```

**Key Points:**
- Measures how many treatment plans are accepted by patients
- Includes both scheduled and same-day treatments
- Target: 80-90% acceptance rate

### 3. Hygiene Reappointment Rate

```python
def calculate_hygiene_reappointment(df: pd.DataFrame) -> float:
    """Hygiene Reappointment = (Reappointed / Total) × 100"""
    total = df['Total hygiene Appointments'].sum()
    not_reappointed = df['Number of patients NOT reappointed?'].sum()
    if total == 0:
        return 0.0
    return ((total - not_reappointed) / total) * 100
```

**Key Points:**
- Measures patient retention for hygiene appointments
- Critical for practice health and recurring revenue
- Target: 85-95% reappointment rate

### 4. Daily New Patients

```python
def calculate_daily_new_patients(df: pd.DataFrame) -> pd.Series:
    """Daily new patients from month-to-date cumulative values."""
    ordered = df.sort_values('Submission Date')
    cumulative = ordered['New Patients - Total Month to Date'].astype(float)
    deltas = cumulative.diff().fillna(cumulative).clip(lower=0)
    return deltas
```

**Key Points:**
- Calculates daily new patients from cumulative MTD values
- Uses diff() to find daily increments
- Handles month boundaries (resets to new cumulative)
- Target varies by practice size (typically 30-50 new patients/month)

### 5. Production Total

```python
def calculate_production_total(df: pd.DataFrame) -> float:
    """Production Total = Gross Production + Adjustments + Write-offs

    Note: Adjustments and write-offs are typically negative values
    that reduce production, so adding them gives net production.
    """
    production = df['Total Production Today'].sum()
    adjustments = df['Adjustments Today'].sum()  # Usually negative
    writeoffs = df['Write-offs Today'].sum()      # Usually negative
    return production + adjustments + writeoffs
```

**Key Points:**
- Represents total value of work performed
- Adjustments and write-offs are typically negative
- This gives you the net production figure

## Data Validation Rules

### Collection Rate Validation
```python
def validate_collection_rate(rate: float) -> str:
    """Flag abnormal collection rates based on industry standards"""
    if rate > 200:
        return "⚠️ ANOMALY: Rate >200% - Check data entry"
    elif rate < 50:
        return "🚨 CRITICAL: Rate <50% - Collection process failure"
    elif rate < 91:
        return "⚠️ BELOW AVERAGE: Rate <91% - Needs improvement"
    elif rate >= 98:
        return "✅ EXCELLENT: Rate ≥98% - Meeting target"
    else:
        return "📊 AVERAGE: Rate 91-97% - Room for improvement"
```

## Industry Benchmarks

| KPI | Excellent | Good | Average | Poor |
|-----|-----------|------|---------|------|
| Collection Rate | 98-100% | 95-97% | 91-94% | <91% |
| Case Acceptance | 85-95% | 75-84% | 65-74% | <65% |
| Hygiene Reappointment | 90-95% | 85-89% | 80-84% | <80% |
| New Patients/Month | 40+ | 30-39 | 20-29 | <20 |
| Daily Production | Varies by practice size and location |

## Common Calculation Errors

### ❌ Incorrect Collection Rate
```python
# WRONG - Uses gross production
collection_rate = collections / gross_production * 100
```

### ✅ Correct Collection Rate
```python
# CORRECT - Uses adjusted production
adjusted_production = gross_production - abs(adjustments) - abs(writeoffs)
collection_rate = collections / adjusted_production * 100
```

## Data Source Mapping

### EOD Sheet Columns
- **Column I**: Total Production Today (Gross Production)
- **Column J**: Adjustments Today
- **Column K**: Write-offs Today
- **Column L**: Patient Income Today
- **Column M**: Unearned Income Today
- **Column N**: Insurance Income Today
- **Column O**: New Patients - Total Month to Date

### Front KPI Sheet Columns
- **Column K**: Treatments Presented
- **Column L**: Treatments Scheduled
- **Column M**: $ Same Day Treatment
- **Column T**: Total Hygiene Appointments
- **Column U**: Number of Patients NOT Reappointed

## Important Notes

1. **Adjusted vs Gross Production**: Always use adjusted production for collection rate calculations
2. **Currency Formatting**: Remove $ and commas before calculations
3. **Negative Values**: Adjustments and write-offs are often negative (reductions)
4. **Unearned Income**: Can be negative when previously collected funds are applied
5. **Data Validation**: Implement checks for impossible values (>200% collection rates, etc.)

---

*This reference document is the authoritative source for all dental KPI calculations in the analytics dashboard.*
