# Architecture Decision Records

## ADR-001: Streamlit for Frontend
**Decision:** Use Streamlit instead of React/Vue/Angular
**Rationale:** Fastest development, Python-only, built-in components
**Trade-offs:** Less customization, Python server required

## ADR-002: No Database
**Decision:** Direct Google Sheets connection without local DB
**Rationale:** Simplicity, real-time data, no sync issues
**Trade-offs:** API dependency, rate limits, no historical data

## ADR-003: Monolithic Architecture
**Decision:** Single application instead of microservices
**Rationale:** Under 200 lines total, single purpose
**Trade-offs:** Less scalable, harder to extend

## ADR-004: Service Account Auth
**Decision:** Service account instead of OAuth2 user flow
**Rationale:** Zero user interaction, simpler implementation
**Trade-offs:** Shared credentials, less granular permissions
