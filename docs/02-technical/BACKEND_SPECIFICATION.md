# Backend Specification

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Define the backend layering, runtime, and implementation behavior.  
**Scope:** Covers the proposed Backend Specification behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Runtime and lifecycle

Use Python 3.12, FastAPI, Pydantic v2, pydantic-settings, HTTPX, SQLAlchemy 2 async ORM, Alembic, and psycopg 3. Exact compatible versions are selected and locked in the implementation milestone. FastAPI lifespan owns one async HTTPX client and one SQLAlchemy async engine/session factory per process. Dispose both at shutdown. Each request/job/tool invocation owns a separate AsyncSession and transaction; never share one session across concurrent tasks.

Settings are immutable at runtime and validated at startup: environment, public origin, NASA service URLs fixed by code, timeouts, DB URL, OIDC issuer/audience/JWKS, rate limits, OpenRouter key/model/limits, log level, retention, and feature flags. A production setting that weakens auth/TLS, enables demo credentials, or enables debug must fail validation.

## Layering

1. API routers validate versioned DTOs, enforce auth/limits, invoke services, and map typed errors.
2. Application services implement search, comparison, ingestion, provenance, and report workflows.
3. Domain models contain normalized units/classification semantics and no HTTP or SQLAlchemy types.
4. Adapters implement NASA/OpenRouter/MCP/database protocols.
5. Repositories use parameterized SQLAlchemy statements, bounded pagination, explicit transactions, and owner scoping.

## Logging and observability

Use JSON structured logs with UTC timestamp, level, service, environment, request/job ID, operation, source code, status class, duration, retry count, and safe error code. Never log keys, authorization headers, full URLs with query strings, prompt bodies, full user conversations, raw NASA payloads, or database credentials. Keep user identifiers hashed/pseudonymous in logs. Expose health and aggregate metrics without sensitive labels.

## Idempotent ingestion

Use unique upstream identity plus payload SHA-256. Same identity and same hash is unchanged; same identity and new hash updates raw payload/retrieval metadata and normalized fields under one transaction; new identity inserts. Do not delete history when a source omits a record on a later page. Mark a requested window complete only when all pages are fetched/validated according to its contract.

## Acceptance criteria

- Startup rejects invalid production configuration before listening.
- No route contains direct SQL or NASA normalization logic.
- Every DB operation is parameterized and paginated.
- Liveness is process-only; readiness checks database/migration compatibility without requiring NASA or OpenRouter availability.
- Database exceptions map to stable safe API errors and carry a correlation ID.

## Related documents

[API Specification](API_SPECIFICATION.md), [Data Engineering](DATA_ENGINEERING.md), [Error Handling](ERROR_HANDLING.md), [Database Schema](DATABASE_SCHEMA.md).
