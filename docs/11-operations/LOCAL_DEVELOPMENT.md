# Local Development

**Version:** 1.0<br>
**Last updated:** 2026-11-14<br>
**Status:** Local Compose workflow rebuilt and ready for hands-on application testing<br>
**Purpose:** Explain the implemented local Compose workflow and its limits.<br>
**Scope:** Local dashboard, API, PostgreSQL, migrations, worker, MCP, proxy, configuration, and verification commands. Production deployment remains out of scope.<br>
**Assumptions:** The Python API requires Python 3.12. Docker Compose is the supported way to start the full local stack. Upstream NASA services may be unavailable or rate-limited.<br>



## Target developer workflow

Prerequisite: Docker Engine/Desktop with Docker Compose plugin. Start the current development slice with:

~~~sh
docker compose up --build -d
~~~

This starts the frontend, API, PostgreSQL, one-shot migrations, ingestion worker, private MCP service, and local Caddy proxy. The worker waits for explicitly enqueued APOD, NeoWs, DONKI, or EONET jobs. Deterministic daily schedules are available by setting `WORKER_SCHEDULES_ENABLED=true` in the ignored local environment; the default is false. MCP is available at `http://localhost:8080/mcp`; in local development use an MCP client with `Authorization: Bearer local:your-test-user`. This token form is accepted only with development auth enabled. A developer does not need host Python, Node, or PostgreSQL to run this stack. Open `http://localhost:8080`; the machine-readable API schema is at `http://localhost:8080/api/v1/openapi.json` (interactive docs are development-only; local workspace APIs use a development identity when enabled, without browser OIDC sign-in). Use `docker compose logs -f`, `docker compose exec api ...`, and `docker compose down` for routine work. `docker compose down` retains the named database volume.

## Current repository status

The Compose smoke check on 2026-11-14 confirmed successful migration; healthy API/frontend/PostgreSQL containers; liveness/readiness/auth-session/OpenAPI responses through Caddy; worker schedules confirmed disabled. No NASA route was called during smoke checks. Automated backend/frontend verification and current feature limits are recorded in `docs/IMPLEMENTATION_PROGRESS.md`. This is a local development workflow, not a production deployment.

Compose uses `DEMO_KEY` when `NASA_API_KEY` is unset. A locally configured `NASA_API_KEY` may be supplied in the ignored `.env`; Compose passes it to the API and ingestion worker at runtime. Neither process logs or returns the key. The Docker build context excludes `.env` files, and the frontend image does not receive the key. Production should use a protected file-backed secret, not a committed environment file. Never put the actual key in a command that may be recorded or in a committed file.

## Related documents

[Docker Compose Specification](../08-infrastructure/DOCKER_COMPOSE_SPECIFICATION.md), [README](../../README.md), [Troubleshooting](TROUBLESHOOTING.md).
