# Engineering Roadmap

The roadmap is outcome-based. Scope may change when official API contracts, testing or engineering evidence justify it.

## Phase 0 — Foundation and research
- [x] Create public repository and initial project documentation.
- [x] Add Python packaging, environment template and secret exclusions.
- [ ] Confirm local Python/Git environment.
- [ ] Verify current NASA endpoint documentation and inspect live APOD response.
- [ ] Record initial architecture decisions and acceptance criteria.

## Phase 1 — First production-minded API client
- [ ] Implement configuration using typed settings.
- [ ] Implement an asynchronous HTTPX client with timeouts.
- [ ] Parse and validate the current APOD response contract.
- [ ] Handle upstream errors, rate limits, invalid JSON and timeouts.
- [ ] Add deterministic tests using mocked HTTP responses.
- [ ] Add a minimal FastAPI health and APOD endpoint.

## Phase 2 — NASA integration layer
- [ ] Near-Earth Object Web Service (NeoWs).
- [ ] DONKI space-weather events.
- [ ] EONET natural events (after confirming supported API version).
- [ ] NASA Image and Video Library.
- [ ] Shared retry, rate-limit and provenance policies.

## Phase 3 — Data engineering
- [ ] Define canonical domain models.
- [ ] Add PostgreSQL and SQLAlchemy persistence.
- [ ] Add Alembic migrations.
- [ ] Implement idempotent ingestion and duplicate handling.
- [ ] Record source, retrieval time and upstream identifiers.

## Phase 4 — Scientific intelligence
- [ ] Search, filter and compare records.
- [ ] Add transparent analytics and visualisations.
- [ ] Generate reproducible reports with source references.

## Phase 5 — Web application
- [ ] React, TypeScript and Vite foundation.
- [ ] Responsive dashboard and search experiences.
- [ ] Charts, loading/error states and accessibility checks.

## Phase 6 — Evidence-grounded AI assistant
- [ ] Provider abstraction and structured output schemas.
- [ ] Retrieval limited to validated application records.
- [ ] Source citations and explicit uncertainty.
- [ ] Prompt-injection and unsupported-claim evaluations.

## Phase 7 — MCP server
- [ ] Official Python SDK integration.
- [ ] Typed tools, resources and prompts.
- [ ] Input validation, safe errors and structured results.
- [ ] MCP Inspector/manual compatibility checks and automated tests.

## Phase 8 — Production readiness
- [ ] Threat model and security review.
- [ ] Rate limiting, observability and operational health checks.
- [ ] Docker and Docker Compose.
- [ ] GitHub Actions: lint, type check, tests and build.
- [ ] Dependency and secret scanning.

## Phase 9 — Deployment and portfolio release
- [ ] Deploy to Ubuntu VPS behind HTTPS reverse proxy.
- [ ] Validate persistence, backups and recovery.
- [ ] Publish architecture diagrams, screenshots and demo instructions.
- [ ] Complete assessment and record known limitations.