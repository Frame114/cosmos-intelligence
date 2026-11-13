# Implementation Plan

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline; implementation not started  
**Purpose:** Specify the intended Implementation Plan requirements and implementation constraints.  
**Scope:** Covers the proposed Implementation Plan behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Delivery order

1. Repository/architecture foundation and source-of-truth review.
2. Docker and reproducible local services.
3. Backend settings, lifecycle, logging, health, and typed errors.
4. Database schema, migrations, repositories, and job lease.
5. Shared NASA client and APOD Basic contract.
6. NeoWs, DONKI, EONET v3, and NASA Media adapters.
7. Normalizers, ingestion worker, provenance, and replay.
8. Versioned internal API and authentication.
9. React/Vite foundation and accessible design system.
10. Domain explorers and charts/map.
11. PostgreSQL retrieval and saved records/reports.
12. Provider abstraction and AI evaluation; keep public generation feature-flagged off until NASA policy approval.
13. Official MCP SDK server and tools/resources/prompts.
14. Security hardening, full tests, observability, backup/restore.
15. Ubuntu VPS deployment and portfolio release.

## Milestone gates

| Milestone | Exit criteria |
|---|---|
| M0 Specification handoff | Docs index/source-of-truth rules, open questions and risks reviewed. |
| M1 Docker/repo | Clean checkout starts core services via Docker Compose; non-root and health/network checks pass. |
| M2 Backend/data | Migration, repository, job, and error contracts are tested against PostgreSQL. |
| M3 NASA integration | Each selected service has current docs review, sanitized fixture, failure tests, normalization, and provenance. |
| M4 Product/API | API OpenAPI and critical domain journeys pass contract tests. |
| M5 Frontend | Accessible layouts/states and explorer journeys pass component/E2E tests. |
| M6 AI/MCP | AI evaluation thresholds, policy gate, citation checks, MCP schemas/auth and service reuse pass. |
| M7 Release | Security, backup restore, performance, deployment smoke, docs, and release checklist complete. |

## Parallel work

Safe after M0: separate NASA adapter investigations for NeoWs, DONKI, EONET, and Media; UX/design tokens alongside backend foundation; test fixture catalog and security threat test planning. Sequential: Docker before full-stack execution; migrations before persistence; APOD pattern before shared adapter generalization; domain services/API before frontend integrations; retrieval/evals before enabling AI; auth/tool policies before MCP exposure; successful backup/restore before production deployment.

## Risks and blockers

Public NASA-derived AI generation has a policy/attribution review gate. Map tile provider terms and production OIDC issuer remain decisions before public launch. APOD source docs conflict on date parameter names. These are tracked in the task backlog and must not be silently bypassed.

## Related documents

[Phase Breakdown](PHASE_BREAKDOWN.md), [Task Backlog](TASK_BACKLOG.md), [Dependency Graph](DEPENDENCY_GRAPH.md), [Codex Instructions](CODEX_IMPLEMENTATION_INSTRUCTIONS.md).
