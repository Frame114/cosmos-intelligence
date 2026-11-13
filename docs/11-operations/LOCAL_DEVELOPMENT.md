# Local Development

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Target workflow; Compose files are not yet implemented  
**Purpose:** Specify the intended Local Development requirements and implementation constraints.  
**Scope:** Covers the proposed Local Development behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Target developer workflow

Prerequisite: Docker Engine/Desktop with Docker Compose plugin. The full-stack target command is:

~~~text
docker compose up --build
~~~

This starts frontend, API, PostgreSQL, worker, MCP, and local proxy/service dependencies in containers. A developer does not install Python, Node, or PostgreSQL on the host to run the full application. Use docker compose logs -f, docker compose exec api ..., and docker compose down for routine work. Database reset is destructive and requires an explicit local-development confirmation; never use volume deletion on production.

## Current repository status

At the documentation handoff, Compose/Docker files do not exist. The repository contains an initial Python FastAPI health slice, APOD client/model prototype, tests, and a Python 3.11 CI workflow. Until implementation milestone INF-01, a contributor may run that prototype using the README’s Python development steps, but this is a temporary foundation workflow and not the target full-stack setup.

Use a git-ignored `.env` for private local settings only when needed; the current working tree has `.env.example` deleted, so do not assume a template is present. Follow the variable names in [environment configuration](../08-infrastructure/ENVIRONMENT_CONFIGURATION.md). Use DEMO_KEY for low-volume exploration or the privately held developer key in local secret configuration. Never put the actual key in a command that may be recorded or in a committed file.

## Related documents

[Docker Compose Specification](../08-infrastructure/DOCKER_COMPOSE_SPECIFICATION.md), [README](../../README.md), [Troubleshooting](TROUBLESHOOTING.md).
