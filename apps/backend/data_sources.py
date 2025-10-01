# Legacy compatibility module for SheetsProvider imports.
"""Compatibility wrapper preserving the historical data_sources import path."""

from __future__ import annotations

from .data_providers import SheetsProvider

__all__ = ["SheetsProvider"]
