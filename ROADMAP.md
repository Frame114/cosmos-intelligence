# Engineering Roadmap

This roadmap separates specifications from working features. A checked documentation item means that a specification exists; it does not mean the corresponding software has shipped.

## Phase 0 — Repository foundation and research

- [x] Establish Python repository foundation and project records.
- [x] Research selected NASA service documentation and inspect limited live response examples.
- [x] Prepare product, architecture, security, AI/MCP, UX, infrastructure, QA, implementation, and operations specifications.
- [ ] Review and reconcile specification assumptions against current package metadata and CI.
- [ ] Run and record repository checks; no result is claimed by the documentation phase.

## Phase 1 — Docker-first application foundation

- [ ] Reconcile supported Python version, package metadata, and CI baseline.
- [ ] Implement Docker Compose services, network boundaries, health/readiness, and environment handling.
- [ ] Implement backend settings, lifecycle, logging, request IDs, and health endpoints.
- [ ] Add PostgreSQL migrations and readiness checks.
- [ ] Demonstrate a clean-checkout local startup using the Compose workflow.

## Phase 2 — NASA data and ingestion

- [ ] Implement shared outbound HTTP policy and APOD Basic adapter using the dedicated guide and a verified date-filter contract.
- [ ] Add NeoWs, DONKI, EONET v3, and NASA Media adapters with typed validation and sanitized fixtures.
- [ ] Implement normalization, provenance, idempotent ingestion, retry bounds, and operational job visibility.
- [ ] Keep EPIC and Exoplanet Archive deferred until user journeys and contracts justify them.

## Phase 3 — Product API and web dashboard

- [ ] Implement versioned APIs, authentication, pagination, ownership boundaries, and error contracts.
- [ ] Build React/TypeScript shell and accessible design system.
- [ ] Deliver astronomy, asteroid, space-weather, Earth-event, and media journeys with freshness, units, attribution, and useful empty/error states.
- [ ] Add charts, filtering, saved records, and reproducible reports where acceptance criteria require them.

## Phase 4 — AI assistant and MCP

- [ ] Implement bounded retrieval from validated application records and provider abstraction.
- [ ] Establish evaluation fixtures, citation checks, budget controls, and prompt-injection tests.
- [ ] Resolve NASA AI/SI and attribution review before enabling generated output based on NASA-derived content.
- [ ] Implement the MCP server only after identity, authorization, rate, and tool scope decisions are enforceable.

## Phase 5 — Production readiness and portfolio release

- [ ] Complete security, accessibility, performance, and end-to-end acceptance checks.
- [ ] Add monitoring, secret-safe logs, encrypted backups, and a verified restore exercise.
- [ ] Deploy to an Ubuntu VPS behind HTTPS after resolving OIDC and map-provider decisions.
- [ ] Capture deployment evidence, known limitations, diagrams, screenshots, and demo instructions.

## Status and acceptance

Current status is maintained in [PROJECT_STATUS.md](PROJECT_STATUS.md). Detailed dependencies and acceptance evidence live in the [implementation plan](docs/10-implementation/IMPLEMENTATION_PLAN.md), [phase breakdown](docs/10-implementation/PHASE_BREAKDOWN.md), and [task backlog](docs/10-implementation/TASK_BACKLOG.md). Product tests should be added and run during implementation; this roadmap update does not report tests as run.
