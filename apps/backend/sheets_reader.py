# Legacy module - DEPRECATED
# This module has been replaced by data_providers.py
# All functionality moved to alias-based SheetsProvider

# For backward compatibility during transition period,
# redirect imports to new provider system

import warnings
from typing import Any


def __getattr__(name: str) -> Any:
    if name == "SheetsReader":
        warnings.warn(
            "SheetsReader is deprecated. Use data_providers.build_sheets_provider() instead.",  # noqa: E501
            DeprecationWarning,
            stacklevel=2,
        )
        from .data_providers import SheetsProvider

        return SheetsProvider

    if name == "SPREADSHEET_ID":
        warnings.warn(
            "SPREADSHEET_ID constant is deprecated. Configure via config/sheets.yml instead.",  # noqa: E501
            DeprecationWarning,
            stacklevel=2,
        )
        return "1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8"

    if name == "SCOPES":
        warnings.warn(
            "SCOPES constant is deprecated. Configure via config/sheets.yml instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
