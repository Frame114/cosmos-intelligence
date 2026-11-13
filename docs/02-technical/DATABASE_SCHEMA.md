# Database Schema

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Define normalized records, provenance, user content, constraints, and retention.  
**Scope:** Covers the proposed Database Schema behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Entity relationship diagram

~~~mermaid
erDiagram
  DATA_SOURCE ||--o{ SOURCE_RECORD : identifies
  SOURCE_RECORD ||--o| APOD_RECORD : normalizes_to
  SOURCE_RECORD ||--o| NEO_OBJECT : normalizes_to
  NEO_OBJECT ||--o{ NEO_APPROACH : has
  SOURCE_RECORD ||--o{ NEO_APPROACH : supports
  SOURCE_RECORD ||--o| SPACE_WEATHER_EVENT : normalizes_to
  SOURCE_RECORD ||--o| EARTH_EVENT : normalizes_to
  SOURCE_RECORD ||--o| MEDIA_RECORD : normalizes_to
  INGESTION_JOB }o--|| DATA_SOURCE : targets
  USER_ACCOUNT ||--o{ SAVED_RECORD : owns
  USER_ACCOUNT ||--o{ RESEARCH_CONVERSATION : owns
  RESEARCH_CONVERSATION ||--o{ RESEARCH_MESSAGE : contains
  USER_ACCOUNT ||--o{ AI_REPORT : owns
  PROMPT_VERSION ||--o{ AI_REPORT : produced_with
  AI_REPORT ||--o{ REPORT_EVIDENCE : cites
  SOURCE_RECORD ||--o{ REPORT_EVIDENCE : cited_record
~~~

## Tables

| Table | Key columns and types | Constraints/indexes |
|---|---|---|
| data_source | code TEXT PK, display_name, base_host, enabled BOOLEAN, policy JSONB | code allowlist; no arbitrary user host. |
| source_record | id UUID PK, source_code FK, external_id TEXT, source_url TEXT nullable, retrieved_at TIMESTAMPTZ, source_updated_at nullable, payload_hash CHAR(64), raw_payload JSONB, schema_version TEXT, created_at | UNIQUE(source_code, external_id); INDEX(source_code, retrieved_at DESC); GIN on raw_payload only if query use justifies it. |
| apod_record | source_record_id UUID PK/FK, apod_date DATE UNIQUE, title TEXT, explanation TEXT, media_type TEXT CHECK, page_url TEXT, media_url TEXT nullable, hd_url TEXT nullable, alt_text TEXT nullable, credit TEXT nullable, copyright TEXT nullable | INDEX(apod_date DESC); treat HTML as untrusted and do not store rendered executable markup. |
| neo_object | source_record_id UUID PK/FK, neo_id TEXT UNIQUE, name TEXT, absolute_magnitude DOUBLE PRECISION nullable, diameter_min_km NUMERIC nullable, diameter_max_km NUMERIC nullable, potentially_hazardous BOOLEAN nullable, sentry_object BOOLEAN nullable, jpl_url TEXT nullable | Diameter min <= max when both present; INDEX(name); nullable preserves absent upstream values. |
| neo_approach | id UUID PK, source_record_id FK, neo_id FK, approach_date DATE, epoch_date_close TIMESTAMPTZ nullable, velocity_km_s NUMERIC nullable, miss_distance_km NUMERIC nullable, miss_distance_au NUMERIC nullable, orbiting_body TEXT nullable | UNIQUE(neo_id, approach_date, orbiting_body); INDEX(approach_date); validate nonnegative. |
| space_weather_event | source_record_id UUID PK/FK, event_type TEXT, activity_id TEXT, start_time TIMESTAMPTZ nullable, end_time nullable, class_type TEXT nullable, source_location TEXT nullable, details JSONB, link TEXT nullable | INDEX(event_type, start_time DESC); unique upstream source_record key combines event type and upstream ID. |
| earth_event | source_record_id UUID PK/FK, eonet_id TEXT UNIQUE, title TEXT, description TEXT nullable, opened_at TIMESTAMPTZ nullable, closed_at nullable, categories JSONB, sources JSONB, geometry JSONB nullable, geometry_type TEXT nullable, magnitude_value NUMERIC nullable, magnitude_unit TEXT nullable | INDEX(closed_at, opened_at); JSONB preserved; bbox filtering is bounded and geometry-aware in app until PostGIS is justified. |
| media_record | source_record_id UUID PK/FK, nasa_id TEXT UNIQUE, title TEXT, media_type TEXT, date_created TIMESTAMPTZ nullable, description TEXT nullable, description_508 TEXT nullable, keywords JSONB, creators JSONB, asset_manifest_url TEXT, detail_url TEXT, rights_note TEXT nullable | INDEX(media_type, date_created DESC); store metadata and links, not binary assets. |
| ingestion_job | id UUID PK, source_code FK, job_type TEXT, window_start/end DATE nullable, state TEXT CHECK, attempts INT, next_run_at, lease_until nullable, locked_by nullable, started_at/finished_at nullable, counts JSONB, safe_error_code nullable | INDEX(state, next_run_at); attempts >= 0; lease expiry enables recovery. |
| api_request_log | id UUID PK, source_code nullable, operation TEXT, started_at, duration_ms INT, status_code nullable, outcome TEXT, retry_count INT, rate_limit_remaining INT nullable, request_id TEXT | Retain 30 days; no bodies, URL query, auth, or response text. |
| user_account | id UUID PK, oidc_subject TEXT UNIQUE, role TEXT, created_at, last_seen_at nullable | Store opaque subject/role; do not require email or profile unless needed. |
| saved_record | id UUID PK, user_id FK, source_record_id FK, created_at | UNIQUE(user_id, source_record_id); cascade delete on user deletion. |
| research_conversation | id UUID PK, user_id FK, title TEXT nullable, created_at, updated_at, deleted_at nullable | INDEX(user_id, updated_at DESC); owner-scoped. |
| research_message | id UUID PK, conversation_id FK, role TEXT CHECK, content TEXT, created_at, prompt_version_id FK nullable, model_id TEXT nullable, usage JSONB nullable, status TEXT | No secrets in content; delete with conversation; user messages are untrusted. |
| prompt_version | id UUID PK, name TEXT, version TEXT, system_template TEXT, created_at, checksum CHAR(64), active BOOLEAN | UNIQUE(name, version); code review required to activate. |
| ai_report | id UUID PK, user_id FK, prompt_version_id FK, title TEXT, question TEXT, structured_answer JSONB, model_id TEXT, created_at, deleted_at nullable | INDEX(user_id, created_at DESC); generated output clearly labelled. |
| report_evidence | report_id FK, source_record_id FK, citation_key TEXT, excerpt_hash CHAR(64) nullable, rank INT | PK(report_id, source_record_id); citation validated against retrieval result. |

## Types and normalization

- Store absolute timestamps as TIMESTAMPTZ and dates as DATE. NASA close-approach calendar dates remain source dates; do not infer a local timezone.
- Use NUMERIC for displayed scientific measurements that require stable decimal persistence; use source units and preserve raw values. Float may be used only for geometry calculations.
- Preserve nullable estimates as NULL; zero is a scientific value and must not stand for missing.
- Store upstream raw payload only in source_record. Domain tables contain fields needed for filters, pages, and charts.
- JSONB arrays keep variable NASA event metadata where a normalized child-table contract would add no query value. Promote fields only after a concrete query requirement.
- No user-authored geometry or URLs are accepted in release 1.

## Idempotency, provenance, and migrations

Canonical identity is source code plus upstream identifier; APOD uses APOD date, EONET uses EONET ID, media uses NASA ID, NeoWs uses NeoWs numeric ID, and DONKI uses event type plus activity ID or a stable documented source link. Upsert is atomic with the normalized record. Hash changes update current source payload while recorded retrieval metadata allows audit. Alembic migrations are hand-reviewed; autogenerate output is only a candidate and must be checked for renames, constraints, data loss, and PostgreSQL behavior.

## Retention policy

| Data | Default policy |
|---|---|
| Normalized scientific records and provenance identity/hash | Retain for historical search while the service is operated; source licenses/terms may require a source-specific policy. |
| Raw upstream JSON | Retain 24 months, then purge raw JSON while preserving normalized fields, source ID/URL, timestamps, hash, and schema version. |
| Request and worker event logs | 30 days; aggregate counters may be retained longer without request content. |
| Completed ingestion jobs | 180 days; purge verbose failure diagnostics at 30 days. |
| Conversations/messages | 90 days from last update by default; user can delete earlier. |
| Reports and evidence links | 1 year by default or user deletion, whichever is earlier; exports are user responsibility. |
| Saved-record references | Until user deletion/account deletion. |

## Related documents

[Data Engineering](DATA_ENGINEERING.md), [API Provenance](../03-integrations/API_PROVENANCE.md), [Backup and Recovery](../08-infrastructure/BACKUP_AND_RECOVERY.md).
