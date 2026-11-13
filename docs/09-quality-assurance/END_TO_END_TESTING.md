# End-to-End Testing

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 E2E plan  
**Purpose:** Specify the intended End-to-End Testing requirements and implementation constraints.  
**Scope:** Covers the proposed End-to-End Testing behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Critical journeys

1. Open Overview and see source freshness/empty states.
2. Search historical APOD, open detail, inspect credit/provenance, save and remove.
3. Filter NEO approaches, inspect detail and compare two objects with missing values.
4. Filter DONKI event type/date and open original source.
5. Filter EONET category/status and switch map/list selection with keyboard.
6. Search NASA media by text/type/year, open asset manifest and rights panel.
7. Sign in, ask an answerable question against fixtures, inspect citations, delete conversation.
8. Attempt cross-user report access and confirm denial.
9. Call MCP search/detail tool using the local test server; assert schema and provenance.

## Environment

Run against isolated Docker Compose with fixed PostgreSQL seed fixtures, mocked identity provider, mocked NASA/LLM adapters, deterministic clock, and stable viewport. Never use production account/data or real provider keys in standard E2E CI.

## Related documents

[Testing Strategy](TESTING_STRATEGY.md), [Acceptance Criteria](ACCEPTANCE_CRITERIA.md), [Local Development](../11-operations/LOCAL_DEVELOPMENT.md).
