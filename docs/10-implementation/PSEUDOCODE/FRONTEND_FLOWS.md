# Pseudocode: Frontend Flows

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Implementation blueprint  
**Purpose:** Specify the intended Pseudocode: Frontend Flows requirements and implementation constraints.  
**Scope:** Covers the proposed Pseudocode: Frontend Flows behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Dashboard load/search

1. Mount AppShell and request overview with AbortController and request ID; show labelled skeletons per panel.
2. Decode typed API response, render only validated fields, include source/freshness badges, and retain accessible heading/focus order.
3. On filter change, validate locally, debounce text query, cancel previous request, update query state only with nonprivate filters, then request page 1.
4. On success, render table/cards plus chart/map summary and an empty state when total is zero.
5. On refresh failure, keep previous results and mark them stale. On first-load failure, display source-specific error and retry.
6. On detail selection, open a labelled drawer, preserve list scroll, request one record, and show provenance/source link.
7. On save, require sign-in, POST the record reference, announce success, and handle 401 by returning to sign-in without losing current context.

## Assistant flow

1. Validate question length and selected record IDs; announce evidence search.
2. Submit through authenticated API with request ID and abort signal.
3. Show separate retrieval/generation progress, never expose provider keys or raw prompts.
4. Render answer sections, verified citations, generated-content label, limitations, and stale/partial data.
5. If API returns evidence gap, explain missing record coverage; if provider fails, preserve draft and offer safe retry.
