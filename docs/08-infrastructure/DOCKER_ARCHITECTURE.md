# Docker Architecture

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 infrastructure baseline  
**Purpose:** Make development and Ubuntu VPS deployment reproducible without host Python, Node, or PostgreSQL.  
**Scope:** Covers the proposed Docker Architecture behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Services

| Service | Image strategy | Network and persistence |
|---|---|---|
| postgres | Official PostgreSQL 18 image; password via POSTGRES_PASSWORD_FILE; pg_isready healthcheck. Recheck supported major at lock time. | Internal data network; named PGDATA volume; no host port. |
| api | Multi-stage Python 3.12 image, minimal runtime, non-root UID. | Proxy, private data, and outbound networks; internal port only. |
| worker | Reuse immutable backend image with worker command, non-root. | Private data and outbound networks. |
| mcp | Reuse backend image with MCP command, separate auth/limits. | Proxy and private data networks; outbound only if AI enabled; no public host port. |
| frontend | Multi-stage Node 22 build; non-root static HTTP server. | Proxy network; no secrets in bundle. |
| caddy | Official Caddy 2 image with Caddyfile and certificate-state volume. | Only service publishing host ports. |
| migrate | One-shot backend image running Alembic to head before app startup. | Private data network; must exit successfully first. |

## Networks and volumes

- proxy/edge: Caddy, frontend, API, MCP; only Caddy maps public ports.
- data: internal-only bridge shared with PostgreSQL and services that need DB access; PostgreSQL has no other network.
- outbound: API/worker and optional MCP for NASA/OpenRouter HTTPS. No inbound host port.
- Named volumes: postgres-data, caddy-data. App root filesystems are read-only where practical, with tmpfs for temporary files.
- No Docker socket, broad host filesystem bind, host network, privileged mode, or host PID namespace.

## Health, hardening, resources

PostgreSQL health uses pg_isready. API liveness is process-only; readiness checks DB/schema. Worker health reports heartbeat/lease. MCP readiness confirms startup only. Compose dependencies use service_healthy and service_completed_successfully. Run as non-root, drop capabilities, set no-new-privileges, use resource limits, rotate logs, scan images, and never bake secrets into layers.

Initial VPS estimate: 2 vCPU, 4 GB RAM, 40 GB SSD for one portfolio deployment; validate with measured load and alert at 75% disk/80% memory. Media files are linked, not mirrored.

## Related documents

[Compose Specification](DOCKER_COMPOSE_SPECIFICATION.md), [Network Architecture](NETWORK_ARCHITECTURE.md), [VPS Deployment](VPS_DEPLOYMENT.md), [Backup and Recovery](BACKUP_AND_RECOVERY.md).
