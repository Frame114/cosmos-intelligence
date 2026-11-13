# MCP Resources and Prompts

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Specify the intended MCP Resources and Prompts requirements and implementation constraints.  
**Scope:** Covers the proposed MCP Resources and Prompts behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Resources

| URI/template | MIME/type | Contents and access |
|---|---|---|
| cosmos://catalog/sources | application/json | Supported source names, domains, freshness state, and source terms links; no secrets. |
| cosmos://records/{source}/{record_id} | application/json | One public normalized record with provenance and retrieval time; validates source and ID. |
| cosmos://reports/{report_id} | application/json | Owner-scoped generated report; requires authenticated subject and report access. |
| cosmos://help/scientific-limitations | text/markdown | Units, classification meaning, stale-data rules, uncertainty, and no impact-prediction statement. |

Do not expose raw database rows, full user conversations, authentication configuration, prompt templates with hidden secrets, or arbitrary resource URLs. Resource contents are size bounded and public records remain validated.

## Prompts

| Prompt name | Arguments | Purpose |
|---|---|---|
| explain_scientific_record | source, record_id, audience=general|student|technical | Requests a concise explanation using only the supplied record, with provenance, unknowns, and an explicit generated-content label. |
| compare_scientific_records | record_ids (2–10), comparison_goal | Aligns equivalent fields/units and requests missing-value disclosure; does not infer impact risk. |
| draft_source_grounded_report | question, domain, date range | Requests a structured report from retrieved evidence; requires research:generate authorization and respects the AI release gate. |

Prompts provide reusable task text, not permission. The host still invokes tools and the server independently validates authorization and input.

## Related documents

[MCP Specification](MCP_SPECIFICATION.md), [MCP Tools](MCP_TOOLS.md), [AI Guardrails](../04-ai-engineering/AI_GUARDRAILS.md).
