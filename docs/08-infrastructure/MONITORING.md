# Monitoring and Operations Visibility

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 design baseline  
**Purpose:** Specify the intended Monitoring and Operations Visibility requirements and implementation constraints.  
**Scope:** Covers the proposed Monitoring and Operations Visibility behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Signals and alerts

Collect liveness/readiness, app version, DB reachability/migration version, per-source request outcome/status/latency/retries/quota headers/last-success, queue depth/oldest due/lease expiry/failures/validation rejects, AI availability/model/latency/token usage/citation rejects/budget, and VPS CPU/memory/disk/PostgreSQL storage/backup age/Caddy cert age/container restarts.

Initial alerts: application unavailable 5 minutes; DB unready 2 minutes; failed backup; disk >75%; sustained memory >80%; quota remaining <10%; worker oldest due >30 minutes; repeated NASA 429/5xx; AI budget >80%.

## Exposure and logging

Admin summaries require cosmos_admin. Detailed metrics, if added, bind only on private network. Public health reveals coarse status only. No metric label contains user ID, prompt, full URL, source key, or arbitrary exception. JSON logs go to stdout/stderr with Docker rotation; retain application logs 30 days and admin audit metadata 180 days. Do not log SQL bind values, user content, or full upstream payloads.

## Related documents

[Error Handling](../02-technical/ERROR_HANDLING.md), [Rate Limiting](../03-integrations/RATE_LIMITING.md), [Backup and Recovery](BACKUP_AND_RECOVERY.md).
