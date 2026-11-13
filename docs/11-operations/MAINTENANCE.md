# Maintenance

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Operations baseline  
**Purpose:** Specify the intended Maintenance requirements and implementation constraints.  
**Scope:** Covers the proposed Maintenance behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Recurring work

- Weekly: review CI/security alerts, failed jobs, source quota/freshness, certificate status, disk, and backup age.
- Monthly: verify dependency updates, restore one backup into isolation, inspect AI evaluation drift if enabled, and review NASA/API docs for breaking notices.
- Quarterly: review Python/PostgreSQL/Node/MCP SDK support, update locks/base images, rotate credentials according to issuer policy, and retest restore/performance.
- Before any integration release: review official source docs and inspect a live bounded response; update contract fixtures and last-verified date.

## Change management

Use small version-controlled migrations and ADRs. Review retention/rights rules when new sources or AI use are added. Update README, documentation index, PROJECT_STATUS.md, ROADMAP.md, CHANGELOG.md, DECISIONS.md, and TECHNICAL_DEBT.md when their evidence changes.

## Related documents

[CI/CD Specification](../08-infrastructure/CI_CD_SPECIFICATION.md), [NASA Integrations](../03-integrations/NASA_INTEGRATIONS.md), [Codex Instructions](../10-implementation/CODEX_IMPLEMENTATION_INSTRUCTIONS.md).
