# Architecture Diagrams

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Provide canonical system, data, database, AI, MCP, container, and deployment diagrams.  
**Scope:** Covers the proposed Architecture Diagrams behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


The detailed system and ingestion/AI diagrams are maintained in [System Architecture](SYSTEM_ARCHITECTURE.md) and [Data Flow](DATA_FLOW.md). Database entities are in [Database Schema](../02-technical/DATABASE_SCHEMA.md). Network and deployment boundaries are in [Network Architecture](../08-infrastructure/NETWORK_ARCHITECTURE.md).

## Browser request sequence

~~~mermaid
sequenceDiagram
  participant U as User browser
  participant C as Caddy
  participant A as FastAPI
  participant S as Application service
  participant R as Repository
  participant P as PostgreSQL
  U->>C: HTTPS GET /api/v1/asteroids
  C->>A: Forward same-origin API request
  A->>A: Validate schema, auth and rate budget
  A->>S: SearchAsteroids(filters)
  S->>R: parameterized query + page
  R->>P: SQL
  P-->>R: normalized records + provenance
  R-->>S: domain page
  S-->>A: API response model
  A-->>C: JSON + request ID
  C-->>U: HTTPS response
~~~

## Container relationships

~~~mermaid
flowchart TB
  subgraph Public
    User[Browser]
    Edge[80 and 443 Caddy]
  end
  subgraph AppNet[Private application network]
    Web[Static frontend]
    API[FastAPI]
    Worker[Worker]
    MCP[MCP Streamable HTTP]
    Svc[Shared application services]
  end
  subgraph DataNet[Private data network]
    PG[(PostgreSQL)]
  end
  User --> Edge
  Edge --> Web
  Edge --> API
  Edge --> MCP
  API --> Svc
  Worker --> Svc
  MCP --> Svc
  Svc --> PG
~~~

The MCP call path reuses the same service and repository layer as REST and ingestion. See the [MCP request flow](../05-mcp/MCP_SPECIFICATION.md#mcp-request-flow).

## Related documents

[System Architecture](SYSTEM_ARCHITECTURE.md), [Data Flow](DATA_FLOW.md), [Database Schema](../02-technical/DATABASE_SCHEMA.md), [Docker Architecture](../08-infrastructure/DOCKER_ARCHITECTURE.md).
