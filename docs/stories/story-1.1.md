# Story 1.1: Project Foundation and Google Sheets Connection

## Status
Draft

## Story
**As a** developer,  
**I want** to set up the project structure and establish Google Sheets API connection,  
**so that** the application has a solid foundation and can access practice data.

## Acceptance Criteria
1. Project repository initialized with proper directory structure (backend/, frontend/, config/)
2. pyproject.toml configured with all required dependencies using uv
3. Google Cloud project created with Sheets API enabled
4. Service account credentials generated and stored in config/credentials.json
5. Backend module sheets_reader.py successfully connects to spreadsheet ID `1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8`
6. Function can read and return raw data from "EOD - Baytown Billing" sheet as pandas DataFrame
7. Basic error handling returns None with logged error message if connection fails

## Tasks / Subtasks

- [ ] **Task 1: Initialize Project Structure** (AC: 1)
  - [ ] Create project root directory if not exists
  - [ ] Create backend/ directory for Python modules
  - [ ] Create frontend/ directory for Streamlit app
  - [ ] Create config/ directory for credentials
  - [ ] Create tests/ directory for test files
  - [ ] Initialize git repository with .gitignore (credentials excluded)

- [ ] **Task 2: Configure Python Dependencies** (AC: 2)
  - [ ] Create pyproject.toml with project metadata
  - [ ] Add core dependencies:
    - google-auth>=2.23
    - google-api-python-client>=2.103
    - pandas>=2.1
    - streamlit>=1.30
  - [ ] Add test dependencies:
    - pytest>=7.4.0
    - pytest-cov>=4.1.0
    - pytest-mock>=3.11.0
  - [ ] Run `uv sync` to create lockfile and install dependencies
  - [ ] Verify all packages install successfully

- [ ] **Task 3: Set Up Google Cloud and API Access** (AC: 3, 4)
  - [ ] Follow docs/guides/google-cloud-setup.md for detailed steps
  - [ ] Create Google Cloud project
  - [ ] Enable Google Sheets API v4
  - [ ] Create service account "dental-dashboard-reader"
  - [ ] Download JSON credentials
  - [ ] Save as config/credentials.json
  - [ ] Set file permissions to 600 (Unix/Mac)
  - [ ] Add service account email to spreadsheet with Viewer permission

- [ ] **Task 4: Implement SheetsReader Module** (AC: 5, 6, 7)
  - [ ] Create backend/__init__.py (empty file)
  - [ ] Create backend/sheets_reader.py with SheetsReader class
  - [ ] Implement __init__ method with credentials loading
  - [ ] Implement get_sheet_data() method returning pandas DataFrame
  - [ ] Add proper error handling and logging
  - [ ] Include constants: SPREADSHEET_ID and SCOPES

- [ ] **Task 5: Test Google Sheets Connection** (AC: 5, 6)
  - [ ] Create test_connection.py in project root
  - [ ] Test connection to spreadsheet
  - [ ] Verify reading "EOD - Baytown Billing" sheet
  - [ ] Verify DataFrame structure (columns, data types)
  - [ ] Test error handling with invalid range
  - [ ] Confirm None returned on failure

## Dev Notes

### Technology Stack
[Source: architecture/fullstack/technology-stack.md]
- **Language:** Python 3.10+
- **Package Manager:** uv (NOT pip, poetry, or conda)
- **Frontend:** Streamlit 1.30+
- **Data Processing:** pandas 2.1+
- **API Client:** google-api-python-client 2.103+
- **Authentication:** google-auth 2.23+
- **Version Control:** Git

### Directory Structure
[Source: PRD Epic 1.1 and architecture patterns]
```
dental-analytics/
├── backend/           # Python modules for data processing
│   ├── __init__.py
│   └── sheets_reader.py
├── frontend/          # Streamlit UI code
│   └── app.py (future story)
├── config/           # Configuration and credentials
│   └── credentials.json (NEVER commit to git)
├── tests/            # Test files
│   └── test_connection.py
├── pyproject.toml    # Project dependencies
├── uv.lock          # Dependency lockfile
├── .gitignore       # Must exclude config/credentials.json
└── README.md        # Project documentation
```

### SheetsReader Implementation Details
[Source: architecture/backend/core-components.md#google-sheets-reader-module]
```python
class SheetsReader:
    """Handles all Google Sheets API interactions."""
    
    SPREADSHEET_ID = '1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    def __init__(self, credentials_path: str = 'config/credentials.json'):
        """Initialize with service account credentials."""
        self.creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=self.SCOPES
        )
        self.service = build('sheets', 'v4', credentials=self.creds)
    
    def get_sheet_data(self, range_name: str) -> Optional[pd.DataFrame]:
        """Fetch data from specified sheet range."""
        # Implementation per architecture specs
```

### Google Sheets API Configuration
[Source: docs/guides/google-cloud-setup.md]
- **Service Account:** Use service account authentication (no user interaction)
- **Permissions:** Read-only scope for security
- **Spreadsheet ID:** `1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8`
- **Target Sheets:**
  - "EOD - Baytown Billing"
  - "EOD - Humble Billing" (future)
  - "Front KPI - Baytown" (future)
  - "Front KPI - Humble" (future)

### Error Handling Requirements
[Source: architecture/backend/error-handling-philosophy.md]
- Never crash the application
- Return None for errors (not exceptions)
- Log errors with descriptive messages
- Graceful degradation pattern

### Security Considerations
[Source: architecture/backend/security-considerations.md]
- credentials.json MUST be in .gitignore
- Use read-only API scope
- No user data storage
- Service account with minimal permissions

## Testing

### Testing Standards
[Source: docs/stories/story-1.6-testing-framework.md]
- **Test Location:** tests/ directory
- **Test Framework:** pytest (will be set up in Story 1.6)
- **For this story:** Create manual test_connection.py script
- **Test Coverage:** Not required for initial setup story
- **Validation Method:** Manual execution and verification

### Test Script Requirements
```python
# test_connection.py
def test_google_sheets_connection():
    """Test connection to Google Sheets API."""
    # Should print success message with sheet names
    # Should handle errors gracefully
```

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-09-04 | 1.0 | Initial story creation | Scrum Master |

## Dev Agent Record

### Agent Model Used
_To be populated by dev agent_

### Debug Log References
_To be populated by dev agent_

### Completion Notes List
_To be populated by dev agent_

### File List
_To be populated by dev agent_

## QA Results
_To be populated by QA agent_