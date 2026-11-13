# NASA Image and Video Library Specification

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Official API documentation and live search reachability checked; page-specific rights require review.  
**Purpose:** Specify the intended NASA Image and Video Library Specification requirements and implementation constraints.  
**Scope:** Covers the proposed NASA Image and Video Library Specification behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## API

Base: https://images-api.nasa.gov. Method: GET. Authentication is not documented in the reviewed API guide.

| Method/route | Result |
|---|---|
| GET /search | Collection search. Requires at least one filter/search parameter. |
| GET /asset/{nasa_id} | Media asset manifest. |
| GET /metadata/{nasa_id} | Metadata location. |
| GET /captions/{nasa_id} | Caption location for video. |
| GET /album/{album_name} | Album collection. |

Search parameters documented by NASA: q, center, description, description_508, keywords, location, media_type (image/video/audio; comma-separated), nasa_id, page (starts at 1), page_size (documented default 100), photographer, secondary_creator, title, year_start, and year_end. No maximum page_size was confirmed in the official guide; the app should request 20–50 records and bound any administrator backfill.

Search JSON has a collection envelope containing items, metadata, and pagination links. Each result item has data metadata and links. Asset manifests return actual file URLs and extensions; never construct extension/file URLs by guessing. HTTP errors use standard status codes; the NASA PDF lists 400, 404, and server errors as possible.

## Storage and display

Cache title, NASA ID, media type, date, descriptive/508 text, keywords, creator/photographer, location, album, detail URL, manifest URL, and item-level copyright/credit fields when present. Do not persist image/video bytes. Load thumbnails lazily from NASA-hosted assets and link to the NASA detail page. Do not render description HTML.

NASA’s current media guidelines say NASA material is generally not copyrighted but can include third-party copyrighted material; check the record’s rights/credit and obtain third-party permission where needed. NASA logos/insignia have separate restrictions and use may not imply endorsement. Media policy and current AI/SI wording are a release gate for the assistant, as noted in NASA_INTEGRATIONS.md.

## Caching and errors

Cache search results for 1 hour and metadata/manifests for 24 hours as initial policy. No service-specific rate limit or cache validator is assumed. Retry only bounded transient errors; preserve stale metadata and safe asset source links if refresh fails.

## Related documents

[NASA Integrations](NASA_INTEGRATIONS.md), [API Provenance](API_PROVENANCE.md), [Security Specification](../06-security/SECURITY_SPECIFICATION.md).
