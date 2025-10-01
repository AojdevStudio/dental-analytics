# Tests for validation_rules.py
"""Comprehensive tests for KPI validation rules with goal-based checks.

Tests cover:
- Loading goals from YAML configuration
- Daily production goal retrieval by location and day of week
- Production validation with variance thresholds (±50% over, ±30% under)
- Collection rate validation (50-110% acceptable, 98-100% target)
- Case acceptance validation (target 80-90%, warning >100%)
- Hygiene reappointment validation (95%+ target, error if outside 0-100%)
- New patients validation (negative check)
"""

from datetime import date

from core.business_rules.validation_rules import KPIValidationRules
from core.models.kpi_models import ValidationSeverity


class TestGoalsLoading:
    """Tests for loading goals configuration from YAML."""

    def test_loads_goals_on_init(self):
        """Should load goals.yml configuration during initialization."""
        rules = KPIValidationRules()

        assert rules.goals_config is not None
        assert "production_goals" in rules.goals_config
        assert "production_variance" in rules.goals_config
        assert "collection_rate" in rules.goals_config

    def test_handles_missing_goals_file(self, tmp_path, monkeypatch):
        """Should handle missing goals.yml gracefully."""
        # Change to temp directory where goals.yml doesn't exist
        monkeypatch.chdir(tmp_path)

        rules = KPIValidationRules()

        assert rules.goals_config == {}


class TestGetDailyProductionGoal:
    """Tests for retrieving daily production goals."""

    def test_baytown_monday_goal(self):
        """Should return $7,620 for Baytown on Monday."""
        rules = KPIValidationRules()
        monday = date(2025, 1, 6)  # Monday

        goal = rules.get_daily_production_goal("baytown", monday)

        assert goal == 7620.0

    def test_baytown_friday_goal(self):
        """Should return $6,980 for Baytown on Friday."""
        rules = KPIValidationRules()
        friday = date(2025, 1, 10)  # Friday

        goal = rules.get_daily_production_goal("baytown", friday)

        assert goal == 6980.0

    def test_baytown_saturday_goal(self):
        """Should return $5,080 for Baytown on Saturday."""
        rules = KPIValidationRules()
        saturday = date(2025, 1, 11)  # Saturday

        goal = rules.get_daily_production_goal("baytown", saturday)

        assert goal == 5080.0

    def test_humble_monday_goal(self):
        """Should return $7,500 for Humble on Monday."""
        rules = KPIValidationRules()
        monday = date(2025, 1, 6)  # Monday

        goal = rules.get_daily_production_goal("humble", monday)

        assert goal == 7500.0

    def test_humble_friday_goal_closed(self):
        """Should return $0 for Humble on Friday (closed)."""
        rules = KPIValidationRules()
        friday = date(2025, 1, 10)  # Friday

        goal = rules.get_daily_production_goal("humble", friday)

        assert goal == 0.0

    def test_sunday_goals_zero_both_locations(self):
        """Should return $0 for both locations on Sunday (closed)."""
        rules = KPIValidationRules()
        sunday = date(2025, 1, 12)  # Sunday

        baytown_goal = rules.get_daily_production_goal("baytown", sunday)
        humble_goal = rules.get_daily_production_goal("humble", sunday)

        assert baytown_goal == 0.0
        assert humble_goal == 0.0


class TestValidateProduction:
    """Tests for production validation with goal-based variance checks."""

    def test_within_acceptable_range_no_issues(self):
        """Should return no issues when production is close to goal."""
        rules = KPIValidationRules()
        monday = date(2025, 1, 6)  # Monday, Baytown goal $7,620

        # $7,700 is ~1.1% over goal - within acceptable variance
        issues = rules.validate_production(7700, "baytown", monday)

        assert len(issues) == 0

    def test_slightly_under_goal_no_issues(self):
        """Should return no issues when production is slightly under goal."""
        rules = KPIValidationRules()
        monday = date(2025, 1, 6)  # Monday, Baytown goal $7,620

        # $6,500 is ~14.7% under goal - within acceptable variance (< 30%)
        issues = rules.validate_production(6500, "baytown", monday)

        assert len(issues) == 0

    def test_over_goal_threshold_warning(self):
        """Should warn when production is >50% over goal."""
        rules = KPIValidationRules()
        monday = date(2025, 1, 6)  # Monday, Baytown goal $7,620

        # $12,000 is 57.5% over goal - should trigger warning
        issues = rules.validate_production(12000, "baytown", monday)

        assert len(issues) == 1
        assert issues[0].code == "production.over_goal"
        assert issues[0].severity == ValidationSeverity.WARNING
        assert "57.5%" in issues[0].message

    def test_under_goal_threshold_warning(self):
        """Should warn when production is >30% under goal."""
        rules = KPIValidationRules()
        monday = date(2025, 1, 6)  # Monday, Baytown goal $7,620

        # $3,500 is 54.1% under goal - should trigger warning
        issues = rules.validate_production(3500, "baytown", monday)

        assert len(issues) == 1
        assert issues[0].code == "production.under_goal"
        assert issues[0].severity == ValidationSeverity.WARNING
        assert "54.1%" in issues[0].message

    def test_exactly_at_goal_no_issues(self):
        """Should return no issues when production exactly matches goal."""
        rules = KPIValidationRules()
        monday = date(2025, 1, 6)  # Monday, Baytown goal $7,620

        issues = rules.validate_production(7620, "baytown", monday)

        assert len(issues) == 0

    def test_closed_day_no_validation(self):
        """Should skip validation when goal is 0 (closed day)."""
        rules = KPIValidationRules()
        sunday = date(2025, 1, 12)  # Sunday, both locations closed

        # Even with high production, no validation on closed days
        issues = rules.validate_production(10000, "baytown", sunday)

        assert len(issues) == 0

    def test_none_value_no_issues(self):
        """Should return no issues when value is None."""
        rules = KPIValidationRules()
        monday = date(2025, 1, 6)

        issues = rules.validate_production(None, "baytown", monday)

        assert len(issues) == 0


class TestValidateCollectionRate:
    """Tests for collection rate validation."""

    def test_within_target_range_no_issues(self):
        """Should return no issues when collection rate is 98-100%."""
        rules = KPIValidationRules()

        issues = rules.validate_collection_rate(99.0)

        assert len(issues) == 0

    def test_below_target_info_issue(self):
        """Should return info issue when below 98% target."""
        rules = KPIValidationRules()

        issues = rules.validate_collection_rate(95.0)

        assert len(issues) == 1
        assert issues[0].code == "collection_rate.outside_target"
        assert issues[0].severity == ValidationSeverity.INFO

    def test_above_target_info_issue(self):
        """Should return info issue when above 100% target."""
        rules = KPIValidationRules()

        issues = rules.validate_collection_rate(105.0)

        assert len(issues) == 1
        assert issues[0].code == "collection_rate.outside_target"
        assert issues[0].severity == ValidationSeverity.INFO

    def test_below_warning_threshold_error(self):
        """Should return error when collection rate below 50%."""
        rules = KPIValidationRules()

        issues = rules.validate_collection_rate(40.0)

        assert len(issues) == 1
        assert issues[0].code == "collection_rate.too_low"
        assert issues[0].severity == ValidationSeverity.ERROR

    def test_above_warning_threshold_warning(self):
        """Should return warning when collection rate above 110%."""
        rules = KPIValidationRules()

        issues = rules.validate_collection_rate(120.0)

        assert len(issues) == 1
        assert issues[0].code == "collection_rate.too_high"
        assert issues[0].severity == ValidationSeverity.WARNING

    def test_none_value_no_issues(self):
        """Should return no issues when value is None."""
        rules = KPIValidationRules()

        issues = rules.validate_collection_rate(None)

        assert len(issues) == 0


class TestValidateCaseAcceptance:
    """Tests for case acceptance validation."""

    def test_within_target_range_no_issues(self):
        """Should return no issues when case acceptance is 80-90%."""
        rules = KPIValidationRules()

        issues = rules.validate_case_acceptance(85.0)

        assert len(issues) == 0

    def test_below_target_info_issue(self):
        """Should return info issue when below 80% target."""
        rules = KPIValidationRules()

        issues = rules.validate_case_acceptance(75.0)

        assert len(issues) == 1
        assert issues[0].code == "case_acceptance.below_target"
        assert issues[0].severity == ValidationSeverity.INFO

    def test_above_target_info_issue(self):
        """Should return info issue when above 90% target but below 100%."""
        rules = KPIValidationRules()

        issues = rules.validate_case_acceptance(95.0)

        assert len(issues) == 1
        assert issues[0].code == "case_acceptance.above_target"
        assert issues[0].severity == ValidationSeverity.INFO

    def test_over_100_percent_warning(self):
        """Should return warning when case acceptance above 100%."""
        rules = KPIValidationRules()

        issues = rules.validate_case_acceptance(105.0)

        assert len(issues) == 1
        assert issues[0].code == "case_acceptance.over_100"
        assert issues[0].severity == ValidationSeverity.WARNING

    def test_none_value_no_issues(self):
        """Should return no issues when value is None."""
        rules = KPIValidationRules()

        issues = rules.validate_case_acceptance(None)

        assert len(issues) == 0


class TestValidateHygieneReappointment:
    """Tests for hygiene reappointment validation."""

    def test_within_target_range_no_issues(self):
        """Should return no issues when hygiene reappointment is 95%+."""
        rules = KPIValidationRules()

        issues = rules.validate_hygiene_reappointment(97.0)

        assert len(issues) == 0

    def test_below_target_info_issue(self):
        """Should return info issue when below 95% target."""
        rules = KPIValidationRules()

        issues = rules.validate_hygiene_reappointment(90.0)

        assert len(issues) == 1
        assert issues[0].code == "hygiene_reappointment.below_target"
        assert issues[0].severity == ValidationSeverity.INFO

    def test_below_zero_error(self):
        """Should return error when hygiene reappointment below 0%."""
        rules = KPIValidationRules()

        issues = rules.validate_hygiene_reappointment(-5.0)

        assert len(issues) == 1
        assert issues[0].code == "hygiene_reappointment.invalid_range"
        assert issues[0].severity == ValidationSeverity.ERROR

    def test_above_100_error(self):
        """Should return error when hygiene reappointment above 100%."""
        rules = KPIValidationRules()

        issues = rules.validate_hygiene_reappointment(105.0)

        assert len(issues) == 1
        assert issues[0].code == "hygiene_reappointment.invalid_range"
        assert issues[0].severity == ValidationSeverity.ERROR

    def test_none_value_no_issues(self):
        """Should return no issues when value is None."""
        rules = KPIValidationRules()

        issues = rules.validate_hygiene_reappointment(None)

        assert len(issues) == 0


class TestValidateNewPatients:
    """Tests for new patients validation."""

    def test_positive_count_no_issues(self):
        """Should return no issues for positive new patient count."""
        rules = KPIValidationRules()

        issues = rules.validate_new_patients(50)

        assert len(issues) == 0

    def test_zero_count_no_issues(self):
        """Should return no issues for zero new patients."""
        rules = KPIValidationRules()

        issues = rules.validate_new_patients(0)

        assert len(issues) == 0

    def test_negative_count_error(self):
        """Should return error when new patients is negative."""
        rules = KPIValidationRules()

        issues = rules.validate_new_patients(-5)

        assert len(issues) == 1
        assert issues[0].code == "new_patients.negative"
        assert issues[0].severity == ValidationSeverity.ERROR

    def test_none_value_no_issues(self):
        """Should return no issues when value is None."""
        rules = KPIValidationRules()

        issues = rules.validate_new_patients(None)

        assert len(issues) == 0


class TestEdgeCases:
    """Edge case tests for validation robustness."""

    def test_production_with_zero_goal(self):
        """Should handle production validation when goal is 0."""
        rules = KPIValidationRules()
        sunday = date(2025, 1, 12)  # Sunday, closed

        # Even $0 production on closed day should not trigger issues
        issues = rules.validate_production(0, "baytown", sunday)

        assert len(issues) == 0

    def test_collection_rate_exact_boundaries(self):
        """Should handle exact boundary values correctly."""
        rules = KPIValidationRules()

        # Exactly at warning thresholds
        issues_50 = rules.validate_collection_rate(50.0)
        issues_110 = rules.validate_collection_rate(110.0)

        # Should be acceptable (not below/above threshold)
        assert len(issues_50) == 1  # Outside target, but not error
        assert issues_50[0].severity == ValidationSeverity.INFO
        assert len(issues_110) == 1  # Outside target, but not warning
        assert issues_110[0].severity == ValidationSeverity.INFO

    def test_hygiene_exact_boundaries(self):
        """Should handle exact 0% and 100% correctly."""
        rules = KPIValidationRules()

        issues_0 = rules.validate_hygiene_reappointment(0.0)
        issues_100 = rules.validate_hygiene_reappointment(100.0)

        # 0% is valid (though below target)
        assert len(issues_0) == 1
        assert issues_0[0].code == "hygiene_reappointment.below_target"

        # 100% is valid and meets target
        assert len(issues_100) == 0
