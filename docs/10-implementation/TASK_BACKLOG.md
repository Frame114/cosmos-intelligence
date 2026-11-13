# Implementation Task Backlog

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** All tasks not started; acceptance and evidence columns are mandatory at execution  
**Purpose:** Specify the intended Implementation Task Backlog requirements and implementation constraints.  
**Scope:** Covers the proposed Implementation Task Backlog behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



Each task lists dependencies, affected components, acceptance, required tests, and completion evidence. “Test” means add and run the specified test in the implementation phase; this documentation phase has not run product tests.

| ID | Task and dependencies | Components/files | Acceptance criteria | Test and completion evidence |
|---|---|---|---|---|
| CI-01 | Reconcile repository metadata with docs; none | README, status, roadmap, pyproject/CI review | Python 3.12 target and docs source-of-truth plan agree | CI config review; checked diff, decision record |
| INF-01 | Build Compose foundation; CI-01 | Dockerfiles, compose.yaml, env template | docker compose up --build starts DB/API/frontend/worker/MCP | Compose config/build; healthy service output |
| INF-02 | Add networks/Caddy; INF-01 | Caddyfile, production overlay | Only Caddy publishes ports; DB private | Compose network/port inspection and HTTPS smoke |
| BE-01 | Settings and lifespan; INF-01 | app/core, main, settings | Strict settings, HTTPX and DB lifecycle close cleanly | Unit tests for valid/invalid settings and client lifecycle |
| BE-02 | Errors/logging/health; BE-01 | API core, middleware, schemas | RFC problem response, request ID, redacted JSON logs; liveness/readiness differ | API/error/readiness tests; redaction sample |
| DB-01 | PostgreSQL models and migrations; BE-01 | app/db, Alembic | Schema matches DATABASE_SCHEMA and Alembic autogenerate reviewed | PostgreSQL migration/integrity tests; reviewed SQL revision |
| DB-02 | Repositories/provenance; DB-01 | repositories, domain models | Atomic idempotent upsert and source-record linkage | Duplicate/revised-payload transaction tests and record hashes |
| WRK-01 | Durable job queue/worker; DB-01 | app/worker, job model | Lease, retries, failed terminal state, no duplicate parallel processing | Concurrent lease and restart/reclaim integration tests |
| NASA-01 | Shared NASA transport; BE-01 | app/clients/nasa | Timeout, host allowlist, quota headers, bounded retries, key redaction | Mocked retry/error/redirect/key-redaction tests |
| INT-APOD | APOD Basic; NASA-01 | APOD adapter/models/tests | page/per_page and date_from/date_to contract; media optional fields | Sanitized contract fixture, date-filter test, invalid-shape test |
| INT-NEO | NeoWs; NASA-01 | Neo adapter/models/tests | feed window validation, object/approach units and flags normalized | Fixture tests for missing/duplicate units/approaches |
| INT-DONKI | DONKI; NASA-01 | DONKI adapters/models | Requested event types have typed common envelope and raw details | Per-type sanitized fixture and malformed item tests |
| INT-EONET | EONET v3; NASA-01 | EONET adapter/models | Filters, IDs, geometry, curation/provenance modeled | Point/polygon/empty/malformed geometry tests |
| INT-MEDIA | NASA Media; NASA-01 | Media adapter/models | Search pagination, manifest and item rights metadata normalized; no binary copy | Mock search/asset pagination and unsafe URL tests |
| ING-01 | Ingestion and normalization; DB-02, WRK-01, INT-* | worker/services/repos | Source jobs are idempotent, bounded, and observable | Replay, partial-page, quarantine, retry tests |
| API-01 | Versioned REST routes; DB-02, ING-01 | app/api/v1, OpenAPI | Endpoints/schemas/errors match API spec | Contract/schema/auth tests and OpenAPI diff |
| AUTH-01 | OIDC and user ownership; API-01 | auth middleware, DB user model | Prod fails closed; each private resource owner-scoped | Token-claim and cross-user access tests |
| FE-01 | Vite/React shell/design tokens; INF-01 | frontend app | Strict TypeScript, responsive app shell and typed API client | Build/typecheck/component tests |
| FE-02 | Overview/Astronomy/Asteroids; FE-01, API-01 | pages/components/charts | Freshness, units, hazard labels and source links visible | Component and E2E APOD/NEO journeys |
| FE-03 | Space-weather/Earth/Media pages; FE-01, API-01 | map/list/media pages | Filters and accessible map/list/media attribution work | Component and E2E domain journeys |
| USER-01 | Saved records/reports UI; AUTH-01, FE-01 | UI pages/API | Account owner can save/list/delete own records | Owner-isolation API and E2E tests |
| RET-01 | PostgreSQL full-text retrieval; DB-02, API-01 | search index/retrieval service | Structured + text retrieval bounded, explainable and indexed | Search fixture recall/latency integration tests |
| AI-01 | Provider adapter; RET-01, AUTH-01 | app/clients/llm, settings | Configurable model, schema validation, budgets and safe failure | Mock provider success/timeout/429/schema tests |
| AI-02 | Evaluations/policy review; AI-01 | eval fixtures, ADR, docs | Thresholds pass and NASA AI/SI use decision documented | Versioned eval report and approval evidence |
| AI-03 | Assistant/report routes/UI; AI-02 | services/API/frontend/report tables | Evidence-only answers, owner-scoped storage, feature gate | Evals, citation-validator tests, E2E gated state |
| MCP-01 | SDK v2 server base; API-01, AUTH-01 | app/mcp, image command | Streamable HTTP private; stdio dev; health/auth configured | SDK in-memory client and local transport smoke |
| MCP-02 | Tool/resource/prompt catalog; MCP-01, services | MCP handlers | All 10 schemas call shared services and enforce caps | Tool schema/authorization/ownership tests, Inspector evidence |
| SEC-01 | Security hardening; AUTH-01, MCP-02 | Caddy, middleware, images | Threat controls and no known high/critical finding | Security tests/scans and signed review record |
| QA-01 | Full quality suite; features | tests/frontend/evals/CI | Coverage ≥85%, critical E2E pass, AI eval thresholds | CI run ID, coverage/eval reports, E2E evidence |
| OPS-01 | Monitoring/logging dashboards; BE-02, WRK-01 | health/metrics/log config | Source/job/AI/DB state available to admin without secrets | Health/failure injection and redaction review |
| OPS-02 | Encrypted backups/restore; DB-01 | backup script/runbook | Daily backup plus isolated restore meets target | Restore transcript, counts/checksum, timing |
| OPS-03 | VPS deploy/release; INF-02, SEC-01, QA-01, OPS-02 | deploy workflow/runbooks | TLS, private DB, migrations, smoke checks and rollback plan | Approved release/deployment logs and smoke report |

## Parallel lanes

After NASA-01, INT-NEO/INT-DONKI/INT-EONET/INT-MEDIA can proceed independently with dedicated reviewers. FE-01 design-system work may proceed while API contracts stabilize. AI-02 dataset authoring can begin in parallel with UI but cannot enable runtime generation before AI-01 and policy review.

## Related documents

[Implementation Plan](IMPLEMENTATION_PLAN.md), [Dependency Graph](DEPENDENCY_GRAPH.md), [Definition of Done](../../DEFINITION_OF_DONE.md).
