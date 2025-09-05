import pandas as pd


class MetricsCalculator:
    """Calculates dental KPIs from raw data."""

    @staticmethod
    def calculate_production_total(df: pd.DataFrame | None) -> float | None:
        """Sum daily production from Column E (total_production)."""
        if df is None or df.empty:
            return None
        try:
            return float(pd.to_numeric(df["total_production"], errors="coerce").sum())
        except KeyError:
            return None

    @staticmethod
    def calculate_collection_rate(df: pd.DataFrame | None) -> float | None:
        """Calculate collection rate percentage: (collections / production) * 100."""
        if df is None or df.empty:
            return None
        try:
            collections = pd.to_numeric(df["total_collections"], errors="coerce").sum()
            production = pd.to_numeric(df["total_production"], errors="coerce").sum()
            if production == 0:
                return None
            return float((collections / production) * 100)
        except KeyError:
            return None

    @staticmethod
    def calculate_new_patients(df: pd.DataFrame | None) -> int | None:
        """Count new patients from Column J (new_patients) in EOD sheets."""
        if df is None or df.empty:
            return None
        try:
            return int(pd.to_numeric(df["new_patients"], errors="coerce").sum())
        except KeyError:
            return None

    @staticmethod
    def calculate_treatment_acceptance(df: pd.DataFrame | None) -> float | None:
        """Calculate treatment acceptance rate: (scheduled / presented) * 100."""
        if df is None or df.empty:
            return None
        try:
            scheduled = pd.to_numeric(df["treatments_scheduled"], errors="coerce").sum()
            presented = pd.to_numeric(df["treatments_presented"], errors="coerce").sum()
            if presented == 0:
                return None
            return float((scheduled / presented) * 100)
        except KeyError:
            return None

    @staticmethod
    def get_all_kpis() -> dict[str, float | None]:
        """Orchestrate all KPI calculations from Google Sheets data."""
        from backend.sheets_reader import SheetsReader

        reader = SheetsReader()
        eod_data = reader.get_sheet_data("EOD - Baytown Billing!A:N")
        front_kpi_data = reader.get_sheet_data("Front KPI - Baytown!A:N")
        return {
            "production_total": MetricsCalculator.calculate_production_total(eod_data),
            "collection_rate": MetricsCalculator.calculate_collection_rate(eod_data),
            "new_patients": MetricsCalculator.calculate_new_patients(eod_data),
            "treatment_acceptance": MetricsCalculator.calculate_treatment_acceptance(
                front_kpi_data
            ),
        }
