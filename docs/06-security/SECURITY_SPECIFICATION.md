# Security Specification

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 baseline; implementation must threat-review each feature  
**Purpose:** Specify the intended Security Specification requirements and implementation constraints.  
**Scope:** Covers the proposed Security Specification behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Security objectives

- Protect NASA/OpenRouter/database/identity credentials.
- Prevent unauthorized access to user saves, conversations, and reports.
- Preserve integrity and provenance of scientific records.
- Limit SSRF, XSS, SQL injection, prompt injection, AI cost abuse, and MCP tool misuse.
- Keep PostgreSQL and application-only services off public interfaces.
- Produce enough sanitized operational evidence to detect and recover from failures.

## Required controls

| Area | Control |
|---|---|
| Input | Pydantic v2 schemas, length/range caps, strict enums, validated date/unit/ID formats. |
| SQL | SQLAlchemy parameter binding; whitelisted sort/order expressions; no model-generated SQL. |
| Authentication | OIDC Authorization Code + PKCE; API validates signature, iss, aud, exp, nbf, subject, scope/role. |
| Authorization | Public read domain routes; per-subject ownership for user content; admin scope for operations; protected AI writes. |
| CORS | Production same-origin only; explicit environment allowlist in development; credentials disabled for wildcard origins. |
| Browser | Text rendering, no raw NASA HTML, CSP, secure headers, output URL scheme/host validation, no provider secrets. |
| CSRF | Bearer tokens in Authorization header; if cookie sessions are introduced, SameSite, CSRF token, origin check, and secure cookie are mandatory. |
| Rate limiting | Per-IP reads and per-subject AI/write budgets; request size caps; single-instance limitation documented. |
| SSRF | Fixed HTTPS service hosts, no user URL input, redirect policy checked, outbound destination allowlist at app layer. |
| Secrets | Private env in local only; production Compose secret files or host secret manager; no bake-in, print, or query-string logs. |
| Containers | Non-root, minimal multi-stage images, read-only root filesystem where feasible, dropped capabilities, no privileged mode, resource limits. |
| Database | Internal network only, least-privilege app role, password secret file, backups protected/encrypted off-host. |
| Logs | Structured allowlisted fields; redact credentials, prompts, raw payloads, PII, and URL queries. |
| Dependencies | Lockfiles, automated update review, vulnerability scan, SBOM/image scan before release. |
| MCP | Streamable HTTP private route + OAuth, strict schemas, reauthorization every call, output-size and cost caps. |
| AI | Retrieval allowlist, untrusted-source boundaries, citation validation, no arbitrary tools, independent factuality/security evaluation. |

## Data classification

Public: published NASA normalized records and public provenance.  
Private: OIDC subject mapping, saved record associations, conversations, user reports, access/audit events.  
Secret: NASA key, OpenRouter key, DB password, OIDC client secret, TLS private key.  
Secrets never enter analytics, client-side code, version control, test fixtures, prompt context, support screenshots, or normal logs.

## Acceptance checklist

- [ ] Secret scan and dependency/image scans have no unwaived critical/high release issue.
- [ ] PostgreSQL has no host port and cannot be reached from Caddy or the Internet.
- [ ] Caddy is the only production public listener; 80/443 TCP, optional UDP 443 only if enabled.
- [ ] Auth bypass is impossible in production configuration.
- [ ] Cross-user read/write tests cover every user-content endpoint.
- [ ] Malicious URLs, HTML, Unicode/oversized strings, SQL-like filters, and prompt injection are tested.
- [ ] Key, bearer-token, prompt, and query-string redaction is tested.
- [ ] Backup is protected and a restore is demonstrated before release.
- [ ] Security incident and credential rotation runbook is documented.

## Related documents

[Threat Model](THREAT_MODEL.md), [Secrets Management](SECRETS_MANAGEMENT.md), [Authentication](AUTHENTICATION.md), [Security Testing](SECURITY_TESTING.md).
