---
title: "Print Backend KPIs from Terminal"
description: "Quick commands to fetch and print the backend KPI values that the Streamlit app displays."
category: "Guides"
subcategory: "CLI"
product_line: "Dental Analytics"
audience: "Developers"
status: "Active"
author: "AOJDevStudio"
created_date: "2025-09-05"
last_updated: "2025-09-05"
tags:
  - kpi
  - cli
  - backend
  - streamlit
  - google-sheets
---

# Print Backend KPIs from Terminal

This guide shows how to print the exact KPI values the Streamlit app displays, directly from your terminal using `uv` and Python one‑liners.

## Prerequisites

- Python 3.10+ and `uv` installed
- Dependencies installed: `uv sync`
- Google Sheets credentials at `config/credentials.json`
- Service account has Viewer access to the target spreadsheet

Optional: Verify or change the spreadsheet ID in `backend/sheets_reader.py` (`SPREADSHEET_ID`).

## One-Command Script (recommended)

Use the helper script for quick checks:

```bash
uv run python scripts/print_kpis.py                  # pretty output
uv run python scripts/print_kpis.py --json           # JSON output
uv run python scripts/print_kpis.py --metrics production_total collection_rate
uv run python scripts/print_kpis.py --show-raw eod --show-raw front
uv run python scripts/print_kpis.py --spreadsheet-id YOUR_SHEET_ID
```

Options:
- `--metrics`: limit to specific metrics
- `--json` and `--indent`: JSON output formatting
- `--show-raw eod|front`: show first rows of source sheets
- `--spreadsheet-id`: override spreadsheet for ad-hoc runs

## All KPIs (same as frontend)

Return all KPIs as JSON (zsh-safe quoting):

```bash
uv run python -c 'import json; from backend.metrics import get_all_kpis; print(json.dumps(get_all_kpis(), indent=2))'
```

Pretty print with labels:

```bash
uv run python - <<'PY'
from backend.metrics import get_all_kpis
kpis = get_all_kpis()
for name, value in kpis.items():
    print(f"{name:22} -> {value}")
PY
```

## Individual KPIs

Daily Production (EOD sheet):

```bash
uv run python -c 'from backend.sheets_reader import SheetsReader; from backend.metrics import calculate_production_total as f; r=SheetsReader(); df=r.get_sheet_data("EOD - Baytown Billing!A:N"); print(f(df))'
```

Collection Rate % (EOD sheet):

```bash
uv run python -c 'from backend.sheets_reader import SheetsReader; from backend.metrics import calculate_collection_rate as f; r=SheetsReader(); df=r.get_sheet_data("EOD - Baytown Billing!A:N"); print(f(df))'
```

Treatment Acceptance % (Front KPI sheet):

```bash
uv run python -c 'from backend.sheets_reader import SheetsReader; from backend.metrics import calculate_case_acceptance as f; r=SheetsReader(); df=r.get_sheet_data("Baytown Front KPIs Form responses!A:N"); print(f(df))'
```

Hygiene Reappointment % (Front KPI sheet):

```bash
uv run python -c 'from backend.sheets_reader import SheetsReader; from backend.metrics import calculate_hygiene_reappointment as f; r=SheetsReader(); df=r.get_sheet_data("Baytown Front KPIs Form responses!A:N"); print(f(df))'
```

New Patients (currently placeholder):

```bash
uv run python -c 'from backend.sheets_reader import SheetsReader; from backend.metrics import calculate_new_patients as f; r=SheetsReader(); df=r.get_sheet_data("EOD - Baytown Billing!A:N"); print(f(df))' 
```

Note: `calculate_new_patients` returns `None` until the correct column is confirmed and implemented.

## Inspect Raw Data

Quickly preview the first rows of each sheet range:

```bash
uv run python -c 'from backend.sheets_reader import SheetsReader; r=SheetsReader(); print(r.get_sheet_data("EOD - Baytown Billing!A:N").head())'
```

```bash
uv run python -c 'from backend.sheets_reader import SheetsReader; r=SheetsReader(); print(r.get_sheet_data("Baytown Front KPIs Form responses!A:N").head())'
```

## Troubleshooting

- Auth errors or `Data Unavailable`:
  - Verify `config/credentials.json` exists and is valid
  - Ensure the service account has access to the spreadsheet
  - Confirm the exact sheet range names match your Google Sheet

- Change spreadsheet at runtime (temporary):

```bash
uv run python - <<'PY'
from backend.sheets_reader import SheetsReader
SheetsReader.SPREADSHEET_ID = 'YOUR_SHEET_ID'
print(SheetsReader().get_sheet_data('EOD - Baytown Billing!A:N').shape)
PY
```

## How It Connects to the Frontend

- The Streamlit app imports the backend directly: `from backend.metrics import get_all_kpis`
- There is no separate API server; values come from Python calls in‑process
- Google Sheets data is read via `backend/sheets_reader.SheetsReader` and passed to KPI functions in `backend/metrics`
