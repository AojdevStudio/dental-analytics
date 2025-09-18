#!/usr/bin/env python3
"""
Demonstration of Operational Day Logic for Dental Practice

This script demonstrates the core operational day logic implemented for Story 2.1:
- Monday-Saturday are operational days
- Sundays fall back to Saturday data
- Latest available data retrieval logic
"""

import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.append(".")

from apps.backend.historical_data import HistoricalDataManager


def main():
    """Demonstrate operational day logic."""
    print("=== Dental Practice Operational Day Logic Demo ===")
    print("Operational Days: Monday (0) - Saturday (5)")
    print("Non-operational: Sunday (6)")
    print()

    # Create manager (will fail to connect to Google Sheets, but that's ok for demo)
    try:
        manager = HistoricalDataManager()
    except Exception:
        # Create manually for demo purposes
        manager = HistoricalDataManager.__new__(HistoricalDataManager)
        manager.operational_days = {0, 1, 2, 3, 4, 5}  # Monday-Saturday
        print("Note: Using demo mode (no Google Sheets connection)")
        print()

    # Test dates for a full week
    test_dates = [
        (datetime(2025, 9, 15), "Monday"),  # 0
        (datetime(2025, 9, 16), "Tuesday"),  # 1
        (datetime(2025, 9, 17), "Wednesday"),  # 2
        (datetime(2025, 9, 18), "Thursday"),  # 3
        (datetime(2025, 9, 19), "Friday"),  # 4
        (datetime(2025, 9, 20), "Saturday"),  # 5
        (datetime(2025, 9, 21), "Sunday"),  # 6
    ]

    print("Testing is_operational_day() for each day of the week:")
    for test_date, day_name in test_dates:
        is_operational = manager.is_operational_day(test_date)
        status = "✅ OPERATIONAL" if is_operational else "❌ NON-OPERATIONAL"
        print(f"  {day_name:10} ({test_date.strftime('%Y-%m-%d')}): {status}")

    print()
    print("Testing get_latest_operational_date() fallback logic:")

    # Test fallback from Sunday to Saturday
    sunday = datetime(2025, 9, 21)  # Sunday
    latest_from_sunday = manager.get_latest_operational_date(sunday)
    print(
        f"  From Sunday {sunday.strftime('%Y-%m-%d')}: → {latest_from_sunday.strftime('%Y-%m-%d')} ({latest_from_sunday.strftime('%A')})"
    )

    # Test operational day returns itself
    friday = datetime(2025, 9, 19)  # Friday
    latest_from_friday = manager.get_latest_operational_date(friday)
    print(
        f"  From Friday {friday.strftime('%Y-%m-%d')}: → {latest_from_friday.strftime('%Y-%m-%d')} ({latest_from_friday.strftime('%A')})"
    )

    print()
    print("Testing date range calculation:")

    # Test 7-day range
    start_date, end_date = manager.get_date_range_for_period(7)
    print(
        f"  7-day range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )

    # Test 30-day range
    start_date, end_date = manager.get_date_range_for_period(30)
    print(
        f"  30-day range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )

    print()
    print("=== Operational Day Logic Summary ===")
    print("✅ Monday-Saturday: Practice is operational, use current day data")
    print("📅 Sunday: Practice closed, automatically fallback to Saturday data")
    print("🔄 Smart fallback ensures users always see latest operational day data")
    print("🏥 Designed specifically for dental practice operational schedules")


if __name__ == "__main__":
    main()
