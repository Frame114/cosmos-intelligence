# NASA API Integration Notes

**Research checkpoint:** 2026-11-13  
**Implementation status:** Research required; no API client implemented yet.

## Current APOD migration

NASA's API portal documents a replacement APOD endpoint:

`https://science.nasa.gov/wp-json/wp/v2/apod-basic`

NASA has announced retirement of the legacy APOD API endpoint on **2026-12-01**. New development should not depend on the retiring legacy endpoint.

The portal lists query parameters including `date`, `start_date`, `end_date`, `count` (up to 25) and `api_key`. Parameter combinations have constraints. Verify the current official documentation and inspect an actual response before defining application models.

Official references:
- [NASA API portal](https://api.nasa.gov/)
- [Replacement APOD endpoint](https://science.nasa.gov/wp-json/wp/v2/apod-basic)

## Candidate integrations

| Service | Purpose | Verification required |
|---|---|---|
| APOD | Astronomy picture and explanation | Replacement endpoint, response shape, date parameters and key behaviour |
| NeoWs | Near-Earth object data | Current endpoints, date-window constraints, pagination and rate limits |
| DONKI | Space-weather event data | Endpoint-specific schemas, filters and event identifiers |
| EONET | Curated natural-event metadata | Supported API version, category and geometry semantics |
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