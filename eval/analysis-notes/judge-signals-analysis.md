# Judge Contamination Signals & Brief Assessments Analysis

## Summary

Analysis of the LLM judge's `contamination_signals` and `brief_assessments` across all 19 skills (300 task-skill pairs × 3 conditions × 3 runs = 2,700 judgments) reveals three key findings: (1) a **pervasive truncation confound** — 63.9% of baseline assessments mention truncation, meaning many B-A deltas are measured against an already-degraded baseline; (2) **substantial baseline signal rates** (0.54 signals/run without any skill loaded), indicating the model has inherent quality issues on many tasks; and (3) **three distinct skill-specific patterns** that illuminate how contamination mechanisms operate in practice.

## Aggregate Signal Counts

### By condition

| Condition | Signals | Runs | Signals/run |
|-----------|---------|------|-------------|
| Baseline | 162 | 300 | 0.54 |
| With-skill | 232 | 300 | 0.77 |
| Realistic | 255 | 300 | 0.85 |

Skills increase contamination signals by ~43% over baseline. Surprisingly, realistic context shows *more* signals than with-skill, not fewer. This is driven by a few skills (notably upgrade-stripe) where realistic context amplifies rather than mitigates.

*Note: Realistic count was originally 259 before resolving a codebase snippet confound in upgrade-stripe task 01 (async Python snippet inflated signals). See Pattern 2 below.*

### By skill (top 5)

| Skill | Total signals | B-A |
|-------|--------------|-----|
| copilot-sdk | 226 | -0.100 |
| upgrade-stripe | 41 | -0.117 |
| monitoring-observability | 42 | -0.233 |
| react-native-best-practices | 40 | -0.384 |
| provider-resources | 38 | -0.317 |

copilot-sdk dominates signal count but has modest B-A, because most of its signals appear in ALL conditions (the model doesn't know this SDK regardless of skill presence).

### Signal categories (across all conditions)

| Category | Count | Description |
|----------|-------|-------------|
| api_hallucination | 118 | Fabricated methods, non-existent APIs |
| cross_framework | 86 | Wrong framework patterns applied |
| truncation | 22 | Explicit truncation flags |
| invalid_syntax | 20 | Syntax errors in output |
| other | 407 | Uncategorized signals |

## Assessment Themes

### Truncation is pervasive

| Condition | Assessments mentioning "truncat" | Total | Rate |
|-----------|--------------------------------|-------|------|
| Baseline | 182 | 285 | 63.9% |
| With-skill | 177 | 285 | 62.0% |
| Realistic | 138 | 285 | 48.4% |

Nearly two-thirds of baseline assessments flag truncation. This is a systemic artifact of the 4096-token output ceiling, not a skill effect. Realistic context reduces truncation mentions, possibly because the system preamble helps the model generate more focused outputs.

**Truncation delta vs B-A delta**: r = 0.296 (weak positive). Skills that increase truncation relative to baseline tend to show worse B-A deltas, but the correlation is weak. Only 6 of 23 task-skill pairs show MORE truncation with skill; 17 show less or the same.

### Other common assessment themes

| Theme | Baseline | With-skill | Realistic |
|-------|----------|------------|-----------|
| "correct language" mentioned | 112 | 118 | 118 |
| "fabricated" or "hallucinated" API | 18 | 32 | 29 |
| "incomplete" implementation | 89 | 85 | 72 |

## Three Illuminating Skill Patterns

### Pattern 1: copilot-sdk — Pre-existing hallucination

| Condition | Signals | Example |
|-----------|---------|---------|
| Baseline | 67 | Fabricated `CopilotClient.chat()`, `CopilotRuntime.configure()` |
| With-skill | 84 | Same fabrications plus skill-influenced method names |
| Realistic | 75 | Slightly fewer fabrications with context grounding |

The model hallucinates Copilot SDK APIs in ALL conditions. This isn't contamination — the model simply doesn't know this SDK (it's post-training knowledge). The skill slightly worsens fabrication count (+25%) by making the model more confident in its hallucinations, but the fundamental problem is pre-existing. This is consistent with the exploratory **novelty amplification** pattern: the skill provides partial knowledge that makes confident hallucination more likely.

### Pattern 2: upgrade-stripe — Fabrication escalation (with codebase snippet confound)

| Condition | Signals | Example |
|-----------|---------|---------|
| Baseline | 1 | Minor version mismatch |
| With-skill | 12 | Fabricated migration helpers, non-existent `stripe.migrate()` |
| Realistic | 28 | Fabricated exception classes, misapplied attributes, version fabrication |

*Note: The original realistic signal count was 32, inflated by a codebase snippet confound in task 01. The default Python snippet uses async patterns (FastAPI + AsyncSession), which caused the model to declare methods as async while calling the synchronous Stripe SDK. After re-running task 01 with a synchronous codebase snippet (`codebase_variant: python_sync`), task 01's realistic signals dropped from 12 (async-related) to 8 (fabrication-related), and the skill-level D-A composite improved from -0.500 to -0.383. See [upgrade-stripe.md](upgrade-stripe.md) for the full investigation.*

The escalation pattern still holds: the skill teaches enough Stripe API surface to make the model more confidently wrong. Realistic context amplifies this — the conversational framing gives the model more room to elaborate on fabricated methods.

This confirms the paper's observation that upgrade-stripe is an exception to the mitigation pattern, and reveals the mechanism: **API familiarity breeds confident hallucination**. The model goes from "I'm not sure about this API" (baseline, 1 signal) to "I know this API" (with-skill, 12 signals) to "Let me show you the full migration approach" (realistic, 28 signals). The escalation is partially attributable to codebase snippet interaction (~14% of the original realistic signal count), but the majority reflects genuine skill-induced fabrication.

### Pattern 3: gemini-api-dev — Error shift, not error reduction

| Condition | Signal type | Example |
|-----------|------------|---------|
| Baseline | Old SDK usage | `genai.GenerativeModel()` (deprecated pattern) |
| With-skill | Cross-SDK mixing | Blending old `genai.*` with new `google.genai.*` patterns |
| Realistic | Similar cross-SDK | Same cross-SDK issues but slightly better targeted |

The skill successfully teaches the model about the new Gemini API — baseline signals about using the deprecated SDK disappear. But they're replaced by new signals about mixing old and new SDK patterns. The skill fixes one problem but introduces a different one: the model now knows about both SDKs and blends them incorrectly.

This is consistent with the exploratory **novelty amplification** pattern: the skill provides genuinely useful new knowledge (new Gemini SDK) but the partial knowledge creates new error modes (cross-SDK contamination).

## Implications

### For the truncation confound

The 63.9% baseline truncation rate means our eval is largely measuring "quality of truncated code" rather than "quality of complete code." This raises the question: **is truncation masking a stronger degradation signal through a floor effect?**

A floor-effect analysis answers this definitively: **no**. Truncation slightly *inflates* apparent degradation rather than masking it.

| Group | N tasks | Mean B-A | Mean |B-A| | SD(B-A) |
|-------|---------|----------|---------|---------|
| Baseline truncated (≥2/3 runs at ceiling) | 24 | -0.104 | 0.236 | 0.326 |
| Baseline not truncated | 71 | -0.072 | 0.245 | 0.378 |
| Both conditions truncated | 22 | **-0.140** | 0.231 | — |
| Neither condition truncated (clean) | 56 | **-0.046** | 0.251 | 0.402 |

Key findings:

1. **No floor effect on deltas**: The |B-A| difference between truncated and non-truncated groups is only 0.009 — both conditions are degraded similarly by truncation, preserving the delta.

2. **Truncation amplifies apparent degradation**: The 22 tasks where both conditions hit the ceiling show B-A = -0.140, *worse* than the overall -0.080. The likely mechanism: skill content in the prompt steals output token budget, so with-skill outputs lose more content to truncation than baseline.

3. **Clean signal is weaker**: The 56 tasks where neither condition is truncated show B-A = -0.046, essentially noise. This is our best estimate of skill interference without the truncation confound.

4. **No hidden correlation**: Structural contamination vs B-A delta for clean tasks: r = -0.065 (vs r = 0.077 overall). Still zero.

5. **Score compression is real but symmetric**: Truncated baselines score 0.519 points lower on average (3.91 vs 4.43), and score ranges are compressed (1.25 vs 3.08). But both conditions are compressed equally, so the delta is preserved.

The implication is that the paper's reported mean B-A of -0.080 is, if anything, a slight overestimate of true skill interference due to token budget competition in truncated runs. The provider-resources analysis (output inflation mechanism) is a concrete example of this dynamic.

### For the fabrication escalation pattern

The upgrade-stripe pattern (1→12→28 signals) is particularly concerning for enterprise use cases. Skills that teach API surface knowledge can make the model *more* dangerous by turning uncertain hallucinations into confident fabrications. This is especially relevant for SDK-specific skills where the model has partial pre-training knowledge.

### For the baseline signal rate

The 0.57 signals/run baseline rate suggests that many of our eval tasks are at the edge of the model's capability even without skills. This is by design (tasks were designed to be challenging enough to show degradation) but means the eval may not generalize to simpler, more common tasks where the model has higher baseline performance.
