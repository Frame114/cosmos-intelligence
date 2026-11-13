# AI Architecture

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Proposed; public NASA-derived generation is gated on usage-policy review  
**Purpose:** Specify a provider-independent, evidence-bounded research assistant.  
**Scope:** Covers the proposed AI Architecture behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Components

1. Assistant API validates identity, question size, conversation ownership, request budget, and feature availability.
2. Intent parser classifies a fixed set of supported intents: explain, find, compare, summarize, report, and clarification-needed.
3. Retrieval service searches normalized PostgreSQL records using exact filters and full-text rank.
4. Context builder removes duplicates, caps record count and text size, assigns evidence keys, and marks all source text as untrusted data.
5. Provider adapter sends a versioned prompt and validated context to OpenRouter Chat Completions with a configured model.
6. Output validator checks structure, answer sections, uncertainty, evidence IDs, length, and policy labels.
7. Persistence stores user message, generated message, prompt/model metadata, usage metadata, and evidence references under the user.

No model directly accesses PostgreSQL, NASA, the internet, shell, MCP clients, or arbitrary URLs. Tool execution remains application-controlled.

## Request and degradation

The assistant is optional. If provider credentials, model capability, or budget is unavailable, return a stable AI-disabled/unavailable result and keep all scientific browsing/search active. An unavailable evidence index produces an explicit evidence-gap answer; do not fall back to model parametric knowledge for NASA claims.

## Output contract

Answer fields: status, answer_summary, factual_statements[], interpretation[], limitations[], evidence[], generated_by, model_id, prompt_version, generated_at. Each factual statement has one or more evidence IDs; interpretation is explicitly labelled. If a conclusion is not supported, say insufficient retrieved evidence. Output text is labelled Cosmos-generated and not NASA reviewed or endorsed.

## Launch gate

Before a public assistant can summarize NASA-derived records, resolve the current NASA AI/SI media guidance for the specific API data and output citation behavior. Keep the capability feature-flagged off in production until the decision is documented in an ADR and verified against current NASA terms. This is a product/policy dependency, not a code guess.

## Related documents

[Provider Design](LLM_PROVIDER_DESIGN.md), [Context Engineering](CONTEXT_ENGINEERING.md), [Retrieval](RETRIEVAL_ARCHITECTURE.md), [Evaluation](AI_EVALUATION.md), [Guardrails](AI_GUARDRAILS.md).
