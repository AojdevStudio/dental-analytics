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
from collections.abc import Iterable

from apps.backend.data_providers import build_sheets_provider
from apps.backend.metrics import get_all_kpis, get_combined_kpis

# Location-specific ranges
LOCATION_RANGES = {
    "baytown": {
        "eod": "EOD - Baytown Billing!A:AG",
        "front": "Baytown Front KPIs Form responses!A:Z",
    },
    "humble": {
        "eod": "EOD - Humble Billing!A:AG",
        "front": "Humble Front KPIs Form responses!A:Z",
    },
}


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
        help=(
            "Temporarily override spreadsheet ID for this run (not implemented with new provider)."
        ),
    )
    parser.add_argument(
        "--location",
        choices=["baytown", "humble", "both"],
        default="baytown",
        help="Location to get KPIs for (baytown, humble, or both). Default: baytown.",
    )
    return parser.parse_args()


def filter_metrics(all_kpis: dict[str, float | None], names: Iterable[str] | None):
    if not names:
        return all_kpis
    return {k: all_kpis.get(k) for k in names}


def print_pretty(kpis: dict[str, float | None]) -> None:
    for name, value in kpis.items():
        print(f"{name:22} -> {value}")


def print_raw(show_raw: list[str] | None, location: str = "baytown") -> None:
    if not show_raw:
        return
    provider = build_sheets_provider()

    if "eod" in show_raw:
        eod_alias = provider.get_location_aliases(location, "eod")
        df = provider.fetch(eod_alias) if eod_alias else None
        print(f"\n# Raw: EOD {location.title()} - first rows")
        print(df.head() if df is not None else "<no data>")
    if "front" in show_raw:
        front_alias = provider.get_location_aliases(location, "front")
        df = provider.fetch(front_alias) if front_alias else None
        print(f"\n# Raw: Front KPIs {location.title()} - first rows")
        print(df.head() if df is not None else "<no data>")


def main() -> None:
    args = parse_args()

    if args.spreadsheet_id:
        print("Warning: --spreadsheet-id is not implemented with new provider system")
        # TODO: Implement custom config loading if needed

    if args.location == "both":
        # Get KPIs for both locations
        all_kpis = get_combined_kpis()

        for location, kpis in all_kpis.items():
            filtered_kpis = filter_metrics(kpis, args.metrics)

            if args.json:
                print(f"# {location.title()} KPIs")
                print(json.dumps(filtered_kpis, indent=args.indent))
                print()  # Empty line between locations
            else:
                print(f"\n=== {location.title()} KPIs ===")
                print_pretty(filtered_kpis)
                print()

            # Show raw data if requested
            if args.show_raw:
                print_raw(args.show_raw, location)
    else:
        # Get KPIs for single location
        kpis = get_all_kpis(args.location)
        kpis = filter_metrics(kpis, args.metrics)

        if not args.json:
            print(f"=== {args.location.title()} KPIs ===")

        if args.json:
            print(json.dumps(kpis, indent=args.indent))
        else:
            print_pretty(kpis)

        print_raw(args.show_raw, args.location)


if __name__ == "__main__":
    main()
