# Engineering Roadmap

This roadmap separates specifications from working features. A specification or a checked item does not mean that the corresponding software has shipped. Current evidence is summarized in [project status](PROJECT_STATUS.md) and detailed in [implementation progress](docs/IMPLEMENTATION_PROGRESS.md).

## Phase 0 — Repository foundation and research

- [x] Establish Python repository foundation and project records.
- [x] Research selected NASA service documentation and inspect limited live response examples.
- [x] Prepare product, architecture, security, AI/MCP, UX, infrastructure, QA, implementation, and operations specifications.
- [x] Reconcile the Python 3.12 package/CI baseline and record NASA/OIDC/map/AI decisions.

## Phase 1 — Docker-first application foundation

- [x] Implement backend settings, application lifecycle, request IDs, safe errors, liveness, and database/schema readiness.
- [x] Add PostgreSQL models and initial Alembic migration; verify against disposable PostgreSQL 18.
- [x] Add local Compose API, migration, PostgreSQL, frontend, and Caddy services with isolated service networks.
- [x] Build and smoke-test the local Compose slice through Caddy.
- [ ] Add and verify production Compose secrets, domain/TLS setup, resource limits, persistent certificate state, and restore/deployment runbook.

## Phase 2 — NASA data and ingestion

- [x] Implement bounded shared HTTP transport and typed APOD Basic, NeoWs, DONKI, EONET v3, and NASA Media clients.
- [x] Add normalized source models and verify repeated-upsert persistence for each selected NASA source against disposable PostgreSQL.
- [x] Add and test PostgreSQL job enqueue/claim, exclusive lease ownership, expiry recovery, and retry limits.
- [x] Add a worker process and bounded APOD, NeoWs, DONKI, and EONET handlers; test APOD persistence and mocked source dispatch.
- [x] Add unique schedule keys and test repeat-safe daily APOD, NeoWs, DONKI, and EONET job generation; keep scheduling disabled by default.
- [x] Implement public astronomy/APOD, asteroid, space-weather, Earth-event, and NASA Media explorer routes, including detail endpoints and stored space-weather summary.
- [ ] Complete route-level acceptance and provenance/error coverage for every public NASA route.
- [ ] Expand route-level contract/error/provenance tests to every integration.
- [ ] Add lease-loss runtime tests, worker health/job visibility, and a bounded NASA Media query contract; move upstream reads out of request handlers.
- [ ] Add API caching/freshness semantics and verify quota behavior.
- [ ] Keep EPIC and Exoplanet Archive deferred until user journeys and contracts justify them.

## Phase 3 — Product API and web dashboard

- [x] Complete the React/TypeScript shell, shared API client, explorer pages, accessible states, and local REST wiring for current explorers.
- [x] Implement owner-scoped saved records, conversations, report listing/read/delete, local identity controls, and asteroid comparison.
- [x] Add unit/diameter filters, pagination, NASA Media details, DONKI summary, and EONET map/list selection.
- [ ] Add browser Authorization Code with PKCE and choose the production OIDC issuer/role mapping.
- [ ] Implement provider-backed report generation and reproducible evidence export after the NASA policy gate and retrieval/evaluation work.
- [ ] Add end-to-end browser and accessibility checks for complete user journeys.

## Phase 4 — AI assistant and MCP

- [ ] Implement bounded retrieval only over validated application records.
- [ ] Establish citation checks, evaluation fixtures, spend controls, and prompt-injection tests.
- [ ] Resolve NASA AI/SI and attribution review before enabling generated output based on NASA-derived content.
- [x] Implement a private authenticated MCP service with ten tools, two static resources, two templates, and three prompts; verify transport/auth/input bounds through Caddy.

## Phase 5 — Production readiness and portfolio release

- [ ] Complete security, accessibility, performance, and end-to-end acceptance checks.
- [ ] Add monitoring, secret-safe logs, encrypted backups, and a verified restore exercise.
- [ ] Pin and scan release images; establish reproducible dependency locking and update policy.
- [ ] Deploy to an Ubuntu VPS behind HTTPS after resolving OIDC and map-provider decisions.
- [ ] Capture deployment evidence, known limitations, diagrams, screenshots, and demo instructions.

## Acceptance status

The local app is ready for hands-on testing of the implemented flows, but AI generation, browser OIDC sign-in, MCP Inspector and production OIDC evidence, release-quality E2E/security evidence, and production deployment remain incomplete. See [implementation progress](docs/IMPLEMENTATION_PROGRESS.md), the [task backlog](docs/10-implementation/TASK_BACKLOG.md), and [release checklist](docs/09-quality-assurance/RELEASE_CHECKLIST.md).
