# System Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                  GOOGLE SHEETS                       │
│         (Source of Truth - Practice Data)            │
└────────────────────┬─────────────────────────────────┘
                     │ API v4
                     ▼
┌──────────────────────────────────────────────────────┐
│               BACKEND LAYER (100 lines)              │
├──────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────┐  │
│  │          data_providers.py (50 lines)           │  │
│  │  - Service Account Authentication              │  │
│  │  - Spreadsheet Connection                      │  │
│  │  - Data Retrieval & DataFrame Conversion       │  │
│  └──────────────────┬─────────────────────────────┘  │
│                     │ pandas DataFrame               │
│  ┌──────────────────▼─────────────────────────────┐  │
│  │            metrics.py (50 lines)               │  │
│  │  - calculate_production_total()                │  │
│  │  - calculate_collection_rate()                 │  │
│  │  - calculate_new_patients()                    │  │
│  │  - calculate_case_acceptance()            │  │
│  │  - calculate_hygiene_reappointment()           │  │
│  │  - get_all_kpis() → Dict[str, float]          │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
                     │ Python Dict/DataFrame
                     ▼
              [Frontend Layer]
```
