# Internal REST API Specification

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Define the stable REST contract; OpenAPI generated from implementation is the machine-readable source.  
**Scope:** Covers the proposed Internal REST API Specification behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Conventions

- Prefix all product routes with /api/v1. Keep /health/live and /health/ready outside the versioned product API. Preserve current GET /health as a temporary compatibility alias until the first release.
- JSON UTF-8; UTC timestamps in ISO 8601; dates as YYYY-MM-DD; scientific numeric units are included in schema or named fields.
- Read queries use GET. Mutations use POST/PATCH/DELETE and require OIDC authorization.
- Search page size defaults to 20, hard maximum 100. Sort fields are enumerated per resource. Invalid filters return 422.
- List envelope: items, page, page_size, total, retrieved_at/freshness as applicable. Never return unvalidated raw NASA JSON as a product contract.
- OpenAPI is emitted at /api/v1/openapi.json; production Swagger UI may be disabled by configuration.

## Endpoint catalog

| Method and path | Auth | Purpose / query |
|---|---|---|
| GET /api/v1/astronomy/apod | Public read | date or start_date/end_date, page, page_size. |
| GET /api/v1/astronomy/apod/{date} | Public read | Canonical APOD by ISO date. |
| GET /api/v1/astronomy/records | Public read | q, source, date range, page/page_size. |
| GET /api/v1/asteroids | Public read | q, close_approach_start/end, hazardous, min/max diameter, sort, page/page_size. |
| GET /api/v1/asteroids/{neo_id} | Public read | NEO details and approach records. |
| POST /api/v1/asteroids/compare | Authenticated | 2–10 known NEO identifiers; returns aligned fields and explicit missing values. |
| GET /api/v1/space-weather/events | Public read | type, start_date, end_date, page/page_size. |
| GET /api/v1/space-weather/summary | Public read | start_date, end_date, grouped counts and source metadata. |
| GET /api/v1/earth-events | Public read | category, status, start/end, bbox, page/page_size. |
| GET /api/v1/earth-events/{event_id} | Public read | Event detail and available geometry/source references. |
| GET /api/v1/media | Public read | q, media_type, year_start/end, page/page_size. |
| GET /api/v1/media/{nasa_id} | Public read | Stored media metadata and source asset links. |
| POST /api/v1/research/conversations | Authenticated | Create conversation and first question; rate-limited. |
| POST /api/v1/research/conversations/{id}/messages | Owner | Submit one question and receive validated answer/evidence. |
| GET /api/v1/research/conversations/{id} | Owner | Read conversation. |
| DELETE /api/v1/research/conversations/{id} | Owner | Delete conversation and dependent generated content. |
| POST /api/v1/reports | Authenticated | Generate structured report from query/evidence; rate/cost limited. |
| GET /api/v1/reports | Owner | List reports, paginated. |
| GET /api/v1/reports/{id} | Owner | Read report with evidence snapshot. |
| DELETE /api/v1/reports/{id} | Owner | Delete report. |
| POST /api/v1/saved-records | Authenticated | Save source/domain record reference. |
| GET /api/v1/saved-records | Owner | List saved records. |
| DELETE /api/v1/saved-records/{id} | Owner | Remove saved reference. |
| GET /api/v1/admin/sources | Admin role | Source health, last successful retrieval, safe quota headers. |
| GET /api/v1/admin/jobs | Admin role | Filterable ingestion job summaries. |
| POST /api/v1/admin/jobs/{id}/retry | Admin role | Retry an eligible failed job. |

## Example response

~~~json
{
  "items": [
    {
      "id": "neo-3542519",
      "name": "Example object",
      "potentially_hazardous": false,
      "estimated_diameter_km": {"min": 0.12, "max": 0.27},
      "close_approaches": [
        {
          "date": "2026-11-13",
          "relative_velocity_km_s": 8.3,
          "miss_distance_km": 12000000,
          "orbiting_body": "Earth"
        }
      ],
      "provenance": {
        "source": "NEOWS",
        "upstream_id": "3542519",
        "retrieved_at": "2026-11-13T10:00:00Z",
        "source_url": "https://api.nasa.gov/neo/rest/v1/neo/3542519"
      }
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1,
  "freshness": "current"
}
~~~

## Errors

Use RFC 9457 problem details with application/problem+json. Required members: type, title, status, detail (safe and concise), instance, code, request_id; optional retryable and upstream. Do not return stack traces, SQL, raw upstream errors, API keys, provider responses, or other-user existence details. Rate-limited responses include Retry-After when known.

## Authorization and rate limits

Public reads are unauthenticated but bounded per client IP. Saves, conversation/report operations, and model-backed features require a valid OIDC subject. Administration requires cosmos_admin role/scope. Repository owner scope is mandatory for user content. Initial single-instance limits are token-bucket or fixed-window: public reads 120/minute/IP, AI calls 5/minute/subject and 30/day/subject, report generation 3/hour/subject; configuration and burst are visible to administrators. In-memory limiter is acceptable only for one API instance; shared infrastructure is a scale-out prerequisite.

## Example request/response errors

Invalid query dates return 422 and field paths. Unknown public record returns 404. NASA timeout returns 504; quota or service failure returns 503 or 502 with source code and retryable state. OIDC failures return 401/403 without provider details.

## Related documents

[Backend Specification](BACKEND_SPECIFICATION.md), [Error Handling](ERROR_HANDLING.md), [Authentication](../06-security/AUTHENTICATION.md), [NASA Integrations](../03-integrations/NASA_INTEGRATIONS.md).
