# Product Scope

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Separate first-release deliverables from extensions and exclusions.  
**Scope:** Covers the proposed Product Scope behavior and interfaces; current implementation status is tracked separately.  


## First public release

- Five integrations: NASA APOD Basic, NeoWs, DONKI, EONET v3, and the NASA Image and Video Library.
- Normalized records, raw-payload provenance, idempotent ingestion, date/search/filter endpoints, and historical views.
- Overview, Astronomy, Asteroids, Space Weather, Earth Events, NASA Media, AI Research Assistant, Reports, and Settings areas.
- PostgreSQL-backed per-user saved records, conversations, and reports; OIDC for account, AI, and administration routes.
- Provider-configurable OpenRouter chat-completions adapter; structured outputs are validated locally.
- PostgreSQL full-text and structured retrieval; no vector database in release 1.
- Official MCP Python SDK v2 server with read/search/compare tools and an explicitly guarded report-generation tool.
- Docker Compose local and production configurations, Caddy HTTPS edge, CI checks, health/metrics, backup and recovery instructions.

## Explicitly out of scope for release 1

- Independent orbit propagation, impact prediction, warning or alert delivery, risk scoring, or operational space-weather advice.
- Raw-media mirroring, model training on NASA content, citizen-science uploads, user-supplied URLs, or arbitrary browsing tools.
- External scientific feeds beyond the selected NASA services.
- Paid geospatial base-map service decision; Earth-event geometry is shown with a configured public/approved tile source and the source attribution supplied by that source.
- Vector embeddings, pgvector, external vector database, autonomous agents, model-directed arbitrary code or SQL, and background web search.
- Multi-region HA, multiple deployment tenants, mobile native application, and billing.

## Deferred integrations

| Candidate | Decision | Rationale / trigger |
|---|---|---|
| EPIC | Defer; optional first extension. | Official API is reachable and supplies DSCOVR EPIC daily/natural imagery metadata, but no requested product journey depends on it. Add after an Earth imagery use case and image attribution/freshness policy are specified. |
| NASA Exoplanet Archive TAP | Defer. | Official TAP supports ADQL-like queries and JSON/CSV/VOTable, but its data/table interfaces are specialized and evolve; add with a defined exoplanet product page and table/column contract. |
| NASA Earth API | Exclude. | NASA API portal reports it archived and replaced by Earthdata GIBS services. EONET v3 is the selected curated event metadata source; GIBS imagery may be added through a reviewed layer integration. |
| Mars Rover Photos API | Exclude. | NASA API portal reports this service archived. Do not build a new dependency on it. |
| NASA CNEOS Sentry/CAD | Defer as separate source. | Needed only if a reviewed feature explicitly requires impact-risk and close-approach interfaces beyond NeoWs. The product must use authoritative JPL CNEOS definitions and clearly avoid presenting Cosmos as an independent predictor. |

## Assumptions

- NASA upstream data and attribution fields remain available for the selected records.
- Users accept an account requirement for saved server-side data, AI use, reports, and administration.
- A deployment operator configures a supported OIDC issuer and a tile source before production launch.

## Change control

Any change to the release set updates this table, the NASA integration matrix, ADRs, data schema, implementation backlog, and acceptance criteria together.

## Related documents

[NASA Integrations](../03-integrations/NASA_INTEGRATIONS.md), [Tech Stack](../02-technical/TECH_STACK.md), [Implementation Plan](../10-implementation/IMPLEMENTATION_PLAN.md).
