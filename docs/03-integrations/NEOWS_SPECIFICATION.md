# NeoWs Specification

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Verified against NASA portal and a live DEMO_KEY request; recheck before implementation.  
**Purpose:** Specify the intended NeoWs Specification requirements and implementation constraints.  
**Scope:** Covers the proposed NeoWs Specification behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Endpoints

Base: https://api.nasa.gov/neo/rest/v1. Auth uses NASA api_key query parameter, default DEMO_KEY by the portal; the real key is supplied from secret configuration and redacted from logs.

| Method/route | Purpose | Parameters |
|---|---|---|
| GET /feed | NEOs by close approach date | start_date required for bounded query; end_date optional, documented default seven days after start_date; key. Keep feed windows within documented seven-day scope; validate server maximum before backfill. |
| GET /neo/{asteroid_id} | One object by NASA JPL small-body SPK-ID | integer asteroid_id path and key. |
| GET /neo/browse | Browse dataset | key and returned pagination metadata/links where provided. |

NASA portal documents close-approach feed, lookup, and browse. Live DEMO_KEY feed returned HTTP 200 with near_earth_objects grouped by date, element_count, and asteroid objects. Observed object fields include id, neo_reference_id, name, absolute_magnitude_h, estimated_diameter, is_potentially_hazardous_asteroid, is_sentry_object, close_approach_data, nasa_jpl_url, and links.

## Normalized semantics

Diameter is an estimate interval in kilometers; preserve minimum and maximum. Relative velocity data may provide km/s and other unit variants; persist the original plus one canonical km/s value after explicit conversion. Miss distance can arrive in several units; preserve source values and use kilometers for the default display. Each approach retains its source date, orbiting body, and available epoch.

Keep NASA’s potentially hazardous classification as an upstream boolean and label it as such. It is not a probability that the object will hit Earth. Sentry classification is a separate upstream flag. Cosmos does not perform orbit propagation, impact-risk scoring, or independent predictions.

## Retrieval, cache, errors

Use 15-minute freshness for upcoming feed and 24-hour freshness for historical object/approach data. Upsert by NeoWs identifier and stable approach identity. Feed date windows are split if required by documented server constraints. NASA api.nasa.gov key quota is shared with other APIs at the documented portal level; observe quota headers and pace backfills.

HTTP 429/transient server/timeout retries are bounded; bad dates and invalid IDs are not retried. Preserve stale persisted object/approach data when refresh fails.

## Related documents

[NASA Integrations](NASA_INTEGRATIONS.md), [Database Schema](../02-technical/DATABASE_SCHEMA.md), [API Provenance](API_PROVENANCE.md).
