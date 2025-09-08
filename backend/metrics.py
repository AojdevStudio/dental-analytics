import pandas as pd


def _get_latest_entry(df: pd.DataFrame | None) -> pd.DataFrame | None:
    """Get the most recent date's data from the dataframe."""
    if df is None or df.empty:
        return None

    # Find the date column - look for common date column names
    date_columns = ["Date", "date", "DATE", "Timestamp", "timestamp"]
    date_col = None

    for col in date_columns:
        if col in df.columns:
            date_col = col
            break

    if date_col is None:
        # If no date column found, return the last row
        return df.tail(1)

    # Convert date column to datetime and get the latest date
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    if df.empty:
        return None

    # Get the latest date and return all rows for that date
    latest_date = df[date_col].max()
    return df[df[date_col] == latest_date]


def _safe_numeric_value(df: pd.DataFrame | None, col: str) -> float:
    """Helper: safely get numeric value from column, handling currency format."""
    if df is None or df.empty or col not in df.columns:
        return 0

    # Get the latest entry first
    latest_df = _get_latest_entry(df)
    if latest_df is None or latest_df.empty:
        return 0

    # Get the first value from the latest entry
    value = latest_df[col].iloc[0] if not latest_df[col].empty else 0

    # Clean and convert to numeric
    if isinstance(value, str):
        value = value.replace("$", "").replace(",", "").replace("%", "")

    return pd.to_numeric(value, errors="coerce") or 0


def calculate_production_total(df: pd.DataFrame | None) -> float | None:
    """Calculate daily production: Column I + J + K (Total Production + Adjustments + Write-offs)."""
    if df is None or df.empty:
        return None

    # Column I: Total Production Today
    # Column J: Adjustments Today
    # Column K: Write-offs Today
    prod_total = _safe_numeric_value(df, "Total Production Today")
    adjustments = _safe_numeric_value(df, "Adjustments Today")
    writeoffs = _safe_numeric_value(df, "Write-offs Today")

    total = prod_total + adjustments + writeoffs
    return float(total) if total > 0 else None


def calculate_collection_rate(df: pd.DataFrame | None) -> float | None:
    """Calculate collection rate: (L+M+N) / (I+J+K) * 100 for latest date only."""
    if df is None or df.empty:
        return None

    # Collections: Columns L+M+N (Patient Income + Insurance Income + Adjustment Offset)
    patient_income = _safe_numeric_value(df, "Patient Income Today")
    insurance_income = _safe_numeric_value(df, "Insurance Income Today")
    adjustment_offset = _safe_numeric_value(df, "Adjustment Offset Today")
    total_collections = patient_income + insurance_income + adjustment_offset

    # Production: Columns I+J+K
    prod_total = _safe_numeric_value(df, "Total Production Today")
    adjustments = _safe_numeric_value(df, "Adjustments Today")
    writeoffs = _safe_numeric_value(df, "Write-offs Today")
    total_production = prod_total + adjustments + writeoffs

    return (
        float((total_collections / total_production) * 100)
        if total_production > 0
        else None
    )


def calculate_new_patients(df: pd.DataFrame | None) -> int | None:
    """Get new patients from Column S: New Patients - Total Month to Date."""
    if df is None or df.empty:
        return None

    # Column S: New Patients - Total Month to Date
    new_patients = _safe_numeric_value(df, "New Patients - Total Month to Date")
    return int(new_patients) if new_patients >= 0 else None


def calculate_treatment_acceptance(df: pd.DataFrame | None) -> float | None:
    """Get treatment acceptance from Column R: Cases Accepted (Percentage)."""
    if df is None or df.empty:
        return None

    # Column R: Cases Accepted (Percentage) - already calculated as percentage
    acceptance_rate = _safe_numeric_value(df, "Cases Accepted (Percentage)")
    return float(acceptance_rate) if acceptance_rate >= 0 else None


def calculate_hygiene_reappointment(df: pd.DataFrame | None) -> float | None:
    """Calculate hygiene reappointment percentage for latest date."""
    if df is None or df.empty:
        return None

    total = _safe_numeric_value(df, "Total hygiene Appointments")
    not_reappointed = _safe_numeric_value(df, "Number of patients NOT reappointed?")

    if total <= 0:
        return None

    return float(((total - not_reappointed) / total) * 100)


def get_baytown_kpis() -> dict[str, float | None]:
    """Calculate KPIs for Baytown location."""
    from backend.sheets_reader import SheetsReader

    reader = SheetsReader()
    # Updated range to include all columns needed (A through S for new patients)
    eod_data = reader.get_sheet_data("EOD - Baytown Billing!A:S")
    front_kpi_data = reader.get_sheet_data("Baytown Front KPIs Form responses!A:S")

    return {
        "production_total": calculate_production_total(eod_data),
        "collection_rate": calculate_collection_rate(eod_data),
        "new_patients": calculate_new_patients(eod_data),
        "treatment_acceptance": calculate_treatment_acceptance(front_kpi_data),
        "hygiene_reappointment": calculate_hygiene_reappointment(front_kpi_data),
    }


def get_humble_kpis() -> dict[str, float | None]:
    """Calculate KPIs for Humble location."""
    from backend.sheets_reader import SheetsReader

    reader = SheetsReader()
    # Updated range to include all columns needed (A through S for new patients)
    eod_data = reader.get_sheet_data("EOD - Humble Billing!A:S")
    front_kpi_data = reader.get_sheet_data("Humble Front KPIs Form responses!A:S")

    return {
        "production_total": calculate_production_total(eod_data),
        "collection_rate": calculate_collection_rate(eod_data),
        "new_patients": calculate_new_patients(eod_data),
        "treatment_acceptance": calculate_treatment_acceptance(front_kpi_data),
        "hygiene_reappointment": calculate_hygiene_reappointment(front_kpi_data),
    }


def get_all_kpis() -> dict[str, dict[str, float | None]]:
    """Calculate all KPIs for both locations.

    Returns nested structure:
    {
        "baytown": {...kpis...},
        "humble": {...kpis...}
    }
    """
    return {
        "baytown": get_baytown_kpis(),
        "humble": get_humble_kpis(),
    }
