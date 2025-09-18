# Tests for Google Sheets integration and data retrieval

from typing import Any
from unittest.mock import Mock, patch

from googleapiclient.errors import HttpError

from apps.backend.sheets_reader import SCOPES, SPREADSHEET_ID, SheetsReader


class TestSheetsReader:
    """Test cases for SheetsReader class."""

    def test_initialization_success(self) -> None:
        """Test successful SheetsReader initialization."""
        with (
            patch("apps.backend.sheets_reader.service_account"),
            patch("apps.backend.sheets_reader.build"),
            patch("apps.backend.sheets_reader.Path.exists", return_value=True),
        ):
            reader = SheetsReader()
            assert reader.service is not None

    def test_initialization_failure(self) -> None:
        """Test SheetsReader initialization failure."""
        with patch("apps.backend.sheets_reader.service_account") as mock_sa:
            mock_sa.Credentials.from_service_account_file.side_effect = (
                FileNotFoundError("credentials.json not found")
            )

            reader = SheetsReader()
            assert reader.service is None

    def test_get_sheet_data_success(self) -> None:
        """Test successful sheet data retrieval."""
        mock_service = Mock()
        mock_values: list[list[str]] = [
            ["Date", "Provider", "Production"],
            ["2024-01-15", "Dr. Smith", "5000"],
            ["2024-01-16", "Dr. Jones", "4500"],
        ]

        mock_result: dict[str, Any] = {"values": mock_values}
        mock_service.spreadsheets().values().get().execute.return_value = mock_result

        with (
            patch("apps.backend.sheets_reader.service_account"),
            patch("apps.backend.sheets_reader.build", return_value=mock_service),
            patch("apps.backend.sheets_reader.Path.exists", return_value=True),
        ):

            reader = SheetsReader()
            df = reader.get_sheet_data("TestSheet")

            assert df is not None
            assert len(df) == 2
            assert list(df.columns) == ["Date", "Provider", "Production"]
            assert df.iloc[0]["Provider"] == "Dr. Smith"

    def test_get_sheet_data_no_data(self) -> None:
        """Test sheet data retrieval with no data returned."""
        mock_service = Mock()
        mock_result: dict[str, Any] = {}  # No 'values' key
        mock_service.spreadsheets().values().get().execute.return_value = mock_result

        with (
            patch("apps.backend.sheets_reader.service_account"),
            patch("apps.backend.sheets_reader.build", return_value=mock_service),
            patch("apps.backend.sheets_reader.Path.exists", return_value=True),
        ):

            reader = SheetsReader()
            df = reader.get_sheet_data("TestSheet")

            assert df is None

    def test_get_sheet_data_service_not_initialized(self) -> None:
        """Test sheet data retrieval when service is not initialized."""
        reader = SheetsReader()
        reader.service = None

        df = reader.get_sheet_data("TestSheet")
        assert df is None

    def test_get_sheet_data_api_error(self) -> None:
        """Test sheet data retrieval with API error."""
        mock_service = Mock()
        mock_service.spreadsheets().values().get().execute.side_effect = HttpError(
            resp=Mock(status=404), content=b"Not found"
        )

        with (
            patch("apps.backend.sheets_reader.service_account"),
            patch("apps.backend.sheets_reader.build", return_value=mock_service),
            patch("apps.backend.sheets_reader.Path.exists", return_value=True),
        ):

            reader = SheetsReader()
            df = reader.get_sheet_data("TestSheet")

            assert df is None

    def test_get_sheet_data_empty_range(self) -> None:
        """Test sheet data retrieval with empty range."""
        mock_service = Mock()
        mock_result: dict[str, list[Any]] = {"values": []}  # Empty values
        mock_service.spreadsheets().values().get().execute.return_value = mock_result

        with (
            patch("apps.backend.sheets_reader.service_account"),
            patch("apps.backend.sheets_reader.build", return_value=mock_service),
            patch("apps.backend.sheets_reader.Path.exists", return_value=True),
        ):

            reader = SheetsReader()
            df = reader.get_sheet_data("TestSheet")

            assert df is None

    def test_get_sheet_data_headers_only(self) -> None:
        """Test sheet data retrieval with headers only - should return None."""
        mock_service = Mock()
        mock_values: list[list[str]] = [
            ["Date", "Provider", "Production"]
        ]  # Only headers

        mock_result: dict[str, Any] = {"values": mock_values}
        mock_service.spreadsheets().values().get().execute.return_value = mock_result

        with (
            patch("apps.backend.sheets_reader.service_account"),
            patch("apps.backend.sheets_reader.build", return_value=mock_service),
            patch("apps.backend.sheets_reader.Path.exists", return_value=True),
        ):

            reader = SheetsReader()
            df = reader.get_sheet_data("TestSheet")

            # Current behavior: returns None when only headers found
            # This matches the actual implementation in backend/sheets_reader.py:62-63
            assert df is None

    def test_constants(self) -> None:
        """Test class constants are correctly defined."""
        assert SPREADSHEET_ID == "1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8"
        assert SCOPES == ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    def test_get_eod_data_calls_correct_range(self) -> None:
        """Test that get_eod_data calls get_sheet_data with correct range."""
        mock_service = Mock()
        mock_values: list[list[str]] = [
            ["Date", "Production"],
            ["2024-01-15", "5000"],
        ]
        mock_result: dict[str, Any] = {"values": mock_values}
        mock_service.spreadsheets().values().get().execute.return_value = mock_result

        with (
            patch("apps.backend.sheets_reader.service_account"),
            patch("apps.backend.sheets_reader.build", return_value=mock_service),
            patch("apps.backend.sheets_reader.Path.exists", return_value=True),
        ):
            reader = SheetsReader()
            df = reader.get_eod_data()

            # Verify the correct range was called
            mock_service.spreadsheets().values().get.assert_called_with(
                spreadsheetId=SPREADSHEET_ID, range="EOD - Baytown Billing!A:AG"
            )
            assert df is not None
            assert len(df) == 1

    def test_get_front_kpi_data_calls_correct_range(self) -> None:
        """Test that get_front_kpi_data calls get_sheet_data with correct range."""
        mock_service = Mock()
        mock_values: list[list[str]] = [
            ["Date", "Hygiene"],
            ["2024-01-15", "5"],
        ]
        mock_result: dict[str, Any] = {"values": mock_values}
        mock_service.spreadsheets().values().get().execute.return_value = mock_result

        with (
            patch("apps.backend.sheets_reader.service_account"),
            patch("apps.backend.sheets_reader.build", return_value=mock_service),
            patch("apps.backend.sheets_reader.Path.exists", return_value=True),
        ):
            reader = SheetsReader()
            df = reader.get_front_kpi_data()

            # Verify the correct range was called
            mock_service.spreadsheets().values().get.assert_called_with(
                spreadsheetId=SPREADSHEET_ID,
                range="Baytown Front KPIs Form responses!A:Z",
            )
            assert df is not None
            assert len(df) == 1

    def test_get_sheet_data_general_exception(self) -> None:
        """Test sheet data retrieval with general exception."""
        mock_service = Mock()
        mock_service.spreadsheets().values().get().execute.side_effect = Exception(
            "Network error"
        )

        with (
            patch("apps.backend.sheets_reader.service_account"),
            patch("apps.backend.sheets_reader.build", return_value=mock_service),
            patch("apps.backend.sheets_reader.Path.exists", return_value=True),
        ):
            reader = SheetsReader()
            df = reader.get_sheet_data("TestSheet")

            assert df is None
