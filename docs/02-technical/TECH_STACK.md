# Technology Stack

**Version:** 1.0  
**Last updated / research date:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Scope:** Covers the proposed Technology Stack behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  

**Purpose:** Record the selected stack, compatibility approach, and official research links.  

## Selected stack

| Area | Selection | Reason and implementation rule |
|---|---|---|
| Runtime | Python 3.12 | Security-supported through 2028-10 per Python Developer Guide; mature library compatibility. Set requires-python and CI matrix to 3.12 in implementation. Recheck a newer supported runtime quarterly. |
| HTTP API | FastAPI + Pydantic v2 + pydantic-settings | Typed request/response validation, generated OpenAPI, dependency injection, settings from env/secrets. |
| HTTP client | HTTPX AsyncClient | Shared async connection pool with explicit connect/read/write/pool timeout, bounded connections, and mocked contracts. |
| Persistence | PostgreSQL 18 + SQLAlchemy 2 + Alembic + psycopg 3 | Relational constraints, JSONB provenance, transactional upsert, full-text search. Review the PostgreSQL supported major before image lock. |
| Background work | Separate Python worker + PostgreSQL job/lease table | Durable work without Redis; queue operations use short transactions and idempotent handlers. |
| Frontend | React + TypeScript + Vite | Component UI and typed browser contracts; Vite current docs require Node 20.19+ or 22.12+. Use Node 22 LTS image initially and confirm active LTS when locking. |
| Styling | Tailwind CSS 4 | Utility styling; current v4 browser baseline is Safari 16.4+, Chrome 111+, Firefox 128+. Confirm user browser support before release. |
| Charts/icons/maps | Recharts, Lucide React, Leaflet with React Leaflet | Declarative accessible chart wrappers, tree-shakable SVG icons, event geometry maps. Select and document a permitted tile provider and attribution before production. |
| AI gateway | OpenRouter Chat Completions API through a provider protocol | Configurable model/provider routing; current capabilities are discovered/configured, never assumed permanent. |
| Agent protocol | Official MCP Python SDK, current stable line at lock time (v2 as researched) | Typed tools/resources/prompts; use Streamable HTTP for deployment and stdio locally. Read the migration guide before adopting v2 breaking changes. |
| Containers/edge | Docker Engine, Compose Specification, multi-stage images, Caddy | Reproducible host-independent dev; one HTTPS edge; private application/data networks. |
| Quality | pytest, Ruff, mypy, GitHub Actions | Unit/contract/integration/evaluation coverage; deterministic CI without real NASA/LLM keys. |

## Dependency and version policy

Use tested compatible ranges during active work, then produce and commit one lockfile per package manager. CI and release images install from the lockfile. Dependabot or equivalent proposes updates; review changelogs, run focused contract/security/AI evaluations, and roll updates in small batches. Never make the documentation version string a substitute for a lockfile.

The repository presently advertises Python 3.11+, CI uses 3.11, and pyproject.toml has uncommitted work. This specification does not alter that file. Milestone 1 must reconcile the source metadata, container base image, and CI around Python 3.12.

## Research sources

Official sources reviewed 2026-11-13:

- Python lifecycle: [Python versions](https://devguide.python.org/versions/)
- FastAPI/Pydantic: [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/), [Pydantic models](https://pydantic.dev/docs/validation/latest/concepts/models/)
- HTTPX: [timeouts](https://www.python-httpx.org/advanced/timeouts/)
- SQLAlchemy/Alembic: [SQLAlchemy 2.0 asyncio](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html), [Alembic autogenerate limitations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- PostgreSQL: [current documentation](https://www.postgresql.org/docs/current/), [full-text search types](https://www.postgresql.org/docs/current/datatype-textsearch.html)
- Frontend: [React](https://react.dev/), [React with TypeScript](https://react.dev/learn/typescript), [TypeScript handbook](https://www.typescriptlang.org/docs/handbook/intro.html), [Vite guide](https://vite.dev/guide/), [Tailwind upgrade/current major guidance](https://tailwindcss.com/docs/upgrade-guide), [Recharts](https://recharts.github.io/en-US/), [Lucide React](https://lucide.dev/guide/react/)
- Docker/Caddy: [Compose Specification](https://docs.docker.com/reference/compose-file/), [secrets](https://docs.docker.com/compose/how-tos/use-secrets), [multi-stage builds](https://docs.docker.com/build/building/multi-stage/), [Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)
- AI/MCP: [OpenRouter chat completion API](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion), [official MCP Python SDK](https://py.sdk.modelcontextprotocol.io/), [MCP SDK transport guide](https://py.sdk.modelcontextprotocol.io/run/)
- Quality/CI: [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html), [Ruff](https://docs.astral.sh/ruff/), [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)

## Security and operations

Containers run as non-root where practical, use minimal runtime stages, pin supported image majors/digests for releases, and receive secrets at runtime. Host ports are not exposed from PostgreSQL, API, worker, or MCP. Build credentials use BuildKit secret mounts, not ARG/ENV or image layers. Run dependency and image scanning on change and before release.

## Known limitations

Current official SDK/library docs change continuously. Exact versions, model IDs, provider capabilities, tile-source terms, and image patch tags remain implementation-time checks. Tailwind v4 browser support and the map tile source are product/deployment gates.

## Related documents

[Architecture Decisions](../01-architecture/ARCHITECTURE_DECISIONS.md), [Docker Architecture](../08-infrastructure/DOCKER_ARCHITECTURE.md), [AI Provider Design](../04-ai-engineering/LLM_PROVIDER_DESIGN.md).
