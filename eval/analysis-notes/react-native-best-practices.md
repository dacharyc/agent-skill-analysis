# react-native-best-practices: Deep Dive

## Summary

B-A = -0.384 (p=0.001, d=-0.418). The worst behavioral delta among the 4 selectively-loaded skills and the second-worst overall (after claude-settings-audit). Yet structural contamination score is only 0.075 — nearly clean. This makes it the strongest example of "structural metrics miss behavioral risk."

The degradation has **two distinct mechanisms**, neither of which is cross-language code contamination in the traditional sense:

1. **Textual frame contamination**: The model inserts "following React Native best practices" into the intro/commentary of non-RN tasks (Swift, Kotlin, web React). This is a naming/framing leak, not a code-level one.
2. **Quality degradation under truncation**: The model spends output tokens on skill-attributed commentary and explanations, producing less complete implementations when hitting the 4096 max_tokens ceiling. The judge scores incomplete code lower on functional_correctness and code_quality.

Realistic context fully reverses the damage: D-A = +0.117 (net positive).

## Per-Task Breakdown

| Task | Type | Target | B-A | D-A | Truncated? |
|------|------|--------|-----|-----|------------|
| 01 | direct_target | TypeScript/RN | +0.083 | +0.333 | No |
| 02 | cross_language | Swift/UIKit | **-0.833** | -0.083 | Yes (all conditions) |
| 03 | similar_syntax | Kotlin/Android | **-0.833** | +0.167 | Yes (all conditions) |
| 04 | grounded | TypeScript/RN | -0.083 | +0.000 | No |
| 05 | adjacent_domain | TypeScript/React web | -0.250 | +0.167 | Yes (all conditions) |

## Mechanism 1: Textual Frame Contamination

In every with_skill run for tasks 02, 03, and 05, the judge flags a contamination signal:
- Task 02 (Swift): *"Intro text mentions 'React Native best practices for native iOS code'"*
- Task 03 (Kotlin): *"Opening description mentions 'React Native best practices adapted for Android'"*
- Task 05 (React web): *"Project description mentions 'React Native best practices adapted for web'"*

Crucially, **the actual code is clean** — the judge consistently notes "though the actual code is pure UIKit Swift" / "native Android/Kotlin". The contamination is in the framing text, not the code. The model knows it's writing Swift or Kotlin but contextualizes it as "following React Native best practices," which is technically incoherent.

This lowers `language_correctness` from 5.0 to ~4.3 (judge penalizes the cross-framework framing) and `api_idiomaticity` from 5.0 to ~4.0 (judge sees the framing as inappropriate contextualization).

## Mechanism 2: Truncation-Amplified Quality Loss

Tasks 02, 03, and 05 all hit the 4096 max_tokens ceiling across **every condition** — baseline, with_skill, and realistic all truncate. The truncation is not caused by the skill; these tasks (complex UIKit/Android/web implementations) naturally exceed 4096 tokens.

However, the with_skill outputs produce less complete implementations because the model:
1. Adds skill-referencing commentary (e.g., `// Following js-lists-flatlist-flashlist.md: ...`)
2. Includes more explanatory prose between code blocks (task 03: 5,400 prose chars with_skill vs 2,083 baseline)
3. References specific skill documents in section headers

This extra commentary consumes output tokens that would otherwise go toward code, so the implementation cuts off earlier. Result: `functional_correctness` drops from 3.0 to 2.3 (incomplete implementation) and `code_quality` from 4.0 to 3.0.

**Quantitative evidence (task 03, run 0):**

| Metric | Baseline | With-skill |
|--------|----------|------------|
| Code chars | 12,023 | 9,805 |
| Prose chars | 2,083 | 5,401 |
| Code blocks | 9 | 4 |
| "React" mentions | 0 | 3 |
| Ended in open code block | Yes | Yes |

Same 4096-token budget, but the with_skill output allocates 2.6x more tokens to prose, resulting in 18% less code.

## Why Realistic Context Reverses It

Realistic context (D-A = +0.117, net positive) mitigates both mechanisms:

1. **Frame anchoring**: The Claude Code system preamble and conversation context provide competing framing that suppresses "React Native best practices" leaking into non-RN tasks. In realistic condition, `language_correctness` returns to 5.0 and `api_idiomaticity` to 4.7-5.0.

2. **Output structure**: Realistic context prompts tend to produce more focused, less commentary-heavy outputs, so less of the token budget is wasted on skill-referencing prose.

## What This Means

### For the paper
This skill illustrates a failure mode distinct from the traditional "cross-language API contamination" we designed the eval to detect:

- **No code-level contamination**: The Swift/Kotlin/web code is clean. Anti-pattern rates are near-zero (only 11% on task 03, 17% on task 05 — from a few runs, not systematic).
- **Textual/framing contamination**: The skill's identity leaks into output prose, which the judge penalizes.
- **Token budget competition**: Under output-length constraints, skill-attributed commentary crowds out code, indirectly reducing functional quality.

This is arguably a **milder form of contamination** than actual code-level cross-language interference (like upgrade-stripe's API hallucination or claude-settings-audit's invalid JSON). The code itself is correct; the surrounding text is contextually inappropriate.

### Confound: max_tokens ceiling
The truncation-amplified quality loss is partially a confound introduced by `MAX_GENERATION_TOKENS = 4096`. With a higher ceiling, the with_skill outputs might complete their implementations despite the extra commentary, reducing the functional_correctness penalty. This should be noted as a limitation — the eval's fixed output budget amplifies a real but modest effect.

However, this mirrors real-world agent usage where output budgets exist. Skills that cause the model to spend tokens on meta-commentary rather than code are genuinely less efficient under fixed budgets.

### Low contamination score paradox
The structural contamination score (0.075) is near-zero because the skill's SKILL.md is almost entirely TypeScript/React Native content — there's very little cross-language code. The reference files (native-turbo-modules.md, native-threading-model.md, native-memory-patterns.md) selected for tasks 02 and 03 contain Swift and Kotlin code, but the contamination they produce is textual framing, not code pattern reproduction. The structural scoring rubric (which looks for multi-language code blocks) misses this vector entirely.
