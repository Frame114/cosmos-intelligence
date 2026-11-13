# Frontend Specification

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Define SPA structure, API behavior, and visual states.  
**Scope:** Covers the proposed Frontend Specification behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Foundation

Use React, strict TypeScript, Vite, Tailwind CSS 4, Recharts, Lucide React, and Leaflet/React Leaflet. Lock Node and npm/pnpm versions in repository files and use the same major in the frontend image and CI. Build static assets in a Node build stage; serve them through a non-root static server or Caddy stage.

## Navigation and pages

| Route | Main content | API integration |
|---|---|---|
| /overview | Source status, APOD feature, asteroid close approaches, recent space-weather and Earth events | overview endpoints; source freshness |
| /astronomy | APOD date picker, media viewer, explanation, archive filters, save control | APOD search/detail |
| /asteroids | Search/filter table, diameter and approach charts, compare tray, detail panel | NEO search/detail/compare |
| /space-weather | Event-type chips, date range, timeline, event cards/detail | DONKI search/summary |
| /earth-events | Category/date/status filters, map and event list linked by selection | EONET search/detail |
| /media | Text/media type/year filters, responsive result grid, metadata and asset panel | NASA media search/asset |
| /assistant | Question, evidence cards, answer sections, citations, uncertainty marker | assistant conversations |
| /reports | Saved report list, detail, citation links, delete/export | report CRUD |
| /settings | Profile, accessibility, source disclosure, retention/delete controls | identity/user settings |

## State model

Every data panel supports initial loading, background refresh, empty result, stale-data banner, request error with retry, and partial-data state. Preserve old successful data during a refresh failure with an explicit stale marker. Abort superseded search requests. Debounce text search by 250–400 ms; do not issue an API request on each keystroke.

## API client

One typed client targets same-origin /api/v1, sends OIDC access token only for protected routes, attaches a client-generated request ID, decodes RFC 9457 problem responses, and supports AbortSignal. No NASA API key, OpenRouter key, or arbitrary upstream URL is included in the frontend bundle. API response models are generated or checked from OpenAPI in CI.

## Data display

- Use labels and unit strings from the domain schema; never infer an absent unit.
- Show source and retrieval time in the record detail and near chart/map context.
- Chart includes a summary table or accessible data description; units, time zone, and missing values are explicit.
- External links open safely with noreferrer; image alt text uses upstream alt if present, otherwise the UI marks it as unavailable rather than generating a factual description.
- NASA third-party credits and media-use notices stay adjacent to media.

## Security

Render text as text. Do not use raw HTML from APOD Basic or NASA media descriptions. If an APOD video/iframe is embedded, sanitize using a fixed allowlist and CSP; otherwise link to NASA. No sensitive state is written to localStorage; short-lived auth handling follows the selected OIDC client’s security guidance. User saves are server-side and owner-scoped.

## Related documents

[UX Specification](../07-ux-design/UX_SPECIFICATION.md), [Design System](../07-ux-design/DESIGN_SYSTEM.md), [Accessibility](../07-ux-design/ACCESSIBILITY.md), [API Specification](API_SPECIFICATION.md).
