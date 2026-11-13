# Data Engineering

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Define acquisition, validation, normalization, replay, and analytical-query behavior.  
**Scope:** Covers the proposed Data Engineering behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Ingestion modes

- Scheduled bounded refresh for current/high-change records: APOD latest daily; NeoWs rolling near-term approach windows; DONKI recent event windows; EONET open events and changed recent events; media is demand-driven search plus metadata cache.
- Backfill jobs use explicit date/id windows, bounded page size, pause controls, and operator visibility. Do not crawl a full historical archive without a storage/quota plan.
- Admin retry reuses the original source and parameters after correcting transient/configuration failures; users cannot submit arbitrary upstream jobs.

## Pipeline

1. A job is due; worker claims it under a lease and increments attempts atomically.
2. Adapter validates parameters and performs an HTTPS GET with timeout and rate budget.
3. Parse JSON; reject non-JSON or unexpected top-level shape. Validate provider schema with extra fields ignored only when policy permits.
4. Normalize units and identifiers in a pure function with explicit source-schema version.
5. In one database transaction, upsert source_record and typed domain row/children; record counts.
6. Mark complete only after all expected pages/windows are processed. Retry only transient errors with cap and jitter; permanent failures are terminal until operator action.
7. Emit outcome counters and safe error codes, never payloads or secrets.

## Analytics

Asteroid comparisons align by common source units and chosen approach window. Report any missing/different dates. Space-weather summary groups by event type and UTC date; it is a count of DONKI records, not a severity score. Earth-event charts summarize curated metadata and must state that event definition and coverage are curated. APOD historical views respect media_type and date. Never compare different units without explicit conversion and recorded conversion.

## Freshness and consistency

Each normalized record includes retrieval time and source update time if present. API responses label data stale after per-source thresholds. Existing records remain available during upstream downtime. No background refresh is triggered by every browser user; cache misses may return 202 with a safe refresh/job status only where supported.

## Related documents

[Database Schema](DATABASE_SCHEMA.md), [NASA Integrations](../03-integrations/NASA_INTEGRATIONS.md), [Error Handling](ERROR_HANDLING.md).
