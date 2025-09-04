# Security Architecture

## Authentication & Authorization

**Service Account Security:**
```json
{
  "type": "service_account",
  "project_id": "dental-analytics",
  "client_email": "readonly@project.iam.gserviceaccount.com",
  "private_key": "[ENCRYPTED]"
}
```

**API Permissions:**
- Scope: `spreadsheets.readonly`
- No write access
- No user data access
- Limited to specific spreadsheet

## Data Security

**In Transit:**
- HTTPS for all API calls
- TLS 1.2+ encryption
- Certificate validation

**At Rest:**
- No data storage
- Memory-only processing
- Cleared after request

**Compliance:**
- No PHI/PII storage
- HIPAA considerations addressed
- Aggregate metrics only

## Access Control

**Dashboard Access:**
- Option 1: No authentication (internal network only)
- Option 2: Streamlit Cloud authentication
- Option 3: Custom auth layer (post-MVP)
