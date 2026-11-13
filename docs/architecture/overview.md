# Architecture Overview

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

## Incremental delivery

The first working slice is deliberately narrow: inspect and integrate the current APOD endpoint, test it independently, and expose it through a small service. Other integrations follow only after the shared patterns are understood and tested.