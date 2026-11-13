# Acceptance Criteria

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 release criteria  
**Purpose:** Specify the intended Acceptance Criteria requirements and implementation constraints.  
**Scope:** Covers the proposed Acceptance Criteria behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



| ID | Journey/quality | Acceptance |
|---|---|---|
| AC-01 | Clean developer setup | On a clean checkout with Docker Compose only, documented command builds and starts frontend/API/MCP/worker/database; ready endpoints pass. |
| AC-02 | APOD | Current, historical, list, single record, image/video/iframe, missing fields, and date filtering follow dedicated APOD Basic guide; conflicting portal parameters are covered by a contract test. |
| AC-03 | NEO | Search/detail/compare show units, nullable estimates, hazardous and sentry source flags, and no impact-prediction claim. |
| AC-04 | DONKI | At least requested types have fixtures and normalized source links; dates/timezones and variable fields are preserved. |
| AC-05 | EONET | v3 category/status/date/bbox searches and point/polygon/empty geometry render with curation note and accessible list. |
| AC-06 | Media | Text/type/year search and pagination work; metadata/manifest links and rights/credit appear; binaries are not mirrored. |
| AC-07 | Provenance | Every science record has source identity, retrieval time, hash, and source link where supplied; completeness ≥99.9%. |
| AC-08 | AI | Feature remains off until NASA policy gate passes; enabled answers validate schema/citations, abstain without evidence, label generated text, and pass evaluation thresholds. |
| AC-09 | User content | Owner-scoped save/report/conversation read/delete tests pass; admin has no default access to conversation content. |
| AC-10 | MCP | All tool schemas/caps/auth are enforced; same services as REST; Inspector can list/call tools; no public port. |
| AC-11 | Security | DB unreachable publicly; secret scans clean; auth/rate/CSP/CORS checks pass; no high-severity unwaived finding. |
| AC-12 | Recovery | Encrypted off-host backup and isolated restore meet 24h RPO/4h RTO. |

## Related documents

[PRD](../00-project/PRD.md), [Release Checklist](RELEASE_CHECKLIST.md), [Definition of Done](../../DEFINITION_OF_DONE.md).
