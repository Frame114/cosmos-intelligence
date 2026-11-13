# NASA API Integration Notes (legacy research summary)

| Field | Value |
|---|---|
| Version | 1.0 |
| Last updated | 2026-11-13 |
| Status | Legacy research summary; current service specifications are authoritative. |
| Purpose | Preserve initial NASA API notes while directing readers to current service specifications. |
| Scope | APOD migration and initial NASA service notes; see current integration specifications for implementation contracts. |
| Assumptions | This research snapshot can become stale; refresh mutable upstream contracts before implementation. |

The current integration source of truth is [NASA Integrations](../03-integrations/NASA_INTEGRATIONS.md) and its service-specific specifications. Refresh all upstream contracts before implementing a connector.

## Current APOD migration

NASA's API portal documents a replacement APOD endpoint:

`https://science.nasa.gov/wp-json/wp/v2/apod-basic`

NASA has announced retirement of the legacy APOD API endpoint on **2026-12-01**. New development should not depend on the retiring legacy endpoint.

The dedicated [APOD API guide](https://api.nasa.gov/assets/files/apod/APOD-APIs-and-RSS-info.pdf) describes `page`, `per_page` (up to 25), and `date_from`/`date_to` parameters. The portal summary also mentions `date`, `start_date`, `end_date`, `count`, and `api_key`. A limited live check found that `date_from`/`date_to` selected a date while `date=` returned the latest entry in the observed request. Treat the parameter discrepancy and key/quota behavior as unresolved; verify the dedicated contract again before implementation.

Official references:
- [NASA API portal](https://api.nasa.gov/)
- [Replacement APOD endpoint](https://science.nasa.gov/wp-json/wp/v2/apod-basic)

## Candidate integrations

| Service | Purpose | Verification required |
|---|---|---|
| APOD Basic | Astronomy picture and explanation | Recheck replacement response, date parameters, key behavior, and quota; see the APOD-specific specification |
| NeoWs | Near-Earth object data | Current endpoints, date-window constraints, pagination and rate limits |
| DONKI | Space-weather event data | Endpoint-specific schemas, filters and event identifiers |
| EONET v3 | Curated natural-event metadata | Current stable version, category and geometry semantics |
| NASA Image and Video Library | Search and retrieve media metadata/assets | Search parameters, pagination and asset links |

## Integration verification checklist

For every service, record:
1. Official documentation URL and date checked.
2. Base URL and exact endpoint.
3. Authentication and key requirements.
4. Query/path parameters, types, defaults and constraints.
5. A redacted real response example and observed schema.
6. Pagination and rate-limit behaviour.
7. Error response examples and retry guidance.
8. Attribution, licensing and usage restrictions.
9. Contract tests and fixture provenance.

## Rate limiting and resilience

NASA API services may apply shared or service-specific request limits. Do not hard-code a rate limit based on an old tutorial. Inspect current portal guidance and response headers such as `X-RateLimit-Limit` and `X-RateLimit-Remaining` where supplied.

Use bounded timeouts and retries only for transient failures. Avoid retrying non-idempotent operations or permanent client errors. Respect `Retry-After` when provided.

## Important implementation rule

Do not create a Pydantic model from a guessed payload. First capture and inspect the live response, then write the model and fixtures to match the verified contract.

NASA's current AI/SI wording also requires policy review before generated content based on NASA-derived material is enabled. See [API provenance](../03-integrations/API_PROVENANCE.md).
