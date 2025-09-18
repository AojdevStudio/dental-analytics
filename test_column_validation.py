#!/usr/bin/env python3
"""
Test script for Story 2.1 validation gate: Column mapping verification.

This script validates that all mapped columns in data_sources.py
actually exist in the target Google Sheets.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.data_sources import (
    COLUMN_MAPPINGS,
    get_actual_sheet_columns,
    validate_column_mappings_against_sheets,
)


def main():
    """Run column validation for Story 2.1."""
    print("🔍 Story 2.1 Column Validation Gate")
    print("=" * 50)

    # Show current mappings
    print("\n📋 Current Column Mappings:")
    for source_name, mappings in COLUMN_MAPPINGS.items():
        print(f"\n{source_name.upper()}:")
        for logical_name, actual_column in mappings.items():
            print(f"  {logical_name} → '{actual_column}'")

    print("\n🔬 Validating against actual Google Sheets...")

    # Run validation
    validation_results = validate_column_mappings_against_sheets()

    print("\n📊 Validation Results:")
    print("-" * 30)

    all_valid = True
    for source_name, is_valid in validation_results.items():
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"{source_name}: {status}")

        if not is_valid:
            all_valid = False
            print("  Getting actual columns for debugging...")
            actual_columns = get_actual_sheet_columns(source_name)
            if actual_columns:
                print(f"  Actual columns: {actual_columns[:5]}... (showing first 5)")

    print("\n" + "=" * 50)
    if all_valid:
        print("🎉 Story 2.1 Validation Gate: PASSED")
        print("All column mappings are valid!")
        return 0
    else:
        print("🚫 Story 2.1 Validation Gate: FAILED")
        print("Some column mappings need correction.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
