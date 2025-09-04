# Architecture Decision Records

## ADR-001: Framework-Agnostic Backend
**Decision:** Backend modules have zero framework dependencies
**Rationale:** Allows frontend technology changes without backend modifications
**Consequences:** Clean separation, easy testing, potential reuse

## ADR-002: Pandas for Data Processing
**Decision:** Use pandas DataFrames for all data manipulation
**Rationale:** Powerful data operations, familiar to data scientists
**Consequences:** 5MB dependency, excellent calculation capabilities

## ADR-003: No Database Layer
**Decision:** Direct Google Sheets connection without local persistence
**Rationale:** Simplicity, real-time data, no sync issues
**Consequences:** API dependency, potential latency, rate limits
