# Code Block Language Labels vs. Behavioral Degradation

## Summary

Code block language labeling in skill content does not predict reduced behavioral degradation. If anything, the correlation runs in the wrong direction: fully-labeled skills (100% label rate) show worse mean degradation (-0.105) than partially-labeled skills (-0.052). This is a negative result that complicates the paper's recommendation to "label code blocks explicitly" as a contamination mitigation.

The number of distinct application languages in a skill's code blocks is a weak predictor of degradation (r=-0.334 among multi-app-language skills, n=8), consistent with the PLC theory, but the signal is small and confounded by skill-specific effects.

## Data

### Label rates and behavioral deltas (n=19, sorted by label rate)

| Skill | Blocks | Label rate | App langs | B-A | Contam |
|-------|--------|-----------|-----------|-----|--------|
| gemini-api-dev | 6 | 67% | 4 (go, java, py, ts) | +0.200 | 0.55 |
| skill-creator | 15 | 67% | 0 | +0.050 | 0.46 |
| monitoring-observability | 311 | 68% | 4 (go, java, js, py) | -0.233 | 0.50 |
| prompt-agent | 13 | 77% | 0 | -0.000 | 0.48 |
| provider-resources | 20 | 90% | 1 (go) | -0.317 | 0.55 |
| wiki-agents-md | 12 | 92% | 0 | +0.200 | 0.57 |
| ossfuzz | 17 | 94% | 2 (c++, py) | +0.017 | 0.53 |
| react-native-best-practices | 281 | 94% | 8 (cpp, js, jsx, kt, objc, swift, tsx, ts) | -0.384 | 0.07 |
| neon-postgres | 107 | 96% | 4 (js, py, tsx, ts) | +0.000 | 0.00 |
| sharp-edges | 282 | 100% | 12 (c, c#, go, java, js, kt, php, py, rb, rust, swift, ts) | -0.083 | 0.62 |
| azure-containerregistry-py | 62 | 100% | 1 (py) | -0.117 | 0.33 |
| azure-identity-dotnet | 46 | 100% | 1 (c#) | -0.017 | 0.33 |
| azure-identity-java | 79 | 100% | 1 (java) | +0.050 | 0.52 |
| azure-security-keyvault-secrets-java | 56 | 100% | 1 (java) | +0.000 | 0.52 |
| claude-settings-audit | 9 | 100% | 0 | -0.483 | 0.63 |
| copilot-sdk | 25 | 100% | 4 (c#, go, py, ts) | -0.100 | 0.63 |
| fastapi-router-py | 29 | 100% | 1 (py) | -0.133 | 0.00 |
| pdf | 18 | 100% | 1 (py) | -0.050 | 0.33 |
| upgrade-stripe | 9 | 100% | 3 (js, py, rb) | -0.117 | 0.93 |

### Correlations

| Metric | r vs B-A | r vs |B-A| | r vs contam |
|--------|---------|-----------|------------|
| Label rate (combined) | **-0.249** | -0.065 | -0.090 |
| n_app_langs (all skills) | -0.170 | +0.108 | -0.033 |
| n_total_langs (all skills) | -0.303 | +0.198 | -0.064 |
| Unlabeled block count | -0.256 | — | -0.022 |

### Group comparisons

| Group | n | Mean B-A |
|-------|---|---------|
| Partial labeling (<100%) | 9 | -0.052 |
| Full labeling (100%) | 10 | **-0.105** |
| Multi-app-language (≥2 app langs) | 8 | -0.088 |
| Single/zero-app-language (≤1) | 11 | -0.074 |

### Among multi-app-language skills only (n=8)

| Metric | r vs B-A |
|--------|---------|
| label_rate | -0.236 |
| n_app_langs | **-0.334** |

## Interpretation

### Why labeling doesn't help

The PLC literature (Moumoula et al. 2025) finds that explicit language keywords are the most effective mitigation for Programming Language Confusion — the phenomenon where a model generates code in the wrong language. Our eval measures a different phenomenon: whether skill content degrades output quality on *separate* tasks. These are related but distinct:

- **PLC**: "I see Python and JavaScript in the same context → I generate Python syntax when asked for JavaScript"
- **Our eval**: "I see a React Native skill in my context → my output quality on a separate Swift/Kotlin task degrades"

Language labels address the first mechanism (helping the model keep languages separate within a single context). They don't address the mechanisms we observe in practice:

1. **Template propagation** (claude-settings-audit, 100% labeled): Invalid JSON syntax in labeled code blocks is reproduced faithfully. The label doesn't prevent the model from copying invalid patterns.
2. **Textual frame leakage** (react-native-best-practices, 94% labeled): The skill's identity bleeds into output prose ("following React Native best practices for native iOS code"). Labels on code blocks don't prevent prose-level contamination.
3. **Token budget competition** (react-native-best-practices): Commentary referencing skill content crowds out code. Labels are irrelevant to this mechanism.
4. **API hallucination** (upgrade-stripe, 100% labeled): The model invents plausible API methods after seeing similar APIs. Labels don't prevent this.

### The sharp-edges anomaly

sharp-edges is particularly instructive: 12 distinct application languages, 282 code blocks, 100% labeling, high contamination score (0.62) — yet only -0.083 B-A delta. Compare to react-native-best-practices: 8 app langs, 94% labeling, low contamination (0.07), yet -0.384.

The difference isn't labeling. It's content type. sharp-edges teaches security vulnerability patterns across languages (the same conceptual pattern expressed in different syntaxes). react-native-best-practices teaches framework-specific implementation patterns (FlashList, Turbo Modules, threading models) that are tightly bound to specific platforms. The security patterns are language-portable and don't interfere; the framework patterns are language-specific and do.

### App language diversity as a weak predictor

Among multi-app-language skills, n_app_langs vs B-A shows r=-0.334. More application languages correlate with worse degradation. This is directionally consistent with PLC theory but weak (n=8) and confounded:
- react-native-best-practices (8 app langs, -0.384) and monitoring-observability (4 app langs, -0.233) drive most of the signal
- sharp-edges (12 app langs, -0.083) is a strong counterexample
- gemini-api-dev (4 app langs, +0.200) shows that multi-language skills can help

The confound is that language count covaries with content type. Skills with many app languages tend to be cross-platform or multi-SDK skills whose content is more likely to be framework-specific (and thus more contaminating) — but the contamination comes from the content specificity, not the language count per se.

## Implications

### For the paper's recommendations

The paper currently recommends:
- **Rec 9**: "Label code blocks explicitly... explicit language keywords provide the most effective mitigation for Programming Language Confusion"
- **Spec rec 3**: "Require code block language annotations: Make unlabeled code blocks a validation error"

These remain reasonable as general software practice (labeled code blocks are more readable, more parseable, and may help in scenarios our eval doesn't test). But the behavioral eval doesn't support the claim that labeling mitigates contamination in the skill context. The recommendation should be reframed from "safeguard against contamination" to "good practice that aids readability and may help models disambiguate languages, though our behavioral eval did not find a protective effect."

### For the "what predicts degradation" narrative

Code block labeling joins the list of things that don't predict behavioral degradation:
- Structural contamination score (r=0.077)
- Skill size / token overhead (r=-0.188)
- LLM quality dimensions (all |r| < 0.25)
- Code block label rate (r=-0.249, wrong direction)

What does predict it (weakly): task type (grounded/cross_language worst), novelty amplification (r=+0.327 for |B-A|), and content specificity (framework-specific > language-portable). None of these are easily reduced to a single structural metric.

## Caveats

- n=19 is small. All correlations are exploratory.
- The label rate distribution is bimodal: 10 skills at 100%, 9 below. Limited variance for correlation analysis.
- We measure labels at the skill level but degradation at the task level. A skill could have perfectly labeled Python blocks but unlabeled YAML, and the YAML may or may not be the contamination vector.
- The eval doesn't test classic PLC (asking the model to generate Language A when it just saw Language B in the same code block context). It tests cross-task interference from skill content. These are different phenomena.
- The PLC research used different models, different prompting patterns, and different evaluation criteria. The lack of labeling effect in our eval doesn't invalidate the PLC findings.
