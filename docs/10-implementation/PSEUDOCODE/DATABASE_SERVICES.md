# Pseudocode: Database Services

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Implementation blueprint  
**Purpose:** Specify the intended Pseudocode: Database Services requirements and implementation constraints.  
**Scope:** Covers the proposed Pseudocode: Database Services behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Upsert and search

1. Receive a validated domain record and source envelope; require source, external ID, retrieval timestamp, and SHA-256.
2. Open a task-scoped AsyncSession and transaction.
3. Insert/upsert source_record by unique source_code + external_id. On same hash, avoid rewriting unchanged normalized fields; update last-seen/retrieved metadata. On new hash, replace the current raw payload/version.
4. Insert/update the normalized domain row and child rows in the same transaction. Enforce units/check constraints and stable uniqueness. Roll back on any failure.
5. Return persisted record IDs and insert/update/unchanged result.

## Search

1. Validate page size, filters, date range, and allowed sort key at service boundary.
2. Construct a SQLAlchemy expression with bound values and joins to source/provenance.
3. Add mandatory owner predicate for user tables from authenticated identity, never request body.
4. Apply stable secondary sort by primary key and bounded offset/page. Use exact indexes/full-text query and count strategy appropriate to page.
5. Map rows to response DTOs; include source ID, retrieval time, freshness, and safe source URL.
6. Close session; log timing and row count only.

## Job lease

Select one due queued job with row-level skip-locked behavior; set owner and expiry in the same transaction. Renew only while active. Completion/failure updates must match job ID and lock owner. Expired lease returns to retryable queue after a grace interval.
