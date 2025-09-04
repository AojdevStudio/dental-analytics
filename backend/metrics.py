# KPI calculations for dental analytics dashboard

import pandas as pd


class MetricsCalculator:
    """Calculates dental KPIs from raw data."""

    @staticmethod
    def calculate_production_total(df: pd.DataFrame) -> float | None:
        """Sum daily production from Column E (total_production)."""
        if df is None or df.empty:
            return None
        try:
            production_values = pd.to_numeric(df["total_production"], errors="coerce")
            return float(production_values.sum())
        except KeyError:
            return None

    @staticmethod
    def calculate_collection_rate(df: pd.DataFrame) -> float | None:
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
