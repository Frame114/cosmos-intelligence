# Cosmos Intelligence

Cosmos Intelligence is a planned open-source platform for exploring NASA astronomy, near-Earth object, space-weather, Earth-event, and media data. The project combines a Python API, a web dashboard, a provenance-aware data layer, and optional evidence-grounded AI and Model Context Protocol (MCP) access.

**Current state:** architecture and documentation baseline. The repository also contains an early FastAPI foundation and APOD prototype. A complete Docker-first full-stack application has not yet been implemented or verified. See [project status](PROJECT_STATUS.md) for the evidence-based breakdown.

## Start here

- [Documentation index](docs/README.md)
- [Product requirements](docs/00-project/PRD.md)
- [System architecture](docs/01-architecture/SYSTEM_ARCHITECTURE.md)
- [NASA integration research](docs/03-integrations/NASA_INTEGRATIONS.md)
- [Implementation plan](docs/10-implementation/IMPLEMENTATION_PLAN.md)
- [Roadmap](ROADMAP.md)

## Product direction

The planned application will:

- Integrate selected NASA data services with explicit validation, source provenance, and attribution.
- Support searching, comparing, and visualizing astronomy, near-Earth objects, space weather, natural events, and NASA media.
- Present media links with item-level rights metadata; the application will not mirror NASA media binaries by default.
- Add an optional research assistant whose answers reference validated source records and disclose uncertainty.
- Expose selected application capabilities through typed MCP tools and resources.
- Run reproducibly in Docker Compose for local development and deploy behind HTTPS on an Ubuntu VPS.

These are planned capabilities, not a claim that the features already exist. See [product scope](docs/00-project/PRODUCT_SCOPE.md) for explicit inclusions and exclusions.

## Target architecture

| Area | Documented direction |
|---|---|
| Backend | Python, FastAPI, Pydantic, HTTPX, SQLAlchemy, Alembic |
| Database | PostgreSQL |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Charts and maps | Recharts; map provider remains a deployment decision |
| AI | Optional provider abstraction; public generation remains gated on policy review |
| Interoperability | Official Python MCP SDK, with transport and authorization boundaries |
| Operations | Docker Compose, GitHub Actions, Caddy for HTTPS |

The target and rationale are in [technology stack](docs/02-technical/TECH_STACK.md); [Docker architecture](docs/08-infrastructure/DOCKER_ARCHITECTURE.md) is a specification, not an available compose deployment yet.

## NASA integrations and research freshness

The current research baseline selects APOD Basic, NeoWs, DONKI, EONET v3, and NASA's Image and Video Library. Endpoint behavior can change; each integration must be rechecked against its linked official documentation and a fresh response before implementation. NASA's published APOD migration retires the legacy APOD API on 2026-12-01; implementation should use the replacement service and verify the dedicated date-filter contract.

NASA-branded or NASA-derived content is not an endorsement. Asset-level copyright/credit may vary, and NASA's current AI/SI language needs formal review before the project enables generated responses based on NASA data. See [NASA attribution and provenance](docs/03-integrations/API_PROVENANCE.md) and the integration-specific policy gate.

Official starting points: [NASA API portal](https://api.nasa.gov/), [APOD Basic](https://science.nasa.gov/wp-json/wp/v2/apod-basic), [NeoWs](https://api.nasa.gov/), [EONET v3](https://eonet.gsfc.nasa.gov/api/v3), [NASA Image and Video Library](https://images-api.nasa.gov/).

## Development

The current executable repository is an early Python backend prototype, not the full-stack target. For the existing environment and commands, consult [local development](docs/11-operations/LOCAL_DEVELOPMENT.md), then check that guide against the current repository before relying on any command. It describes intended setup steps and does not assert a successful build, test run, or Docker startup.

Do not place real NASA or LLM credentials in source control, logs, example fixtures, or URLs. The architecture provides secret-handling rules in [secrets management](docs/06-security/SECRETS_MANAGEMENT.md).

## Project records

- [Project status](PROJECT_STATUS.md)
- [Engineering roadmap](ROADMAP.md)
- [Architecture decision log](DECISIONS.md)
- [Technical debt register](TECHNICAL_DEBT.md)
- [Engineering assessment](ASSESSMENT.md)
- [Changelog](CHANGELOG.md)
- [Definition of done](DEFINITION_OF_DONE.md)

## Licensing and disclaimer

Repository source code is licensed under MIT (see [LICENSE](LICENSE)). NASA datasets and media remain subject to their own terms, attribution rules, and item-specific rights. Cosmos Intelligence is an independent educational and research project, not an official NASA product. Its content is not authoritative operational, safety, or scientific advice.
