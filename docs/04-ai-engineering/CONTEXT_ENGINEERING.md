# Context Engineering

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Specify evidence ranking and budget behavior for each question.  
**Scope:** Covers the proposed Context Engineering behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Retrieval and prioritization

Use intent filters to select the product domain, then combine required structured constraints with PostgreSQL full-text search. Prioritize exact identifier/date/category matches, then source-specific title/name match, then text relevance. Add a bounded recency adjustment only for explicitly current questions; historical questions must not be biased to recent records. Deduplicate by source record ID and preserve one record’s units/metadata.

## Context assembly

For each evidence item include a stable key, domain type, source name and URL, source identifier, event/observation date, retrieved_at, normalized values with units, record hash, and a short validated excerpt. Evidence IDs are request-local and cannot be invented by the model. Label source prose as untrusted. Include explicit unknown/null fields only when important to answer.

## Insufficient evidence

If retrieval returns no records, incompatible date ranges, or fewer than the minimum evidence threshold for a requested comparison, do not call the model for scientific assertions. Return a clarification request or a deterministic evidence-gap response. If only partial evidence exists, permit a narrow answer and list missing coverage.

## Context overflow

Trim conversation first, then low-ranked records, then long descriptions. Never truncate numeric field names, values, units, time basis, source identity, or citation keys. Record how many results were available and included. If evidence was cut due to budget, state the limit in answer metadata.

## Related documents

[Retrieval Architecture](RETRIEVAL_ARCHITECTURE.md), [Prompt Architecture](PROMPT_ARCHITECTURE.md), [AI Evaluation](AI_EVALUATION.md).
