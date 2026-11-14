# CI/CD Specification

**Version:** 1.0<br>
**Last updated:** 2026-11-14<br>
**Status:** Design baseline with partial Python, PostgreSQL, and frontend workflow implemented<br>
**Purpose:** Specify the intended CI/CD Specification requirements and implementation constraints.<br>
**Scope:** Covers the proposed CI/CD Specification behavior and interfaces; current implementation status is tracked separately.<br>
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.<br>



## Pull request checks

Use least-privilege GitHub Actions permissions, pin third-party actions to reviewed commit SHAs before release, and never make secrets available to untrusted PR code. Checks: Python 3.12 lock install, Ruff lint/format, mypy, backend tests/coverage, frontend lint/typecheck/unit/build, OpenAPI schema diff, Alembic migration check, MCP tests, Compose config, image build, dependency/secret/image scan.

NASA and OpenRouter tests use mocked fixtures with no real key. A separate manually triggered protected contract workflow may use a restricted secret and make one bounded public read.

## Release and deployment

Tag a version after checks and release checklist. Build immutable images, produce SBOM, scan, publish to a registry, and deploy through a protected GitHub environment with reviewer approval and masked production secrets. Deployment is never triggered from arbitrary PR code. Run backup → migration → rollout → smoke check and preserve previous image tags.

The current `.github/workflows/ci.yml` uses Python 3.12, Ruff, mypy, disposable PostgreSQL migration/drift checks, backend tests, and frontend install/type/test/build checks. The workflow has not been run on GitHub for this working tree. Reviewed action SHA pinning, dependency lock installation, OpenAPI diffing, MCP tests, Compose validation/build, and dependency/secret/image scanning remain open.

## Related documents

[Testing Strategy](../09-quality-assurance/TESTING_STRATEGY.md), [VPS Deployment](VPS_DEPLOYMENT.md), [Codex Instructions](../10-implementation/CODEX_IMPLEMENTATION_INSTRUCTIONS.md).
