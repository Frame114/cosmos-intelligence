# Changelog
## Repository release preparation (2026-11-14)

- Replaced the outdated planned-project README with current local-build capabilities, architecture, prerequisites, Compose setup, configuration, test commands, integration notes, and limitations.
- Added contributor setup and quality-check guidance; corrected the documentation index, local development guide, and Compose specification to reflect the running MCP service and implemented local workflows.
- Corrected Ruff violations and a type-narrowing issue in the JPL orbit map route found during the release audit.
- Re-ran the Python 3.12 suite against disposable PostgreSQL: 49 tests passed, Ruff and mypy passed, both migrations applied, and Alembic detected no schema drift. App coverage measured 66%.
- Frontend typecheck, 4 Vitest tests, production build, Compose config, and local API/frontend/PostgreSQL health checks passed. Previous GitHub Actions baseline run failed on Ruff; the corrected release push will trigger a new run.

## Local test build update (2026-11-14)

- Added a bounded DONKI fallback to NASA Open APIs when the migrated CCMC primary times out or returns a retryable server failure. The local runtime returned ten notifications for the 30-day window through the fallback; rate-limit failures do not trigger fallback.
- Added the private authenticated MCP Streamable HTTP service, ten tools, two static resources, two templates, and three prompts. It delegates to the existing REST API and has no published host port.
- Verified MCP client initialization and tool listing through Caddy with a development-only test identity; invalid asteroid input was rejected without a NASA request.
- Increased Nginx request-header buffers after the browser returned 400 for oversized headers; rebuilt frontend now serves the dashboard with HTTP 200.
- MCP and browser smoke checks leave NASA worker schedules disabled; AI report generation remains gated and unavailable.


## Unreleased — local test build checkpoint (2026-11-14)

- Completed local API contracts for asteroid comparison, diameter filtering, stored DONKI summary, NASA Media details, saved-record CRUD, conversation/report ownership, and admin source/job visibility/retry.
- Wired configured OIDC bearer-token validation to protected REST routes and added development-only browser identity/token controls.
- Connected the explorer pages, pagination, EONET map/list selection, save actions, media details, saved workspace, reports, settings, and assistant gate to the API.
- Rebuilt and started the local Compose stack. API/frontend/PostgreSQL are healthy through Caddy; worker schedules remain disabled.
- Verification: 49 backend tests passed (71% coverage), Ruff, mypy, Alembic migration/drift checks, four frontend tests, frontend typecheck/build, and local health/auth/OpenAPI smoke checks passed.
- AI generation remains unavailable pending NASA policy approval and implementation of retrieval/provider validation; MCP is implemented and locally smoke-tested; production OIDC, AI generation, and deployment remain incomplete.

This log records repository-level changes. Specifications describe future work and do not imply implementation.

## [Unreleased] — 2026-11-14

### Added

- PostgreSQL models, an Alembic initial migration, provenance-preserving ingestion helpers, and public NASA read routes.
- Typed APOD Basic, NeoWs, current DONKI, EONET v3, and NASA Media clients with bounded shared HTTP behavior.
- React dashboard pages and shared API components for the selected data areas.
- A local Docker Compose stack with PostgreSQL, a one-shot migration service, non-root backend image, static frontend, and Caddy reverse proxy.
- Disposable PostgreSQL integration coverage and an updated CI workflow for Python 3.12 and Node 22.22.2.
- PostgreSQL job enqueue/claim, exclusive lease, expiry recovery, owner validation, and retry primitives with integration tests.
- A separate Compose worker process with lease heartbeats, safe retry handling, and bounded allowlisted APOD, NeoWs, DONKI, and EONET ingestion handlers.
- A schema migration and deterministic, idempotent daily job generation for APOD, NeoWs, DONKI, and EONET; automated scheduling is disabled by default.
- Production API documentation is disabled when `APP_ENV=production`.

### Changed

- Project status, roadmap, local development, Compose architecture, and implementation progress now reflect verified local implementation and open work.
- `.dockerignore` excludes `.env` files from the image build context; `.env.example` uses safe placeholder values.
- CI now applies and checks Alembic migrations against disposable PostgreSQL and runs strict application type checking.

### Verification

- Backend: Ruff, mypy (40 source files), 32 pytest cases, PostgreSQL migrations, and Alembic metadata check passed (74% total app coverage).
- Frontend: npm install, type check, three unit tests, and production build passed.
- Compose: config and image builds passed; migration completed; API, frontend, and PostgreSQL are healthy; worker is running idle; readiness and dashboard returned HTTP 200 through Caddy.
- No live NASA data request, GitHub Actions run, or production deployment is claimed.

## [Phase 1 documentation] — 2026-11-13

### Added

- Phase 1 documentation package covering product, system architecture, technical design, five selected NASA integrations, AI/MCP, security, UX, infrastructure, QA, implementation, and operations.
- Documentation index, Codex implementation instructions, pseudocode references, and definition of done.
- Research notes that record source links, observed contracts, uncertainty, and unresolved NASA AI/media policy decisions.

### Changed

- README, project status, roadmap, architecture decision log, technical debt register, and assessment distinguish specifications from verified product behavior.

### Not claimed

- The documentation milestone did not implement or verify a full-stack deployment, frontend, database, production NASA connector, AI assistant, MCP server, or VPS deployment.
