# Rate Limiting and Upstream Budgets

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Protect NASA quotas, prevent abuse, and bound provider cost.  
**Scope:** Covers the proposed Rate Limiting and Upstream Budgets behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## NASA

NASA API portal documented defaults at research time: registered key 1,000 requests/hour shared across api.nasa.gov endpoints; DEMO_KEY 30/hour and 50/day per IP; quota headers X-RateLimit-Limit and X-RateLimit-Remaining. A real key is private configuration. These defaults may change or differ by service. EONET, APOD Science, EPIC, and NASA Media are separate hosts; do not count them against api.nasa.gov quota without current NASA documentation.

Track quota by source host/key identity (store only a non-reversible configured-key fingerprint for grouping), observe response headers, and enforce a local budget at no more than 70% of the documented quota for scheduled work, leaving headroom for interactive queries. If remaining quota drops below 10%, pause backfills and reduce current refreshes. A 429 opens a source-specific cooldown, honors Retry-After where provided, and creates an operator-visible status.

Deduplicate identical jobs, use bounded time windows, cache results according to per-source policy, and coordinate all API/worker calls through one source budget manager. Never retry 401/403 as a transient condition.

## Internal application

Initial single-instance per-process limits are specified in API_SPECIFICATION.md. Require authentication and low per-subject budgets for OpenRouter-backed routes. Report 429 with a retry estimate and request ID. Keep public-search and AI/report budgets separate.

## OpenRouter

Set daily token/spend budgets and per-user request limits using configuration. Record model, request ID, prompt version, estimated and returned usage/cost metadata when provided. Use provider fallback only when configured and capability-compatible. If actual usage is absent, mark cost unknown rather than estimating from a guessed price. Never retry a billable request blindly after an ambiguous timeout; use provider request IDs/idempotency support only if current docs verify it.

## Related documents

[NASA Integrations](NASA_INTEGRATIONS.md), [Error Handling](../02-technical/ERROR_HANDLING.md), [AI Provider Design](../04-ai-engineering/LLM_PROVIDER_DESIGN.md), [Monitoring](../08-infrastructure/MONITORING.md).
