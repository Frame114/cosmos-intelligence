# Docker Compose Specification

**Version:** 1.0<br>
**Last updated:** 2026-11-14<br>
**Status:** The local Compose stack is implemented; production overlay and deployment controls remain open.<br>
**Purpose:** Document local Compose services and identify production infrastructure gaps.<br>
**Scope:** Covers `compose.yaml` as shipped for local development. Production TLS, secrets mounts, backups, and resource controls are not implemented here.<br>
**Assumptions:** Docker Engine/Desktop and the Compose plugin are available. Recheck upstream image tags and API contracts during deployment preparation.<br>



## Files and workflows

- compose.yaml is the local development stack and supports `docker compose up --build` when Docker Compose is available.
- The current stack contains PostgreSQL, a one-shot migration task, API, ingestion worker, static frontend, private MCP service, and local Caddy proxy. It supports deterministic daily jobs when `WORKER_SCHEDULES_ENABLED=true`; this remains disabled by default.
- There is no production overlay yet. Production domain/TLS configuration, resource limits, backup workflow, and file-backed Compose secret mounts remain release work.
- `.env` and local secret files are ignored; `.env.example` contains placeholders only. Compose reads local environment values at runtime, and the Docker build context excludes `.env` files.
- Backend, worker, and MCP use one immutable backend image with distinct commands.

## Base service dependencies

~~~yaml
services:
  postgres:
    image: postgres:18
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
  migrate:
    depends_on:
      postgres:
        condition: service_healthy
  api:
    depends_on:
      migrate:
        condition: service_completed_successfully
~~~

The current implementation follows this startup dependency order and validates its configuration with `docker compose config --quiet`. The doubled dollar in the PostgreSQL healthcheck defers variable expansion to the container shell.

## Production controls

Publish Caddy TCP 80 and 443 only; optionally UDP 443 if HTTP/3 is enabled. Do not publish any internal service port. Use per-service Compose secrets, named volumes, restart policies, resource limits, non-root images, and log rotation. File-backed secrets are mounted files, not an encrypted secret manager; protect their host files and disk.

Apply database migrations as a one-shot task after a backup and before starting the new app version. Stop deployment on migration failure. Keep previous image tags and a reviewed rollback/restore plan.

## Related documents

[Docker Architecture](DOCKER_ARCHITECTURE.md), [Environment Configuration](ENVIRONMENT_CONFIGURATION.md), [Secrets Management](../06-security/SECRETS_MANAGEMENT.md).
