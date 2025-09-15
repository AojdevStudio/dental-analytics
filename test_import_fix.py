#!/usr/bin/env python3
"""
Test script to verify the import fix works correctly.
This mimics exactly what happens when the Streamlit app starts.
"""
import sys
from pathlib import Path

print("Testing import fix for dental analytics...")
print(f"Python version: {sys.version}")
print(f"Current working directory: {Path.cwd()}")

# Mimic the path resolution logic from apps/frontend/app.py
app_file = Path(__file__).parent / "apps" / "frontend" / "app.py"
project_root = app_file.parent.parent.parent

print(f"App file path: {app_file}")
print(f"Project root: {project_root}")
print(f"Project root exists: {project_root.exists()}")

# Add project root to Python path (same as in app.py)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    print(f"✅ Added project root to Python path: {project_root}")
else:
    print("ℹ️  Project root already in Python path")

# Test the critical import
try:
    from apps.backend.metrics import get_all_kpis

    print("✅ Successfully imported get_all_kpis")

    # Test other imports from the app (these are required by the app)
    from datetime import datetime  # noqa: F401

    import streamlit as st  # noqa: F401

    print("✅ Successfully imported other dependencies")

    # Verify the function is callable
    print(f"get_all_kpis function: {get_all_kpis}")
    print(f"Function callable: {callable(get_all_kpis)}")

    print("\n🎉 All imports successful! The Streamlit app should now work.")

except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Import path debugging:")
    for i, path in enumerate(sys.path[:5]):
        print(f"  {i}: {path}")
    sys.exit(1)

print("\nRunning final integration test...")
try:
    # This would fail if credentials aren't set up, but import should work
    result = get_all_kpis()
    print(f"✅ get_all_kpis() executed successfully: {type(result)}")
except Exception as e:
    print(f"⚠️  get_all_kpis() failed (expected if no credentials): {e}")
    print("But the import worked, which is what we're testing!")

print("\n✅ Import fix verification complete!")
