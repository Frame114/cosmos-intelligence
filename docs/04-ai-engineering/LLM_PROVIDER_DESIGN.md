# LLM Provider Design

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 specification baseline  
**Purpose:** Define model transport abstraction and operational controls.  
**Scope:** Covers the proposed LLM Provider Design behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Interface

Application code depends on a provider protocol with one operation: complete(messages, response_schema, tool_definitions, generation_options, deadline) returning normalized content, tool calls, finish reason, provider request ID, model ID, and usage metadata. The OpenRouter adapter implements it using HTTPS POST https://openrouter.ai/api/v1/chat/completions and Bearer authentication. API route and domain logic never import OpenRouter-specific response models.

## Configuration and model selection

Runtime settings include OpenRouter key from secret file, exact model ID, provider routing preferences if any, request timeout, max output tokens, temperature, daily spend/token budgets, fallback allowlist, and feature flag. Do not default silently to a model name in source code. At deployment, choose a model based on current supported-parameter metadata for structured outputs and tool calling, quality evaluation, context size, latency, price, data policy, and availability. Store the selected model ID with each generation.

Provider fallback is allowed only when the fallback supports the exact required response schema and data handling policy. Do not retry an ambiguous billable timeout unless the provider exposes and documents safe idempotency behavior. Use bounded retry for explicitly transient 429/5xx errors and account for potential double billing.

## Structured outputs and tool calls

Prefer strict JSON Schema response_format when the selected model/provider route supports it and can fail loudly when unsupported. Otherwise use a forced single schema tool call to collect structured output, or deterministic JSON mode plus local validation. Provider support varies, so always validate with Pydantic locally. Model tool calls are requests only: the application validates and runs allowlisted tools, then sends compact results back if another completion is required.

## Timeouts, usage, and cost

Set a provider deadline (initial default 30 seconds), cap input/output tokens, cap concurrent completions, and store returned token/cost metadata when available. Track usage by user pseudonym, model, prompt version, request ID, and day. If actual cost is not returned and pricing is not locked/current, report usage without an invented monetary figure.

## Security

Store key as a secret, redact Authorization and provider response bodies, prevent prompt content from appearing in request logs, set a strict timeout, and never proxy model output as executable HTML. OpenRouter or model-provider outage is isolated from non-AI routes.

## Official sources

[OpenRouter Chat Completions API](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion), [OpenRouter structured output guidance](https://openrouter.ai/docs/guides/features/structured-outputs), [models/capability metadata](https://openrouter.ai/models).

## Related documents

[AI Architecture](AI_ARCHITECTURE.md), [Secrets Management](../06-security/SECRETS_MANAGEMENT.md), [AI Evaluation](AI_EVALUATION.md).
