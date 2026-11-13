# Secrets Management

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Specify the intended Secrets Management requirements and implementation constraints.  
**Scope:** Covers the proposed Secrets Management behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Secret inventory

NASA API key; OpenRouter API key; PostgreSQL application password and bootstrap password; OIDC client secret where a confidential client is needed; Caddy DNS-provider credential only if a custom DNS module is selected; off-site backup encryption key; TLS private material if certificates are not automated.

## Local development

For local development, use a git-ignored `.env` for private developer settings and the NASA key when needed; check that it remains ignored before use. This working tree currently has `.env.example` deleted, so do not assume a template is present. Reintroduce a placeholder-only template as a reviewed configuration task if implementation needs one. Use Compose secret files for production credentials. The real NASA key is privately configured and is not reproduced in this specification. Do not add real credentials to source, tests, screenshots, AI prompts, issues, or logs.

## Compose and production

Use Compose secrets backed by files outside the repository and grant each secret only to services that need it. The API receives NASA/OpenRouter credentials; PostgreSQL receives its bootstrap password; worker receives NASA credentials; MCP receives OpenRouter only if report generation is enabled. Each application secret is read from a configured *_FILE path. Use root-owned files with mode 0400/0440 on the Ubuntu host and encrypted off-host secret backup.

Docker Compose file-backed secrets are mounted files and are not an encrypted secret manager. Protect the host disk, backups, deployment account, and Docker socket. Do not expose secrets through env interpolation in CI logs or process command lines. Nonsecret settings may use environment variables.

## Rotation and incident handling

Rotate any suspected credential immediately at its issuing service, update secret files, restart dependent services, verify masked health, and review access logs for use. Record rotation date and affected secret name, never its value. Rotate all dependent credentials if host or Docker control plane is compromised.

## Related documents

[Security Specification](SECURITY_SPECIFICATION.md), [Environment Configuration](../08-infrastructure/ENVIRONMENT_CONFIGURATION.md), [Docker Compose Specification](../08-infrastructure/DOCKER_COMPOSE_SPECIFICATION.md).
