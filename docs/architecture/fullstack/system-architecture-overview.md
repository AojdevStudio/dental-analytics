# System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         USERS                              │
│                  (Practice Managers)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    WEB BROWSER                             │
│              (Chrome 90+, Firefox 88+)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ Port 8501
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 PRESENTATION LAYER                         │
│                   Streamlit Server                         │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           apps/frontend/app.py (~80 lines)          │  │
│  │  • Page Configuration & Theming                     │  │
│  │  • KPI Display Components (st.metric)               │  │
│  │  • Layout Management (st.columns)                   │  │
│  │  • Error State Handling                             │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │ Function Calls
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  BUSINESS LOGIC LAYER                      │
│              Backend Python Modules (100 lines)            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │         apps/backend/metrics.py (~92 lines)         │  │
│  │  • calculate_production_total()                     │  │
│  │  • calculate_collection_rate()                      │  │
│  │  • calculate_new_patients()                         │  │
│  │  • calculate_case_acceptance()                 │  │
│  │  • calculate_hygiene_reappointment()                │  │
│  │  • get_all_kpis() orchestrator                      │  │
│  └──────────────────┬──────────────────────────────────┘  │
│                     │                                      │
│  ┌──────────────────▼──────────────────────────────────┐  │
│  │      apps/backend/sheets_reader.py (~77 lines)      │  │
│  │  • Service Account Authentication                   │  │
│  │  • Google Sheets API Connection                     │  │
│  │  • Data Retrieval & DataFrame Conversion            │  │
│  └──────────────────┬──────────────────────────────────┘  │
└─────────────────────┼────────────────────────────────────────┘
                      │ HTTPS API v4
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCE LAYER                       │
│                     Google Sheets                          │
│            ID: 1lTDek2zvQNYwlIXss6yW9uawASAWbDIKR1E...   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  • EOD - Baytown Billing (Production/Collections)   │  │
│  │  • EOD - Humble Billing (Production/Collections)    │  │
│  │  • Baytown Front KPIs Form responses (Treatment/Hygiene)          │  │
│  │  • Humble Front KPIs Form responses (Treatment/Hygiene)           │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```
