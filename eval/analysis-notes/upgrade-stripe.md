# upgrade-stripe: Realistic Context Amplifies Degradation

## Summary

The upgrade-stripe skill (contamination score 0.93, highest in dataset) shows a modest B-A delta (-0.117, not significant at p=0.108) but a larger D-A delta (-0.383). Realistic context amplifies rather than mitigates the skill's effect — the opposite of the expected pattern.

## Per-Task Breakdown

| Task | Type | Language | B-A Δ | D-A Δ | Condition D failure mode |
|------|------|----------|-------|-------|-------------------------|
| 01 | direct_target | python | 0.000 | -0.250 | Hallucinated APIs: `StripeErrorWithParamCode`, `e.user_message` misuse, module-level globals vs StripeClient |
| 02 | cross_language | go | -0.167 | -0.666 | Non-idiomatic global state, fabricated v81 version, non-existent `SetStripeVersion()` method |
| 03 | similar_syntax | javascript | -0.167 | -0.334 | Manual crypto reimplementation instead of SDK method, TypeScript option in JS |
| 04 | grounded | python | +0.167 | 0.000 | Neutral — grounded code context anchors the model |
| 05 | adjacent_domain | ruby | -0.417 | -0.667 | Truncation + idiomaticity drops |

## Codebase Snippet Confound: Task 01 Investigation

Task 01's original realistic condition used the default Python codebase snippet (FastAPI + async SQLAlchemy), which contains `async def`, `AsyncSession`, and `await` patterns. The judge flagged async-related signals ("async-declared but sync calls") as contamination, producing a D-A composite of -0.833 — the worst in the skill.

**Hypothesis**: The async patterns in the codebase snippet, not the skill, were driving the model to declare methods as async while calling the synchronous Stripe SDK.

**Test**: Re-ran task 01 with `codebase_variant: python_sync` — a Flask + SQLAlchemy (synchronous) codebase snippet with no async/await patterns.

**Result**: D-A composite dropped from -0.833 to -0.250. The async-related signals disappeared entirely, confirming the confound. However, the realistic condition still degrades — the judge now flags a different set of signals (fabricated exception classes, method attribute misuse), indicating a residual skill-interaction effect independent of the codebase snippet.

| Metric | Before (async snippet) | After (sync snippet) |
|--------|----------------------|---------------------|
| Task 01 D-A composite | -0.833 | -0.250 |
| Task 01 judge signals (realistic) | async calls, fake kwargs | `StripeErrorWithParamCode`, `e.user_message` |
| Task 01 anti-pattern hits | 0 | 0 |
| Skill-level D-A | -0.500 | -0.383 |

The skill-level D-A improved from -0.500 to -0.383, a 23% reduction, attributable entirely to task 01. The remaining degradation is distributed across tasks 02, 03, and 05.

## Key Observation: API Hallucination, Not Cross-Language Contamination

The Condition D failure mode is not the expected cross-contamination (mixing Python syntax into Go, etc.). Instead, the model **hallucinates plausible-sounding but non-existent API patterns**:
- `StripeErrorWithParamCode` — sounds real, doesn't exist
- `e.user_message` on `InvalidRequestError` — real attribute on `CardError` but misapplied
- `params.SetStripeVersion()` in Go — invented method
- `stripe-go/v81` — fabricated version number (real versions are v76-v79)

These hallucinations are thematically consistent with the skill's detailed API versioning content. The skill teaches extensively about version pinning, migration patterns, and per-request version overrides. Under realistic context (with its richer system prompt), the model appears to over-engineer version management, inventing API patterns that "should" exist based on the skill's conceptual framing.

## Why Grounded Task (04) Is Immune

Task 04 provides actual Python code to modify. With concrete code context, the model stays focused on the specific changes requested (update version string, update Stripe.js URL) and doesn't attempt to demonstrate sophisticated version management patterns. This is consistent with the broader finding that grounded tasks provide anchoring against hallucination.

## Statistical Detail

| Metric | B-A | D-A |
|--------|-----|-----|
| Mean delta | -0.117 | -0.383 |

## Context

- Smallest skill in dataset by token overhead (1,527 tokens)
- Highest contamination score (0.93) — Python, Ruby, JavaScript examples for same Stripe API
- Despite high contamination score, the B-A effect is modest and not statistically significant
- The D-A amplification is the largest in the dataset; realistic context worsens rather than mitigates performance
- Task 01's async codebase snippet confound has been resolved; remaining degradation is genuine skill-interaction effect

## Implications

1. The B-A result actually challenges the structural contamination score — the highest-risk skill shows only modest degradation when the skill is the only context
2. **Codebase snippets can confound Condition D results.** The async Python snippet contributed ~70% of task 01's original D-A degradation. Other tasks with language-specific codebase snippets may have similar confounds. The `codebase_variant` mechanism allows targeted re-testing.
3. The D-A amplification may reflect an interaction between skill content density and system prompt complexity, not contamination per se
4. The API hallucination failure mode is distinct from cross-language contamination and may warrant separate analysis
5. Grounded tasks (with existing code context) appear to provide anchoring against both contamination and hallucination
