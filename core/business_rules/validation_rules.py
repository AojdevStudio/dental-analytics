# Validation rules for KPI values based on business goals and acceptable ranges.
"""Goal-based validation rules for dental practice KPIs.

This module provides validation logic that compares actual KPI values against
configured business goals and acceptable ranges. It generates ValidationIssue
objects that describe when values are outside expected bounds.

The validation rules are loaded from config/business_rules/goals.yml and include:
- Daily production goals by location and day of week
- Collection rate acceptable ranges (50-110%, target 98-100%)
- Case acceptance acceptable ranges (target 80-90%, warning >100%)
- Hygiene reappointment acceptable ranges (95-100%)
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from core.models.kpi_models import Location, ValidationIssue, ValidationSeverity

logger = logging.getLogger(__name__)


class KPIValidationRules(BaseModel):
    """Validation rules for KPI values based on business goals.

    This class loads goal configurations from YAML and provides validation
    methods that return ValidationIssue objects when values are outside
    acceptable ranges.

    Attributes
    ----------
    goals_config:
        Dictionary loaded from goals.yml containing all target values and
        acceptable ranges for each KPI.

    Examples
    --------
    >>> rules = KPIValidationRules()
    >>> goal = rules.get_daily_production_goal("baytown", date(2025, 1, 6))  # Monday
    >>> goal
    6000.0

    >>> issues = rules.validate_production(8000, "baytown", date(2025, 1, 6))
    >>> len(issues)
    0  # Within acceptable variance

    >>> issues = rules.validate_production(12000, "baytown", date(2025, 1, 6))
    >>> len(issues)
    1  # Over 50% above goal - warning issued
    """

    goals_config: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True

    def __init__(self, **data: Any):
        """Initialize validation rules by loading goals configuration.

        Loads goals.yml from config/business_rules/ directory.
        If the file doesn't exist or is invalid, logs a warning and uses
        empty configuration (all validations will pass).
        """
        super().__init__(**data)

        # Load goals configuration from YAML file
        goals_path = Path("config/business_rules/goals.yml")

        if not goals_path.exists():
            logger.warning(
                "validation_rules.goals_file_missing",
                extra={"path": str(goals_path)},
            )
            self.goals_config = {}
            return

        try:
            with goals_path.open() as f:
                self.goals_config = yaml.safe_load(f) or {}
            logger.info(
                "validation_rules.goals_loaded",
                extra={"path": str(goals_path), "keys": list(self.goals_config.keys())},
            )
        except (yaml.YAMLError, OSError) as e:
            logger.error(
                "validation_rules.goals_load_failed",
                extra={"path": str(goals_path), "error": str(e)},
            )
            self.goals_config = {}

    def get_daily_production_goal(self, location: Location, target_date: date) -> float:
        """Get the daily production goal for a location on a specific date.

        Parameters
        ----------
        location:
            Practice location ("baytown" or "humble").
        target_date:
            The date to get the production goal for. Day of week determines
            which goal applies.

        Returns
        -------
        float
            The daily production goal in dollars. Returns 0.0 if no goal
            configured for the location/day combination.

        Examples
        --------
        >>> rules = KPIValidationRules()
        >>> rules.get_daily_production_goal("baytown", date(2025, 1, 6))  # Monday
        6000.0

        >>> rules.get_daily_production_goal("baytown", date(2025, 1, 10))  # Friday
        5500.0

        >>> rules.get_daily_production_goal("humble", date(2025, 1, 10))
        # Friday (closed)
        0.0
        """
        # Get day of week name in lowercase
        day_name = target_date.strftime("%A").lower()

        # Navigate through nested config structure
        production_goals = self.goals_config.get("production_goals", {})
        location_goals = production_goals.get(location, {})
        goal = location_goals.get(day_name, 0.0)

        logger.debug(
            "validation_rules.production_goal_retrieved",
            extra={
                "location": location,
                "date": str(target_date),
                "day_name": day_name,
                "goal": goal,
            },
        )

        return float(goal)

    def validate_production(
        self, value: float | None, location: Location, target_date: date
    ) -> list[ValidationIssue]:
        """Validate production value against daily goal with variance thresholds.

        Checks if production is significantly over or under the daily goal:
        - Warning if >50% over goal
        - Warning if >30% under goal

        Parameters
        ----------
        value:
            Actual production value in dollars.
        location:
            Practice location.
        target_date:
            Date for which production is being validated.

        Returns
        -------
        list[ValidationIssue]
            List of validation issues. Empty if within acceptable range.

        Examples
        --------
        >>> rules = KPIValidationRules()
        >>> rules.validate_production(6100, "baytown", date(2025, 1, 6))
        # Close to goal
        []

        >>> rules.validate_production(12000, "baytown", date(2025, 1, 6))  # 2x goal
        [ValidationIssue(code='production.over_goal', ...)]
        """
        issues: list[ValidationIssue] = []

        if value is None:
            return issues

        # Get the goal for this location/date
        goal = self.get_daily_production_goal(location, target_date)

        # If no goal configured (e.g., closed day), skip validation
        if goal == 0.0:
            logger.debug(
                "validation_rules.production_no_goal",
                extra={"location": location, "date": str(target_date)},
            )
            return issues

        # Get variance thresholds from config
        variance_config = self.goals_config.get("production_variance", {})
        over_threshold = variance_config.get("over_goal_threshold", 0.50)
        under_threshold = variance_config.get("under_goal_threshold", 0.30)

        # Calculate variance from goal
        variance = value - goal
        variance_pct = (variance / goal) * 100

        # Check if over goal threshold
        if variance > (goal * over_threshold):
            issues.append(
                ValidationIssue(
                    code="production.over_goal",
                    message=(
                        f"Production ${value:,.2f} is {variance_pct:.1f}% over "
                        f"goal of ${goal:,.2f}. Verify production entry is correct."
                    ),
                    severity=ValidationSeverity.WARNING,
                )
            )
            logger.info(
                "validation_rules.production_over_goal",
                extra={
                    "location": location,
                    "date": str(target_date),
                    "value": value,
                    "goal": goal,
                    "variance_pct": variance_pct,
                },
            )

        # Check if under goal threshold
        elif variance < -(goal * under_threshold):
            issues.append(
                ValidationIssue(
                    code="production.under_goal",
                    message=(
                        f"Production ${value:,.2f} is {abs(variance_pct):.1f}% under "
                        f"goal of ${goal:,.2f}. Consider reviewing daily metrics."
                    ),
                    severity=ValidationSeverity.WARNING,
                )
            )
            logger.info(
                "validation_rules.production_under_goal",
                extra={
                    "location": location,
                    "date": str(target_date),
                    "value": value,
                    "goal": goal,
                    "variance_pct": variance_pct,
                },
            )

        return issues

    def validate_collection_rate(self, value: float | None) -> list[ValidationIssue]:
        """Validate collection rate is within acceptable range.

        Target range: 98-100%
        Warning range: 50-110%

        Parameters
        ----------
        value:
            Collection rate as a percentage (e.g., 95.5 for 95.5%).

        Returns
        -------
        list[ValidationIssue]
            List of validation issues. Empty if within acceptable range.

        Examples
        --------
        >>> rules = KPIValidationRules()
        >>> rules.validate_collection_rate(99.0)  # Within target
        []

        >>> rules.validate_collection_rate(120.0)  # Over 110%
        [ValidationIssue(code='collection_rate.too_high', ...)]
        """
        issues: list[ValidationIssue] = []

        if value is None:
            return issues

        # Get thresholds from config
        config = self.goals_config.get("collection_rate", {})
        warning_min = config.get("warning_min", 50.0)
        warning_max = config.get("warning_max", 110.0)
        target_min = config.get("target_min", 98.0)
        target_max = config.get("target_max", 100.0)

        # Check if below minimum acceptable threshold
        if value < warning_min:
            issues.append(
                ValidationIssue(
                    code="collection_rate.too_low",
                    message=(
                        f"Collection rate {value:.1f}% is below acceptable minimum "
                        f"of {warning_min:.0f}%. Review collection procedures."
                    ),
                    severity=ValidationSeverity.ERROR,
                )
            )

        # Check if above maximum acceptable threshold
        elif value > warning_max:
            issues.append(
                ValidationIssue(
                    code="collection_rate.too_high",
                    message=(
                        f"Collection rate {value:.1f}% exceeds {warning_max:.0f}%. "
                        f"Verify production and collection entries."
                    ),
                    severity=ValidationSeverity.WARNING,
                )
            )

        # Check if outside target range (info only, not error/warning)
        elif value < target_min or value > target_max:
            issues.append(
                ValidationIssue(
                    code="collection_rate.outside_target",
                    message=(
                        f"Collection rate {value:.1f}% is outside target range "
                        f"of {target_min:.0f}-{target_max:.0f}%."
                    ),
                    severity=ValidationSeverity.INFO,
                )
            )

        return issues

    def validate_case_acceptance(self, value: float | None) -> list[ValidationIssue]:
        """Validate case acceptance rate is within acceptable range.

        Target range: 80-90%
        Warning if >100% (indicates data quality issue)

        Parameters
        ----------
        value:
            Case acceptance rate as a percentage (e.g., 85.0 for 85%).

        Returns
        -------
        list[ValidationIssue]
            List of validation issues. Empty if within acceptable range.

        Examples
        --------
        >>> rules = KPIValidationRules()
        >>> rules.validate_case_acceptance(85.0)  # Within target
        []

        >>> rules.validate_case_acceptance(105.0)  # Over 100%
        [ValidationIssue(code='case_acceptance.over_100', ...)]
        """
        issues: list[ValidationIssue] = []

        if value is None:
            return issues

        # Get thresholds from config
        config = self.goals_config.get("case_acceptance", {})
        warning_max = config.get("warning_max", 100.0)
        target_min = config.get("target_min", 80.0)
        target_max = config.get("target_max", 90.0)

        # Check if over 100% (data quality issue)
        if value > warning_max:
            issues.append(
                ValidationIssue(
                    code="case_acceptance.over_100",
                    message=(
                        f"Case acceptance {value:.1f}% exceeds 100%. "
                        f"Verify presented and scheduled treatment counts."
                    ),
                    severity=ValidationSeverity.WARNING,
                )
            )

        # Check if outside target range (info only)
        elif value < target_min:
            issues.append(
                ValidationIssue(
                    code="case_acceptance.below_target",
                    message=(
                        f"Case acceptance {value:.1f}% is below target minimum "
                        f"of {target_min:.0f}%."
                    ),
                    severity=ValidationSeverity.INFO,
                )
            )
        elif value > target_max:
            issues.append(
                ValidationIssue(
                    code="case_acceptance.above_target",
                    message=(
                        f"Case acceptance {value:.1f}% is above target maximum "
                        f"of {target_max:.0f}%."
                    ),
                    severity=ValidationSeverity.INFO,
                )
            )

        return issues

    def validate_hygiene_reappointment(
        self, value: float | None
    ) -> list[ValidationIssue]:
        """Validate hygiene reappointment rate is within valid range.

        Valid range: 0-100%
        Target: 95%+
        Error if outside 0-100% range (data quality issue)

        Parameters
        ----------
        value:
            Hygiene reappointment rate as a percentage (e.g., 96.5 for 96.5%).

        Returns
        -------
        list[ValidationIssue]
            List of validation issues. Empty if within acceptable range.

        Examples
        --------
        >>> rules = KPIValidationRules()
        >>> rules.validate_hygiene_reappointment(97.0)  # Within target
        []

        >>> rules.validate_hygiene_reappointment(105.0)  # Over 100%
        [ValidationIssue(code='hygiene_reappointment.invalid_range', ...)]
        """
        issues: list[ValidationIssue] = []

        if value is None:
            return issues

        # Get thresholds from config
        config = self.goals_config.get("hygiene_reappointment", {})
        error_min = config.get("error_min", 0.0)
        error_max = config.get("error_max", 100.0)
        target_min = config.get("target_min", 95.0)

        # Check if outside valid 0-100% range (data error)
        if value < error_min or value > error_max:
            issues.append(
                ValidationIssue(
                    code="hygiene_reappointment.invalid_range",
                    message=(
                        f"Hygiene reappointment {value:.1f}% is outside valid "
                        f"range of {error_min:.0f}-{error_max:.0f}%. "
                        f"Verify total hygiene and not reappointed counts."
                    ),
                    severity=ValidationSeverity.ERROR,
                )
            )

        # Check if below target (info only)
        elif value < target_min:
            issues.append(
                ValidationIssue(
                    code="hygiene_reappointment.below_target",
                    message=(
                        f"Hygiene reappointment {value:.1f}% is below target "
                        f"minimum of {target_min:.0f}%."
                    ),
                    severity=ValidationSeverity.INFO,
                )
            )

        return issues

    def validate_new_patients(self, value: int | None) -> list[ValidationIssue]:
        """Validate new patients count is reasonable.

        This is a simple validation that checks for obviously incorrect values.
        No specific goals enforced at this time.

        Parameters
        ----------
        value:
            New patients count for the period.

        Returns
        -------
        list[ValidationIssue]
            List of validation issues. Empty if value is reasonable.

        Examples
        --------
        >>> rules = KPIValidationRules()
        >>> rules.validate_new_patients(50)  # Normal count
        []

        >>> rules.validate_new_patients(-5)  # Negative (impossible)
        [ValidationIssue(code='new_patients.negative', ...)]
        """
        issues: list[ValidationIssue] = []

        if value is None:
            return issues

        # Check for negative values (data error)
        if value < 0:
            issues.append(
                ValidationIssue(
                    code="new_patients.negative",
                    message=(
                        f"New patients count {value} is negative. "
                        f"Verify data entry."
                    ),
                    severity=ValidationSeverity.ERROR,
                )
            )

        # Future: Could add monthly target validation here
        # config = self.goals_config.get("new_patients", {})
        # location_config = config.get(location, {})
        # monthly_target = location_config.get("monthly_target")

        return issues
