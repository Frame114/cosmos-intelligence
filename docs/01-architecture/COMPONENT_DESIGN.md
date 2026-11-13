# Component Design

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Give implementation boundaries, dependencies, and likely package locations.  
**Scope:** Covers the proposed Component Design behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Backend package boundaries

~~~text
app/
  api/v1/                 # route adapters, schemas, error mapping
  core/                   # settings, logging, security, request IDs
  clients/nasa/            # shared HTTP transport and source adapters
  clients/llm/             # OpenRouter adapter and provider protocol
  domain/{astronomy,neo,space_weather,earth,media}/
  services/                # search, ingestion, comparison, report, assistant
  repositories/            # SQLAlchemy query and persistence boundaries
  db/                      # engine, session, models, migration integration
  worker/                  # scheduler, claim/lease, runners
  mcp/                     # tool/resource/prompt transport adapter
~~~

The existing app/main.py, app/clients/nasa_apod.py, and app/models/apod.py are a prototype slice. Before extending it, implementation must check the APOD contract, separate the domain model from route code, inject typed settings/client lifecycle, and add integration error mapping. The prototype is not evidence of a complete integration.

## Component contracts

| Component | Input | Output | Failure contract |
|---|---|---|---|
| NASA adapter | Validated internal query and settings | Typed provider-neutral response plus response headers/metadata | Typed upstream error with source, status class, retryability; no key/URL query in message. |
| Normalizer | Typed upstream model and retrieval timestamp | Domain model plus source-record envelope | Validation issue path and source ID; rejected record is quarantined and counted. |
| Repository | Domain model and transaction/session | Persisted row or page result | Transaction rolls back; unique conflict is idempotent upsert, not duplicate. |
| Application service | Domain query/command and service dependencies | Domain result | Domain errors; no HTTP or MCP-specific exception types. |
| REST adapter | Pydantic request/response | Stable JSON API v1 | RFC 9457 problem body and request ID. |
| AI orchestrator | Question, authorized context, retrieved records | Validated answer/evidence structure | Provider or schema failure returns safe AI-unavailable/invalid-output error; browsing still works. |
| MCP adapter | Typed tool arguments and auth context | JSON object matching declared output schema | Safe protocol error with stable code; internal exception details stay in logs. |

## Lifecycle and dependency injection

FastAPI lifespan creates and closes the shared HTTPX async client, settings, database engine/session factory, repository factories, and application services. Each request receives a scoped database session; each concurrent worker task gets its own AsyncSession. The worker owns a separate process lifecycle. MCP constructs the same service graph at startup and closes clients/engine on shutdown.

## Frontend component hierarchy

AppShell → Navigation / PageHeader / GlobalStatus → FeaturePage → FilterToolbar + ResultsTable/Cards + DetailDrawer + ProvenancePanel. Charts and maps always have adjacent text summaries or data tables. A single ApiClient owns base URL, auth token attachment, request IDs, timeout/abort, and API error decoding; page components do not construct NASA URLs.

## Security considerations

The NASA URL host and endpoint path are constants. A source adapter cannot accept a user-supplied URL. AI tool selection is mapped from an explicit allowlist. Each user-data query includes the authenticated subject as a mandatory repository predicate.

## Related documents

[Backend Specification](../02-technical/BACKEND_SPECIFICATION.md), [Frontend Specification](../02-technical/FRONTEND_SPECIFICATION.md), [MCP Specification](../05-mcp/MCP_SPECIFICATION.md).
