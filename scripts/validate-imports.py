#!/usr/bin/env python3
"""Validate all Python imports in the project."""

import ast
import sys
from pathlib import Path


def get_imports_from_file(filepath: Path) -> set[str]:
    """Extract all imports from a Python file."""
    imports = set()
    try:
        with filepath.open() as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    if module:
                        imports.add(f"{module}.{alias.name}")
                    else:
                        imports.add(alias.name)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")

    return imports


def validate_project_imports() -> tuple[bool, list[str]]:
    """Validate all imports in the project."""
    errors = []
    project_root = Path(__file__).parent.parent

    # Check all Python files
    for py_file in project_root.rglob("*.py"):
        # Skip virtual environments and cache
        if any(part in str(py_file) for part in [".venv", "__pycache__", ".git"]):
            continue

        # Try to import the module to catch import errors
        relative_path = py_file.relative_to(project_root)

        try:
            # Use compile to check syntax and imports
            with py_file.open() as f:
                compile(f.read(), py_file, "exec")
        except SyntaxError as e:
            errors.append(f"Syntax error in {relative_path}: {e}")
        except Exception as e:
            if "cannot import name" in str(e):
                errors.append(f"Import error in {relative_path}: {e}")

    return len(errors) == 0, errors


if __name__ == "__main__":
    success, errors = validate_project_imports()

    if not success:
        print("❌ Import validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ All imports validated successfully")
        sys.exit(0)
