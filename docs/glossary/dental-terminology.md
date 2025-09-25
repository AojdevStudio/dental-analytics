---
title: "Dental Practice Terminology Glossary"
description: "Comprehensive glossary of dental practice management terms and KPI definitions for accurate analytics."
category: "Reference"
subcategory: "Terminology"
product_line: "Dental Analytics"
audience: "Development Team, Practice Managers"
status: "Active"
author: "James (Dev Agent)"
created_date: "2025-09-24"
last_updated: "2025-09-24"
tags:
  - dental-terminology
  - kpi-definitions
  - practice-management
  - collections
  - production
---

# Dental Practice Terminology Glossary

## Production Terms

### Production (Gross Production)
- **Definition**: Total dollar value of all dental procedures performed before any adjustments
- **Synonyms**: Gross Production, Total Production
- **Example**: If you perform $10,000 worth of procedures in a day, that's your gross production
- **Formula**: Sum of all procedure fees at standard rates

### Adjusted Production (Net Production)
- **Definition**: Production after subtracting adjustments and write-offs
- **Synonyms**: Net Production, Adjusted Gross Production
- **Formula**: Gross Production - Adjustments - Write-offs
- **Usage**: **This is the denominator for collection rate calculations**
- **Example**: $10,000 gross production - $500 adjustments - $300 write-offs = $9,200 adjusted production

### Adjustments
- **Definition**: Reductions to charges (insurance contractual adjustments, discounts, etc.)
- **Impact**: Reduces gross production to get adjusted production
- **Examples**: PPO contractual write-downs, senior discounts, payment plan discounts

### Write-offs
- **Definition**: Amounts written off as uncollectible or bad debt
- **Impact**: Reduces gross production to get adjusted production
- **Examples**: Bad debt, charity care, uncollectible accounts

## Collection Terms

### Collections
- **Definition**: Total money actually received (cash, checks, credit cards, insurance payments)
- **Formula**: Patient Payments + Insurance Payments + Unearned Income Applied
- **Components**:
  - Patient Income Today
  - Insurance Income Today
  - Unearned Income Today (can be negative when applied to treatment)

### Collection Rate
- **Definition**: Percentage of adjusted production actually collected
- **Formula**: **Total Collections ÷ Adjusted Production × 100**
- **Industry Target**: 98%-100%
- **Industry Average**: 91%
- **Critical Error**: Never use gross production in denominator!

### Unearned Income
- **Definition**: Payments received before treatment is completed
- **When Positive**: Money received in advance (prepayments)
- **When Negative**: Previously received unearned money applied to completed treatment
- **Impact**: Counts toward collections when applied (negative unearned income)

## KPI Calculation Formulas

### Correct Collection Rate Formula
```
Collection Rate = (Patient Income + Insurance Income + Unearned Income) ÷ (Gross Production - Adjustments - Write-offs) × 100

Where:
- Numerator = Total Collections
- Denominator = Adjusted Production (NOT Gross Production)
```

### September 23rd Corrected Calculation Example
```
Collections = $2,189.77 + $1,809.38 + (-$2,967.77) = $1,031.38
Adjusted Production = $6,826.49 - (-$4,294.00) - (-$3,679.39) = $14,799.88
Collection Rate = $1,031.38 ÷ $14,799.88 × 100 = 6.97%
```

## Data Source Column Mapping

### EOD Sheet Columns (Baytown/Humble)
- **Column I**: Total Production Today (Gross Production)
- **Column J**: Adjustments Today
- **Column K**: Write-offs Today
- **Column L**: Patient Income Today
- **Column M**: Unearned Income Today
- **Column N**: Insurance Income Today

### Calculated Fields
- **Adjusted Production** = Column I - Column J - Column K
- **Total Collections** = Column L + Column M + Column N
- **Collection Rate** = Total Collections ÷ Adjusted Production × 100

## Common Misconceptions

### ❌ Wrong Collection Rate Calculation
```
Collection Rate = Collections ÷ Gross Production × 100
```

### ✅ Correct Collection Rate Calculation
```
Collection Rate = Collections ÷ Adjusted Production × 100
```

### Why This Matters
- Using gross production inflates the denominator
- Results in artificially low collection rates
- Masks true collection performance
- Industry benchmarks assume adjusted production in denominator

## Industry Benchmarks

| Metric | Excellent | Good | Average | Poor |
|--------|-----------|------|---------|------|
| Collection Rate | 98-100% | 95-97% | 91-94% | <91% |

**Note**: All benchmarks assume adjusted production as denominator

## Related Terms

### Patient Portion
- Amount patient owes after insurance processing
- Collected as patient income

### Insurance Portion
- Amount insurance companies pay
- Collected as insurance income

### Contractual Adjustments
- Difference between full fee and contracted rate with insurance
- Recorded as adjustments (reduces adjusted production)

---

*This glossary ensures consistent terminology across all KPI calculations and reporting.*