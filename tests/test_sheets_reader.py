"""Tests for SheetsReader module."""

from unittest.mock import Mock, patch

import pandas as pd

from backend.sheets_reader import SheetsReader


class TestSheetsReader:
    """Test cases for SheetsReader class."""

    def test_initialization_success(self) -> None:
        """Test successful SheetsReader initialization."""
        with (
            patch("backend.sheets_reader.service_account") as mock_sa,
            patch("backend.sheets_reader.build") as mock_build,
        ):

            mock_creds = Mock()
            mock_sa.Credentials.from_service_account_file.return_value = mock_creds
            mock_service = Mock()
            mock_build.return_value = mock_service

            reader = SheetsReader()

            assert reader.service == mock_service
            mock_sa.Credentials.from_service_account_file.assert_called_once_with(
                "config/credentials.json", scopes=SheetsReader.SCOPES
            )

    def test_initialization_failure(self) -> None:
        """Test SheetsReader initialization failure."""
        with patch("backend.sheets_reader.service_account") as mock_sa:
            mock_sa.Credentials.from_service_account_file.side_effect = Exception(
                "File not found"
            )

            reader = SheetsReader()

            assert reader.service is None

    def test_get_sheet_data_success(self) -> None:
        """Test successful sheet data retrieval."""
        mock_service = Mock()
        mock_values = [
            ["Date", "Provider", "Production"],
            ["2025-01-01", "Dr. Smith", "1000"],
            ["2025-01-02", "Dr. Jones", "1200"],
        ]

        mock_result = {"values": mock_values}
        mock_service.spreadsheets().values().get().execute.return_value = mock_result

        with (
            patch("backend.sheets_reader.service_account"),
            patch("backend.sheets_reader.build", return_value=mock_service),
        ):

            reader = SheetsReader()
            df = reader.get_sheet_data("TestSheet")

            expected_df = pd.DataFrame(mock_values[1:], columns=mock_values[0])
            assert df is not None
            pd.testing.assert_frame_equal(df, expected_df)

    def test_get_sheet_data_no_data(self) -> None:
        """Test sheet data retrieval with no data."""
        mock_service = Mock()
        mock_service.spreadsheets().values().get().execute.return_value = {"values": []}

        with (
            patch("backend.sheets_reader.service_account"),
            patch("backend.sheets_reader.build", return_value=mock_service),
        ):

            reader = SheetsReader()
            result = reader.get_sheet_data("EmptySheet")

            assert result is None

    def test_get_sheet_data_service_not_initialized(self) -> None:
        """Test sheet data retrieval when service is not initialized."""
        with patch("backend.sheets_reader.service_account") as mock_sa:
            mock_sa.Credentials.from_service_account_file.side_effect = Exception(
                "Error"
            )

            reader = SheetsReader()
            result = reader.get_sheet_data("TestSheet")

            assert result is None

    def test_get_sheet_data_api_error(self) -> None:
        """Test sheet data retrieval with API error."""
        mock_service = Mock()
        mock_service.spreadsheets().values().get().execute.side_effect = Exception(
            "API Error"
        )

        with (
            patch("backend.sheets_reader.service_account"),
            patch("backend.sheets_reader.build", return_value=mock_service),
        ):

            reader = SheetsReader()
            result = reader.get_sheet_data("TestSheet")

            assert result is None

    def test_get_sheet_data_empty_range(self) -> None:
        """Test sheet data retrieval with empty range name."""
        mock_service = Mock()

        with (
            patch("backend.sheets_reader.service_account"),
            patch("backend.sheets_reader.build", return_value=mock_service),
        ):

            reader = SheetsReader()

            # Test empty string
            result = reader.get_sheet_data("")
            assert result is None

            # Test whitespace only
            result = reader.get_sheet_data("   ")
            assert result is None

    def test_get_sheet_data_headers_only(self) -> None:
        """Test sheet data retrieval with headers only."""
        mock_service = Mock()
        mock_values = [["Date", "Provider", "Production"]]  # Only headers

        mock_result = {"values": mock_values}
        mock_service.spreadsheets().values().get().execute.return_value = mock_result

        with (
            patch("backend.sheets_reader.service_account"),
            patch("backend.sheets_reader.build", return_value=mock_service),
        ):

            reader = SheetsReader()
            df = reader.get_sheet_data("TestSheet")

            # Should return empty DataFrame with column names
            assert df is not None
            assert len(df) == 0
            assert list(df.columns) == ["Date", "Provider", "Production"]

    def test_constants(self) -> None:
        """Test class constants are correctly defined."""
        assert (
            SheetsReader.SPREADSHEET_ID
            == "1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8"
        )
        assert SheetsReader.SCOPES == [
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        ]
