# Project Status

**Last updated:** 2026-11-14<br>
**Current phase:** Phase 2 implementation<br>
**Overall status:** The local data-explorer and user-workspace flows are implemented and ready for hands-on testing at `http://localhost:8080`. AI generation is not implemented; the private authenticated MCP surface is locally implemented; production sign-in and release operations remain incomplete.

## Current evidence

| Area | Current evidence | State |
|---|---|---|
| Documentation | Product, architecture, selected NASA integrations, AI/MCP, security, UX, infrastructure, QA, implementation, and operations specs under `docs/` | Available; updated docs now distinguish the local implementation from the release target |
| Backend | FastAPI lifecycle and safe error handling; liveness/readiness; versioned NASA read routes; asteroid comparison and JPL Horizons paths; stored space-weather summary; media details; owner-scoped workspace; admin job summaries/retry | Implemented; Python 3.12 Ruff/mypy and 49 backend tests pass. Current measured app coverage is 66%, below the release target. OIDC token validation protects authenticated routes; browser PKCE sign-in is absent. |
| Database and worker | PostgreSQL models, Alembic migrations, provenance-preserving upserts, durable lease/retry queue, worker process, bounded APOD/NeoWs/DONKI/EONET handlers, deterministic daily schedule generator | Migration, metadata check, feed upserts, queue leases, worker APOD persistence, mocked dispatch, and repeat-safe schedule tests pass on disposable PostgreSQL 18. Scheduling is disabled by default; NASA Media job inputs and worker health visibility remain. |
| NASA integrations | Typed APOD Basic, NeoWs, DONKI, EONET, and NASA Media clients with bounded HTTP behavior | Mocked client contract/error tests and PostgreSQL idempotency route tests pass for the main listings; detail/error branches and live NASA behavior are not fully verified. |
| Frontend | React/TypeScript astronomy, asteroid, space-weather, Earth-event map/list, media details, assistant gate, reports, saved records, and settings pages | Typecheck, four unit tests, production build, and dashboard HTTP smoke pass. Current flows are wired to REST APIs; assistant generation and report creation show the closed feature gate. |
| Local infrastructure | Compose API, PostgreSQL, migration task, worker, frontend, and Caddy proxy; no database/API/worker host port | Latest images rebuilt and started; API/frontend/PostgreSQL healthy; liveness/readiness/auth-session/OpenAPI/dashboard and authenticated MCP checks pass through Caddy. Worker schedules are confirmed disabled. |
| CI | Python 3.12 and Node 22.22.2 jobs; lint, mypy, disposable PostgreSQL migrations/drift, backend tests, frontend checks/tests/build | The previous run on baseline `30a1263` failed on two Ruff findings; the findings are corrected and the release push will trigger a new run. |
| AI/MCP | AI policy gate plus private MCP Streamable HTTP service | MCP has ten tools, two resources, two templates and three prompts; authenticated Caddy smoke passes. AI retrieval/provider validation and generation remain unimplemented and gated. |
| Deployment | No production overlay, domain/TLS setup, backups, or VPS deployment evidence | Not deployed. |

Exact check commands, counts, and limits are recorded in [implementation progress](docs/IMPLEMENTATION_PROGRESS.md).

## Open gates

1. Implement browser OIDC Authorization Code with PKCE and select the production issuer/role mapping; API token validation is wired and fails closed when unconfigured.
2. Increase automated route and worker-runtime coverage (currently 66%) and add browser end-to-end/accessibility journeys.
3. Add heartbeat-loss runtime tests, worker health/job visibility, and bounded NASA Media job inputs; scheduled jobs remain off by default, while interactive NASA reads remain request-backed.
4. Keep AI generation disabled until formal NASA AI/SI/attribution review passes; the retrieval/provider pipeline, citation checks, and evaluation suite also need implementation.
5. Add MCP Inspector and production OIDC evidence; local authenticated MCP works through Caddy.
6. Resolve map-tile provider terms before public Earth-event map use.
7. Add production Compose secrets, HTTPS/domain configuration, resource limits, monitoring, encrypted backups, restore evidence, and image scanning.
8. Run the updated CI workflow in GitHub and establish reproducible Python dependency locking.

## Status definitions

- **Not started:** no implementation evidence.
- **In progress:** implementation exists but acceptance evidence is incomplete.
- **Implemented:** code or documentation exists, artifact named.
- **Tested:** relevant automated/manual checks passed and evidence is recorded.
- **Verified:** behavior and evidence reviewed against acceptance criteria.
- **Deployed:** running in the intended target environment.
- **Blocked:** an unresolved dependency prevents progress.

The [roadmap](ROADMAP.md), [task backlog](docs/10-implementation/TASK_BACKLOG.md), and [release checklist](docs/09-quality-assurance/RELEASE_CHECKLIST.md) define the remaining acceptance evidence. This is a local test build, not a full product release or production deployment.
