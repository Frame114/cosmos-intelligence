# Data Flow

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Specify the flow from upstream acquisition to UI and AI.  
**Scope:** Covers the proposed Data Flow behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Ingestion flow

~~~mermaid
sequenceDiagram
  participant S as Scheduler / worker
  participant J as PostgreSQL job queue
  participant N as NASA adapter
  participant P as Pydantic validation and normalizer
  participant D as PostgreSQL repositories
  S->>J: claim due job with lease
  S->>N: request bounded date/page window
  N->>N: timeout, status, quota and JSON checks
  N-->>S: typed source payload + retrieval metadata
  S->>P: validate source model and normalize
  P->>D: persist hashed raw record and domain rows
  D-->>S: inserted/updated/unchanged counts
  S->>J: complete or schedule bounded retry
~~~

Each item persists atomically with its normalized row. Stable source identifiers and a unique constraint make replays idempotent. An invalid item is recorded as a validation failure with a sanitized path and payload hash; it is not inserted into searchable domain tables. Partial-page failure does not mark the whole requested window complete.

## Read/search flow

The browser calls the same-origin API. The route validates request limits and auth, the application service builds a domain query, and a repository runs parameterized SQL with whitelisted sorts and indexes. A response includes canonical fields, provenance reference(s), retrieval time, and pagination metadata. It does not leak the unfiltered raw upstream object to the browser.

## AI answer flow

~~~mermaid
flowchart TD
  Q[Question + authorized conversation] --> Intent[Bound intent and filter extraction]
  Intent --> Retrieve[PostgreSQL structured filters + full-text search]
  Retrieve --> Gate{Sufficient validated evidence?}
  Gate -->|No| Gap[Return clarification or evidence gap]
  Gate -->|Yes| Context[Rank, deduplicate, cap context, mark untrusted source text]
  Context --> Model[Configured OpenRouter model]
  Model --> Parse[Parse strict response schema]
  Parse --> Verify{Every citation is in retrieved set?}
  Verify -->|No| Reject[Reject or repair once using deterministic validator]
  Verify -->|Yes| Answer[Answer with evidence and labelled interpretation]
  Answer --> Persist[Store answer, prompt version, model metadata, evidence IDs]
~~~

Source prose and NASA media descriptions are treated as untrusted content, never as instructions. The model cannot broaden its search to arbitrary URLs, fetch external media, or execute user SQL. Search and report generation have explicit row, token, and cost budgets.

## Invalidation and freshness

Responses can include freshness state current, stale, or unknown and a retrieval timestamp. Record freshness thresholds are source-specific and configurable; a stale record remains discoverable if labelled. Cache keys include validated filters and domain, not credentials or raw prompts.

## Related documents

[Data Engineering](../02-technical/DATA_ENGINEERING.md), [AI Architecture](../04-ai-engineering/AI_ARCHITECTURE.md), [API Provenance](../03-integrations/API_PROVENANCE.md).
