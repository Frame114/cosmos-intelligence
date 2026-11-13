# Network Architecture

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 deployment baseline  
**Purpose:** Specify the intended Network Architecture requirements and implementation constraints.  
**Scope:** Covers the proposed Network Architecture behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



~~~mermaid
flowchart LR
  Internet[Internet users]
  Firewall[Ubuntu firewall: 80/443 and restricted SSH]
  Caddy[Caddy HTTPS edge]
  Frontend[Frontend static service]
  API[API]
  MCP[MCP service]
  Worker[Worker]
  DB[(PostgreSQL)]
  NASA[NASA HTTPS services]
  OpenRouter[OpenRouter HTTPS]
  OIDC[OIDC provider]
  Internet --> Firewall --> Caddy
  Caddy --> Frontend
  Caddy --> API
  Caddy --> MCP
  API --> DB
  Worker --> DB
  MCP --> DB
  API --> NASA
  Worker --> NASA
  API --> OpenRouter
  MCP --> OpenRouter
  API --> OIDC
~~~

Caddy is the only public application listener. Database joins no edge/outbound network and publishes no port. Only API/worker and, if reports are enabled, MCP receive outbound HTTPS capability. Restrict SSH to admin source addresses. Do not trust forwarded client-IP headers except from a specifically configured CDN/proxy.

## Related documents

[Docker Architecture](DOCKER_ARCHITECTURE.md), [VPS Deployment](VPS_DEPLOYMENT.md), [Threat Model](../06-security/THREAT_MODEL.md).
