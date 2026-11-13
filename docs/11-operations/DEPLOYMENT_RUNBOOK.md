# Deployment Runbook

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Target runbook; not yet exercised in production  
**Purpose:** Specify the intended Deployment Runbook requirements and implementation constraints.  
**Scope:** Covers the proposed Deployment Runbook behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Pre-deploy

1. Confirm release tag, required CI/evaluation/security evidence, change log, and approved release checklist.
2. Verify host health, disk capacity, DNS, firewall, off-host backup status, and secret file permissions.
3. Review production Compose output with docker compose config without printing secrets.
4. Take a new encrypted DB backup and verify its checksum.
5. Pull the new immutable image and verify registry digest/SBOM.

## Deploy

1. Run the one-shot migration service and inspect exit code/logs; stop on error.
2. Start API, worker, MCP, frontend, and Caddy using the production overlay.
3. Verify container health and Caddy HTTPS/certificate state.
4. Check liveness/readiness, source freshness, worker heartbeat, OIDC, and restricted MCP.
5. Run smoke checks: public APOD/NEO search, authenticated save/delete, owner isolation, policy-gated AI state, and MCP tool with test credentials.
6. Review sanitized logs and resource metrics; confirm PostgreSQL is not host-published.

## Rollback

If application-only failure occurs, redeploy previous compatible image. If schema migration is backward-incompatible, do not blindly downgrade; use a reviewed forward fix or restore the pre-deploy backup into a compatible release. Record incident, migration revision, restoration point, and user-visible impact in project status/changelog.

## Related documents

[VPS Deployment](../08-infrastructure/VPS_DEPLOYMENT.md), [Backup and Recovery](../08-infrastructure/BACKUP_AND_RECOVERY.md), [Release Checklist](../09-quality-assurance/RELEASE_CHECKLIST.md).
