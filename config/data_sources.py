"""Data Sources Configuration for Historical Data Collection.

Configures data source mapping, operational schedules, and chart defaults
for dental practice analytics. Supports Monday-Saturday operational
schedule with Sunday/holiday fallback logic.
"""

import sys
from datetime import datetime, timedelta

import structlog

# Configure structured logging to stderr
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)

log = structlog.get_logger()

# Google Sheets Configuration
SPREADSHEET_ID = "1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Data Source Definitions
DATA_SOURCES = {
    "eod_billing": {
        "sheet_name": "EOD - Baytown Billing",
        "range_suffix": "A:N",
        "date_column": "Submission Date",
        "operational_days_only": True,  # Monday-Saturday for dental practice
        "latest_fallback": True,
        "description": "End of Day billing data with production and collection metrics",
    },
    "front_kpis": {
        "sheet_name": "Baytown Front KPIs Form responses",
        "range_suffix": "A:N",
        "date_column": "Submission Date",
        "operational_days_only": True,  # Monday-Saturday for dental practice
        "latest_fallback": True,
        "description": "Front office KPIs including treatment acceptance and hygiene",
    },
}

# Operational Schedule Configuration
OPERATIONAL_SCHEDULE = {
    "operational_days": [0, 1, 2, 3, 4, 5],  # Monday=0 to Saturday=5
    "non_operational_days": [6],  # Sunday=6
    "practice_name": "Baytown Dental",
    "timezone": "America/Chicago",
}

# Chart Configuration Defaults
CHART_DEFAULTS = {
    "historical_range_days": 30,
    "max_range_days": 90,
    "min_data_points": 5,
    "date_format": "%Y-%m-%d",
    "timestamp_format": "%Y-%m-%d %H:%M:%S",
    "missing_data_policy": "skip",  # 'skip', 'interpolate', or 'zero'
}

# Column Mapping for Historical Data
# VALIDATED AGAINST ACTUAL GOOGLE SHEETS (2025-09-15)
COLUMN_MAPPINGS = {
    "eod_billing": {
        "date": "Submission Date",
        "production": "Total Production Today",  # Column I
        "adjustments": "Adjustments Today",  # Column J
        "writeoffs": "Write-offs Today",  # Column K
        "new_patients_mtd": "New Patients - Total Month to Date",  # Column S
        # Collections = Patient Income + Unearned Income + Insurance Income
        "patient_income": "Patient Income Today",  # Column L
        "unearned_income": "Unearned Income Today",  # Column M
        "insurance_income": "Insurance Income Today",  # Column N
    },
    "front_kpis": {
        "date": "Submission Date",
        "treatments_presented": "treatments_presented",  # Column L
        "treatments_scheduled": "treatments_scheduled",  # Column M
        "hygiene_total": "Total hygiene Appointments",  # Column C
        "hygiene_not_reappointed": "Number of patients NOT reappointed?",  # Column D
        "same_day_treatment": "$ Same Day Treatment",  # Column N
        "follow_ups_created": "# of Follow ups created",  # Column G
        "total_calls": "# OF UNSCHEDULED TX CALLS",  # Column E
        "patients_scheduled": "# of patient Scheduled",  # Column F
    },
}


def get_data_source_config(source_name: str) -> dict | None:
    """Get configuration for a specific data source.

    Args:
        source_name: Name of the data source ('eod_billing' or 'front_kpis')

    Returns:
        Configuration dictionary or None if source not found
    """
    if source_name not in DATA_SOURCES:
        log.warning("data_source.not_found", source=source_name)
        return None

    config = DATA_SOURCES[source_name].copy()
    config["full_range"] = f"{config['sheet_name']}!{config['range_suffix']}"

    log.debug("data_source.config_retrieved", source=source_name)
    return config


def is_operational_day(date: datetime) -> bool:
    """Check if a given date is an operational day (Monday-Saturday).

    Args:
        date: Date to check

    Returns:
        True if operational day, False if non-operational (Sunday)
    """
    weekday = date.weekday()  # Monday=0, Sunday=6
    is_operational = weekday in OPERATIONAL_SCHEDULE["operational_days"]

    log.debug(
        "operational_day.check",
        date=date.strftime("%Y-%m-%d"),
        weekday=weekday,
        is_operational=is_operational,
    )

    return is_operational


def get_latest_operational_date(reference_date: datetime | None = None) -> datetime:
    """Get the most recent operational day from a reference date.

    Args:
        reference_date: Date to work backward from (defaults to today)

    Returns:
        Most recent operational day (Monday-Saturday)
    """
    if reference_date is None:
        reference_date = datetime.now()

    # Remove time component for date calculations
    check_date = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # Look back up to 7 days to find last operational day
    for days_back in range(8):
        candidate_date = check_date - timedelta(days=days_back)
        if is_operational_day(candidate_date):
            log.info(
                "latest_operational.found",
                reference_date=reference_date.strftime("%Y-%m-%d"),
                latest_operational=candidate_date.strftime("%Y-%m-%d"),
                days_back=days_back,
            )
            return candidate_date

    # Fallback: should never reach here with normal schedule
    log.error(
        "latest_operational.not_found",
        reference_date=reference_date.strftime("%Y-%m-%d"),
    )
    return check_date


def get_historical_date_range(days_back: int = 30) -> tuple[datetime, datetime]:
    """Get date range for historical data collection.

    Args:
        days_back: Number of days to look back from latest operational day

    Returns:
        Tuple of (start_date, end_date) for historical range
    """
    end_date = get_latest_operational_date()
    start_date = end_date - timedelta(days=days_back)

    log.info(
        "historical_range.calculated",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        days_back=days_back,
    )

    return start_date, end_date


def get_operational_days_in_range(
    start_date: datetime, end_date: datetime
) -> list[datetime]:
    """Get list of operational days within a date range.

    Args:
        start_date: Start of date range
        end_date: End of date range

    Returns:
        List of operational dates (Monday-Saturday only)
    """
    operational_days = []
    current_date = start_date

    while current_date <= end_date:
        if is_operational_day(current_date):
            operational_days.append(current_date)
        current_date += timedelta(days=1)

    log.debug(
        "operational_days.calculated",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        count=len(operational_days),
    )

    return operational_days


def validate_data_source_config() -> bool:
    """Validate data source configuration integrity.

    Returns:
        True if configuration is valid, False otherwise
    """
    required_keys = ["sheet_name", "range_suffix", "date_column"]

    for source_name, config in DATA_SOURCES.items():
        for key in required_keys:
            if key not in config:
                log.error(
                    "config.validation_failed",
                    source=source_name,
                    missing_key=key,
                )
                return False

        # Validate column mappings exist
        if source_name not in COLUMN_MAPPINGS:
            log.error(
                "config.validation_failed",
                source=source_name,
                missing_mapping=True,
            )
            return False

    log.info("config.validation_passed")
    return True


def validate_column_mappings_against_sheets() -> dict[str, bool]:
    """Validation gate for Story 2.1: Verify column mappings against actual Google Sheets.

    This function validates that all mapped columns actually exist in the target sheets.
    Critical for ensuring data collection reliability in historical metrics.

    Returns:
        Dictionary with validation results per data source
    """
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from pathlib import Path

    log.info("column_validation.story_2_1_gate_start")

    validation_results = {}

    # Initialize Google Sheets service
    credentials_path = "config/credentials.json"
    if not Path(credentials_path).exists():
        log.error("column_validation.credentials_missing", path=credentials_path)
        return {source: False for source in DATA_SOURCES.keys()}

    try:
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES
        )
        service = build("sheets", "v4", credentials=creds)

        # Validate each data source
        for source_name, source_config in DATA_SOURCES.items():
            log.info("column_validation.checking_source", source=source_name)

            # Get header row from sheet
            range_name = f"{source_config['sheet_name']}!1:1"
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=SPREADSHEET_ID, range=range_name)
                .execute()
            )

            actual_columns = (
                result.get("values", [[]])[0] if result.get("values") else []
            )
            mapped_columns = list(COLUMN_MAPPINGS.get(source_name, {}).values())

            # Check if all mapped columns exist in actual sheet
            missing_columns = [
                col for col in mapped_columns if col not in actual_columns
            ]

            if missing_columns:
                log.error(
                    "column_validation.missing_columns",
                    source=source_name,
                    missing=missing_columns,
                    available=actual_columns,
                )
                validation_results[source_name] = False
            else:
                log.info(
                    "column_validation.source_valid",
                    source=source_name,
                    mapped_count=len(mapped_columns),
                )
                validation_results[source_name] = True

    except Exception as e:
        log.error("column_validation.failed", error=str(e))
        return {source: False for source in DATA_SOURCES.keys()}

    all_valid = all(validation_results.values())
    log.info(
        "column_validation.story_2_1_gate_complete",
        all_valid=all_valid,
        results=validation_results,
    )

    return validation_results


def get_actual_sheet_columns(source_name: str) -> list[str]:
    """Get actual column names from a Google Sheet for debugging.

    Args:
        source_name: Name of the data source ('eod_billing' or 'front_kpis')

    Returns:
        List of actual column names from the sheet
    """
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from pathlib import Path

    if source_name not in DATA_SOURCES:
        log.error("get_columns.invalid_source", source=source_name)
        return []

    credentials_path = "config/credentials.json"
    if not Path(credentials_path).exists():
        log.error("get_columns.credentials_missing", path=credentials_path)
        return []

    try:
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES
        )
        service = build("sheets", "v4", credentials=creds)

        sheet_name = DATA_SOURCES[source_name]["sheet_name"]
        range_name = f"{sheet_name}!1:1"

        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=SPREADSHEET_ID, range=range_name)
            .execute()
        )

        columns = result.get("values", [[]])[0] if result.get("values") else []

        log.info("get_columns.success", source=source_name, column_count=len(columns))

        return columns

    except Exception as e:
        log.error("get_columns.failed", source=source_name, error=str(e))
        return []


def calculate_total_collections(
    patient_income: float, unearned_income: float, insurance_income: float
) -> float:
    """Calculate total collections from the three income components.

    Collections = Patient Income + Unearned Income + Insurance Income

    Args:
        patient_income: Patient payment amount
        unearned_income: Unearned income amount
        insurance_income: Insurance payment amount

    Returns:
        Total collections amount
    """
    total = patient_income + unearned_income + insurance_income

    log.debug(
        "collections.calculated",
        patient_income=patient_income,
        unearned_income=unearned_income,
        insurance_income=insurance_income,
        total=total,
    )

    return total
