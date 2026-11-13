# Backup and Recovery

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 design baseline  
**Purpose:** Specify the intended Backup and Recovery requirements and implementation constraints.  
**Scope:** Covers the proposed Backup and Recovery behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Targets

Initial recovery point objective: 24 hours. Initial recovery time objective: 4 hours for one VPS. Validate these targets with a timed restore; adjust as use grows.

## Backup procedure

Run a daily logical PostgreSQL custom-format dump from a client container on the private data network. Encrypt before transfer to a separate off-host location using a key stored separately. Retain 14 daily and 8 weekly backups; record checksum, size, DB version, migration revision, and completion. Do not include plaintext secret files.

## Restore test

At least monthly, restore into an isolated PostgreSQL instance, verify schema and expected table counts/hash samples, run API smoke queries, and record elapsed time/recovery point. A backup without a restore test is unverified.

## Recovery

Document host loss, corruption, credential exposure, accidental delete, and bad migration actions. Avoid docker compose down -v in production. For migration failures, take a fresh backup and use a reviewed forward migration or restore. Protect encryption keys separately from backups.

## Related documents

[VPS Deployment](VPS_DEPLOYMENT.md), [Deployment Runbook](../11-operations/DEPLOYMENT_RUNBOOK.md), [Security Testing](../06-security/SECURITY_TESTING.md).
