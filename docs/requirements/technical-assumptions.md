# Technical Assumptions

## Repository Structure: Monorepo
Single repository containing all frontend, backend, and configuration files for the dental analytics dashboard with clear separation of concerns.

## Service Architecture
**Modular monolithic application** - Clean separation between backend logic (data fetching, KPI calculations) and frontend presentation (Streamlit UI). Backend modules are framework-agnostic, allowing future frontend swaps without touching business logic.

## Testing Requirements
**Manual testing only for MVP** - Given the 200-line constraint and read-only nature, formal test suites deferred to post-MVP. Manual verification of:
- Google Sheets connection
- KPI calculation accuracy against known values
- Dashboard display on target browsers

## Additional Technical Assumptions and Requests

- **Language:** Python 3.10+ exclusively
- **Frontend Framework:** Streamlit for MVP (replaceable - see architecture notes)
- **Data Processing:** pandas for all KPI calculations
- **API Integration:** Google Sheets API v4 with OAuth 2.0 service account
- **Package Management:** uv for all dependencies (no pip/poetry/conda)
- **Configuration:** credentials.json in config/ directory for Google API auth
- **Deployment:** Streamlit Community Cloud (free tier) or local execution
- **Data Storage:** No database; calculations performed on-demand from Google Sheets
- **Caching:** Framework-agnostic caching strategy in backend layer
- **Error Handling:** Backend returns structured error responses; frontend displays appropriately
- **Logging:** Basic console output only (no formal logging framework)
- **Version Control:** Git with .gitignore for credentials

**Critical Architecture Decision - Separation of Concerns:**
- **backend/** directory: Pure Python modules with no Streamlit dependencies
  - `data_providers.py`: Google Sheets API connection and data fetching
  - `metrics.py`: KPI calculation logic returning structured data
- **frontend/** directory: Presentation layer (Streamlit for MVP)
  - `app.py`: UI components that call backend modules
- Backend modules return standard Python dictionaries/DataFrames, making them reusable with any frontend framework (Next.js, Flask, FastAPI, etc.)
