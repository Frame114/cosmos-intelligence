# User Personas

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Anchor product and UX decisions in task needs.  
**Scope:** Covers the proposed User Personas behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


| Persona | Needs | Risks and support |
|---|---|---|
| Public explorer | Find an image or event, understand its date and context, open the primary source. | Avoid unexplained jargon; show last updated and any missing field. |
| Student/educator | Compare records, understand units and classifications, save a cited explanation. | Teach uncertainty and source distinctions; do not imply forecasts or official endorsement. |
| Research analyst | Apply filters, inspect values and raw-source provenance, repeat a search, export a report. | Record query window, filters, units, source version/time, and normalization version. |
| MCP client operator | Discover tools, validate input/output, control authorization, and trace results. | Minimize tools and permissions; expose no secrets, raw SQL, or arbitrary URL access. |
| Deployment administrator | Configure secrets, identity, backups, source limits, and inspect failures. | Protect operations endpoints, avoid payload/key logging, document recovery evidence. |

## Shared accessibility needs

All personas require keyboard access, semantic headings and labels, non-color-only data signals, chart summaries or tables, text equivalents for maps, reduced-motion behavior, visible focus, and meaningful loading/error/empty states.

## Related documents

[PRD](PRD.md), [UX Specification](../07-ux-design/UX_SPECIFICATION.md), [Accessibility](../07-ux-design/ACCESSIBILITY.md).
