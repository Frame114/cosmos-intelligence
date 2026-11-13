# Success Metrics

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Define measurable evidence that the release works and communicates science responsibly.  
**Scope:** Covers the proposed Success Metrics behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


| Measure | Initial target | Measurement |
|---|---:|---|
| Critical user journeys | 100% pass | E2E suite for APOD lookup, asteroid detail/compare, event filter, media search, cited answer, save/delete. |
| Backend meaningful coverage | ≥85% | Coverage plus review of branch and failure-path evidence; exclude generated/migration files only with documented rationale. |
| Provenance completeness | ≥99.9% persisted source records | Required source code, upstream ID, retrieval timestamp, payload hash; report exceptions. |
| Citation integrity | 100% generated citation IDs in retrieved set | Deterministic post-generation validator and eval report. |
| Unsupported high-confidence science claims | 0 in release eval set | Human-reviewed, versioned factuality and uncertainty suite. |
| Security findings | 0 known critical/high exploitable at release | Dependency, container, secret, and application review; exceptions have owner/expiry. |
| API availability SLO | 99.5% monthly for the single VPS, excluding NASA/provider outages | Probe readiness; separately report upstream and provider status. |
| Browser performance | p75 LCP ≤2.5 s on representative mid-tier broadband | Lighthouse/Web Vitals sample; large NASA assets load lazily and from source hosts. |
| Failure transparency | 100% critical upstream failures yield a safe typed error and recorded job/request state | Fault-injection cases and operator-visible status. |

## Guardrails on interpretation

- Metrics measure Cosmos implementation behavior, not NASA science quality or impact risk.
- Report NASA upstream availability separately; upstream outage is not hidden by a high application SLO.
- Coverage is a diagnostic. It does not replace contract, security, accessibility, or domain review.

## Related documents

[Testing Strategy](../09-quality-assurance/TESTING_STRATEGY.md), [AI Evaluation](../04-ai-engineering/AI_EVALUATION.md), [Monitoring](../08-infrastructure/MONITORING.md).
