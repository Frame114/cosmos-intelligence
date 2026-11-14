# MCP Specification

**Version:** 1.0
**Last updated:** 2026-11-13
**Status:** Specification baseline; local authenticated Streamable HTTP implementation is smoke-tested; production identity and Inspector evidence remain
**Purpose:** Define a safe MCP adapter over shared Cosmos application services.
**Scope:** Covers the proposed MCP Specification behavior and interfaces; local implementation is available; production acceptance is tracked separately.
**Assumptions:** Local implementation exists; verify mutable upstream contracts before release.


## SDK and transport

Use the official MCP Python SDK current stable line at implementation. As researched 2026-11-13, official SDK docs identify v2 as stable and require Python 3.11+. Read the v1-to-v2 migration guide because class/import names changed. Use Streamable HTTP for the deployed service and stdio only for local desktop clients. Legacy SSE is not selected for new deployments.

Remote MCP listens only on a private container interface and is routed by Caddy. Require configured OAuth/OIDC authorization, audience/scope checks, rate limits, and separate permissions for data reads and report generation. Local stdio inherits the invoking process identity and must not print protocol noise to stdout.

## Service boundary

MCP handlers validate typed inputs, authorize the caller, invoke the same Python application services used by FastAPI, enforce row/time/cost budgets, and validate structured output. Do not make a second NASA/OpenRouter client in the MCP package and do not read/write tables directly from a handler.

## MCP request flow

~~~mermaid
sequenceDiagram
  participant C as MCP client
  participant E as Caddy/private edge
  participant M as MCP SDK server
  participant A as Auth and policy
  participant S as Shared application service
  participant R as Repository
  participant D as PostgreSQL
  C->>E: Streamable HTTP request
  E->>M: Forward over private network
  M->>A: Validate token, scope, input and budget
  A-->>M: Authorized typed operation
  M->>S: Invoke shared domain service
  S->>R: Parameterized domain query
  R->>D: Read validated records
  D-->>R: Records and provenance
  R-->>S: Domain result
  S-->>M: Bounded typed output
  M-->>C: Structured MCP result or safe error
~~~

Local stdio clients use the same auth and service policy through the invoking user's configured identity. Transport setup never grants tool permissions by itself.

## Tool result and errors

Return structured JSON results with stable domain fields, provenance, and limits. Errors include safe code and concise message. Input schema errors are protocol validation failures; missing records are not-found; upstream outage returns a retryable service error; authorization denies protected tools. Never expose stack, secret, provider body, SQL, or another user’s data.

## Security considerations

Tool descriptions are user-facing and must not claim prediction or NASA endorsement. Tools are capabilities, not model-executed code; every call is re-authorized server-side. Keep the allowlist small, no arbitrary URL/SQL/filesystem tools, and record tool name, caller pseudonym, time, outcome, and request ID without logging full sensitive arguments.

## Acceptance

- MCP Inspector can list tools/resources/prompts against the deployment.
- Each tool has strict input and output schema and one shared service call path.
- Unauthorized report-generation and admin access fail closed.
- Unit tests use the SDK in-memory client where supported; integration tests run a local Streamable HTTP server without real NASA/LLM secrets.
- Remote MCP is unreachable on a host-published port.

## Official sources

[Official MCP Python SDK](https://py.sdk.modelcontextprotocol.io/), [SDK running/transport guide](https://py.sdk.modelcontextprotocol.io/run/), [SDK v1-to-v2 migration guide](https://py.sdk.modelcontextprotocol.io/migration/).

## Related documents

[MCP Tools](MCP_TOOLS.md), [Resources](MCP_RESOURCES.md), [MCP Security](MCP_SECURITY.md), [Application Architecture](../01-architecture/INTEGRATION_ARCHITECTURE.md).
