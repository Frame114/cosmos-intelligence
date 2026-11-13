# Threat Model

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Initial STRIDE-oriented model; review at each trust-boundary change  
**Purpose:** Specify the intended Threat Model requirements and implementation constraints.  
**Scope:** Covers the proposed Threat Model behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Assets and trust boundaries

Assets: NASA key, OpenRouter key, DB credential/data, OIDC tokens/subject, raw and normalized source records, saved content, generated reports, job state, source credibility, and host TLS key.

Boundaries: public browser ↔ Caddy; Caddy ↔ API/MCP; API/worker/MCP ↔ PostgreSQL; application ↔ NASA/OpenRouter/OIDC; developer workstation ↔ container runtime/host filesystem; GitHub Actions ↔ package registries/registry/VPS.

## Threats and controls

| Threat | Attack path / impact | Required mitigations |
|---|---|---|
| Spoofed identity / broken object authorization | Forged JWT or guessing report IDs exposes another user’s conversations. | Verify JWT claims/signature; owner predicate on every query; opaque UUIDs are not authorization. |
| Secret disclosure | Key in source, image layer, command output, request URL logs, or build cache. | Compose runtime secrets; redact queries/headers; secret scanning; no real keys in repo/tests; rotation runbook. |
| SQL injection | User query or model text enters query string. | Bound parameters; whitelist column names/sort; no LLM-generated SQL. |
| SSRF | User-provided media/source URL tricks server into metadata endpoint or internal services. | Fixed hosts/routes; no arbitrary server-side fetch; validate redirects/IPs; network egress limits. |
| XSS | APOD basic_html/media description or model output injected into React. | Treat all text as text; no raw HTML; CSP; sanitize only allowlisted embeds. |
| CSRF/token theft | OIDC session/token abused from hostile site or XSS. | PKCE/state/nonce; bearer header; restrictive CORS/CSP; secure cookie/CSRF controls if cookies are used. |
| Prompt injection | Upstream narrative or user text asks model to reveal data or invoke tools. | Separate untrusted evidence; no secrets in prompt; tool allowlist; ownership filter; citation/output validation. |
| Hallucinated source or measurement | Model invents a NASA finding, value, or citation. | Retrieval-only scientific answers; post-validate citation IDs and units; abstain threshold; eval gates. |
| Cost exhaustion/tool abuse | Public or MCP user triggers repeated model or large search calls. | Auth for AI; per-subject/IP limits; daily spend/token budgets; caps on pages/context; admin kill switch. |
| Malicious upstream payload | Shape, size, nested JSON, invalid links or geometry exhaust resources or corrupt records. | Response-size cap; Pydantic validation; timeout; geometry/JSON limits; quarantine; resilient parser. |
| Dependency/supply-chain compromise | Malicious Python/npm image or GitHub Action code. | Lockfiles, pinned action SHAs at release, minimal permissions, scanning, SBOM, reviewed updates. |
| Container escape/host attack | Root container, mounted Docker socket, public database. | Non-root, no Docker socket, no privileged mode, read-only FS, minimal mounts, host firewall/updates. |
| Data loss/tampering | Volume failure, destructive migration, compromised app DB role. | Backups, restore drills, restricted DB role, migration review, audit trail, no public DB port. |
| Denial of service | Request floods, slow queries, oversized range/page, upstream outage. | Request/body/time limits, pagination, rate limits, DB pool limits, circuit breaker, health isolation. |
| False endorsement | NASA mark or AI response appears official. | No NASA logo, clear independent-project disclaimer, preserve asset credits, generated-content label, policy review gate. |

## Residual risks

Single VPS and single PostgreSQL node have outage and host-compromise risk. In-memory rate limiting is bypassable across multiple processes. NASA and OpenRouter data policies may change. Public NASA descriptions can be inaccurate, incomplete, or adversarial. Release 1 must disclose these limits and keep backups off-host.

## Related documents

[Security Specification](SECURITY_SPECIFICATION.md), [Network Architecture](../08-infrastructure/NETWORK_ARCHITECTURE.md), [AI Guardrails](../04-ai-engineering/AI_GUARDRAILS.md).
