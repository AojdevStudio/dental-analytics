# Dental Analytics Dashboard

Simple dental analytics dashboard that reads KPI data from Google Sheets, processes it with pandas, and displays metrics in a Streamlit web interface. Built for KamDental practice to automate daily production, collection rate, new patient count, treatment acceptance, and hygiene reappointment tracking.

## Goal
Get 5 numbers on screen from Google Sheets in under 200 lines of code.

## Quick Start

### Environment Setup
```bash
# Install dependencies
uv sync

# Run application
uv run streamlit run frontend/app.py

# Access dashboard at http://localhost:8501
```

### Configuration
1. Set up Google Cloud project with Sheets API enabled
2. Create service account and download credentials
3. Save credentials as `config/credentials.json`
4. Share target spreadsheet with service account email

## Architecture

- **Backend**: Framework-agnostic Python modules (`sheets_reader.py`, `metrics.py`)
- **Frontend**: Streamlit web interface (`app.py`)
- **Data**: Google Sheets API for real-time KPI data
- **Testing**: pytest with comprehensive coverage

## Technology Stack

- Python 3.10+
- Streamlit 1.30+
- pandas 2.1+
- Google Sheets API v4
- uv for dependency management

## Project Structure

```
dental-analytics/
├── backend/           # Python business logic
├── frontend/          # Streamlit UI
├── config/           # Credentials (not committed)
├── tests/            # Test suite
└── docs/            # Documentation
```