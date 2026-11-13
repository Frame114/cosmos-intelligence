# Architecture Overview (legacy summary)

| Field | Value |
|---|---|
| Version | 1.0 |
| Last updated | 2026-11-13 |
| Status | Legacy orientation note |
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

The diagrams above describe the intended system; they do not represent a deployed application. The current repository contains an early FastAPI foundation and APOD prototype. Review [project status](../../PROJECT_STATUS.md) and the [implementation plan](../10-implementation/IMPLEMENTATION_PLAN.md) for the remaining work and acceptance gates.
