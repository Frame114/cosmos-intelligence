# Docker Compose Specification

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Implementation-ready design; Compose files are planned for the Docker milestone.  
**Purpose:** Specify the intended Docker Compose Specification requirements and implementation constraints.  
**Scope:** Covers the proposed Docker Compose Specification behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Files and workflows

- compose.yaml is the development/default stack and supports docker compose up --build from a clean checkout.
- compose.production.yaml overlays production ports, restart policies, secrets, resource limits, read-only filesystems, and Caddy domain configuration.
- When a checked-in example template is present, it contains safe placeholders only. `.env`, local secret files, production certs, and data are ignored. The current working tree has `.env.example` deleted; reconcile this during the Compose implementation milestone if an example is needed.
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

This is a design excerpt, not a complete Compose file. At implementation, pin a currently supported patch/image digest and validate the merged configuration with docker compose config. The doubled dollar in the real Compose YAML defers variable expansion to the container shell.

## Production controls

Publish Caddy TCP 80 and 443 only; optionally UDP 443 if HTTP/3 is enabled. Do not publish any internal service port. Use per-service Compose secrets, named volumes, restart policies, resource limits, non-root images, and log rotation. File-backed secrets are mounted files, not an encrypted secret manager; protect their host files and disk.

Apply database migrations as a one-shot task after a backup and before starting the new app version. Stop deployment on migration failure. Keep previous image tags and a reviewed rollback/restore plan.

## Related documents

[Docker Architecture](DOCKER_ARCHITECTURE.md), [Environment Configuration](ENVIRONMENT_CONFIGURATION.md), [Secrets Management](../06-security/SECRETS_MANAGEMENT.md).
