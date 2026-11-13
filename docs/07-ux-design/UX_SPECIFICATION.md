# UX Specification

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 design baseline  
**Purpose:** Define the scientific dashboard structure, interactions, and state behavior.  
**Scope:** Covers the proposed UX Specification behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Visual direction

Use a dark research-console base with deep navy/charcoal surfaces, high-contrast white text, cool blue/cyan data accents, and restrained amber/red only for clearly labeled source classifications. Avoid decorative star fields behind dense data. Use generous chart whitespace, readable tabular numerals for measurements, and restrained motion. The design is a Cosmos product identity; do not use NASA insignia or imply NASA endorsement.

## Navigation and major screens

| Area | Wireframe description |
|---|---|
| Overview | Left navigation; top row of source-health/freshness chips; large APOD feature; two-column cards for near approaches and recent DONKI/EONET records; each card opens its detail page. |
| Astronomy | Date control and media-type selector; large image/video region; title/date/credit; explanation column; provenance footer; save and ask-assistant actions. |
| Asteroids | Search/filter bar; sortable table/list on left; detail and approach timeline on right; compare tray fixed below result list; hazardous state is source-labeled. |
| Space Weather | Type/date filters; UTC timeline with accessible table alternative; cards grouped by event type; detail drawer lists event links and available measurements. |
| Earth Events | Category/status/date controls; map with event points/polygons; synchronized event list; selecting either highlights the other; text list remains usable without map. |
| NASA Media | Search field and media/year filters; responsive image/video cards; detail panel with NASA ID, creator, description, asset/caption links, copyright note. |
| AI Research Assistant | Question composer; selected record context; response separated into generated answer, facts, interpretation, limitations, and retrieved records. |
| Reports | Saved reports list and detail; scope, date range, generated label, source snapshots, created date, delete/export. |
| Settings | Profile/session, data retention and deletion, accessibility preferences, source/AI disclosure, API status where authorized. |

## Interaction and responsive rules

Filters are reflected in URL query state where no private information is present. Detail panels include source, identifier, source date, retrieval date, and stale marker. Charts include an accessible table; maps synchronize selection with a list. At 360–640 px, navigation becomes an accessible drawer, tables become cards or labelled horizontal scroll, map and list become stacked/tabs, and comparison is vertical. At 641–1024 px use two-column content; wider screens use up to three columns.

Every panel supports initial loading, background refresh, empty results, stale data, request error/retry, and partial data. Preserve stale successful content during refresh failure. Abort superseded searches; debounce text input by 250–400 ms.

## Security and source display

Render source text as text. Do not insert raw APOD Basic HTML or NASA media descriptions. If an iframe is approved, sanitize against a fixed host allowlist and restrictive CSP. No NASA or OpenRouter key is bundled in the frontend. External links use safe schemes and no-opener behavior.

## Related documents

[Design System](DESIGN_SYSTEM.md), [User Journeys](USER_JOURNEYS.md), [Wireframes](WIREFRAMES.md), [Accessibility](ACCESSIBILITY.md).
