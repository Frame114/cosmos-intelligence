# Ubuntu 24.04 VPS Deployment

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Deployment design; first deployment remains incomplete  
**Purpose:** Specify the intended Ubuntu 24.04 VPS Deployment requirements and implementation constraints.  
**Scope:** Covers the proposed Ubuntu 24.04 VPS Deployment behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Host setup

Use a supported Ubuntu 24.04 LTS host with Docker Engine and Docker Compose plugin from official Docker guidance. Create a non-root deployment account, disable password SSH, use keys, restrict SSH ingress, enable security updates, configure firewall, synchronize time, and monitor disk/RAM. Do not install project Python, Node, or PostgreSQL directly on host.

## Release procedure

1. Verify host backup, disk, DNS, firewall, and secret files.
2. Verify CI, release checklist, SBOM, and image scan for the release.
3. Pull/build immutable images.
4. Run database backup.
5. Validate production Compose configuration and secret mounts.
6. Run migration one-shot; stop on error.
7. Start services with health checks; verify Caddy HTTPS and health endpoints.
8. Smoke-check public search, login, saved-record ownership, AI state, and MCP auth.
9. Confirm logs contain no credentials/query keys and review backup status.
10. Keep previous image and rollback instructions available; use forward-fix or reviewed restore for database changes.

## TLS and recovery

Caddy obtains/renews certificates when DNS points to the VPS and inbound HTTP/HTTPS are reachable. Persist Caddy data/config. For host loss, provision a clean host, restore secrets through the approved channel, restore the latest verified encrypted database backup, deploy a compatible release, then validate record counts and auth before routing traffic.

## Related documents

[Network Architecture](NETWORK_ARCHITECTURE.md), [Backup and Recovery](BACKUP_AND_RECOVERY.md), [Deployment Runbook](../11-operations/DEPLOYMENT_RUNBOOK.md).
