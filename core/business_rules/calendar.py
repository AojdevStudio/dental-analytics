# Business calendar rules for practice locations.
"""Domain-specific business calendar logic for Baytown and Humble locations.

The calendar coordinates with configuration data to determine when each dental
practice location is expected to operate. It provides helpers for identifying
standard business days, alternating Saturday schedules, and the reasons behind
expected closures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from core.models.kpi_models import Location


@dataclass(slots=True)
class ExplicitOverrides:
    """Stores optional explicit open/closed date overrides for a location."""

    open_dates: set[date] = field(default_factory=set)
    closed_dates: set[date] = field(default_factory=set)


class BusinessCalendar:
    """Encapsulates business-day logic for supported practice locations."""

    _BASE_OPEN_WEEKDAYS: dict[Location, set[int]] = {
        "baytown": {0, 1, 2, 3, 4},  # Monday-Friday
        "humble": {0, 1, 2, 3},  # Monday-Thursday
    }

    def __init__(
        self,
        saturday_anchor: date = date(2025, 1, 4),
        overrides: dict[Location, ExplicitOverrides] | None = None,
    ) -> None:
        """Create a calendar with optional explicit open/closed overrides.

        Parameters
        ----------
        saturday_anchor:
            The reference Saturday that is known to be open for the alternating
            Baytown schedule. The pattern repeats every 14 days from this date.
        overrides:
            Optional explicit date overrides for each location. Closed overrides
            take precedence over open overrides to ensure safety for operations.
        """

        self._saturday_anchor = saturday_anchor
        self._overrides: dict[Location, ExplicitOverrides] = overrides or {
            "baytown": ExplicitOverrides(),
            "humble": ExplicitOverrides(),
        }

    def is_business_day(self, location: Location, target_date: date) -> bool:
        """Determine whether the requested date is a scheduled business day."""

        self._validate_location(location)

        override = self._overrides.get(location)
        if override and target_date in override.closed_dates:
            return False
        if override and target_date in override.open_dates:
            return True

        weekday = target_date.weekday()

        if weekday in self._BASE_OPEN_WEEKDAYS[location]:
            return True

        if weekday == 5:  # Saturday
            return self._is_open_saturday(location, target_date)

        # Sunday or unsupported weekday => closed
        return False

    def get_expected_closure_reason(
        self, location: Location, target_date: date
    ) -> str | None:
        """Explain why a date is not a business day, if known."""

        if self.is_business_day(location, target_date):
            return None

        override = self._overrides.get(location)
        if override and target_date in override.closed_dates:
            return "Closed per explicit override"

        weekday = target_date.weekday()
        if weekday == 6:
            return "Closed on Sundays"
        if weekday == 5:  # Saturday handling
            if location == "baytown":
                return "Baytown closes on alternating Saturdays"
            return "Humble is closed on Saturdays"
        if location == "humble" and weekday == 4:
            return "Humble is closed on Fridays"
        if location == "baytown" and weekday == 4:
            return None  # Baytown operates on Fridays normally
        return "Non-standard closure"

    def _is_open_saturday(self, location: Location, target_date: date) -> bool:
        """Return whether the Saturday follows the alternating open schedule."""

        if location != "baytown" or target_date.weekday() != 5:
            return False

        delta = target_date - self._saturday_anchor
        return delta.days % 14 == 0

    @staticmethod
    def _validate_location(location: Location) -> None:
        """Guard against unsupported locations early."""

        if location not in BusinessCalendar._BASE_OPEN_WEEKDAYS:
            raise ValueError(f"Unsupported location provided: {location}")
