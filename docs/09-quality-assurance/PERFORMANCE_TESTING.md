# Performance Testing

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 performance plan  
**Purpose:** Specify the intended Performance Testing requirements and implementation constraints.  
**Scope:** Covers the proposed Performance Testing behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Workload and targets

On a seeded single-VPS-like environment, 20 concurrent readers for 10 minutes across cached search/detail requests: API p95 ≤500 ms, error rate <1%, no DB pool exhaustion. Cold full-text search p95 ≤1 second for 100k normalized records. Public UI p75 LCP ≤2.5 s on representative mid-tier broadband. AI completion p95 target ≤30 s only when provider responds successfully; upstream/provider latency is reported separately.

## Scenarios

Measure APOD date lookup, NEO date-window search/compare, DONKI date/type search, EONET bbox/category, NASA media search, report retrieval, DB-down readiness, NASA slow/429, and model slow/invalid-output. Test pagination and maximum permitted filters. Use synthetic data and mocked upstreams; do not generate a NASA quota load test.

## Related documents

[Testing Strategy](TESTING_STRATEGY.md), [Monitoring](../08-infrastructure/MONITORING.md), [Success Metrics](../00-project/SUCCESS_METRICS.md).
