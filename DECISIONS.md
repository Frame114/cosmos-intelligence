# Architecture Decision Log

This is the concise project-level record. Detailed architecture decisions and implementation-specific updates belong in [the ADR register](docs/01-architecture/ARCHITECTURE_DECISIONS.md). Review a decision when evidence or project scope changes.

## DEC-001 — Python backend and FastAPI

- **Status:** Accepted as architecture direction.
- **Decision:** Use a typed Python backend with FastAPI, Pydantic, HTTPX, SQLAlchemy, and Alembic.
- **Reason:** The stack supports asynchronous HTTP integration, explicit validation, API schema generation, and the project's data/AI objectives.
- **Implementation:** Package metadata, CI, and the backend image use Python 3.12; strict mypy checks pass locally.

## DEC-002 — Docker-first full application

- **Status:** Accepted target; local development slice implemented, remaining services/deployment open.
- **Decision:** Use Docker Compose for reproducible local operation and the planned multi-service application.
- **Reason:** The backend, database, frontend, and proxy should run consistently without host-level Python/Node/PostgreSQL. Worker and MCP services remain future work.
- **Reference:** [Docker architecture](docs/08-infrastructure/DOCKER_ARCHITECTURE.md).

## DEC-003 — Verify upstream contracts before implementation

- **Status:** Accepted.
- **Decision:** Base each NASA adapter on current official documentation and an inspected live response. Record limitations, date, rate behavior, source provenance, and rights.
- **Reason:** API versions and schemas change; observed samples are evidence, not a guarantee.
- **Reference:** [NASA integration portfolio](docs/03-integrations/NASA_INTEGRATIONS.md).

## DEC-004 — Persist provenance and distinguish observation from interpretation

- **Status:** Accepted.
- **Decision:** Keep source identifiers, retrieval times, source references, and normalized values traceable. Clearly separate upstream data from Cosmos calculations and AI-written explanations.
- **Reason:** Scientific interpretation requires reproducibility, uncertainty, and clear attribution.

## DEC-005 — AI generation requires policy and evidence gates

- **Status:** Accepted gate; policy question unresolved.
- **Decision:** AI is optional, grounded in validated records, citation-checked, and feature-gated. Do not enable generation from NASA-derived content until formal review resolves NASA AI/SI usage and attribution wording.
- **Reason:** Generated claims and source media require accurate attribution, uncertainty, and policy compliance.
- **Reference:** [AI guardrails](docs/04-ai-engineering/AI_GUARDRAILS.md) and [API provenance](docs/03-integrations/API_PROVENANCE.md).

## DEC-006 — MCP calls shared application services

- **Status:** Accepted direction; not implemented.
- **Decision:** MCP tools should reuse authorized application services and share validation, ownership, limits, and provenance behavior with the REST API.
- **Reason:** Prevent duplicated business rules and bypassed controls.
