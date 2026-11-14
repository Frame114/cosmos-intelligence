# Architecture Overview (legacy summary)

| Field | Value |
|---|---|
| Version | 1.0 |
| Last updated | 2026-11-14 |
| Status | Concise architecture overview; delivery status refreshed |
| Purpose | Preserve a concise overview for existing repository links. |
| Scope | Intended architecture orientation; see the current architecture specification for full details. |
| Assumptions | This is a design baseline; verify repository state and mutable upstream contracts before implementation. |

The current source of truth is [the system architecture specification](../01-architecture/SYSTEM_ARCHITECTURE.md). This page is retained as a short orientation note for existing links.

## Intended system boundaries

```text
NASA public APIs
      |
      v
Integration clients (HTTPX)
      |
      v
Validation and normalisation (Pydantic/domain models)
      |
      +------> API service (FastAPI) ------> Web client (React)
      |
      +------> Persistence (PostgreSQL)
      |
      +------> Analytics and report services
                       |
                       v
                AI assistant (evidence-grounded)
                       |
                       v
                MCP tools/resources
```

## Design constraints

- Upstream services are unreliable dependencies: set timeouts and handle errors explicitly.
- External payloads are untrusted and may change; validate before use.
- Domain logic should not depend directly on HTTP response dictionaries.
- Keep provider-specific API details inside integration adapters.
- Persist source identifiers, source URLs where available, and retrieval timestamps.
- AI components consume validated records and must not invent scientific measurements.
- MCP tools should call the same application services as the REST API rather than duplicate business logic.

## Delivery status

The diagrams above describe the intended system, not a production deployment. A local Compose slice now includes the FastAPI API, PostgreSQL, migrations, static React frontend, and Caddy proxy. Typed NASA clients and public read routes are implemented, but durable workers, protected account/report APIs, AI, MCP, and production deployment remain incomplete. Review [project status](../../PROJECT_STATUS.md) and [implementation progress](../IMPLEMENTATION_PROGRESS.md) for evidence and remaining work.
