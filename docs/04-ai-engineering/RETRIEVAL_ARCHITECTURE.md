# Retrieval Architecture

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Select the smallest retrieval system that supports the initial data scale and evaluation.  
**Scope:** Covers the proposed Retrieval Architecture behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Decision

Release 1 uses PostgreSQL structured filters plus built-in full-text search. It does not add vector columns, pgvector, external embedding APIs, or a dedicated vector database.

## Search design

Index exact IDs, dates, event types, asteroid names, media types, and category/source codes with B-tree indexes. Build a stored/generated tsvector or maintained search document for APOD title/explanation, NEO name, DONKI searchable text fields, EONET title/description, and NASA media title/description/keywords. Use websearch_to_tsquery/ts_rank_cd or equivalent safe query construction. Do not concatenate a user query into SQL. Add trigram or extension indexing only after a benchmarked requirement and migration review.

Search returns domain records with deterministic ordering and stable tiebreaker IDs. User-provided filters are parameterized and allowlisted. Relevant result count, query filters, and selected evidence IDs are recorded for report reproducibility.

## Why no embeddings initially

The initial dataset consists largely of structured measurements, date/category filters, identifiers, and short descriptions. Exact filters and full-text search are explainable, directly tied to record content, and avoid embedding maintenance, vector infrastructure, model embedding drift, and additional API cost. Consider hybrid vector retrieval only if a versioned evaluation shows a material recall gain on natural-language queries that FTS cannot meet.

## Future hybrid gate

Require a labeled query set, recall@k and citation precision comparison, multilingual/domain justification, cost/storage estimate, deletion/re-index plan, and an ADR before adopting embeddings. Store embedding model/version and source hash if approved. Never replace exact scientific field queries with semantic similarity.

## Related documents

[Database Schema](../02-technical/DATABASE_SCHEMA.md), [Context Engineering](CONTEXT_ENGINEERING.md), [AI Evaluation](AI_EVALUATION.md).
