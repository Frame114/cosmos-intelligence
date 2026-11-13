# Error Handling

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Keep failures typed, bounded, safe, and observable.  
**Scope:** Covers the proposed Error Handling behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Error taxonomy

| Category | Examples | Internal treatment | User-facing behavior |
|---|---|---|---|
| Input | Invalid date range, unsupported sort/filter | Pydantic/domain validation | 422 problem response with field path. |
| Not found | No local record or valid source item | Domain NotFound | 404; do not disclose private resource existence. |
| Upstream permanent | NASA 400/401/403/404 or key invalid | Provider error, no retry except corrected configuration | 502 for upstream contract/error; safe source code, admin diagnostic. |
| Upstream transient | Timeout, connection, 429, selected 5xx | Bounded backoff; retain stale data | 502/503/504 and retryable indicator; Retry-After if known. |
| Data contract | Invalid JSON/schema/unit | Quarantine item and increment validation-failure count | Return stored usable data if available with stale/partial label; otherwise 503. |
| Database | Pool exhausted, disconnected, transaction conflict | Roll back; retry only safe serialization/deadlock cases | 503; readiness down when persistent. |
| AI provider | Rate limit, model unavailable, timeout, refusal | Circuit breaker and budget accounting | 503/504 for AI route only; browsing remains usable. |
| AI validation | Invalid JSON/citation/schema | Reject; at most one schema-repair attempt if configured | Safe invalid-output response or evidence-gap result. |
| Authorization | Missing/expired token, wrong role | Fail closed | 401/403 problem response without token detail. |

## Retry and circuit policy

Retry only idempotent GETs or idempotent DB/job operations. Honor Retry-After, use exponential backoff with full jitter, maximum three attempts per operation, and a total deadline. Respect NASA rate limits and do not let retries exceed the job lease. Circuit-break per upstream after repeated transient failures; probe with bounded half-open requests. Do not retry malformed payloads or client errors.

## Logging

Assign request_id before route processing and job_id at claim. Log sanitized source, operation, outcome, HTTP status, elapsed time, retry count, and exception class. Retain detailed stack only in restricted logs; do not return it. Redact URLs, headers, user content, credentials, and NASA/OpenRouter response bodies.

## Related documents

[API Specification](API_SPECIFICATION.md), [Rate Limiting](../03-integrations/RATE_LIMITING.md), [Monitoring](../08-infrastructure/MONITORING.md).
