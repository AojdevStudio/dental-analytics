---
title: "Multi-Sheet Reader Plan"
description: "Roadmap to enable multiple Google Sheets sources and pave the path to a SQLite data provider without preserving the legacy single-sheet API."
category: "Planning"
subcategory: "Backend"
product_line: "Dental Analytics"
audience: "Engineering"
status: "Draft"
author: "AOJDevStudio"
created_date: "2024-10-28"
last_updated: "2024-10-28"
tags:
  - google-sheets
  - data-ingestion
  - roadmap
---

# Multi-Sheet Reader

## Problem Statement
Current `SheetsProvider` is hard-wired to a single Google Sheets spreadsheet via the module-level `SPREADSHEET_ID`, so every consumer assumes one canonical sheet. This blocks the immediate need to read from multiple spreadsheets (e.g., separate EOD, KPI, or location-specific workbooks) and leaves no seam for the longer-term goal of migrating to SQLite or other data backends without rewriting the callers.

## Goals
- Replace the legacy `SheetsProvider` contract with a multi-spreadsheet design that uses aliases instead of a global ID.
- Provide a configuration-driven approach so spreadsheet IDs, ranges, and metadata can be updated without redeploying code.
- Introduce an interface for data access that can be reused when a SQLite provider replaces or augments Google Sheets.
- Allow downstream modules to depend on the new provider abstraction only; the old single-sheet API will be removed.

## Non-Goals
- Maintain backward compatibility with the existing `SheetsProvider()` constructor or module-level constants.
- Implement the SQLite backend immediately (tracked as a future milestone).
- Change KPI calculation formulas or frontend rendering.
- Rework authentication or credential storage.

## Requirements
### Functional
- Support multiple spreadsheet IDs and named ranges keyed by alias (e.g., `baytown_eod`, `humble_front`).
- Require consumers to resolve data via aliases; attempting to use the old API should fail fast with explicit errors.
- Keep public methods returning `pd.DataFrame | None` with explicit logging for empty or failing fetches.

### Non-Functional
- Configuration must live in the repository (`config/sheets.yml` or TOML) and load on reader construction.
- Enforce strict validation: missing aliases or malformed config raise exceptions during startup.
- Ensure revised modules remain within line-count guidance (per AGENTS.md), shifting logic to helper modules when needed.

## Constraints & Dependencies
- Production still relies on Google Sheets service accounts stored at `config/credentials.json`.
- Tests rely heavily on patching `SheetsProvider`; they must be updated to target the new abstraction instead of expecting legacy behavior.

## Proposed Architecture
1. **Config Schema**
   - Introduce `config/sheets.yml` (or `.toml`) with entries:
     ```yaml
     sheets:
       baytown_eod:
         spreadsheet_id: "..."
         range: "EOD - Baytown Billing!A:AG"
       humble_eod:
         spreadsheet_id: "..."
         range: "EOD - Humble Billing!A:AG"
     defaults:
       credentials_path: "config/credentials.json"
       location_alias:
         baytown:
           eod: "baytown_eod"
           front: "baytown_front"
         humble:
           eod: "humble_eod"
           front: "humble_front"
     ```

2. **Data Provider Interface**
   - Define a lightweight protocol or abstract base `DataProvider` with `fetch(alias: str) -> pd.DataFrame | None`.
   - Implement `SheetsProvider` (new class name) using the config to map aliases to spreadsheet ID + range.
   - Remove legacy helpers (`get_eod_data`, `get_front_kpi_data`) from the provider; replace them with alias resolution utilities in consuming modules.

3. **Factory/Injection**
   - Provide a constructor or factory (`build_sheets_provider(config_path: Path | None = None)`) that reads config, validates schema, and returns the new provider.
   - Consumers (metrics, historical data, CLI) must request the provider via dependency injection and use aliases explicitly.

4. **SQLite Readiness**
   - Document expected interface for upcoming SQLite provider (same `DataProvider` contract, but using SQL queries).
   - Ensure config format can extend with `provider: sheets|sqlite` flags per alias.

## Implementation Plan
1. **Configuration & Schema Setup**
   - Add `config/sheets.yml` with current spreadsheet IDs and ranges.
   - Implement validation loader (`load_sheet_config`) with explicit exceptions on failure and unit tests.

2. **Introduce New Provider**
   - Create `SheetsProvider` implementing `DataProvider` with alias-based fetching.
   - Delete module-level `SPREADSHEET_ID` and any helper relying on it.
   - Provide a clear migration error for any attempted `SheetsProvider()` import (e.g., raise `RuntimeError` instructing to use new provider).

3. **Update Call Sites**
   - `apps/backend/metrics.py`: request provider, map location → alias inside metrics module, remove references to legacy helpers.
   - `apps/backend/historical_data.py`: obtain provider and resolve required aliases explicitly.
   - `scripts/print_kpis.py`: pass aliases or allow CLI to select alias per dataset; remove old override flag tied to constants.
   - Remove or rewrite any remaining usage of `SheetsProvider` in docs, stories, and scripts.

4. **Testing & Quality**
   - Update unit tests to construct provider with minimal config dictionaries; add tests for alias resolution, missing config, and error messages.
   - Adjust integration tests to use alias-driven access.
   - Remove assertions referencing `SPREADSHEET_ID`; replace with config-driven expectations.

5. **Documentation & Dev Experience**
   - Refresh README, architecture docs, and stories to describe alias-based configuration and new provider usage.
   - Document migration steps for developers (including how legacy imports now fail).

6. **Future SQLite Prep (Design Only)**
   - Document expected SQLite provider responsibilities (table schema, query interface, caching strategy).
   - Capture open questions about migration (data sync frequency, write path, fallback).

## Testing Strategy
- Unit: patch Google API client, validate alias-to-ID mapping, and ensure meaningful exceptions when aliases are missing.
- Integration: ensure KPI calculations work when different aliases are specified for each location through the new interface.
- CLI: verify new alias flags work end-to-end via automated tests with mocked provider.

## Risks & Mitigations
- **Breaking Change Surface**: Removing the legacy API may break overlooked imports. → Mitigate by search-and-replace sweep, adding aggressive runtime error for residual usage, and highlighting the change in release notes.
- **Config Drift**: Missing aliases could break fetches. → Mitigate by validation on startup and actionable error messages.
- **Line Count Limits**: Additional code may push files over targets. → Shift config parsing into dedicated module and keep helpers concise.

## Open Questions
- Do we ever need to store extra details besides the sheet range (for example, notes about columns)?
  - Decision: stick with range-only for now; add optional notes later if a real use-case appears.
- Will different environments like staging and production need their own sheet IDs?
  - Answer: no, we only operate a single environment for this project.
- When we add SQLite later, how will we handle updating credentials while both systems run together?
  - Plan: run a slow migration where JotForm continues writing to Sheets, a sync job copies Sheets data into SQLite, and the dashboard switches to read from SQLite; once validated, introduce React forms that write straight to SQLite and retire JotForm + Google Sheets.

## Milestones
1. **M1 – Multi-Sheet Config Support (Sprint N)**
   - Config file, new provider in place, legacy API removed, tests green, docs updated.
2. **M2 – Consumer Refactor & Cleanup (Sprint N+1)**
   - All modules consuming the provider via injection, removal of temporary compatibility shims, developer tooling updated.
3. **M3 – SQLite Prototype (Future)**
   - Implement SQLite provider using same interface, smoke-test swap behind feature flag.
