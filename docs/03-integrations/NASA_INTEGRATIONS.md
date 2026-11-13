# NASA Integrations

**Version:** 1.0  
**Last updated / live-check date:** 2026-11-13  
**Status:** Phase 1 specification baseline; recheck before each client implementation  
**Purpose:** Record selected services, verified status, contracts, limits, attribution, and ingestion design.  
**Scope:** Covers the proposed NASA Integrations behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Selection and status

The NASA API portal currently documents APOD’s migration and says the legacy APOD endpoint will be taken offline 2026-12-01. The replacement APOD Basic service is selected. The following request smoke checks were made 2026-11-13 from the research environment using public or DEMO_KEY access; they checked reachability and top-level field names, not scientific correctness, production quota, or full schema.

| Service | Base and principal endpoint | Auth / live result | Release decision |
|---|---|---|---|
| APOD Basic | https://science.nasa.gov/wp-json/wp/v2/apod-basic | No key worked; HTTP 200, current item fields included date, post_id, title, permalink, media_type, explanation, credit, copyright, alt, url, hdurl, basic_html, basic_html_url. | Select; use the dedicated APOD Basic guide contract. |
| NeoWs | https://api.nasa.gov/neo/rest/v1 | NASA API key; DEMO_KEY check HTTP 200, feed envelope and NEO item fields visible. | Select. |
| DONKI | https://api.nasa.gov/DONKI | NASA API key; DEMO_KEY CME date-window check HTTP 200; array items with activityID, catalog, startTime, instruments, cmeAnalyses, link, versionId among observed fields. | Select supported event services; normalize by type. |
| EONET | https://eonet.gsfc.nasa.gov/api/v3 | No key documented; HTTP 200, envelope keys title, description, link, events. | Select current stable v3; v2.1 is not updated. |
| NASA Image and Video Library | https://images-api.nasa.gov | No key documented; HTTP 200, search envelope contains collection. | Select. |
| EPIC | https://epic.gsfc.nasa.gov/api | No key required by examples; reachable official docs. | Defer until Earth imagery journey is specified. |
| Exoplanet Archive | https://exoplanetarchive.ipac.caltech.edu/TAP | TAP with sync/async query formats, no NASA API key; current official docs. | Defer until an exoplanet schema/page is specified. |

The live checks establish service reachability only. They do not establish service-level uptime, stable schemas, permission to redistribute every media item, or current quota for a registered key.

## Selected upstream contracts

| Service | Methods and routes | Filters/pagination | Response and limitations |
|---|---|---|---|
| APOD Basic | GET list; GET /{YYMMDD}; GET /{YYMMDD}/html for raw HTML | Current dedicated guide: page, per_page (capped at 25), date_from/date_to in YYMMDD. List returns APOD objects; date-coded lookup returns one. | Required normalized fields: date, post_id, title, media_type, explanation; optional credit, copyright, alt, url, hdurl, basic_html, basic_html_url. HTML and explanations are untrusted. |
| NeoWs | GET /feed; GET /neo/{asteroid_id}; GET /neo/browse | Feed start_date/end_date ISO dates; browse pagination follows returned links/page fields where present. Feed window is bounded to a short date range (NASA docs describe 7 days); confirm exact server maximum before backfill. | Feed envelope includes near_earth_objects grouped by approach date and element_count; asteroid data includes diameter estimates, close_approach_data, potentially-hazardous and sentry flags. No impact probability is implied by the hazardous boolean. |
| DONKI | GET /CME, /CMEAnalysis, /GST, /IPS, /FLR, /SEP, /MPC, /RBE, /HSS, /WSAEnlilSimulations, /notifications | Most services accept startDate/endDate; CMEAnalysis also documents mostAccurateOnly, speed, halfAngle, catalog; IPS documents location/catalog; notifications type and a maximum 30-day window. | Type-specific arrays and field sets; activityID/link/versionId where available. No common pagination contract. Keep raw fields and typed common envelope; do not coerce event types into false common measurements. |
| EONET v3 | GET /events, /events/{id}, /events/geojson, /categories[/id], /sources[/id], /layers[/id], /magnitudes[/id] | source, category, status, limit, days, inclusive start/end, magID/magMin/magMax, bbox. Status defaults to open. | JSON event envelope/events; event id/title/description/link/closed/categories/sources/geometry and optional magnitude. Geometry can be Point or Polygon; coordinates may be absent or evolving. Curated event definitions are fluid, not exhaustive. |
| NASA Media | GET /search, /asset/{nasa_id}, /metadata/{nasa_id}, /captions/{nasa_id}, /album/{album_name} | Search supports q, center, description, description_508, keywords, location, media_type, nasa_id, page, page_size (documented default 100), photographer, secondary_creator, title, year_start, year_end. At least one search parameter is required. | Search uses collection.items with metadata and links; each item has data metadata and asset links. Asset returns a manifest. Do not assume file extension, store no binaries, and retain item-specific credit/rights. |

## API key and quota policy

NASA’s API portal documents 1,000 requests/hour per registered key across api.nasa.gov APIs and DEMO_KEY at 30 requests/hour and 50/day per IP, and describes X-RateLimit-Limit / X-RateLimit-Remaining headers. Treat these as the portal’s current documented defaults, not a guarantee for each service. EONET and images-api are separate hosts and are not counted in that api.nasa.gov shared quota unless NASA documents otherwise. The user’s real developer key belongs only in a private .env or mounted secret, never in this repository, prompt fixture, screenshot, URL log, or report.

APOD portal summary mentions api_key and date/start_date/end_date/count, while NASA’s dedicated APOD Basic guide documents WordPress pagination and date-code date_from/date_to. A live request with date=2026-11-12 did not filter to that date, while date_from=261112&date_to=261112 did. Implementation must use and contract-test the dedicated guide’s parameters, and must recheck this official documentation disagreement. APOD Basic succeeded without a key in the live check; whether adding the developer key affects its quota remains an implementation-time check. Never include the real key in diagnostic output.

## Caching and ingestion policy

| Data | Initial cache/refresh proposal |
|---|---|
| APOD latest | Cache 6 hours; schedule daily refresh, and refresh on an explicit date lookup only if local record absent. Historical records cache 24 hours after first retrieval. |
| NeoWs near-term feed | Cache 15 minutes; refresh bounded upcoming window every 6 hours. Historical approaches cache 24 hours. |
| DONKI | Cache recent event windows 30 minutes; refresh recent 30-day window every 2 hours; older windows cache 24 hours. |
| EONET open events | Cache 15 minutes; refresh every 30 minutes. Closed historical events cache 24 hours and may be revalidated. |
| NASA media | Search cache 1 hour; item metadata/asset manifest cache 24 hours. Retain URLs and metadata, never mirror media files by default. |

These are application policy values, not NASA-published cache directives. Use validators only if the upstream actually supplies them; do not assume ETag/Last-Modified.

## Errors and attribution

Handle 400/401/403/404 as non-retryable except a configuration correction; 429, timeouts, connection failures, and 500/502/503/504 as bounded transient errors. Parse JSON error payloads only into sanitized internal codes. Respect Retry-After if present but do not assume it exists.

For NASA imagery/media, preserve item-level credit/copyright and check the specific item before redistribution. NASA’s media guidance says much NASA content is generally not copyrighted but third-party content may be marked and requires rights-holder permission; NASA insignia and identifiers have separate protection. The current guideline page also includes special AI/SI usage language restricting attribution of AI-generated outputs. This creates an unresolved release gate for the requested AI assistant: generated text must be labelled as Cosmos-generated, source records can be shown as retrieved evidence, and the project must obtain an explicit policy/legal review of citation wording and permitted reuse before enabling NASA-derived AI answers publicly. Do not imply NASA reviewed or endorses the product.

## Official sources reviewed

- [NASA API portal and service docs](https://api.nasa.gov/)
- [NASA APOD Basic API/feed guide](https://api.nasa.gov/assets/files/apod/APOD-APIs-and-RSS-info.pdf)
- [EONET v3 API documentation](https://eonet.gsfc.nasa.gov/docs/v3) and [EONET overview](https://eonet.gsfc.nasa.gov/)
- [NASA Image and Video Library API documentation](https://images.nasa.gov/docs/images.nasa.gov_api_docs.pdf)
- [EPIC API guide](https://epic.gsfc.nasa.gov/about/api)
- [Exoplanet Archive TAP guide](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html)
- [NASA Images and Media Usage Guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/)

## Related documents

[APOD](APOD_SPECIFICATION.md), [NeoWs](NEOWS_SPECIFICATION.md), [DONKI](DONKI_SPECIFICATION.md), [EONET](EONET_SPECIFICATION.md), [NASA Media](NASA_MEDIA_SPECIFICATION.md), [Rate Limiting](RATE_LIMITING.md), [API Provenance](API_PROVENANCE.md).
