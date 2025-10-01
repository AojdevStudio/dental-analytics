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

Optional: Verify Google Sheets aliases in `config/sheets.yml` (e.g., `baytown_eod`, `baytown_front`).

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
uv run python -c 'import json; from apps.backend.metrics import get_all_kpis; print(json.dumps(get_all_kpis(), indent=2))'
```

Pretty print with labels:

```bash
uv run python - <<'PY'
from apps.backend.metrics import get_all_kpis
kpis = get_all_kpis()
for name, value in kpis.items():
    print(f"{name:22} -> {value}")
PY
```

## Individual KPIs

Run targeted calculations using the alias-based provider:

```bash
uv run python - <<'PY'
from apps.backend.data_providers import build_sheets_provider
from apps.backend.metrics import (
    calculate_production_total,
    calculate_collection_rate,
    calculate_case_acceptance,
    calculate_hygiene_reappointment,
    calculate_new_patients,
)

provider = build_sheets_provider()

eod_df = provider.fetch("baytown_eod")
front_df = provider.fetch("baytown_front")

print("Production:", calculate_production_total(eod_df))
print("Collection Rate:", calculate_collection_rate(eod_df))
print("New Patients:", calculate_new_patients(eod_df))
print("Case Acceptance:", calculate_case_acceptance(front_df))
print("Hygiene Reappointment:", calculate_hygiene_reappointment(front_df))
PY
```

## Inspect Raw Data

Quickly preview the first rows of each sheet range:

```bash
uv run python -c 'from apps.backend.data_providers import build_sheets_provider; r=build_sheets_provider(); print(r.fetch("baytown_eod").head())'
```

```bash
uv run python -c 'from apps.backend.data_providers import build_sheets_provider; r=build_sheets_provider(); print(r.fetch("baytown_front").head())'
```

## Troubleshooting

- Auth errors or `Data Unavailable`:
  - Verify `config/credentials.json` exists and is valid
  - Ensure the service account has access to the spreadsheet
  - Confirm the exact sheet range names match your Google Sheet

- Change spreadsheet at runtime (temporary):

```bash
uv run python - <<'PY'
from apps.backend.data_providers import build_sheets_provider

provider = build_sheets_provider()
provider.config['sheets']["baytown_eod"]["spreadsheet_id"] = 'YOUR_SHEET_ID'
print(provider.fetch('baytown_eod').shape)
PY
```

## How It Connects to the Frontend

- The Streamlit app imports the backend directly: `from apps.backend.metrics import get_all_kpis`
- There is no separate API server; values come from Python calls in‑process
- Google Sheets data is read via `apps/backend/data_providers.py` and passed to KPI functions in `apps/backend/metrics.py`
