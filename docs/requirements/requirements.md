# Requirements

## Functional Requirements

**FR1:** System must authenticate and connect to Google Sheets API using service account credentials stored securely in config/credentials.json

**FR2:** System must read data from spreadsheet ID `1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8` with refresh triggered 3-4 times per 24-hour period (morning, midday, end-of-day)

**FR3:** System must calculate and display Daily Production Total by summing columns B-D (provider production) or reading Column E directly from EOD sheets

**FR4:** System must calculate and display Collection Rate using formula `(total_collections / total_production) × 100` from Column F and Column E

**FR5:** System must display New Patient Count from Column J in EOD sheets

**FR6:** System must calculate and display Treatment Acceptance Rate using formula `(dollar_scheduled / dollar_presented) × 100` from Front KPI sheets Columns M and L

**FR7:** System must calculate and display Hygiene Reappointment Rate using formula `((total_hygiene - not_reappointed) / total_hygiene) × 100` from Front KPI sheets Columns C and D

**FR8:** System must display all five KPIs on a single screen without scrolling, using Streamlit's metric components

## Non-Functional Requirements

**NFR1:** Dashboard must load completely in under 3 seconds on initial page load

**NFR2:** KPI calculations must complete in under 1 second when triggered

**NFR3:** Total production code must not exceed 200 lines across all Python files

**NFR4:** System must handle Google Sheets API rate limits gracefully, staying well within free tier quotas

**NFR5:** System must work on modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)

**NFR6:** No PHI/PII data may be stored in the application; only aggregate metrics

**NFR7:** System must require zero user training for basic dashboard viewing

**NFR8:** All dependencies must be manageable through `uv` package manager with lockfile
