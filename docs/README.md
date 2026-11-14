# Documentation index

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Engineering blueprint with a locally implemented application; status evidence is tracked separately.
**Purpose:** Navigate the Cosmos Intelligence engineering documentation and current implementation evidence.
**Scope:** Product and architecture design, implementation contracts, operations guides, and living project records.
**Assumptions:** Detailed specifications include planned target-state requirements. Consult the project status and implementation progress records to distinguish plans, local implementation, verified behavior, and production deployment.


This index is the entry point for the Cosmos Intelligence engineering documentation. The repository contains both a broad target-state blueprint and a working local development application. The living status records identify which components have implementation and verification evidence; documentation of a target does not by itself mean that target is implemented or deployed.

## Recommended reading order

1. [Project vision](00-project/PROJECT_VISION.md), [product requirements](00-project/PRD.md), and [scope](00-project/PRODUCT_SCOPE.md)
2. [System architecture](01-architecture/SYSTEM_ARCHITECTURE.md), [architecture diagrams](01-architecture/ARCHITECTURE_DIAGRAMS.md), and [decisions](01-architecture/ARCHITECTURE_DECISIONS.md)
3. [Technical stack](02-technical/TECH_STACK.md) and [API specification](02-technical/API_SPECIFICATION.md)
4. [NASA integration overview](03-integrations/NASA_INTEGRATIONS.md) and each service contract
5. [Security specification](06-security/SECURITY_SPECIFICATION.md), then AI and MCP design before implementing those features
6. [Implementation plan](10-implementation/IMPLEMENTATION_PLAN.md), [task backlog](10-implementation/TASK_BACKLOG.md), and [Codex implementation instructions](10-implementation/CODEX_IMPLEMENTATION_INSTRUCTIONS.md)
7. [Local development](11-operations/LOCAL_DEVELOPMENT.md), deployment runbook, and release checklist when the corresponding components exist

## Project and product

- [Project vision](00-project/PROJECT_VISION.md)
- [Product requirements document](00-project/PRD.md)
- [Product scope](00-project/PRODUCT_SCOPE.md)
- [User personas](00-project/USER_PERSONAS.md)
- [Success metrics](00-project/SUCCESS_METRICS.md)

## Architecture

- [System architecture](01-architecture/SYSTEM_ARCHITECTURE.md)
- [Architecture decisions](01-architecture/ARCHITECTURE_DECISIONS.md)
- [Component design](01-architecture/COMPONENT_DESIGN.md)
- [Data flow](01-architecture/DATA_FLOW.md)
- [Integration architecture](01-architecture/INTEGRATION_ARCHITECTURE.md)
- [Architecture diagrams](01-architecture/ARCHITECTURE_DIAGRAMS.md)
- [Existing architecture overview](architecture/overview.md)

## Technical specifications

- [Technology stack](02-technical/TECH_STACK.md)
- [Backend specification](02-technical/BACKEND_SPECIFICATION.md)
- [Frontend specification](02-technical/FRONTEND_SPECIFICATION.md)
- [Application API specification](02-technical/API_SPECIFICATION.md)
- [Database schema](02-technical/DATABASE_SCHEMA.md)
- [Data engineering](02-technical/DATA_ENGINEERING.md)
- [Error handling](02-technical/ERROR_HANDLING.md)

## NASA integrations

- [Integration portfolio and selection](03-integrations/NASA_INTEGRATIONS.md)
- [APOD](03-integrations/APOD_SPECIFICATION.md)
- [Near-Earth Object Web Service](03-integrations/NEOWS_SPECIFICATION.md)
- [DONKI space weather](03-integrations/DONKI_SPECIFICATION.md)
- [EONET natural events](03-integrations/EONET_SPECIFICATION.md)
- [NASA Image and Video Library](03-integrations/NASA_MEDIA_SPECIFICATION.md)
- [Rate limiting and resilience](03-integrations/RATE_LIMITING.md)
- [Data provenance and attribution](03-integrations/API_PROVENANCE.md)
- [Earlier NASA API research notes](integrations/nasa-api-notes.md)

## AI engineering

- [AI architecture](04-ai-engineering/AI_ARCHITECTURE.md)
- [LLM provider design](04-ai-engineering/LLM_PROVIDER_DESIGN.md)
- [Prompt architecture](04-ai-engineering/PROMPT_ARCHITECTURE.md)
- [Context engineering](04-ai-engineering/CONTEXT_ENGINEERING.md)
- [Retrieval architecture](04-ai-engineering/RETRIEVAL_ARCHITECTURE.md)
- [AI evaluation](04-ai-engineering/AI_EVALUATION.md)
- [AI guardrails](04-ai-engineering/AI_GUARDRAILS.md)

## Model Context Protocol

- [MCP specification](05-mcp/MCP_SPECIFICATION.md)
- [MCP tools](05-mcp/MCP_TOOLS.md)
- [MCP resources](05-mcp/MCP_RESOURCES.md)
- [MCP security](05-mcp/MCP_SECURITY.md)

## Security

- [Security specification](06-security/SECURITY_SPECIFICATION.md)
- [Threat model](06-security/THREAT_MODEL.md)
- [Secrets management](06-security/SECRETS_MANAGEMENT.md)
- [Authentication and authorization](06-security/AUTHENTICATION.md)
- [Security testing](06-security/SECURITY_TESTING.md)

## UX and design

- [UX specification](07-ux-design/UX_SPECIFICATION.md)
- [Design system](07-ux-design/DESIGN_SYSTEM.md)
- [User journeys](07-ux-design/USER_JOURNEYS.md)
- [Wireframes](07-ux-design/WIREFRAMES.md)
- [Accessibility](07-ux-design/ACCESSIBILITY.md)

## Infrastructure and operations design

- [Docker architecture](08-infrastructure/DOCKER_ARCHITECTURE.md)
- [Docker Compose specification](08-infrastructure/DOCKER_COMPOSE_SPECIFICATION.md)
- [Network architecture](08-infrastructure/NETWORK_ARCHITECTURE.md)
- [Environment configuration](08-infrastructure/ENVIRONMENT_CONFIGURATION.md)
- [VPS deployment design](08-infrastructure/VPS_DEPLOYMENT.md)
- [CI/CD specification](08-infrastructure/CI_CD_SPECIFICATION.md)
- [Monitoring](08-infrastructure/MONITORING.md)
- [Backup and recovery](08-infrastructure/BACKUP_AND_RECOVERY.md)
- [Local development guide](11-operations/LOCAL_DEVELOPMENT.md)
- [Deployment runbook](11-operations/DEPLOYMENT_RUNBOOK.md)
- [Troubleshooting](11-operations/TROUBLESHOOTING.md)
- [Maintenance](11-operations/MAINTENANCE.md)

## Quality and delivery

- [Testing strategy](09-quality-assurance/TESTING_STRATEGY.md)
- [Acceptance criteria](09-quality-assurance/ACCEPTANCE_CRITERIA.md)
- [Performance testing](09-quality-assurance/PERFORMANCE_TESTING.md)
- [End-to-end testing](09-quality-assurance/END_TO_END_TESTING.md)
- [Release checklist](09-quality-assurance/RELEASE_CHECKLIST.md)
- [Definition of done](../DEFINITION_OF_DONE.md)

## Implementation planning

- [Implementation plan](10-implementation/IMPLEMENTATION_PLAN.md)
- [Phase breakdown](10-implementation/PHASE_BREAKDOWN.md)
- [Task backlog](10-implementation/TASK_BACKLOG.md)
- [Dependency graph](10-implementation/DEPENDENCY_GRAPH.md)
- [Codex implementation instructions](10-implementation/CODEX_IMPLEMENTATION_INSTRUCTIONS.md)

### Pseudocode references

- [NASA API clients](10-implementation/PSEUDOCODE/API_CLIENTS.md)
- [Data ingestion](10-implementation/PSEUDOCODE/DATA_INGESTION.md)
- [Database services](10-implementation/PSEUDOCODE/DATABASE_SERVICES.md)
- [AI assistant](10-implementation/PSEUDOCODE/AI_ASSISTANT.md)
- [MCP server](10-implementation/PSEUDOCODE/MCP_SERVER.md)
- [Frontend flows](10-implementation/PSEUDOCODE/FRONTEND_FLOWS.md)

## Living project records

- [Root README](../README.md)
- [Project status](../PROJECT_STATUS.md)
- [Roadmap](../ROADMAP.md)
- [Architecture decisions](../DECISIONS.md)
- [Technical debt](../TECHNICAL_DEBT.md)
- [Engineering assessment](../ASSESSMENT.md)
- [Changelog](../CHANGELOG.md)

## Research freshness

NASA service behavior and platform documentation can change. Integration specifications include source links and a research checkpoint; recheck primary documentation and live, non-secret response samples before implementing or releasing each connector. Treat unresolved policy and contract questions listed in those specifications as gates.
