# MCP Security

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Specify the intended MCP Security requirements and implementation constraints.  
**Scope:** Covers the proposed MCP Security behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Transport controls

- Local stdio is launched by an explicitly configured client; keep protocol stdout clean and write operational logs to stderr.
- Remote Streamable HTTP is not host-published. Caddy forwards only the intended path over a private app network.
- Validate an OAuth access token, issuer, audience, expiry, signature, scopes, and subject on every protected tool. Use SDK authorization integration only after verifying the current SDK v2 API.
- Separate read scope, research:generate, and admin scope. Report generation has request and spend budgets.

## Tool hardening

Every handler revalidates even if JSON schema passed. Cap IDs, arrays, date ranges, text length, page size, and output bytes. Do not accept URLs, file paths, SQL, code, or model-chosen hostnames. Redact sensitive arguments in logs. Returned media links are treated as data, not followed by the server.

## Monitoring and incident response

Audit caller pseudonym, tool name, request ID, start/end, result code, and record IDs where permitted. Alert on repeated authorization failures, oversized input, rate-limit spikes, and repeated tool errors. Revoke issuer/client credentials and disable expensive tools through configuration if misuse is suspected. Do not log full prompts or access tokens.

## Related documents

[MCP Specification](MCP_SPECIFICATION.md), [Security Specification](../06-security/SECURITY_SPECIFICATION.md), [Authentication](../06-security/AUTHENTICATION.md).
