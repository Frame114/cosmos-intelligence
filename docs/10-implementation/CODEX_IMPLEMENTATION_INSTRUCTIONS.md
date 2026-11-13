# Codex Implementation Instructions

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Governing instructions for the next phase  
**Purpose:** Specify the intended Codex Implementation Instructions requirements and implementation constraints.  
**Scope:** Covers the proposed Codex Implementation Instructions behavior and interfaces; current implementation status is tracked separately.  



## Source of truth

This documentation package is the implementation source of truth. Read docs/README.md first, then read the product, architecture, technical, NASA, AI, MCP, security, infrastructure, UX, QA, implementation, and operations documents that apply to the task. Inspect the repository and all local guidance before changing files. If implementation code conflicts with a specification, stop that local work, explain the discrepancy, and resolve it through a documented decision; never silently discard a requirement.

## Required workflow

1. Read every specification before implementation begins.
2. Inspect the existing repository, including uncommitted changes, tests, workflows, package metadata, and local instructions.
3. Identify missing requirements, contradictions, stale API assumptions, and risks; record them before changing architecture.
4. Produce a milestone implementation plan with dependencies, files, acceptance criteria, test plan, and completion evidence.
5. Implement in small, logically grouped milestones with reviewable diffs.
6. Use Docker Compose as the standard full-stack development environment; do not require host Python, Node, or PostgreSQL.
7. Create automated tests alongside each feature and cover failure paths.
8. Validate each NASA/technology integration against current official documentation before implementing or upgrading it.
9. Never hard-code credentials, keys, URLs containing keys, or passwords.
10. Never commit secrets, local .env files, secret fixtures, tokens, or production data.
11. Run linting, type checks, migrations, integration tests, E2E tests, and evaluation suites required by the milestone.
12. Fix failures instead of hiding, skipping, or weakening checks without a documented reason.
13. Maintain PROJECT_STATUS.md with honest state and evidence.
14. Maintain CHANGELOG.md for user-visible and technical changes.
15. Maintain DECISIONS.md / architecture ADRs for material decisions.
16. Update TECHNICAL_DEBT.md when a genuine implementation debt is introduced, found, or resolved.
17. Record actual command output or CI links as implementation evidence.
18. Never claim tests, builds, security scans, or deployment succeeded unless they actually ran and passed.
19. Stop and report genuine blockers with what was tried and what decision/input is needed.
20. Request human approval before destructive operations, irreversible data changes, production deployment, or public release.

## Engineering requirements

- Follow the API, database, provenance, security, testing, Docker, and UI contracts.
- Use one application service layer for REST, worker, and MCP.
- Preserve units, nullable source data, source IDs, retrieval times, and record hashes.
- No public NASA-derived AI output before the documented NASA policy review gate passes.
- Update affected specification pages and acceptance evidence when implementation reveals a contract change.

## Related documents

[Implementation Plan](IMPLEMENTATION_PLAN.md), [Definition of Done](../../DEFINITION_OF_DONE.md), [Security Specification](../06-security/SECURITY_SPECIFICATION.md).
