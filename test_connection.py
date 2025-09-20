"""Test script for Google Sheets API connection."""

import sys
from pathlib import Path

from apps.backend.data_providers import build_sheets_provider


def test_google_sheets_connection():
    """Test connection to Google Sheets API."""
    print("🔍 Testing Google Sheets connection...")

    # Check if credentials file exists
    credentials_path = Path("config/credentials.json")
    if not credentials_path.exists():
        print("❌ Credentials file not found!")
        print(f"   Expected location: {credentials_path.absolute()}")
        print("   Please complete Google Cloud setup as described in:")
        print("   docs/guides/google-cloud-setup.md")
        return False

    print(f"✅ Found credentials file: {credentials_path}")

    try:
        # Initialize SheetsProvider
        provider = build_sheets_provider()

        print("✅ Google Sheets provider initialized successfully")

        # Test connection by reading Baytown EOD data
        alias = "baytown_eod"
        print(f"📊 Testing data read using alias '{alias}'...")

        df = provider.fetch(alias)

        if df is None:
            print("❌ Failed to read sheet data")
            print("   Possible causes:")
            print("   - Service account not shared on spreadsheet")
            print("   - Invalid spreadsheet ID or alias configuration")
            print("   - Sheet alias doesn't exist in config")
            return False

        print(f"✅ Successfully read {len(df)} rows using alias '{alias}'")
        print(f"📋 Columns found: {list(df.columns)}")

        # Show first few rows (without sensitive data)
        if len(df) > 0:
            print(f"📈 Data shape: {df.shape}")
            print(f"🗂️  Sample column types: {df.dtypes.to_dict()}")

        print("\n🎉 Connection test successful!")
        print("   ✅ Credentials loaded")
        print("   ✅ Google Sheets API accessible")
        print("   ✅ Target spreadsheet readable")
        print("   ✅ Data retrieved as DataFrame")

        return True

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("\n🛠️  Troubleshooting steps:")
        print("   1. Verify Google Cloud setup is complete")
        print("   2. Check service account has 'Viewer' permission")
        print("   3. Ensure spreadsheet is shared with service account")
        print("   4. Confirm Google Sheets API is enabled")
        return False


def test_error_handling():
    """Test error handling with invalid range."""
    print("\n🧪 Testing error handling...")

    try:
        provider = build_sheets_provider()

        # Test with invalid alias
        result = provider.fetch("NonExistentAlias")

        if result is None:
            print("✅ Error handling works: None returned for invalid alias")
            return True
        else:
            print("❌ Error handling failed: Should return None for invalid alias")
            return False

    except Exception as e:
        print(f"❌ Unexpected exception in error handling test: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 DENTAL ANALYTICS - GOOGLE SHEETS CONNECTION TEST")
    print("=" * 60)

    # Test main connection
    connection_success = test_google_sheets_connection()

    # Test error handling
    error_handling_success = test_error_handling()

    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"   Connection Test: {'✅ PASS' if connection_success else '❌ FAIL'}")
    print(f"   Error Handling:  {'✅ PASS' if error_handling_success else '❌ FAIL'}")

    if connection_success and error_handling_success:
        print("\n🎯 ALL TESTS PASSED! Ready for development.")
        sys.exit(0)
    else:
        print("\n⚠️  TESTS FAILED! Please address issues before continuing.")
        sys.exit(1)
