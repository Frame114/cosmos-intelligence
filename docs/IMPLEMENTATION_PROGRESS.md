# Phase 2 Implementation Progress

**Last updated:** 2026-11-14<br>
**Branch:** `main`<br>
**Status:** Local development build is ready for hands-on testing of the implemented data explorers, account workspace, administrative summaries, and authenticated MCP surface. AI generation remains incomplete; production release gates remain open.

This tracker distinguishes implementation from testing and release. A feature is not called production-ready or deployed because its code exists or its local checks pass.

## Recovery and repository state

- The requested recovery audit was completed and reported before implementation resumed.
- Existing work was preserved. The release candidate has been audited and verified locally; its release commit is the next repository step.
- The repository uses the existing `main` checkout; no additional worktree was found.
- `.env` is ignored by Git and excluded from the Docker build context. Its contents were not read or displayed. Compose may supply configured values to runtime containers; automated tests disable dotenv loading and use test-only values.
- `.env.example` contains placeholders only.

## Current implementation inventory

| Area | Implemented | Evidence and limits |
|---|---|---|
| Runtime/configuration | Python 3.12 metadata, validated Pydantic settings, `SecretStr`, file-backed key/DB URL support, official-host allowlists, safe errors, request IDs, liveness/readiness | `ruff`, `mypy`, and backend tests pass in Python 3.12. OIDC JWT signature/issuer/audience/expiry/scope/role validation is applied to protected REST routes. The browser does not yet implement Authorization Code with PKCE; local testing uses a development-only identity. |
| Database and worker | PostgreSQL models for sources, normalized NASA data, jobs, identities, saved records, conversations, and reports; Alembic migrations; idempotent persistence; durable queue; worker command, heartbeat, retry handling, bounded handlers, and deterministic daily schedule generation | PostgreSQL 18 migration and metadata drift check pass. Feed upserts, worker APOD persistence, unsupported-job rejection, leases, mocked dispatch, and repeat-safe daily scheduling are tested. Scheduling is disabled by default. NASA Media job inputs and worker health visibility are not implemented. |
| NASA integrations | Shared bounded HTTPX transport and typed APOD Basic, NeoWs, current DONKI, EONET v3, and NASA Media clients; DONKI has a bounded NASA Open APIs fallback for transient CCMC connection/server failures | Mocked client contract/error tests pass. A live 30-day DONKI notification request succeeded through the fallback and returned ten records after the primary CCMC host timed out. The API key remained runtime-only. |
| REST API | Public APOD list/detail/search, asteroid list/detail/compare, DONKI events and stored summary, EONET list/detail, NASA Media search/detail, saved records, conversations, reports, settings/session, and admin source/job summaries | Disposable PostgreSQL tests cover primary integration persistence and idempotency, media detail, stored DONKI summary, compare fields/units, AI policy failure, report and conversation ownership, and admin authorization. Some public error/provenance branches remain uncovered. |
| Frontend | React/TypeScript dashboard shell and astronomy, asteroid, space-weather, Earth-event map/list, media detail, assistant gate, reports, saved-record workspace, and settings pages | Typecheck, four Vitest tests, and production build pass. Explorers use the implemented REST contracts. Assistant generation remains a clear gated state; reports can be listed/read/deleted but cannot be generated. |
| Local containers | Python API/worker image, Node/Nginx frontend image, PostgreSQL 18, one-shot migration, Caddy proxy; isolated data/proxy networks and no host-published database/API/worker ports | Latest API/frontend images built and Compose services are healthy; migration task exited 0; liveness, readiness, auth-session, OpenAPI, and dashboard are reachable through Caddy. Worker runs with `WORKER_SCHEDULES_ENABLED=false`; no NASA request was made for runtime smoke checks. |
| AI and MCP | Authenticated private Streamable HTTP MCP adapter with ten tools, two static resources, two resource templates, and three prompts; AI policy gate | MCP delegates through versioned REST, validates OIDC or local-only development identity, enforces per-subject read limits and scopes, and has no host-published port. Authenticated Caddy transport smoke passed. AI retrieval/provider validation and generation remain absent and policy-gated. |
| CI | Python 3.12 and Node 22.22.2 workflow; lint, strict typecheck, disposable PostgreSQL migration/drift checks, backend tests, frontend checks/tests/build | Frontend job passed on `13d429c`; the Python job caught invalid syntax after generated-migration whitespace cleanup. The migration is restored and all Python checks pass locally; the corrective main push will trigger a fresh run. |

## Files changed in this implementation checkpoint

- Backend and API: `app/main.py`, `app/api/`, `app/core/`, `app/clients/`, `app/models/`, `app/services/`, `app/db/`, and `app/worker/`.
- Database: `alembic/alembic.ini`, `alembic/env.py`, and migrations `20261114_0001_initial.py` and `20261114_0002_job_schedule_keys.py`.
- Frontend: `frontend/src/`, `frontend/package.json`, `frontend/package-lock.json`, Vite/TypeScript setup, `frontend/Dockerfile`, and `frontend/nginx.conf`.
- Local runtime and CI: root `Dockerfile`, `compose.yaml`, `Caddyfile`, `.dockerignore`, `.gitignore`, `.env.example`, `pyproject.toml`, and `.github/workflows/ci.yml`.
- Tests: `tests/clients/`, `tests/db/`, `tests/conftest.py`, `tests/test_health.py`, and `tests/test_worker_handlers.py`.
- Project records: `README.md`, `PROJECT_STATUS.md`, `ROADMAP.md`, `CHANGELOG.md`, `TECHNICAL_DEBT.md`, `DECISIONS.md`, and the architecture/operations docs under `docs/`.

## Reconciled architecture decisions

| ID | Decision | Status |
|---|---|---|
| ARC-01 | Align package metadata, CI, and backend image to Python 3.12; use Node 22.22.2 and PostgreSQL 18 | Implemented. Current Docker image patch tags are recorded in the Dockerfiles/Compose file; recheck and scan before release. |
| ARC-02 | APOD Basic uses the dedicated guide's `date_from`/`date_to` and `/{YYMMDD}` contract, with the 25-item API bound | Implemented in the client and API. Keep contract checks current because NASA can change the service. |
| ARC-03 | Use the current CCMC DONKI API base after the 2026-09-30 migration | CCMC is primary; transient connection/server failures fall back to NASA Open APIs DONKI. The live fallback request succeeded; mock contracts pass. |
| ARC-04 | Keep identity provider-neutral; production settings require HTTPS OIDC issuer and audience | JWT signature, issuer, audience, expiry, scope, and role checks protect API routes. Browser PKCE sign-in and broader provider/JWKS acceptance evidence remain open. |
| ARC-05 | Use Leaflet/OpenStreetMap with visible attribution for the event map | Interactive event map is implemented with visible attribution and NASA category imagery overlays. Review tile-provider terms before public use. |
| ARC-06 | AI generation requires both explicit NASA policy approval and OpenRouter configuration | Default-off settings gate exists; no generation route/provider implementation exists. |
| ARC-07 | Keep `NASA_API_KEY` private; read runtime environment or file-backed secret; use ignored `.env` locally and file-backed secrets for production | Local environment remains ignored; `.dockerignore` excludes env files. No key is returned by routes or included in frontend builds. Production Compose secrets are not implemented. |

## Milestones

| ID | Scope | Status | Verification |
|---|---|---|---|
| M0 | Recover state, audit security/inventory, reconcile architecture | Complete | Recovery report delivered; current baseline and open work recorded above. |
| M1 | Settings, API lifecycle, PostgreSQL migration/readiness, local Docker startup | Implemented and locally verified | Python 3.12 checks; PostgreSQL 18 migration/drift check; Compose build/start and health/routing smoke test. No production deployment. |
| M2 | NASA contracts and typed clients | Implemented with mocked tests | APOD Basic, NeoWs, current DONKI, EONET v3, NASA Media adapters; `tests/clients/test_nasa_clients.py`. Live upstream availability/contract is not certified by mocks. |
| M3 | Normalization and idempotent persistence | Implemented for current sources; operational expansion open | PostgreSQL repeated-upsert tests cover APOD, NeoWs, DONKI, EONET, and NASA Media. Job enqueue/claim, exclusive leases, expiry recovery, retry limits, APOD worker persistence, mocked dispatch, and deterministic/idempotent daily schedules are tested. Scheduling is opt-in; heartbeat/lease-loss runtime tests, NASA Media job inputs, worker health visibility, and API-to-worker cutover remain. |
| M4 | Versioned REST, identity boundary, rate limits | Core local flows implemented; coverage incomplete | Owner-scoped saved/conversation/report read/delete, compare, stored summary, auth session, and admin summaries/retry are implemented. Provider-neutral OIDC token validation is wired to protected routes. Browser PKCE sign-in, provider selection, and broader route error/provenance coverage remain. |
| M5 | Dashboard and accessible data explorers | Implemented for the current local REST surface; E2E acceptance open | Typecheck, 4 unit tests, production build, and Compose smoke pass. Full browser journeys and route-specific API coverage remain. |
| M6 | Gated research assistant and MCP | MCP implemented locally; AI pipeline not implemented | Ten tools, two resources, two templates and three prompts; Streamable HTTP smoke through Caddy listed tools and rejected invalid input. Assistant/report generation fails safely behind policy and service gates. |
| M7 | CI, operations, security and release hardening | In progress | CI workflow and local Compose checks are implemented. GitHub Actions, production secret mounts, image scanning, observability, backups, and deployment remain unverified. |

## Verification results

| Check | Result | Scope |
|---|---|---|
| `ruff check .` | Passed | Python 3.12 container; repository Python source and tests. |
| `mypy app` | Passed, no issues in 45 source files | Strict application typing. |
| `pytest --cov=app --cov-report=term-missing` | Passed, 49 tests; 66% total app coverage | Python 3.12 with disposable PostgreSQL `cosmos_test`; coverage remains below release target. |
| `alembic -c alembic/alembic.ini upgrade head` | Passed | Local disposable PostgreSQL 18 service; never production. |
| `alembic -c alembic/alembic.ini check` | Passed: no new upgrade operations | PostgreSQL 18 metadata comparison. |
| `npm ci` | Passed; audit reported 0 vulnerabilities | Node 22.22.2 Linux container. |
| `npm run check` | Passed | TypeScript. |
| `npm test -- --run` | Passed, 4 tests | Vitest on the host Node runtime; container image also builds on the configured Node 22.22.2. |
| `npm run build` | Passed | Vite production bundle; Compose frontend image build passed on Node 22.22.2. |
| `docker compose config --quiet` | Passed | Compose service/network configuration. |
| `docker compose build` | Passed | API and frontend images. |
| Compose runtime smoke | API/frontend/MCP/PostgreSQL healthy; migration exited 0; health, auth-session, OpenAPI, dashboard, authenticated MCP through Caddy, and the 30-day DONKI fallback request passed. MCP listed 10 tools and rejected an invalid asteroid ID. Worker schedules confirmed false. | Local only; the DONKI verification made one live NASA notification request using the runtime key. The key was not displayed or logged. |
| GitHub Actions | Frontend job passed on `13d429c`; Python job failed Ruff because a migration file was collapsed during whitespace cleanup. Restored migration and all local checks now pass; corrective run pending. | The corrective push to `main` triggers the workflow. |

An earlier full coverage attempt timed out while opening a connection to disposable PostgreSQL during the DONKI route test. Later full runs passed. The current 49-test Python 3.12 run is the latest coverage measurement; coverage is lower than earlier partial-suite percentages because it includes all current application modules.

## Outstanding issues and next milestone

1. Add browser OIDC Authorization Code with PKCE and select/configure the production issuer and role mapping; protected API routes already validate configured JWTs and fail closed.
2. Add route-level error/provenance tests for remaining NeoWs, DONKI, EONET, NASA Media, JPL, and GDELT branches; increase overall coverage from the current 66%.
3. Add heartbeat-loss runtime tests, worker health/job visibility, and bounded NASA Media job inputs before moving upstream reads out of request handlers. Daily APOD/NeoWs/DONKI/EONET scheduling remains opt-in.
4. Implement the bounded retrieval and provider adapter, citation/schema validation, evaluations, and spend controls only after the NASA AI/SI approval gate; generation must remain disabled until approval.
5. Add MCP Inspector evidence and production OIDC configuration; the local SDK transport test through Caddy passes.
6. Add a production Compose overlay with file-backed secrets, domain/TLS configuration, resource limits, persistent certificate state, image scanning, backups, and an approved deployment runbook.
7. Resolve dependency lock/review policy and run the updated CI workflow in GitHub.

No migration has been run against production. No production deployment has been performed. The local app is available for testing at `http://localhost:8080`; browser PKCE sign-in, AI generation, production hardening, GitHub CI result, and deployment are not complete.
