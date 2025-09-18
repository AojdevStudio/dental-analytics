---
title: "Google Cloud Setup Guide for Dental Analytics"
description: "Step-by-step instructions for setting up Google Cloud project, enabling APIs, and creating service account credentials for the dental analytics dashboard."
category: "Technical Documentation"
subcategory: "Setup Guides"
product_line: "Dental Analytics Dashboard"
audience: "Development Team"
status: "Final"
author: "AOJDevStudio"
created_date: "2025-09-04"
last_updated: "2025-09-04"
tags:
  - google-cloud
  - setup-guide
  - authentication
  - google-sheets-api
  - service-account
---

# Google Cloud Setup Guide for Dental Analytics

## Overview

This guide provides detailed, step-by-step instructions for setting up Google Cloud services required for the dental analytics dashboard. Total setup time: approximately 30-45 minutes.

## Prerequisites

- Google account (personal or Google Workspace)
- Access to the target Google Sheets spreadsheet
- Credit card (for Google Cloud account, though we'll stay within free tier)
- Administrative permissions on your development machine

## Step 1: Create Google Cloud Account

### 1.1 Navigate to Google Cloud Console
1. Open your browser and go to: https://console.cloud.google.com
2. Sign in with your Google account
3. If first-time user, you'll see "Welcome to Google Cloud Platform"

### 1.2 Accept Terms and Set Up Billing
1. Click "Agree and Continue" to accept terms
2. Click "Activate" or "Start Free Trial"
3. Enter your country and agree to terms
4. Select "Individual" account type (unless using company account)
5. Enter payment information (required but won't be charged for our usage)
6. Click "Start my free trial"

**Note:** Google provides $300 credit valid for 90 days. Our dashboard will use $0 if staying within free tier limits.

## Step 2: Create New Project

### 2.1 Access Project Creation
1. In Google Cloud Console, click the project dropdown (top navigation bar)
2. Click "New Project" button in the modal

### 2.2 Configure Project Settings
```
Project name: dental-analytics-dashboard
Project ID: (auto-generated, e.g., dental-analytics-123456)
Organization: No organization (unless you have one)
Location: (leave as default)
```
3. Click "Create"
4. Wait 30-60 seconds for project creation
5. Ensure new project is selected in dropdown

### 2.3 Verify Project Creation
1. Note your Project ID (you'll need this later)
2. Confirm project name appears in top navigation
3. Dashboard should show "dental-analytics-dashboard"

## Step 3: Enable Google Sheets API

### 3.1 Navigate to API Library
1. Click hamburger menu (☰) in top-left
2. Navigate to "APIs & Services" → "Library"
3. Or direct link: https://console.cloud.google.com/apis/library

### 3.2 Search and Enable Sheets API
1. In search bar, type "Google Sheets API"
2. Click on "Google Sheets API" from results
3. Click blue "ENABLE" button
4. Wait for API to enable (10-20 seconds)
5. You'll be redirected to API dashboard

### 3.3 Verify API Activation
- Status should show "API enabled"
- Dashboard shows "Google Sheets API" in enabled APIs list
- No errors displayed

## Step 4: Create Service Account

### 4.1 Navigate to Service Accounts
1. From left sidebar, click "Credentials"
2. Or navigate: "APIs & Services" → "Credentials"
3. Click "+ CREATE CREDENTIALS" button at top
4. Select "Service account" from dropdown

### 4.2 Service Account Details
**Step 1 - Service account details:**
```
Service account name: dental-dashboard-reader
Service account ID: dental-dashboard-reader (auto-filled)
Description: Read-only access to dental KPI spreadsheets
```
Click "CREATE AND CONTINUE"

### 4.3 Grant Permissions
**Step 2 - Grant this service account access:**
1. Click the "Select a role" dropdown
2. Type "viewer" in search
3. Select "Basic" → "Viewer" role
4. Click "CONTINUE"

**Step 3 - Grant users access (optional):**
- Skip this step, click "DONE"

### 4.4 Service Account Confirmation
- Service account appears in credentials list
- Email format: `dental-dashboard-reader@PROJECT_ID.iam.gserviceaccount.com`
- Copy this email address (needed for Step 5)

## Step 5: Create and Download JSON Key

### 5.1 Access Service Account Keys
1. In Credentials page, find your service account
2. Click on the service account email
3. Navigate to "KEYS" tab
4. Click "ADD KEY" → "Create new key"

### 5.2 Generate JSON Key
1. Select "JSON" key type (should be pre-selected)
2. Click "CREATE"
3. Key file automatically downloads
4. File name format: `dental-analytics-dashboard-xxxxx-xxxxxxxxxxxx.json`

### 5.3 Secure the Credentials
1. Rename downloaded file to `credentials.json`
2. Move to your project directory:
```bash
# Create config directory if it doesn't exist
mkdir -p ~/Projects/unified-dental/dental-analytics/config

# Move and rename the credentials file
mv ~/Downloads/dental-analytics-dashboard-*.json \
   ~/Projects/unified-dental/dental-analytics/config/credentials.json

# Set appropriate permissions (Unix/Mac)
chmod 600 ~/Projects/unified-dental/dental-analytics/config/credentials.json
```

**CRITICAL SECURITY NOTES:**
- Never commit this file to git (already in .gitignore)
- Never share this file publicly
- Keep a secure backup in password manager
- This file grants API access to your project

## Step 6: Grant Spreadsheet Access

### 6.1 Get Service Account Email
1. Return to Google Cloud Console → Credentials
2. Copy the service account email:
   `dental-dashboard-reader@PROJECT_ID.iam.gserviceaccount.com`

### 6.2 Share Target Spreadsheet
1. Open Google Sheets in browser
2. Navigate to spreadsheet ID: `1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8`
3. Click "Share" button (top-right)
4. Paste service account email
5. Ensure "Viewer" permission is selected
6. Uncheck "Notify people" (service accounts can't receive email)
7. Click "Share"

### 6.3 Verify Access
The service account should now appear in the spreadsheet's sharing settings with "Can view" permission.

## Step 7: Test Connection

### 7.1 Install Dependencies
```bash
cd ~/Projects/unified-dental/dental-analytics
uv sync
```

### 7.2 Create Test Script
Create `test_connection.py`:
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

def test_google_sheets_connection():
    """Test connection to Google Sheets API."""
    try:
        # Load credentials
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        creds = service_account.Credentials.from_service_account_file(
            'config/credentials.json', scopes=SCOPES
        )

        # Build service
        service = build('sheets', 'v4', credentials=creds)

        # Test API call
        spreadsheet_id = '1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8'
        result = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

        print(f"✅ Success! Connected to: {result.get('properties', {}).get('title')}")
        print(f"   Sheets found: {len(result.get('sheets', []))}")

        # List sheet names
        for sheet in result.get('sheets', []):
            print(f"   - {sheet['properties']['title']}")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_google_sheets_connection()
```

### 7.3 Run Test
```bash
uv run python test_connection.py
```

**Expected Output:**
```
✅ Success! Connected to: [Spreadsheet Name]
   Sheets found: 4
   - EOD - Baytown Billing
   - EOD - Humble Billing
   - Baytown Front KPIs Form responses
   - Humble Front KPIs Form responses
```

## Step 8: Troubleshooting

### Common Issues and Solutions

#### Issue: "API has not been enabled"
**Solution:** Return to Step 3 and ensure Google Sheets API is enabled

#### Issue: "Permission denied" or 403 error
**Solution:**
1. Verify service account email is correctly shared on spreadsheet
2. Check that "Viewer" permission is granted
3. Ensure credentials.json is from correct project

#### Issue: "File not found: credentials.json"
**Solution:**
1. Verify file exists in `config/` directory
2. Check file permissions
3. Ensure path in code is correct

#### Issue: "Invalid grant" or authentication error
**Solution:**
1. Regenerate service account key (Step 5)
2. Re-download and replace credentials.json
3. Verify project ID matches

#### Issue: Rate limit errors
**Solution:**
1. Google Sheets API allows 100 requests per 100 seconds
2. Implement exponential backoff
3. Cache results for 5 minutes minimum

## Step 9: Production Considerations

### 9.1 Environment Variables (Optional)
For production, consider using environment variables:
```python
import os
from pathlib import Path

# Development: use local file
CREDENTIALS_PATH = os.getenv(
    'GOOGLE_CREDENTIALS_PATH',
    'config/credentials.json'
)

# Production: use environment variable with JSON content
CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')
if CREDENTIALS_JSON:
    import json
    credentials_dict = json.loads(CREDENTIALS_JSON)
    creds = service_account.Credentials.from_service_account_info(
        credentials_dict, scopes=SCOPES
    )
else:
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH, scopes=SCOPES
    )
```

### 9.2 Streamlit Cloud Deployment
When deploying to Streamlit Cloud:
1. Copy contents of credentials.json
2. In Streamlit Cloud settings, add secret:
   ```toml
   [google]
   credentials_json = '''
   {
     "type": "service_account",
     "project_id": "...",
     ...
   }
   '''
   ```
3. Access in code:
   ```python
   import streamlit as st
   import json

   credentials_dict = json.loads(st.secrets["google"]["credentials_json"])
   ```

## Step 10: Security Checklist

- [ ] credentials.json is in .gitignore
- [ ] Service account has minimum required permissions (Viewer only)
- [ ] Spreadsheet sharing is restricted to service account
- [ ] No credentials in source code
- [ ] Backup of credentials stored securely
- [ ] Project follows principle of least privilege
- [ ] API quotas monitored in Google Cloud Console

## Quick Reference

### Key Information
- **Project Name:** dental-analytics-dashboard
- **API:** Google Sheets API v4
- **Service Account:** dental-dashboard-reader@PROJECT_ID.iam.gserviceaccount.com
- **Credentials Location:** `config/credentials.json`
- **Spreadsheet ID:** `1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E_FKFTxQ8`
- **Required Scope:** `https://www.googleapis.com/auth/spreadsheets.readonly`

### Useful Links
- [Google Cloud Console](https://console.cloud.google.com)
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Service Account Documentation](https://cloud.google.com/iam/docs/service-accounts)
- [API Quotas Dashboard](https://console.cloud.google.com/apis/api/sheets.googleapis.com/quotas)

## Completion Confirmation

Once all steps are complete, you should have:
- ✅ Google Cloud project created
- ✅ Google Sheets API enabled
- ✅ Service account created with Viewer role
- ✅ JSON key downloaded and secured
- ✅ Spreadsheet shared with service account
- ✅ Successful test connection

The Google Cloud setup is now complete and ready for development!
