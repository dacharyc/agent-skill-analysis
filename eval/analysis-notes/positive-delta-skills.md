# Positive-Delta Skills: Novel Knowledge Transfer

## Summary

Two skills show statistically or practically notable improvement when loaded: gemini-api-dev (+0.200, B-A and D-A identical) and wiki-agents-md (+0.200 B-A, p=0.018, d=0.701). Both improvements are driven by the skill providing genuinely novel knowledge the model lacks from training data. Both show the same pattern: positive delta on tasks requiring novel knowledge, neutral or negative on tasks where the model already knows the answer.

## gemini-api-dev: Post-Training API Knowledge

The model's training data predates the Gemini SDK rename from `google-generativeai` to `google-genai`. Without the skill, every baseline run uses deprecated patterns: `import google.generativeai as genai`, `genai.GenerativeModel()`, `genai.configure()`, and obsolete model names like `gemini-2.0-flash-exp`.

### Per-Task Breakdown

| Task | Type | Language | Base | Skill | B-A | D-A | Mechanism |
|------|------|----------|------|-------|-----|-----|-----------|
| 01 | direct_target | python | 3.67 | 4.50 | +0.833 | +0.750 | Skill teaches current SDK: `from google import genai`, `genai.Client()`, `client.models.generate_content()`, `gemini-3-flash-preview` |
| 02 | cross_language | rust | 4.42 | 4.83 | +0.417 | +0.250 | Baseline uses wrong model name. Skill provides correct name. No SDK contamination into Rust (raw HTTP, no SDK to confuse) |
| 03 | similar_syntax | typescript | 3.75 | 4.00 | +0.250 | +0.500 | Baseline uses deprecated `@google/generative-ai`. Skill teaches `@google/genai`. Judge notes some Python→TS contamination (`role: "function"` pattern, string types instead of Type enum) |
| 04 | grounded | python | **5.00** | 4.50 | **-0.500** | -0.333 | Baseline already perfect — concrete deprecated code anchors the model. Skill introduces API pattern noise (`Part.from_text()` wrapping, slightly non-idiomatic patterns) |
| 05 | adjacent_domain | go | 3.25 | 3.25 | 0.000 | -0.167 | No effect on B-A. Slight D-A degradation |

### Key Observations

1. **Baseline anti-pattern analysis**: All 3 baseline runs for task 01 hit 3/5 anti-patterns (deprecated SDK import, GenerativeModel class, old model names). The model genuinely does not know the current Gemini API.

2. **With-skill pattern analysis**: All 9 with_skill runs for tasks 01-03 hit 5/5 expected patterns and 0/5 anti-patterns. The skill successfully transfers novel API knowledge.

3. **Grounded task immunity (reversed)**: Task 04 provides concrete deprecated code to migrate. The model produces perfect migration output (5.00) without the skill — the specific code context provides enough signal. Loading the skill then introduces subtle API deviations (Part.from_text wrapping, non-standard config patterns) that the judge marks down to 4.50. **Concrete code context is a stronger anchor than skill content.**

4. **Cross-language transfer works**: Task 02 (Rust) shows the skill helps by providing the correct model name (`gemini-3-flash-preview`) without contaminating the Rust HTTP client code with Python/JS SDK patterns. The skill's multi-language examples transfer the factual API knowledge (endpoint URLs, model names) without the syntactic contamination.

5. **Similar-syntax shows contamination tension**: Task 03 (TypeScript) shows improvement but the judge notes Python SDK patterns bleeding in (`role: "function"` instead of `role: "user"` for function responses, raw string types instead of SDK Type enum). The skill helps with the correct package name and API surface but introduces subtle Python contamination — a net positive overall but with contamination signals present.

### Implications for the Paper

This is a clear case study illustrating that **contamination score and behavioral impact can be orthogonal**. The skill has a contamination score of 0.55 (high risk, multi-language API examples), yet it produces a +0.200 behavioral improvement. The "contaminating" multi-language content is precisely what makes the skill useful — it teaches the model the correct API patterns across languages.

The paper's case study of gemini-api-dev as a contamination risk example needs reframing: structurally it is high-risk (Python/JS/Go/Java examples for the same API), but behaviorally it is net-positive because the content is genuinely novel.

## wiki-agents-md: Specification Template Knowledge

The skill teaches the AGENTS.md specification structure (6 core areas, boundaries section, CLAUDE.md companion), which the model doesn't reliably produce from training data alone.

### Per-Task Breakdown

| Task | Type | Language | Base | Skill | B-A | D-A | Mechanism |
|------|------|----------|------|-------|-----|-----|-----------|
| 01 | direct_target | markdown | 4.50 | 5.00 | +0.500 | +0.500 | Baseline truncated, missing core areas. Skill teaches complete specification → all 6 areas, boundaries section |
| 02 | cross_language | markdown (Rust) | 4.92 | 5.00 | +0.083 | +0.083 | Both excellent. Model already handles Rust AGENTS.md well |
| 03 | similar_syntax | markdown (TS/pnpm) | 4.58 | 5.00 | +0.417 | +0.417 | Baseline truncated. Skill → complete output. Note: `npm` anti-pattern fires in ALL conditions (baseline, skill, realistic) — likely false positive from mentioning npm in context |
| 04 | grounded | markdown | 5.00 | 5.00 | 0.000 | -0.833 | Both perfect under B-A. Realistic context degrades significantly |
| 05 | adjacent_domain | markdown | 5.00 | 5.00 | 0.000 | -0.500 | Both perfect under B-A. Realistic context degrades |

### Key Observations

1. **Completeness, not correctness**: The improvement is about structural completeness. Baselines produce good AGENTS.md content but get truncated or miss sections. The skill anchors the expected structure (6 core areas, boundaries, CLAUDE.md companion).

2. **Statistically significant**: B-A delta of +0.200 with Wilcoxon p=0.018 and Cohen's d=0.701 (medium-large). This is one of only 4 statistically significant results in the entire dataset.

3. **D-A degradation on perfect-baseline tasks**: Tasks 04 and 05, where baseline is already 5.00, show large negative D-A deltas (-0.833 and -0.500). Realistic context (CC system preamble + codebase context) hurts quality on tasks where the model already performs perfectly. This explains why the overall D-A drops to -0.067 — the realistic context noise on easy tasks offsets the gains on harder tasks.

4. **False positive pattern**: The `go build|go test` anti-pattern fires across ALL conditions for the Rust task (02), including baseline with no skill loaded. This is likely the model mentioning Go in a comparison context within the AGENTS.md, not actual contamination. The judge gives 5/5/5/5 regardless, confirming it's a pattern matching artifact.

## Cross-Cutting Finding: Skill Novelty Hypothesis

Both skills demonstrate the same pattern:

| Knowledge State | B-A Delta | Examples |
|----------------|-----------|----------|
| Model lacks knowledge, skill provides it | **Positive** (+0.25 to +0.83) | Gemini SDK rename, AGENTS.md specification structure |
| Model already knows the answer | **Neutral to negative** (-0.50 to 0.00) | Grounded migration task, simple AGENTS.md generation |

**High-novelty skills that teach the model post-training or specification knowledge produce net-positive behavioral effects.** The positive delta is concentrated on direct_target and similar_syntax tasks — exactly the tasks where the skill's domain knowledge is most relevant.

This suggests a practical dimension for skill evaluation:
- **Skill novelty** (does the skill teach something the model doesn't know?) may be a better predictor of behavioral impact than contamination score
- Skills containing post-training API changes, new specification formats, or proprietary patterns are likely to be net-positive
- Skills containing only knowledge already in the model's training data may be neutral or net-negative (adding context noise without adding knowledge)

### Tension with Contamination Framing

The gemini-api-dev skill has a contamination score of 0.55 specifically because it contains multi-language API examples. But this is exactly why it's useful — the model needs the Python, TypeScript, Go, and Java examples to learn the correct patterns for each language. The "contaminating" content IS the value.

This means the paper's structural contamination analysis and behavioral eval tell different stories for high-novelty skills:
- Structural: "This skill has high cross-contamination risk due to multi-language code"
- Behavioral: "This skill improves code quality because it teaches the model API patterns it doesn't know"

The resolution may be that **contamination risk is conditional on knowledge novelty**: multi-language examples are a contamination risk when the model already knows the API (the examples compete with training data), but a knowledge transfer mechanism when the model doesn't know the API (the examples teach rather than confuse).
