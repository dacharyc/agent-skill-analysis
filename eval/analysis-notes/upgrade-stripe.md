# upgrade-stripe: Realistic Context Amplifies Degradation

## Summary

The upgrade-stripe skill (contamination score 0.93, highest in dataset) shows a modest B-A delta (-0.117, not significant at p=0.108) but a much larger D-A delta (-0.500, significant at p≈0.0, Cohen's d = -0.793). Realistic context amplifies rather than mitigates the skill's effect — the opposite of the expected pattern. The mitigation ratio is -3.286 (3.3x worse under realistic context).

## Per-Task Breakdown

| Task | Type | Language | B-A Δ | D-A Δ | Condition D failure mode |
|------|------|----------|-------|-------|-------------------------|
| 01 | direct_target | python | 0.000 | -0.833 | Hallucinated APIs: `StripeErrorWithParamCode`, fake `stripe_version` kwarg, async-declared but sync calls |
| 02 | cross_language | go | -0.167 | -0.666 | Non-idiomatic global state, fabricated v81 version, non-existent `SetStripeVersion()` method |
| 03 | similar_syntax | javascript | -0.167 | -0.334 | Manual crypto reimplementation instead of SDK method, TypeScript option in JS |
| 04 | grounded | python | +0.167 | 0.000 | Neutral — grounded code context anchors the model |
| 05 | adjacent_domain | ruby | -0.417 | -0.667 | Truncation + idiomaticity drops |

## Key Observation: API Hallucination, Not Cross-Language Contamination

The Condition D failure mode is not the expected cross-contamination (mixing Python syntax into Go, etc.). Instead, the model **hallucinates plausible-sounding but non-existent API patterns**:
- `StripeErrorWithParamCode` — sounds real, doesn't exist
- `stripe_version=` as a per-call kwarg — real concept, wrong API surface
- `params.SetStripeVersion()` in Go — invented method
- `stripe-go/v81` — fabricated version number (real versions are v76-v79)

These hallucinations are thematically consistent with the skill's detailed API versioning content. The skill teaches extensively about version pinning, migration patterns, and per-request version overrides. Under realistic context (with its richer system prompt), the model appears to over-engineer version management, inventing API patterns that "should" exist based on the skill's conceptual framing.

## Why Grounded Task (04) Is Immune

Task 04 provides actual Python code to modify. With concrete code context, the model stays focused on the specific changes requested (update version string, update Stripe.js URL) and doesn't attempt to demonstrate sophisticated version management patterns. This is consistent with the broader finding that grounded tasks provide anchoring against hallucination.

## Statistical Detail

| Metric | B-A | D-A |
|--------|-----|-----|
| Mean delta | -0.117 | -0.500 |
| Cohen's d | -0.216 | -0.793 |
| t-stat | -1.606 | -4.472 |
| p-value | 0.108 | ≈0.000 |
| Wilcoxon p | 0.203 | — |
| Mitigation ratio | — | -3.286 |

## Context

- Smallest skill in dataset by token overhead (1,527 tokens)
- Highest contamination score (0.93) — Python, Ruby, JavaScript examples for same Stripe API
- Despite high contamination score, the B-A effect is modest and not statistically significant
- The D-A amplification is the largest in the dataset and is the only skill where realistic context significantly worsens performance

## Implications

1. The B-A result actually challenges the structural contamination score — the highest-risk skill shows only modest degradation when the skill is the only context
2. The D-A amplification may reflect an interaction between skill content density and system prompt complexity, not contamination per se
3. The API hallucination failure mode is distinct from cross-language contamination and may warrant separate analysis
4. Grounded tasks (with existing code context) appear to provide anchoring against both contamination and hallucination
