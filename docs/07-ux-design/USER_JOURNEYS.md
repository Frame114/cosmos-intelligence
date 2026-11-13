# User Journeys

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 design baseline  
**Purpose:** Specify the intended User Journeys requirements and implementation constraints.  
**Scope:** Covers the proposed User Journeys behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Explore an astronomy record

Overview → Astronomy → select date/search historical term → inspect media and explanation → read credit/provenance → optionally save or ask a question. If the APOD is video/iframe or media is unavailable, show a safe NASA source link and explanatory fallback.

## Compare near-Earth objects

Asteroids → apply approach/date filters → open two or more detail records → choose compare → align common units and selected approach window → inspect missing-value labels and upstream classification → save comparison/report. The interface does not calculate impact probability.

## Review an Earth event

Earth Events → select category/status/date → inspect map or list → choose event → detail shows source, geometry observation dates, curation notice, and last retrieval → follow original source. Map failure falls back to the list.

## Ask a research question

Open assistant from a record or assistant page → type a bounded question → review selected evidence → receive a generated answer with separate facts/interpretation/limitations and retrieved record links → save/delete conversation. If evidence is insufficient or provider disabled, return a clear gap instead of a guess.

## Related documents

[UX Specification](UX_SPECIFICATION.md), [AI Architecture](../04-ai-engineering/AI_ARCHITECTURE.md), [Acceptance Criteria](../09-quality-assurance/ACCEPTANCE_CRITERIA.md).
