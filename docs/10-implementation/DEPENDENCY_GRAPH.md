# Dependency Graph

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 dependency baseline  
**Purpose:** Specify the intended Dependency Graph requirements and implementation constraints.  
**Scope:** Covers the proposed Dependency Graph behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



~~~mermaid
flowchart TD
  CI01[CI-01 repository alignment] --> INF01[INF-01 Compose]
  INF01 --> BE01[BE-01 settings/lifecycle]
  INF01 --> FE01[FE-01 UI shell]
  BE01 --> BE02[BE-02 errors/health]
  BE01 --> DB01[DB-01 schema/migrations]
  DB01 --> DB02[DB-02 repositories/provenance]
  BE01 --> NASA01[NASA-01 shared transport]
  NASA01 --> APOD[INT-APOD]
  NASA01 --> NEO[INT-NEO]
  NASA01 --> DONKI[INT-DONKI]
  NASA01 --> EONET[INT-EONET]
  NASA01 --> MEDIA[INT-MEDIA]
  DB01 --> WRK[WRK-01 durable worker]
  DB02 --> ING[ING-01 ingestion]
  WRK --> ING
  APOD --> ING
  NEO --> ING
  DONKI --> ING
  EONET --> ING
  MEDIA --> ING
  ING --> API[API-01 REST]
  API --> AUTH[AUTH-01 OIDC]
  API --> FE02[FE-02 explorers]
  API --> FE03[FE-03 explorers]
  AUTH --> USER[USER-01 saved data]
  DB02 --> RET[RET-01 retrieval]
  AUTH --> AI1[AI-01 provider]
  RET --> AI1
  AI1 --> AI2[AI-02 eval and policy]
  AI2 --> AI3[AI-03 assistant]
  AUTH --> MCP1[MCP-01 server]
  API --> MCP1
  MCP1 --> MCP2[MCP-02 tools]
  MCP2 --> SEC[SEC-01 hardening]
  AI3 --> QA[QA-01 full suite]
  MCP2 --> QA
  FE02 --> QA
  FE03 --> QA
  SEC --> OPS3[OPS-03 VPS release]
  QA --> OPS3
  OPS2[OPS-02 backup/restore] --> OPS3
  INF02[INF-02 Caddy/networks] --> OPS3
~~~

Parallel work is safe only where tasks have isolated adapters/contracts, separate files/ownership, and tests. A shared base model/schema change must be reviewed before parallel merges.

## Related documents

[Task Backlog](TASK_BACKLOG.md), [Implementation Plan](IMPLEMENTATION_PLAN.md).
