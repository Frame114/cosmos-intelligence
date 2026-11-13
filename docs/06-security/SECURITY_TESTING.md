# Security Testing

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 verification plan  
**Purpose:** Specify the intended Security Testing requirements and implementation constraints.  
**Scope:** Covers the proposed Security Testing behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Required checks

- Dependency vulnerability scan for Python, npm, and base images; document severity, exploitability, and fix/exception expiry.
- Secret scanning on source and history-aware CI; prove known test placeholders are the only matches.
- Container scan and Dockerfile policy review for root, privileged mode, capabilities, exposed ports, secrets, and writable filesystems.
- Auth tests for missing/expired/wrong issuer/audience/signature/scope and production identity misconfiguration.
- Authorization matrix tests for cross-user IDs, report deletion, saved records, admin routes, and MCP scope.
- Injection tests for SQL-like filters, script/HTML in NASA fields, hostile links, redirect chains, oversized JSON/geometry, and prompt injection.
- Rate/DoS checks for large page sizes, long date windows, excessive parallel requests, model budgets, and database pool exhaustion.
- CORS, CSP, security headers, HTTPS redirect, and PostgreSQL network exposure checks in production Compose.
- Restore test for encrypted off-host backup and database migrations against production-like data volume.

## Release criteria

No known critical or high-severity exploitable issue at release without a time-bound approved exception. Tests must include evidence and environment; passing scanner output alone is not a complete security review.

## Related documents

[Threat Model](THREAT_MODEL.md), [Release Checklist](../09-quality-assurance/RELEASE_CHECKLIST.md), [Docker Architecture](../08-infrastructure/DOCKER_ARCHITECTURE.md).
