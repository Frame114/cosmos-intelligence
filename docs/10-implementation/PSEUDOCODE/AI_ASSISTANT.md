# Pseudocode: Scientific AI Assistant

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Implementation blueprint; disabled until policy gate  
**Purpose:** Specify the intended Pseudocode: Scientific AI Assistant requirements and implementation constraints.  
**Scope:** Covers the proposed Pseudocode: Scientific AI Assistant behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Algorithm

1. Require feature enabled, authenticated subject, valid conversation ownership, and AI budget. Enforce question length and strip control characters without destroying scientific notation.
2. Classify intent only among supported search/explain/compare/summarize/report/clarify operations. Map to explicit application services; do not allow arbitrary tool names.
3. Retrieve relevant validated domain records through structured filters + PostgreSQL full-text; apply owner/privacy rules, ranking, deduplication, freshness, and row caps.
4. If evidence is absent or insufficient, return a deterministic evidence-gap/clarification response without asking the model to invent knowledge.
5. Build versioned context: system policy, task, bounded conversation summary, evidence blocks with request-local citation keys, source IDs, units, dates, retrieval time, and untrusted-data delimiters. Cap record count/context tokens.
6. Call configured OpenRouter model under deadline, token/cost budget, allowed response schema, and capability-compatible parameters.
7. Parse structured output with Pydantic. Validate labels, lengths, units, dates, and that every citation key maps to a record retrieved for this request.
8. If output schema is invalid, permit one bounded repair with the same evidence; if citations remain invalid, reject the model response.
9. Separate source-backed statements, interpretation, uncertainty, and limitations. Label generated text as Cosmos AI output and do not imply NASA authorship/endorsement.
10. Persist user message, output, prompt version/checksum, model, usage, record IDs/hashes, and timestamps in one transaction.
11. Return answer and evidence references. On provider failure, preserve conversation and provide safe retry status; non-AI browsing remains available.
