# doc-coauthoring: Behavioral Override Finding

## Summary

The doc-coauthoring skill (Anthropic, contamination score 0.00, negative control) produced the largest behavioral delta in the eval (-3.183, Cohen's d = -4.47) despite having zero cross-contamination risk. This is not a control failure — it's evidence of a different phenomenon: **behavioral override**.

## What Happened

Across all 5 tasks and all 3 runs, 14 of 15 `with_skill` conditions scored all-1s from the judge. The consistent assessment: "No code was generated at all. The response consists entirely of clarifying questions."

The one exception (run1/task01) scored 4/3/2/3 but exhibited tool-calling XML contamination (`<function_calls><invoke name="create_file">` syntax in the output).

Baselines scored 4-5 across the board. Realistic context (Condition D) also scored 4-5, completely suppressing the effect.

## Root Cause

The doc-coauthoring SKILL.md is a highly structured collaborative workflow that explicitly instructs the model to:

1. **Not write anything immediately** — start with clarifying questions (Stage 1: Context Gathering)
2. **Offer a 3-stage workflow** before doing any work
3. **Use `str_replace` and `create_file`** for drafting (tool-calling patterns)
4. Trigger on keywords like "write", "draft", "create", "spec" — which match our task prompts

When loaded as the full system prompt (Condition B), the model faithfully follows the skill's instructions and launches into the collaborative workflow instead of generating code. The skill is **working exactly as designed** — it's just incompatible with the eval's expectation of direct code output.

## Why Realistic Context (D) Fixes It

The CC system preamble in Condition D includes "respond with code directly" and "when asked to write code, output the code itself", which overrides the skill's workflow instructions. The skill's behavioral influence is diluted by competing system prompt instructions.

## Why It's Excluded from Contamination Aggregates

- Measures **behavioral override** (skill changes response mode), not **cross-contamination** (skill causes wrong-language patterns)
- The -3.183 delta is 15x larger than the next-worst skill, dominating all aggregate statistics
- Zero contamination score means it distorts the structural-behavioral correlation
- Including it in the control group (n=2) makes the controls appear to have the worst contamination effect, which is misleading

## Potential Framing for Paper

Options to consider:

1. **Separate case study**: Report as an example of "behavioral override" — a category of skill effect distinct from cross-contamination. Skills that change the model's response mode rather than its code patterns.

2. **Limitations/Future Work note**: Skills with strong workflow instructions can dominate model behavior when loaded as system prompts. This is a feature, not a bug, but creates a measurement challenge for contamination evals.

3. **New finding category**: "Behavioral contamination" as a third risk category alongside language contamination and context dilution. Non-code skills that contain strong workflow directives may be the highest-impact category because they don't just degrade code — they prevent code generation entirely.

4. **Positive framing**: The skill is remarkably effective at its stated purpose. The Condition D result shows that the CC system prompt provides sufficient guardrails in production. This could be framed as evidence that the agent framework's system prompt architecture provides resilience against behavioral override from skills.

## Key Data Points

| Metric | Value |
|--------|-------|
| B-A delta (composite) | -3.183 |
| D-A delta (composite) | -0.183 |
| Cohen's d | -4.467 |
| Wilcoxon p | 0.0007 |
| Mitigation ratio (B→D) | ~94% |
| with_skill runs scoring all-1s | 14/15 |
| Contamination score | 0.00 |
| Risk level | control |

## Impact on Aggregate Stats

| Metric | With doc-coauthoring | Without |
|--------|---------------------|---------|
| Correlation (structural vs behavioral) | 0.374 | -0.125 |
| Control group mean delta | -1.658 | -0.133 |
| Overall mean delta (skill-only) | -0.204 | -0.047 |
| n_skills in aggregates | 20 | 19 |
