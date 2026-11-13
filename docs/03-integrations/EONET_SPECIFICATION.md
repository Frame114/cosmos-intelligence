# EONET v3 Specification

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Current stable version verified; live events envelope reachable.  
**Purpose:** Specify the intended EONET v3 Specification requirements and implementation constraints.  
**Scope:** Covers the proposed EONET v3 Specification behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## API and endpoints

Base: https://eonet.gsfc.nasa.gov/api/v3. Method: GET. Current official docs identify v3 as latest/stable; v2.1 remains available but is deprecated/not updated.

| Endpoint | Purpose |
|---|---|
| /events | Event list. |
| /events/{id} | One event. |
| /events/geojson | GeoJSON representation. |
| /categories and /categories/{id} | Category catalog/filter. |
| /sources and /sources/{id} | Source catalog/filter. |
| /layers and /layers/{id} | Related map imagery layers. |
| /magnitudes and /magnitudes/{id} | Magnitude definitions. |

Official query parameters include source, category, status (open/closed/all where supported; events default to open), limit, days, inclusive start/end dates, magID/magMin/magMax, and bbox. Multiple source/category values are comma-separated OR filters. Bbox order is min longitude, max latitude, max longitude, min latitude (upper-left then lower-right coordinates); validate bounds and test ordering before implementation. See the [official EONET v3 parameter documentation](https://eonet.gsfc.nasa.gov/docs/v3).

## Record shape and semantics

Event fields include id, title, optional description, link, closed, categories, sources, and geometry. Geometry pairs a timestamp with GeoJSON Point or Polygon; dates may default to 00:00Z where source time is missing. Event geometry can evolve over time. Preserve all geometry records; map views may simplify only for display and must retain source geometry for detail.

EONET is curated metadata with fluid definitions. A category label or closed timestamp does not prove a complete census or the exact natural event end. Earthquakes are shown only if a current EONET category/source supplies them; do not imply they are universally covered.

## Ingestion and cache

No authentication or rate limit was published in the reviewed EONET v3 guide; implement conservative concurrency and a configurable per-host budget. Refresh open events every 30 minutes and cache closed history for 24 hours as application policy. Upsert by EONET event ID, preserving updated geometry observations and source references.

## Related documents

[NASA Integrations](NASA_INTEGRATIONS.md), [UX Specification](../07-ux-design/UX_SPECIFICATION.md), [API Provenance](API_PROVENANCE.md).
