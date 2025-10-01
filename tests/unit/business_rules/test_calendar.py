# Unit tests for business calendar rules.
"""Ensure the BusinessCalendar correctly models Baytown and Humble schedules."""

from __future__ import annotations

from datetime import date

import pytest

from core.business_rules.calendar import BusinessCalendar


@pytest.fixture(scope="module")
def calendar() -> BusinessCalendar:
    """Provide a calendar anchored to the known open Saturday pattern."""

    return BusinessCalendar(saturday_anchor=date(2025, 1, 4))


def test_monday_is_open_for_both_locations(calendar: BusinessCalendar) -> None:
    """Both Baytown and Humble operate on Mondays."""

    target = date(2025, 1, 6)  # Monday
    assert calendar.is_business_day("baytown", target) is True
    assert calendar.is_business_day("humble", target) is True


def test_friday_is_closed_for_humble(calendar: BusinessCalendar) -> None:
    """Humble practices close on Fridays, Baytown remains open."""

    target = date(2025, 1, 3)  # Friday
    assert calendar.is_business_day("baytown", target) is True
    assert calendar.is_business_day("humble", target) is False
    assert (
        calendar.get_expected_closure_reason("humble", target)
        == "Humble is closed on Fridays"
    )


def test_baytown_alternating_saturdays(calendar: BusinessCalendar) -> None:
    """Baytown opens every other Saturday starting from the anchor date."""

    open_saturday = date(2025, 1, 4)
    closed_saturday = date(2025, 1, 11)
    next_open = date(2025, 1, 18)

    assert calendar.is_business_day("baytown", open_saturday) is True
    assert calendar.is_business_day("baytown", closed_saturday) is False
    assert (
        calendar.get_expected_closure_reason("baytown", closed_saturday)
        == "Baytown closes on alternating Saturdays"
    )
    assert calendar.is_business_day("baytown", next_open) is True


def test_sunday_is_closed_for_both_locations(calendar: BusinessCalendar) -> None:
    """Both locations remain closed on Sundays."""

    target = date(2025, 1, 5)  # Sunday
    assert calendar.is_business_day("baytown", target) is False
    assert calendar.is_business_day("humble", target) is False
    assert (
        calendar.get_expected_closure_reason("baytown", target) == "Closed on Sundays"
    )
    assert calendar.get_expected_closure_reason("humble", target) == "Closed on Sundays"
