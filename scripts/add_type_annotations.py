#!/usr/bin/env python3
"""Add -> None type annotations to test methods."""
import re
import sys
from pathlib import Path


def add_annotations(filepath: Path) -> None:
    """Add -> None annotations to test methods missing them."""
    content = filepath.read_text()

    # Pattern to match test methods without return type annotations
    # Matches: def test_something(self):
    # Replaces with: def test_something(self) -> None:
    pattern = r'(\s+def\s+test_\w+\(self\)):'
    replacement = r'\1 -> None:'

    updated_content = re.sub(pattern, replacement, content)

    filepath.write_text(updated_content)
    print(f"Updated {filepath}")

if __name__ == "__main__":
    test_files = [
        Path("tests/unit/models/test_chart_models.py"),
        Path("tests/unit/models/test_config_models.py"),
    ]

    for filepath in test_files:
        if filepath.exists():
            add_annotations(filepath)
        else:
            print(f"Warning: {filepath} not found", file=sys.stderr)
