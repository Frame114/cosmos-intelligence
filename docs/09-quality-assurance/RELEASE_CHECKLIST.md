# Release Checklist

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 checklist  
**Purpose:** Specify the intended Release Checklist requirements and implementation constraints.  
**Scope:** Covers the proposed Release Checklist behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Product and science

- [ ] Requirements and docs reviewed; selected NASA contracts checked against current official sources.
- [ ] APOD Basic parameter discrepancy contract-tested.
- [ ] NASA source rights/attribution and current AI/SI policy reviewed; AI feature flag enabled only after written decision.
- [ ] Units, hazards, EONET curation, generated-content labels, and limitations reviewed.

## Quality and security

- [ ] CI passes on locked Python/Node versions; coverage target and critical journeys pass.
- [ ] No known unwaived critical/high security finding; SBOM/image scan available.
- [ ] OIDC, owner scoping, rate limiting, error redaction, CORS/CSP, and private DB network tested.
- [ ] Dependency, secret, container, and prompt-injection checks reviewed.

## Operations

- [ ] Backup completed and restore drill evidence available.
- [ ] Migration reviewed and tested; rollback/forward-fix plan exists.
- [ ] DNS, HTTPS, firewall, secrets, quotas, resource alerts, and on-call contact checked.
- [ ] Health/readiness, NASA degradation, worker recovery, and AI disable switch verified.
- [ ] Release notes/changelog and project status updated with evidence.

## Related documents

[Acceptance Criteria](ACCEPTANCE_CRITERIA.md), [VPS Deployment](../08-infrastructure/VPS_DEPLOYMENT.md), [Codex Instructions](../10-implementation/CODEX_IMPLEMENTATION_INSTRUCTIONS.md).
