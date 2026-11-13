# Troubleshooting

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Operational baseline; update with observed implementation failures  
**Purpose:** Specify the intended Troubleshooting requirements and implementation constraints.  
**Scope:** Covers the proposed Troubleshooting behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



| Symptom | First checks | Safe action |
|---|---|---|
| Compose service waits/unhealthy | docker compose ps; service healthcheck logs; docker compose config | Fix health/readiness or dependency; do not add fixed sleeps instead of readiness. |
| API readiness fails | DB container health, migration revision, credentials-file path, private network | Restore DB connectivity/migration; liveness may remain up; do not expose DB port. |
| NASA 429 | Source admin quota state, shared api.nasa.gov request budget, DEMO_KEY use | Pause backfill, respect cooldown/Retry-After, reduce concurrency; never rotate into logs. |
| APOD date lookup returns latest instead | Review dedicated APOD Basic params and fixture test | Use date_from/date_to YYMMDD or /{YYMMDD} per current dedicated guide; re-check NASA portal conflict. |
| Unexpected NASA payload | Source schema version, safe validation path, response hash | Quarantine item, preserve prior valid row, update contract after official review. |
| Media does not render | NASA ID, manifest/status, item rights, browser CSP/network | Link to NASA detail page; do not construct a guessed asset URL. |
| Worker retries forever | Attempts, next_run_at, lease owner/expiry, safe error | Confirm retry cap; mark terminal and alert; retry only after correction. |
| OIDC login fails | issuer/audience/redirect URI/time, JWKS refresh, callback config | Correct deployment config; do not disable production auth. |
| AI answer lacks valid citations | Retrieved evidence set, prompt version, validator result, feature gate | Reject output and return evidence gap; do not remove citation check. |
| MCP client cannot connect | Transport path, Caddy route, auth token audience/scope, service health | Use Streamable HTTP for remote; keep backend port private. |
| Disk nearing full | PostgreSQL volume, Docker images/logs, backup retention | Preserve and verify backup before cleanup; never delete data volume to clear space. |

Always capture request/job ID and safe source/error code, not API keys, authorization, prompts, or raw user payloads.

## Related documents

[Error Handling](../02-technical/ERROR_HANDLING.md), [Monitoring](../08-infrastructure/MONITORING.md), [Deployment Runbook](DEPLOYMENT_RUNBOOK.md).
