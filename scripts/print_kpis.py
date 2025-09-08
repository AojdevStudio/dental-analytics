#!/usr/bin/env python
"""Print backend KPI values from the terminal.

Usage examples:
  uv run python scripts/print_kpis.py                # pretty output
  uv run python scripts/print_kpis.py --json         # JSON output
  uv run python scripts/print_kpis.py --metrics production_total collection_rate
  uv run python scripts/print_kpis.py --show-raw eod --show-raw front
  uv run python scripts/print_kpis.py --spreadsheet-id YOUR_SHEET_ID
"""

from __future__ import annotations

import argparse
import json
from typing import Dict, Iterable

from backend.metrics import get_all_kpis
from backend.sheets_reader import SheetsReader


EOD_RANGE = "EOD - Baytown Billing!A:N"
FRONT_RANGE = "Baytown Front KPIs Form responses!A:N"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print KPI values used by the Streamlit dashboard.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output KPIs as JSON instead of pretty text.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation (with --json). Default: 2.",
    )
    parser.add_argument(
        "--metrics",
        nargs="+",
        choices=[
            "production_total",
            "collection_rate",
            "new_patients",
            "treatment_acceptance",
            "hygiene_reappointment",
        ],
        help="Limit output to specific metrics (space-separated).",
    )
    parser.add_argument(
        "--show-raw",
        choices=["eod", "front"],
        action="append",
        help="Also print first rows of raw data for the selected sheet(s).",
    )
    parser.add_argument(
        "--spreadsheet-id",
        help=("Temporarily override SheetsReader.SPREADSHEET_ID for this run only."),
    )
    return parser.parse_args()


def filter_metrics(all_kpis: Dict[str, float | None], names: Iterable[str] | None):
    if not names:
        return all_kpis
    return {k: all_kpis.get(k) for k in names}


def print_pretty(kpis: Dict[str, float | None]) -> None:
    for name, value in kpis.items():
        print(f"{name:22} -> {value}")


def print_raw(show_raw: list[str] | None) -> None:
    if not show_raw:
        return
    reader = SheetsReader()
    if "eod" in show_raw:
        df = reader.get_sheet_data(EOD_RANGE)
        print("\n# Raw: EOD - first rows")
        print(df.head() if df is not None else "<no data>")
    if "front" in show_raw:
        df = reader.get_sheet_data(FRONT_RANGE)
        print("\n# Raw: Front KPIs - first rows")
        print(df.head() if df is not None else "<no data>")


def main() -> None:
    args = parse_args()

    if args.spreadsheet_id:
        SheetsReader.SPREADSHEET_ID = args.spreadsheet_id  # type: ignore[attr-defined]

    kpis = get_all_kpis()
    kpis = filter_metrics(kpis, args.metrics)

    if args.json:
        print(json.dumps(kpis, indent=args.indent))
    else:
        print_pretty(kpis)

    print_raw(args.show_raw)


if __name__ == "__main__":
    main()
