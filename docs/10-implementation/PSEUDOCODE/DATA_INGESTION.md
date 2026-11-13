# Pseudocode: Data Ingestion

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Implementation blueprint  
**Purpose:** Specify the intended Pseudocode: Data Ingestion requirements and implementation constraints.  
**Scope:** Covers the proposed Pseudocode: Data Ingestion behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Algorithm

1. Worker polls due jobs, opens a short DB transaction, selects one eligible job with a row lock and skip-locked semantics, sets worker ID/lease_until, increments attempt count, commits.
2. Load the job’s fixed source and validated date/page window. Do not accept user-supplied hosts.
3. Fetch the bounded page/window with the NASA adapter. If pagination exists, follow only documented next links or increment validated page values until end/page budget.
4. For each upstream item, validate the provider schema. Derive stable upstream identity and payload hash. Normalize dates, units, flags, and links without replacing missing values with zero.
5. If validation fails, record a sanitized validation issue, source identity/hash if derivable, and failure count; quarantine the item from searchable tables.
6. Begin transaction; upsert source_record on source plus external ID. If hash unchanged, count unchanged and refresh retrieval metadata. If changed, replace raw payload and update normal form. If new, insert both. Apply child approach rows with stable uniqueness.
7. Commit each bounded page transaction. Keep counters for received/inserted/updated/unchanged/rejected.
8. If all pages/windows complete, mark job successful and store counts. If transient failure, schedule bounded retry with next_run_at and safe error. If permanent/exhausted, mark failed and require operator retry.
9. Never mark a date window complete after partial pagination. Lease expiry allows restart recovery; upsert prevents duplicates.
10. Emit metrics and safe logs with job/source/request IDs; no raw payload or key.
