# Testing Strategy

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 test plan  
**Purpose:** Specify the intended Testing Strategy requirements and implementation constraints.  
**Scope:** Covers the proposed Testing Strategy behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Test layers

| Layer | Scope | Tools/evidence |
|---|---|---|
| Unit | Domain calculations, normalizers, error mapping, auth policy, citation validator, rate limiter | pytest; pure deterministic fixtures; branch/failure review. |
| Upstream contract | NASA request parameters, provider payload schemas, pagination, units, error bodies | pytest + respx; sanitized approved fixtures. No live NASA dependency in default CI. |
| Database integration | Migrations, constraints, upserts, FTS ranking, owner scoping, job leases | PostgreSQL service container or Testcontainers; isolated test DB. |
| API contract | Status/schema/error/pagination/auth/OpenAPI compatibility | FastAPI test client and generated schema checks. |
| Frontend | Components, form validation, stale/error/empty states, chart summaries, auth routes | Vitest + Testing Library; mocked API. |
| E2E | Critical user journeys on Compose stack | Playwright against local services and deterministic fixture dataset. |
| MCP | Tool schemas, service calls, authorization, safe errors, resource ownership | Official SDK in-memory client plus local Streamable HTTP compatibility. |
| Security | SQL/XSS/SSRF/prompt injection/auth/cost/secret/container checks | Security test cases, scanner output, manual review. |
| AI evaluation | Retrieval recall, factuality, citation, abstention, unit preservation, prompt injection | Versioned eval set; mock suite on every PR, optional bounded live eval before release. |
| Docker/deployment | Build, non-root, health dependency, migrations, private DB, backup/restore | Compose config/build and smoke/restore evidence. |

## Failure cases

NASA unavailable, invalid key, 429, 500, timeout, invalid JSON, changed shape, missing fields, duplicate records, partial page, DB disconnected, expired lease, OpenRouter failure, malformed model output, invalid citation, malicious source text, and Caddy/API restart are required cases.

## Quality targets

Backend meaningful coverage ≥85%; all critical journeys pass E2E; 100% AI citations belong to retrieved evidence; 0 unsupported high-confidence scientific claims in reviewed release suite; no known critical/high exploitable vulnerabilities at release. Coverage does not replace contract/security/domain review.

## Related documents

[Acceptance Criteria](ACCEPTANCE_CRITERIA.md), [Performance Testing](PERFORMANCE_TESTING.md), [E2E Testing](END_TO_END_TESTING.md), [AI Evaluation](../04-ai-engineering/AI_EVALUATION.md).
