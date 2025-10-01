# Data transformers for converting Google Sheets DataFrames to calculator inputs.
"""Transforms raw pandas DataFrames from Google Sheets into clean numeric inputs.

This module extracts values from DataFrames, handles currency formatting,
deals with nulls and mixed types, and returns the simple numeric values
that the pure calculation functions expect.

The transformer layer sits between the data provider (which returns raw
DataFrames) and the calculators (which expect normalized numbers).
"""

from __future__ import annotations

import logging
import re

import pandas as pd
from pydantic import BaseModel

# Type alias for numeric values that can be None
Number = float | int | None

logger = logging.getLogger(__name__)


class SheetsToKPIInputs(BaseModel):
    """Transformer that extracts calculation inputs from Google Sheets DataFrames.

    This class provides methods to safely extract numeric values from DataFrame
    columns, handling common data quality issues like:
    - Currency formatting (e.g., "$1,234.56")
    - Null/missing values
    - Mixed data types (strings, numbers)
    - Empty DataFrames

    Each extraction method returns a tuple of numeric values ready for the
    calculator functions, or None values when data is unavailable.
    """

    class Config:
        """Pydantic configuration allowing arbitrary types like DataFrames."""

        arbitrary_types_allowed = True

    def _safe_extract(
        self, df: pd.DataFrame | None, column: str, default: Number = None
    ) -> Number:
        """Safely extract a numeric value from a DataFrame column.

        This helper handles all the common data quality issues:
        1. Checks if DataFrame exists and is not empty
        2. Checks if column exists in DataFrame
        3. Extracts the most recent value (last row: iloc[-1])
        4. Cleans currency formatting (removes $, commas)
        5. Converts to float
        6. Returns default value if any step fails

        Parameters
        ----------
        df:
            Source DataFrame from Google Sheets. Can be None or empty.
        column:
            Name of the column to extract value from.
        default:
            Value to return if extraction fails. Defaults to None.

        Returns
        -------
        Number
            The extracted and cleaned numeric value, or the default value.

        Examples
        --------
        >>> df = pd.DataFrame({"Production": ["$1,234.56", "$2,345.67"]})
        >>> transformer = SheetsToKPIInputs()
        >>> transformer._safe_extract(df, "Production")
        2345.67

        >>> transformer._safe_extract(df, "Missing Column")
        None

        >>> empty_df = pd.DataFrame()
        >>> transformer._safe_extract(empty_df, "Production", default=0.0)
        0.0
        """
        # Check if DataFrame exists and has data
        if df is None or df.empty:
            logger.debug(
                "sheets_transformer.empty_dataframe",
                extra={"column": column, "default": default},
            )
            return default

        # Check if column exists
        if column not in df.columns:
            logger.warning(
                "sheets_transformer.missing_column",
                extra={
                    "column": column,
                    "available_columns": list(df.columns),
                    "default": default,
                },
            )
            return default

        try:
            # Extract the most recent value (last row)
            value = df[column].iloc[-1] if len(df) > 0 else default

            # Handle None/NaN values
            if pd.isna(value) or value is None:
                logger.debug(
                    "sheets_transformer.null_value",
                    extra={"column": column, "default": default},
                )
                return default

            # Clean currency formatting if it's a string
            if isinstance(value, str):
                raw_value = value.strip()
                is_accounting_negative = raw_value.startswith(
                    "("
                ) and raw_value.endswith(")")
                if is_accounting_negative:
                    raw_value = raw_value[1:-1]

                # Remove dollar signs, commas, and whitespace
                cleaned = re.sub(r"[\$,\s]", "", raw_value)

                # Handle empty strings after cleaning
                if not cleaned:
                    logger.debug(
                        "sheets_transformer.empty_after_cleaning",
                        extra={"column": column, "original": value, "default": default},
                    )
                    return default

                # Convert to float and apply accounting negative when needed
                value = float(cleaned)
                if is_accounting_negative:
                    value = -value

            # Convert to float (handles int, float, numpy types)
            return float(value)

        except (ValueError, TypeError, IndexError, KeyError) as e:
            logger.warning(
                "sheets_transformer.extraction_failed",
                extra={
                    "column": column,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "default": default,
                },
            )
            return default

    def extract_production_inputs(
        self, eod_df: pd.DataFrame | None
    ) -> tuple[Number, Number, Number]:
        """Extract production calculation inputs from EOD billing DataFrame.

        Extracts the three values needed for production total calculation:
        - Gross production for the day
        - Adjustments applied (typically negative)
        - Write-offs applied (typically negative)

        Parameters
        ----------
        eod_df:
            EOD billing sheet DataFrame with columns:
            - "Total Production Today"
            - "Adjustments Today"
            - "Write-offs Today"

        Returns
        -------
        tuple[Number, Number, Number]
            (production, adjustments, writeoffs) ready for calculator.

        Examples
        --------
        >>> df = pd.DataFrame({
        ...     "Total Production Today": [7772.00],
        ...     "Adjustments Today": [-1572.00],
        ...     "Write-offs Today": [-17237.82]
        ... })
        >>> transformer = SheetsToKPIInputs()
        >>> transformer.extract_production_inputs(df)
        (7772.0, -1572.0, -17237.82)
        """
        production = self._safe_extract(eod_df, "Total Production Today")
        adjustments = self._safe_extract(eod_df, "Adjustments Today", default=0.0)
        writeoffs = self._safe_extract(eod_df, "Write-offs Today", default=0.0)

        logger.info(
            "sheets_transformer.production_inputs_extracted",
            extra={
                "production": production,
                "adjustments": adjustments,
                "writeoffs": writeoffs,
            },
        )

        return (production, adjustments, writeoffs)

    def extract_collection_inputs(
        self, eod_df: pd.DataFrame | None
    ) -> tuple[Number, Number, Number, Number, Number, Number]:
        """Extract collection rate calculation inputs from EOD billing DataFrame.

        Extracts all six values needed for collection rate calculation:
        - Production, adjustments, writeoffs (for denominator)
        - Patient income, unearned income, insurance income (for numerator)

        Parameters
        ----------
        eod_df:
            EOD billing sheet DataFrame with columns:
            - "Total Production Today"
            - "Adjustments Today"
            - "Write-offs Today"
            - "Patient Income Today"
            - "Unearned Income Today"
            - "Insurance Income Today"

        Returns
        -------
        tuple[Number, Number, Number, Number, Number, Number]
            (production, adjustments, writeoffs, patient_income, unearned_income,
             insurance_income) ready for calculator.

        Examples
        --------
        >>> df = pd.DataFrame({
        ...     "Total Production Today": [7772.00],
        ...     "Adjustments Today": [-1572.00],
        ...     "Write-offs Today": [-17237.82],
        ...     "Patient Income Today": [44482.52],
        ...     "Unearned Income Today": [0.0],
        ...     "Insurance Income Today": [7238.73]
        ... })
        >>> transformer = SheetsToKPIInputs()
        >>> inputs = transformer.extract_collection_inputs(df)
        >>> inputs[0]  # production
        7772.0
        """
        production = self._safe_extract(eod_df, "Total Production Today")
        adjustments = self._safe_extract(eod_df, "Adjustments Today", default=0.0)
        writeoffs = self._safe_extract(eod_df, "Write-offs Today", default=0.0)
        patient_income = self._safe_extract(eod_df, "Patient Income Today", default=0.0)
        unearned_income = self._safe_extract(
            eod_df, "Unearned Income Today", default=0.0
        )
        insurance_income = self._safe_extract(
            eod_df, "Insurance Income Today", default=0.0
        )

        logger.info(
            "sheets_transformer.collection_inputs_extracted",
            extra={
                "production": production,
                "adjustments": adjustments,
                "writeoffs": writeoffs,
                "patient_income": patient_income,
                "unearned_income": unearned_income,
                "insurance_income": insurance_income,
            },
        )

        return (
            production,
            adjustments,
            writeoffs,
            patient_income,
            unearned_income,
            insurance_income,
        )

    def extract_new_patients_inputs(self, eod_df: pd.DataFrame | None) -> tuple[Number]:
        """Extract new patients calculation input from EOD billing DataFrame.

        Extracts the month-to-date new patient count. This is a cumulative
        value in the spreadsheet, not a daily count.

        Parameters
        ----------
        eod_df:
            EOD billing sheet DataFrame with column:
            - "New Patients - Total Month to Date"

        Returns
        -------
        tuple[Number]
            (new_patients_mtd,) ready for calculator.

        Examples
        --------
        >>> df = pd.DataFrame({
        ...     "New Patients - Total Month to Date": [52]
        ... })
        >>> transformer = SheetsToKPIInputs()
        >>> transformer.extract_new_patients_inputs(df)
        (52.0,)
        """
        new_patients_mtd = self._safe_extract(
            eod_df, "New Patients - Total Month to Date"
        )

        logger.info(
            "sheets_transformer.new_patients_inputs_extracted",
            extra={"new_patients_mtd": new_patients_mtd},
        )

        return (new_patients_mtd,)

    def extract_case_acceptance_inputs(
        self, front_df: pd.DataFrame | None
    ) -> tuple[Number, Number, Number]:
        """Extract case acceptance calculation inputs from Front KPI DataFrame.

        Extracts the three values needed for case acceptance percentage:
        - Number of treatment plans presented
        - Number of treatments scheduled for future
        - Dollar value of same-day treatment acceptances

        Parameters
        ----------
        front_df:
            Front KPI sheet DataFrame with columns:
            - "treatments_presented"
            - "treatments_scheduled"
            - "$ Same Day Treatment"

        Returns
        -------
        tuple[Number, Number, Number]
            (treatments_presented, treatments_scheduled, same_day_treatment)
            ready for calculator.

        Examples
        --------
        >>> df = pd.DataFrame({
        ...     "treatments_presented": [52085],
        ...     "treatments_scheduled": [2715],
        ...     "$ Same Day Treatment": ["$1,907"]
        ... })
        >>> transformer = SheetsToKPIInputs()
        >>> transformer.extract_case_acceptance_inputs(df)
        (52085.0, 2715.0, 1907.0)
        """
        treatments_presented = self._safe_extract(front_df, "treatments_presented")
        treatments_scheduled = self._safe_extract(front_df, "treatments_scheduled")
        same_day_treatment = self._safe_extract(front_df, "$ Same Day Treatment")

        logger.info(
            "sheets_transformer.case_acceptance_inputs_extracted",
            extra={
                "treatments_presented": treatments_presented,
                "treatments_scheduled": treatments_scheduled,
                "same_day_treatment": same_day_treatment,
            },
        )

        return (treatments_presented, treatments_scheduled, same_day_treatment)

    def extract_hygiene_inputs(
        self, front_df: pd.DataFrame | None
    ) -> tuple[Number, Number]:
        """Extract hygiene reappointment calculation inputs from Front KPI DataFrame.

        Extracts the two values needed for hygiene reappointment percentage:
        - Total number of hygiene appointments completed
        - Number of patients who did not rebook

        Parameters
        ----------
        front_df:
            Front KPI sheet DataFrame with columns:
            - "Total hygiene Appointments"
            - "Number of patients NOT reappointed?"

        Returns
        -------
        tuple[Number, Number]
            (total_hygiene, not_reappointed) ready for calculator.

        Examples
        --------
        >>> df = pd.DataFrame({
        ...     "Total hygiene Appointments": [7],
        ...     "Number of patients NOT reappointed?": [0]
        ... })
        >>> transformer = SheetsToKPIInputs()
        >>> transformer.extract_hygiene_inputs(df)
        (7.0, 0.0)
        """
        total_hygiene = self._safe_extract(front_df, "Total hygiene Appointments")
        not_reappointed = self._safe_extract(
            front_df, "Number of patients NOT reappointed?"
        )

        logger.info(
            "sheets_transformer.hygiene_inputs_extracted",
            extra={
                "total_hygiene": total_hygiene,
                "not_reappointed": not_reappointed,
            },
        )

        return (total_hygiene, not_reappointed)
