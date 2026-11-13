# AI Evaluation

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Specification complete; generation release gate remains open  
**Purpose:** Define repeatable pre-release evaluation for factuality, citations, safety, and regressions.  
**Scope:** Covers the proposed AI Evaluation behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  


## Evaluation set

Maintain a versioned, reviewed set of at least 100 questions across APOD, NeoWs, DONKI, EONET, NASA media, mixed comparison, no-answer, stale-data, and malformed-input cases. Each case records allowed evidence IDs, expected facts/units, acceptable uncertainty, disallowed claims, and expected tool set. Include at least 20 adversarial examples and 20 unanswerable questions. Keep copyrighted source excerpts to the minimum needed for tests and use synthetic non-sensitive prompt-injection strings.

## Metrics and release thresholds

| Metric | Release threshold |
|---|---:|
| Citation validity (all generated IDs are retrieved evidence) | 100% deterministic checks |
| Required answer schema validity | ≥99%; invalid response is not released |
| Unsupported factual claim rate | 0 high-confidence unsupported claims in the curated release suite |
| Unit/date/classification preservation | ≥98% across reviewed cases and 100% for safety-critical labeled checks |
| Correct evidence retrieval recall@10 | ≥95% for the curated answerable set |
| Correctly abstains on no-evidence questions | 100% |
| Prompt injection attempts that change policy or reveal protected data | 0 |
| Tool allowlist violations / side effects outside the chosen operation | 0 |

Metrics are a gate plus a human review of representative failures; averages must not hide severe individual errors.

## Test layers

- Deterministic unit tests validate output schema, citation IDs, evidence allowlist, truncation, permissions, and budget handling without an LLM.
- Mocked provider contract tests cover structured output success, refusal, incomplete finish, malformed JSON, timeout, 429, 5xx, and usage absent.
- Offline evaluations run on fixtures with the exact prompt and model configuration candidate.
- Optional live provider evaluations run manually or in protected scheduled CI with a dedicated test key, fixed small budget, and no production data.
- Human review records evaluator, date, model ID, prompt checksum, rubric, examples, and accepted/blocked findings.

## Reproducibility and safety

Model outputs can vary; store exact model identifier, provider route where available, prompt version/hash, request settings, evidence IDs/hashes, and usage metadata. Do not claim deterministic reproducibility from a seed unless provider docs confirm it. Never put secrets or user production conversations in eval fixtures.

## Launch gate

Before public NASA-derived generated answers: complete legal/policy review of current NASA AI/SI media guidance and cited output format, documenting permitted use. If unresolved, leave assistant generation disabled and ship record search/report templates without model-generated NASA summaries.

## Related documents

[AI Architecture](AI_ARCHITECTURE.md), [Guardrails](AI_GUARDRAILS.md), [Success Metrics](../00-project/SUCCESS_METRICS.md).
