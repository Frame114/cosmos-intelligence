# Phase Breakdown

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Specify the intended Phase Breakdown requirements and implementation constraints.  
**Scope:** Covers the proposed Phase Breakdown behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



| Phase | Scope | Entry dependencies | Completion evidence |
|---|---|---|---|
| A. Foundation | Repo docs/source-of-truth, package target, Compose skeleton, CI baseline | None | Compose config/build and CI green from clean checkout. |
| B. Backend and database | Settings/lifespan, errors, request IDs, PostgreSQL schema, Alembic, repositories | A | Migrations up/down review, integration tests, health readiness. |
| C. Integration/data layer | Shared HTTPX policy, APOD Basic then other four adapters, validation, job worker, provenance | B; API contract review | Sanitized fixtures, adapter/normalizer/error tests, idempotent re-run evidence. |
| D. REST/auth | Versioned API, pagination/filtering, OIDC, saved record endpoints, admin summaries | B/C services | OpenAPI review, contract/auth/owner-isolation tests. |
| E. Frontend | SPA, design system, domain pages, Recharts, Leaflet, loading/error/empty/stale states | D; UX can run parallel with B | Accessibility review, component tests, E2E critical journeys. |
| F. AI/MCP | PostgreSQL retrieval, provider adapter, evaluation suite, policy review; MCP v2 server and tools | C/D; identity and security | Evaluation thresholds; policy ADR; MCP Inspector and schema/auth tests. |
| G. Production | Security review, monitoring, backup/restore, CI image/release, VPS | A–F | Release checklist, verified restore, HTTPS and deployment smoke evidence. |

## Related documents

[Implementation Plan](IMPLEMENTATION_PLAN.md), [Dependency Graph](DEPENDENCY_GRAPH.md), [Task Backlog](TASK_BACKLOG.md).
