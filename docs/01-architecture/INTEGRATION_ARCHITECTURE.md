# Integration Architecture

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Define outbound service boundaries and lifecycle.  
**Scope:** Covers the proposed Integration Architecture behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## NASA clients

Each service adapter has a constant HTTPS base host, endpoint allowlist, typed request parameters, Pydantic provider schemas, and provider-to-domain mapping. A shared HTTPX AsyncClient uses explicit phase timeouts, bounded connection pools, redirect policy, safe user agent, and instrumentation. NASA API keys are injected only into services documented to use the NASA key; request logging and tracing redact query parameters and authorization data.

GET retries are limited to connection errors, timeouts, 429, and selected 5xx responses. They use capped exponential backoff with jitter and Retry-After when valid, and stop before the request deadline. Do not retry 400/401/403/404 or schema/normalization failures automatically. Per-host concurrency and request pacing prevent a single synchronization job from consuming the shared NASA quota.

## OpenRouter

Use the documented chat-completions endpoint through an internal provider protocol. The provider/model ID, allowed parameters, capability support, context limit, structured-output/tool support, timeout, and cost policy are deployment settings informed by current OpenRouter model metadata. The application owns all tool execution and post-validates output. No user browser or MCP client receives the OpenRouter key.

## Authentication provider

OIDC provider is external and replaceable. The API validates access tokens against configured issuer/audience and cached signing keys; the frontend uses Authorization Code with PKCE. Provider availability failures fail closed for protected actions. Public science read routes may continue.

## MCP

MCP tool adapters call application services in-process. Streamable HTTP is internal-network only behind Caddy and an authentication boundary. For local desktop integrations, use stdio; do not launch a remote stdio bridge with ambient secrets. MCP does not call NASA or OpenRouter directly except through shared services.

## Dependency isolation

Outbound targets are allowlisted by adapter configuration. User input may refine supported query parameters but cannot set a host, scheme, port, redirect destination, or file path. Redirects are disabled for API JSON calls unless a service contract documents a fixed safe redirect. Media links are rendered with safe schemes/host handling and never fetched server-side by arbitrary URL.

## Related documents

[NASA Integrations](../03-integrations/NASA_INTEGRATIONS.md), [Provider Design](../04-ai-engineering/LLM_PROVIDER_DESIGN.md), [MCP Security](../05-mcp/MCP_SECURITY.md), [Threat Model](../06-security/THREAT_MODEL.md).
