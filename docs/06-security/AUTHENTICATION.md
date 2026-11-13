# Authentication and Authorization

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Provider-neutral design; production issuer selection remains open  
**Purpose:** Specify the intended Authentication and Authorization requirements and implementation constraints.  
**Scope:** Covers the proposed Authentication and Authorization behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Identity flow

Use OpenID Connect Authorization Code with PKCE for the browser. Configure issuer, client ID, audience, redirect URI, and scopes from deployment settings. Validate access-token signature using issuer JWKS with bounded cache, exact issuer/audience, exp, nbf, subject, and accepted algorithms. Never trust unverified claims or caller-supplied role headers.

The production provider and role mapping are deployment decisions. Until configured, production disables protected endpoints. A development-only mock identity may run in an isolated local Compose profile and must fail startup if APP_ENV is production.

## Authorization matrix

| Operation | Public | Authenticated user | Admin |
|---|---:|---:|---:|
| Search/read public scientific records | Yes | Yes | Yes |
| Create/delete saved-record references | No | Own records | Support access only if explicitly audited |
| Read/delete conversations/reports | No | Own records | No default content access |
| Generate AI report | No | research:generate scope | Yes, subject to budget |
| View source/job/health summaries | No | No | cosmos_admin |
| Trigger retry for a failed ingestion job | No | No | cosmos_admin |

Every user-owned SQL query includes user_id derived from the validated subject. Never use IDs from a request as proof of ownership. Admin access to private user content is not part of release 1.

## Token/session rules

Keep access tokens short-lived according to the selected provider’s current guidance; use refresh only through the OIDC client’s supported secure pattern. Store no long-lived bearer token in localStorage. Require state, nonce, PKCE verifier, secure redirect validation, and logout cleanup. If a backend cookie session is added, use HttpOnly/Secure/SameSite and CSRF defenses.

## Related documents

[Security Specification](SECURITY_SPECIFICATION.md), [Frontend Specification](../02-technical/FRONTEND_SPECIFICATION.md), [MCP Security](../05-mcp/MCP_SECURITY.md).
