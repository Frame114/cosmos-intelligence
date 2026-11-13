# Architecture Decisions

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Proposed baseline; supersedes conflicting early notes when adopted.  
**Purpose:** Specify the intended Architecture Decisions requirements and implementation constraints.  
**Scope:** Covers the proposed Architecture Decisions behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## ADR-001: Python 3.12 baseline

**Decision:** Target Python 3.12 for backend/API/worker/MCP in the first lockfile and container image.  
**Reason:** It is officially in security-fix support through October 2028, is mature across the proposed stack, and satisfies the official MCP Python SDK minimum. Pin an exact patch image and dependency lock at implementation.  
**Consequence:** Keep a quarterly runtime review and move to a newer supported runtime once the complete locked dependency set and image build pass CI. Current repo metadata still allows Python 3.11 and is not changed by this documentation phase.

## ADR-002: PostgreSQL as the sole persistence service

**Decision:** Use PostgreSQL 18 as a proposed image major, reviewed against the current supported major at implementation; use JSONB for source payloads, relational normalized rows, and built-in full-text search.  
**Reason:** Supports transactional ingestion, relational constraints, raw provenance, JSONB, and text ranking without introducing a vector service or Redis.  
**Consequence:** Keep searches grounded in exact structured filters and PostgreSQL full-text retrieval initially. Do not add embeddings until evaluations establish a measurable need.

## ADR-003: Domain services shared by API, worker, and MCP

**Decision:** Put business rules in application/domain services; REST and MCP remain adapters.  
**Reason:** Prevents tool/REST behavior drift and ensures consistent validation, authorization, and citations.

## ADR-004: Separate durable worker with PostgreSQL job leasing

**Decision:** Run a worker container that claims scheduled jobs using short transactions and a lease with SELECT FOR UPDATE SKIP LOCKED.  
**Reason:** In-process FastAPI background tasks are not a durable scheduler; avoiding Redis keeps the initial deployment simpler.  
**Consequence:** Job polling and lease expiry must be idempotent; one worker is an initial deployment assumption.

## ADR-005: Source provenance records plus normalized domain tables

**Decision:** Retain each upstream response as a hashed source record and store normalized query fields separately.  
**Reason:** Enables traceability, replay/debugging, schema evolution, and transparent AI citations.

## ADR-006: Official APOD Basic service; no dependency on legacy APOD

**Decision:** Integrate https://science.nasa.gov/wp-json/wp/v2/apod-basic. The NASA portal says the legacy APOD API is scheduled offline on 2026-12-01.  
**Reason:** This is NASA’s replacement. The dedicated APOD Basic guide and live check show WordPress-oriented page/per_page and date-code date_from/date_to; the portal’s generalized date parameter summary conflicts and must be rechecked during implementation.

## ADR-007: Single-origin browser, Caddy edge

**Decision:** Caddy terminates public HTTPS, serves the static SPA, and forwards /api/v1/* to FastAPI.  
**Reason:** Avoids unnecessary production CORS exposure and leaves TLS automation at one boundary.

## ADR-008: OIDC for protected features

**Decision:** Validate JWT issuer, audience, expiry, signature via cached JWKS, subject, and role/scope. Use OIDC Authorization Code with PKCE in the browser.  
**Reason:** Avoids storing local passwords and enables provider choice.  
**Open decision:** The production OIDC issuer and role mapping are set by the deployment owner. In production, unset identity config disables protected endpoints rather than enabling bypass.

## ADR-009: MCP over Streamable HTTP remotely

**Decision:** Use official Python MCP SDK v2 after compatibility review, Streamable HTTP for the deployed service, and stdio only for local desktop-host integrations.  
**Reason:** Current official SDK docs identify v2 as stable and Streamable HTTP as the deployment transport; legacy SSE is not selected.

## ADR-010: No autonomous impact prediction

**Decision:** Present upstream NeoWs classifications and measurements with source meanings/units; do not infer impact probability or independent risk.  
**Reason:** Product integrity and scientific safety.

## Deferred decisions

- Map tile provider and terms, to be chosen before production launch.
- Final OpenRouter model ID, chosen from current provider capability metadata at deployment; never make it an application-level scientific assumption.
- Retention period adjustments, informed by storage estimates and privacy review before first public release.
- Whether read-only public routes are served without a user account; current design requires authentication only for saving, AI, reports, and administration.

## Related documents

[DECISIONS.md](../../DECISIONS.md), [Tech Stack](../02-technical/TECH_STACK.md), [Authentication](../06-security/AUTHENTICATION.md).
