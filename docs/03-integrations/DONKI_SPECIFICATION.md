# DONKI Specification

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Verified against NASA portal and a live CME request; event-type schemas require typed contract fixtures.  
**Purpose:** Specify the intended DONKI Specification requirements and implementation constraints.  
**Scope:** Covers the proposed DONKI Specification behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Endpoint catalog

Base: https://api.nasa.gov/DONKI. Method: GET. NASA api_key query parameter is used; obtain at runtime from a private setting.

| Path | Event class | Documented query |
|---|---|---|
| /CME | Coronal mass ejection | startDate, endDate |
| /CMEAnalysis | CME analysis | startDate, endDate, mostAccurateOnly, speed, halfAngle, catalog |
| /GST | Geomagnetic storm | startDate, endDate |
| /IPS | Interplanetary shock | startDate, endDate, location, catalog |
| /FLR | Solar flare | startDate, endDate |
| /SEP | Solar energetic particle | startDate, endDate |
| /MPC | Magnetopause crossing | startDate, endDate |
| /RBE | Radiation belt enhancement | startDate, endDate |
| /HSS | High-speed stream | startDate, endDate |
| /WSAEnlilSimulations | WSA+Enlil simulation | startDate, endDate |
| /notifications | Notification feed | startDate, endDate, type; documented type values include all, FLR, SEP, CME, IPS, MPC, GST, RBE, report; maximum window documented as 30 days. |

The portal documents variable defaults for recent date windows; always send explicit UTC-derived dates and split requests to a conservative bounded window. No common pagination contract is documented. The 2026-11-13 live CME result was an array; observed keys included activityID, catalog, startTime, instruments, sourceLocation, activeRegionNum, note, cmeAnalyses, linkedEvents, sentNotifications, link, submissionTime, and versionId. Other event types have different fields.

## Data model and behavior

Use a shared envelope for source_record, event_type, activity_id when supplied, event time fields, source link, and source submission/version metadata. Preserve event-specific fields in raw JSON and selectively normalize fields with an approved type-specific Pydantic schema. Do not infer one type’s properties from another or convert event counts to severity.

When activityID is missing, use a stable source URL or a deterministic hash of documented identity fields, scoped by event type. Validate links as HTTPS and allowlisted NASA/JPL hosts before presenting them.

## Refresh and errors

Cache recent windows 30 minutes and historical windows 24 hours; refresh the most recent 30-day window every two hours as an initial policy. This is application policy, not an upstream promise. Maintain source-type-specific request budgets because the NASA api.nasa.gov hourly quota is shared.

Transient errors keep existing records available and mark refresh stale. Unexpected fields may be ignored only after required-field checks; missing required identity/time fields quarantine that item. Never overwrite a valid record with a contract-invalid payload.

## Related documents

[NASA Integrations](NASA_INTEGRATIONS.md), [Database Schema](../02-technical/DATABASE_SCHEMA.md), [Rate Limiting](RATE_LIMITING.md).
