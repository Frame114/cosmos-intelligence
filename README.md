# Cosmos Intelligence

Cosmos Intelligence is an independent research dashboard and API for exploring NASA astronomy, near-Earth objects, space weather, Earth events, and NASA media. It combines source-backed public data with saved records and other user-workspace features. The current application is a local development build; it is not a production service and is not affiliated with NASA.

**Version:** 0.1.0 (pre-release local build)

## Current status

The Docker Compose application is available for local hands-on testing. Implemented flows include astronomy/APOD browsing, asteroid search and comparison with JPL Horizons trajectory sampling, DONKI space-weather events, EONET Earth events with interactive mapping and related coverage, NASA media search/details, saved records, settings, reports, and an authenticated MCP endpoint. AI-generated answers/reports are deliberately disabled pending policy review and implementation. Production OIDC browser sign-in, operations hardening, and deployment are not complete.

See [project status](PROJECT_STATUS.md), [implementation progress and verification evidence](docs/IMPLEMENTATION_PROGRESS.md), [roadmap](ROADMAP.md), and [technical debt](TECHNICAL_DEBT.md).

## Capabilities

- Browse APOD Basic, NeoWs near-Earth objects, DONKI space-weather notifications, EONET events, and NASA Image and Video Library records.
- View provenance and upstream source links, and save selected records to a user workspace.
- Compare asteroid records and visualize close approaches plus sampled JPL Horizons trajectories. Orbital displays are projections and preserve source units; they are not impact forecasts.
- View EONET event locations, category imagery overlays, NASA media matches, and related news search results.
- Use a responsive React dashboard backed by a versioned FastAPI API.
- Persist source records and user workspace data in PostgreSQL, with Alembic migrations and an opt-in ingestion worker.
- Connect an authenticated Model Context Protocol (MCP) service that delegates to the application API.

## Technology and architecture

| Layer | Implementation |
|---|---|
| Frontend | React, TypeScript, Vite, Leaflet, Three.js, Recharts |
| API and clients | Python 3.12, FastAPI, Pydantic, HTTPX |
| Persistence | PostgreSQL, SQLAlchemy async, Alembic |
| Background work | Separate Python worker with PostgreSQL-backed jobs and leases |
| MCP | Official Python MCP SDK over Streamable HTTP |
| Local operations | Docker Compose, Nginx, Caddy |
| Quality | pytest, Ruff, mypy, Vitest, TypeScript, GitHub Actions |

```text
app/                 API, NASA/JPL clients, persistence, auth, MCP, worker
alembic/             Database migration configuration and revisions
frontend/             React dashboard and frontend checks
tests/               Backend unit, contract, and optional PostgreSQL tests
docs/                Product, architecture, integration, operations, and QA docs
compose.yaml         Local API, database, migrations, worker, frontend, and proxy
```

The API, MCP service, and worker use the same backend image with separate commands. Caddy routes the local dashboard/API/MCP on port 8080. PostgreSQL has no published host port in the default Compose configuration.

## Prerequisites

- Docker Engine/Desktop with the Docker Compose plugin.
- For checks outside Docker: Python 3.12 and Node.js 22.22.2 with npm 11.6.2.
- A NASA API key is optional for local use. Without one, the stack uses NASA's `DEMO_KEY`, which has stricter rate limits.

## Run locally with Docker Compose

```sh
docker compose up --build -d
docker compose ps
```

Open <http://localhost:8080>. The API schema is at <http://localhost:8080/api/v1/openapi.json>. Stop containers with `docker compose down`; this preserves the named PostgreSQL volume. Use `docker compose down -v` only when you intentionally want to remove local database data.

Optional local configuration:

1. Copy `.env.example` to `.env`.
2. Put a private NASA key in `.env` as `NASA_API_KEY=...` if you have one. `.env` is ignored and excluded from Docker build contexts. Never paste real credentials into source files, shell history, issue reports, or logs.
3. Start or rebuild with `docker compose up --build -d`.

Compose enables a development-only identity by default for local workspace testing. It is not a sign-in system and must not be used for a public deployment. Worker schedules are disabled by default; set `WORKER_SCHEDULES_ENABLED=true` in the local environment only when you want the worker to enqueue daily data windows.

## Run checks

Install the backend and development tools:

```sh
python -m pip install -e ".[dev]"
```

Run fast backend tests, lint, and type checking:

```sh
ruff check .
mypy app
python -m pytest -q
```

PostgreSQL-backed integration tests are skipped unless `COSMOS_TEST_DATABASE_URL` points to a disposable test database. Apply migrations to that database before running those tests. Never point test commands at the persistent local or production database. Coverage is available with `python -m pytest --cov=app --cov-report=term-missing` after installing the declared development dependencies.

Run frontend checks:

```sh
cd frontend
npm ci
npm run check
npm test -- --run
npm run build
```

The GitHub Actions workflow runs Python lint/type/tests and migration checks against a disposable PostgreSQL service, plus frontend typecheck/tests/build.

## Integrations and external services

- NASA APOD Basic, NeoWs, DONKI, EONET v3, and NASA Image and Video Library.
- JPL Small-Body Database and Horizons for asteroid details and trajectory samples.
- GDELT DOC API for related news links; NASA GIBS imagery layers for supported Earth-event categories.
- OpenStreetMap tiles for the event map, with on-map attribution. Review tile-provider usage terms before public deployment.
- Docker Hub images for PostgreSQL and Caddy during Compose startup/build.

Upstream APIs and tile/news services can be unavailable, rate-limited, or return no matches. Related news and library images are labeled as unverified matches, not confirmed evidence for an individual event. NASA asset credit and rights remain item-specific. See [NASA integrations](docs/03-integrations/NASA_INTEGRATIONS.md) and [provenance](docs/03-integrations/API_PROVENANCE.md).

## Configuration and security

`.env.example` documents local Compose settings with nonsecret placeholders. `.env`, `.env.*`, `.secrets/`, key files, local data, caches, and build outputs are ignored. NASA and database credentials are read at runtime; the frontend does not receive the NASA key. The API supports secret-file settings for direct runtime configuration, but production Compose secret mounts and deployment configuration are still open work. See [environment configuration](docs/08-infrastructure/ENVIRONMENT_CONFIGURATION.md) and [secrets management](docs/06-security/SECRETS_MANAGEMENT.md).

## Documentation

- [Documentation index](docs/README.md)
- [Architecture](docs/01-architecture/SYSTEM_ARCHITECTURE.md)
- [API specification](docs/02-technical/API_SPECIFICATION.md)
- [Local development](docs/11-operations/LOCAL_DEVELOPMENT.md)
- [Testing strategy](docs/09-quality-assurance/TESTING_STRATEGY.md)
- [Implementation progress](docs/IMPLEMENTATION_PROGRESS.md)
- [Contributing](CONTRIBUTING.md)

## License

The repository code is available under the [MIT License](LICENSE). NASA datasets/media may have separate attribution and usage terms. Cosmos Intelligence is an independent research project and does not represent NASA.
