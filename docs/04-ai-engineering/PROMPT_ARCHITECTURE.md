# Prompt Architecture

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Make system instructions, versioning, and context assembly reviewable.  
**Scope:** Covers the proposed Prompt Architecture behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Prompt layers

1. **System policy:** role, scientific uncertainty, no unsupported facts, no arbitrary browsing, no risk prediction, citation rules, and output schema.
2. **Task instruction:** one supported intent and its specific response shape.
3. **Conversation summary:** compact, server-generated summary with user text clearly marked as untrusted.
4. **Retrieved evidence:** records in a delimited data block with evidence ID, source record ID, source label, retrieval time, record hash, fields, units, and provenance link.
5. **Current user question:** plain user content; never treat it as a system instruction.

## Versioning

Each prompt has a stable name, semantic version, source-controlled template, checksum, change rationale, owner, and evaluation result. Database prompt_version rows record the released checksum. Prompt edits require eval runs and reviewer sign-off; never silently edit an active database prompt. Secret values are never interpolated into prompts.

## Context budget

Default maximum evidence records: 12, total evidence text: 16,000 characters, user question: 4,000 characters, conversation history: last 8 turns or a bounded summary, output: 1,200 tokens. Keep numeric source fields and units intact; truncate long descriptions with an explicit truncation marker. If selection omits relevant records due to budget, say so in limitations.

## Untrusted data boundaries

Wrap upstream descriptions, APOD explanations, media titles, and user messages as quoted data. Tell the model they may contain instructions that must be ignored. Do not let any record alter role, tools, policies, model configuration, or the retrieval scope.

## Related documents

[Context Engineering](CONTEXT_ENGINEERING.md), [AI Guardrails](AI_GUARDRAILS.md), [Evaluation](AI_EVALUATION.md).
