# System Architecture

**Version:** 1.0<br>
**Last updated:** 2026-11-14<br>
**Status:** Target architecture; local API/database/worker/frontend slice is testable; MCP is locally implemented; production controls remain incomplete<br>
**Purpose:** Define runtime boundaries and the dependency direction for implementation.  
**Scope:** Covers the proposed System Architecture behavior and interfaces; current implementation status is tracked separately.  


## Design

The system is a modular Python application with distinct API, worker, and MCP processes. All processes compose the same application services and repositories. The browser receives a built React SPA and uses the versioned FastAPI API. PostgreSQL is the authoritative local store for normalized records, provenance, jobs, and authenticated user data. NASA services are read-only upstream sources. OpenRouter is optional and called only by the AI provider adapter.

The current local Compose stack implements PostgreSQL, Alembic migrations, the API, a separate ingestion worker, a static React frontend, and Caddy routing. The worker consumes bounded APOD, NeoWs, DONKI, and EONET jobs with PostgreSQL leases. Deterministic daily schedules exist but are disabled by default. Owner-scoped account/workspace APIs and admin job summaries exist; browser PKCE sign-in, provider-backed AI, production OIDC, NASA Media job inputs, and production deployment controls remain unimplemented. Do not interpret the target diagram as deployed infrastructure.

~~~mermaid
flowchart LR
  Browser[Browser: React + TypeScript]
  Caddy[Caddy: HTTPS edge]
  API[FastAPI API]
  Worker[Ingestion worker]
  MCP[MCP service: official Python SDK]
  Services[Domain and application services]
  DB[(PostgreSQL)]
  NASA[NASA APIs: APOD, NeoWs, DONKI, EONET, Media]
  OR[OpenRouter]
  Browser -->|HTTPS| Caddy
  Caddy -->|/api/v1| API
  Caddy -->|static assets| Browser
  API --> Services
  Worker --> Services
  MCP --> Services
  Services --> DB
  Worker --> NASA
  API --> NASA
  Services --> OR
~~~

## Boundaries and rules

| Boundary | Owns | Must not own |
|---|---|---|
| Presentation | Navigation, filters, state, charts/maps, accessible status, user-initiated queries. | NASA keys, provider secrets, scientific normalization, authorization decisions. |
| FastAPI adapters | Versioned HTTP schemas, auth dependency, validation, pagination, error mapping. | SQL/domain logic, upstream parsing, model prompts embedded in route handlers. |
| Application services | Search, compare, ingestion orchestration, report workflow, shared business rules. | Protocol-specific serialization and transport startup. |
| NASA adapters | URL allowlist, query construction, timeout/retry, upstream parsing into typed input models, rate-limit observation. | Domain persistence and user authorization. |
| Repositories | SQLAlchemy persistence/query implementation and transaction boundary. | Upstream HTTP or model calls. |
| AI adapter | Provider request/response, token/cost metadata, capability checks. | Executing tools itself or asserting output is true. |
| MCP adapters | SDK tool/resource/prompt schema and auth context. | Duplicated business logic or direct raw SQL. |
| Worker | Durable job claim/lease, schedule, retry state, ingestion invocation. | Serving public HTTP or keeping source truth only in memory. |
| PostgreSQL | Durable source records, normalized domain data, app metadata. | Public network exposure. |

## Data ownership

Upstream records are preserved as provenance-bearing raw JSON and separately mapped into queryable domain tables. User-authored conversations and AI reports are application data; they are labelled as generated, retain prompt/model/evidence references, and can be deleted. Derived aggregates are recomputable and never replace source records.

## Deployment constraints

- Caddy is the only production service publishing host ports: TCP 80 and 443; optional UDP 443 only when HTTP/3 is deliberately enabled.
- API, worker, MCP, and database ports are container-private. MCP uses Streamable HTTP behind Caddy and requires authentication for non-read-only/high-cost tools.
- Database uses a named persistent volume, readiness health checks, backup/restore procedures, and migration-before-new-app startup.
- API and worker may call public NASA services over outbound HTTPS; all inbound data is untrusted.
- The browser must not call authenticated NASA/OpenRouter endpoints directly.

## Failure domains

NASA or OpenRouter failure must not prevent previously stored records from being searched or the dashboard from loading. Worker failure delays freshness but leaves persisted history available. PostgreSQL unavailability causes readiness failure and database-backed endpoints to return safe service errors. MCP may be unavailable independently of REST.

## Assumptions

- The first production installation is one Ubuntu 24.04 VPS, one application deployment, and one PostgreSQL primary.
- No high-availability or horizontal multi-replica guarantee is made in release 1.
- The current stable official MCP SDK major is rechecked at dependency lock time.

## Acceptance criteria

1. API and MCP share application service functions.
2. A database-down state fails readiness but liveness remains responsive.
3. External service failure preserves stored science data and is visible as stale/degraded.
4. No public network path reaches PostgreSQL or an unprotected MCP listener.

## Related documents

[Component Design](COMPONENT_DESIGN.md), [Data Flow](DATA_FLOW.md), [Integration Architecture](INTEGRATION_ARCHITECTURE.md), [Docker Architecture](../08-infrastructure/DOCKER_ARCHITECTURE.md), [Threat Model](../06-security/THREAT_MODEL.md).
