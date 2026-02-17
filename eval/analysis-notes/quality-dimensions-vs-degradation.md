# LLM Quality Dimensions vs. Behavioral Degradation

## Summary

No single content quality dimension from the paper's LLM-as-judge scoring (clarity, actionability, token efficiency, scope discipline, directive precision, novelty) predicts behavioral degradation across the 19 evaluated skills. However, **novelty amplifies effect magnitude in both directions** — high-novelty skills show both the largest positive deltas (when the task matches) and the largest negative deltas (when it doesn't). This interacts with task type: high-novelty skills degrade more on cross-language tasks (r=-0.328) but improve more on similar-syntax and adjacent-domain tasks (r=+0.287, +0.289).

This connects the paper's structural analysis with the exploratory behavioral evaluation: novelty may determine whether the model pays attention to skill content, and that attention could cut both ways.

## Per-Dimension Correlations (n=19)

### All skills

| Dimension | r vs B-A | r vs D-A |
|-----------|---------|---------|
| clarity | +0.061 | +0.104 |
| actionability | -0.100 | +0.246 |
| token_efficiency | -0.005 | -0.031 |
| scope_discipline | -0.086 | -0.068 |
| directive_precision | +0.244 | +0.110 |
| novelty | -0.045 | +0.041 |
| craft composite (excl. novelty) | +0.012 | +0.077 |
| overall composite (all dims) | -0.006 | +0.079 |

All near-zero. A well-crafted skill is not reliably safer than a poorly-crafted one.

### Among negative-delta skills only (n=11)

| Dimension | r vs B-A |
|-----------|---------|
| clarity | **+0.564** |
| token_efficiency | **+0.581** |
| scope_discipline | +0.298 |
| directive_precision | +0.266 |
| novelty | -0.421 |
| actionability | -0.053 |

Among skills that degrade, clarity and token efficiency moderate the severity — clearer, more efficient skills degrade less. However, n=11 is small and the signal is driven partly by two outliers (claude-settings-audit at clarity=4 / B-A=-0.483, react-native-best-practices at clarity=5 / B-A=-0.384). Treat as suggestive, not definitive.

The negative novelty correlation (-0.421) in this subset reflects that the worst degraders (claude-settings-audit nov=5, react-native-best-practices nov=4) happen to be high-novelty skills. See the novelty amplification section below for interpretation.

## Novelty Amplification (Exploratory)

### Novelty vs absolute delta

**novelty vs |B-A|: r=+0.327** — higher novelty skills show larger absolute behavioral effects, both positive and negative.

| Group | n | Mean novelty | Mean B-A | Mean |B-A| |
|-------|---|-------------|---------|---------|
| Positive B-A (skill helps) | 5 | 4.0 | +0.103 | 0.103 |
| Zero B-A (no effect) | 3 | 2.7 | 0.000 | 0.000 |
| Negative B-A (skill hurts) | 11 | 3.4 | -0.186 | 0.186 |

The zero-effect skills are the lowest-novelty group (mean 2.7): azure-security-keyvault-secrets-java (nov=2), neon-postgres (nov=5, the exception), prompt-agent (nov=1). The model largely ignores low-novelty content.

### Novelty × task type interaction

| Task type | novelty vs delta | Mean delta | Interpretation |
|-----------|-----------------|------------|----------------|
| direct_target | r = -0.018 | -0.009 | No relationship — novelty doesn't predict direct target performance |
| cross_language | **r = -0.328** | -0.171 | Higher novelty → worse. Model attends to novel content, bleeds into wrong-language tasks |
| similar_syntax | r = +0.287 | -0.018 | Higher novelty → better. Novel content helps on syntactically adjacent tasks |
| grounded | r = -0.147 | -0.193 | Slight worsening. Existing code anchors, but novel content can compete |
| adjacent_domain | r = +0.289 | -0.009 | Higher novelty → better. Knowledge transfer to adjacent domains |

The **cross_language** pattern is the most revealing. Detail for cross_language tasks:

**Low novelty (≤3):**

| Skill | Novelty | Cross-language Δ |
|-------|---------|-----------------|
| prompt-agent | 1 | +0.000 |
| azure-containerregistry-py | 2 | +0.167 |
| azure-identity-dotnet | 2 | +0.000 |
| azure-identity-java | 2 | +0.250 |
| azure-security-keyvault-secrets-java | 2 | -0.250 |
| fastapi-router-py | 2 | +0.000 |
| monitoring-observability | 2 | -0.083 |
| upgrade-stripe | 3 | -0.167 |
| **Mean** | **2.1** | **-0.010** |

Near-zero mean. Low-novelty skills add noise the model ignores.

**High novelty (≥4):**

| Skill | Novelty | Cross-language Δ |
|-------|---------|-----------------|
| gemini-api-dev | 4 | +0.417 |
| ossfuzz | 4 | -0.250 |
| pdf | 4 | -0.334 |
| provider-resources | 4 | -0.583 |
| react-native-best-practices | 4 | -0.834 |
| sharp-edges | 4 | -0.250 |
| claude-settings-audit | 5 | -0.250 |
| copilot-sdk | 5 | -1.333 |
| neon-postgres | 5 | +0.000 |
| skill-creator | 5 | +0.167 |
| wiki-agents-md | 5 | +0.083 |
| **Mean** | **4.4** | **-0.288** |

Much larger degradation. The high-novelty skills that degrade are those whose novel content is language-specific and bleeds into the cross-language task (copilot-sdk's multi-SDK examples, react-native-best-practices' TypeScript/native bridge content, provider-resources' Go/HCL mixing).

## Interpretation

### Why novelty amplifies in both directions

Novelty measures whether the skill teaches the model something beyond its training data. This determines the degree to which the model *attends to and relies on* the skill content:

- **Low-novelty skills (nov ≤ 2)**: The model already knows this content. The skill is largely redundant — it adds some noise to the context but doesn't change the model's behavior much in either direction. Result: near-zero deltas.

- **High-novelty skills (nov ≥ 4)**: The model encounters genuinely new information and incorporates it into its outputs. When the task matches the skill's domain, this is beneficial — the model produces better code using knowledge it didn't have before (gemini-api-dev +0.833 on direct_target, wiki-agents-md +0.500). When the task doesn't match, the model's increased attention to the novel content means more interference — the new patterns are salient enough to bleed through (copilot-sdk -1.333 on cross_language).

This is the **attention allocation** mechanism: novelty makes content more salient, and salience cuts both ways.

### Observations on the "net negative" risk category

The paper identifies 35 skills with low novelty + high contamination as theoretically worst-case ("the agent gains no new information but is exposed to mixed-language interference"). In our exploratory sample (n=19), the pattern is more nuanced:

- **Low-novelty + high-contamination** skills (e.g., upgrade-stripe nov=3, contam=0.93): modest degradation (B-A=-0.117). The model knows Stripe already and partially ignores the redundant multi-language examples.
- **High-novelty + task-mismatch** skills: much worse degradation. copilot-sdk (nov=5, cross_language=-1.333), react-native-best-practices (nov=4, cross_language=-0.834), claude-settings-audit (nov=5, direct_target=-1.167).

If this pattern holds in larger samples, the risk profile may not be "low novelty + high contamination" but rather **high novelty + content that's relevant enough to capture attention but wrong for the task context**. The model's learning ability — precisely what makes skills valuable — could also be what makes them dangerous when misapplied.

This doesn't invalidate the net-negative category entirely (those skills still add no value), but the behavioral case studies suggest the urgency may be lower than the structural analysis alone implies. However, confirming this requires testing with a larger behavioral sample — these observations are from n=19 skills with all the caveats that entails.

## Negative Results Worth Noting

### Composite quality scores don't predict degradation
Craft composite (r=+0.012) and overall composite (r=-0.006) are essentially zero. A skill's aggregate quality has no bearing on whether it degrades behavior.

### Token efficiency × contamination interaction doesn't work
- Low teff (≤3) + high contam (≥0.4): mean B-A = -0.136 (n=6)
- High teff (≥4) + low contam (<0.4): mean B-A = -0.140 (n=5)

No meaningful difference. These dimensions don't interact multiplicatively to predict degradation.

### No "safe quality threshold"
Even the highest-craft skills degrade: react-native-best-practices (craft=4.8, B-A=-0.384), copilot-sdk (craft=4.8, B-A=-0.100), azure-containerregistry-py (craft=4.8, B-A=-0.117). Craft quality does not provide immunity.

## Caveats

- n=19 skills with 5 tasks each. All correlations should be treated as exploratory.
- The LLM-as-judge quality scores are from the paper's structural content analysis (evaluating SKILL.md text). The behavioral eval measures output quality under the skill's influence. These are different dimensions of the same skill, and the connection is indirect.
- The novelty scores are integers (1-5) with limited variance in this sample — 8 skills at nov=2, 6 at nov=4, 4 at nov=5, 1 at nov=3. Finer-grained novelty measurement might reveal a stronger or weaker signal.
- The per-task-type correlations (e.g., cross_language r=-0.328) are on n=19 single data points per skill. Task-level variance within each skill is substantial.

## Implications for Skill Authors

1. **Novel skills are high-variance.** If your skill teaches genuinely new information, it will change model behavior — for better on-domain and for worse off-domain. This argues for tighter scoping of novel content.
2. **Redundant skills are low-risk but also low-value.** If your skill restates what the model already knows (novelty ≤ 2), it's unlikely to cause degradation — but it's also unlikely to help.
3. **Craft quality doesn't protect against contamination.** A beautifully written skill with cross-language examples will still contaminate. Quality and safety are orthogonal axes.
4. **Among skills that do degrade**: clarity and token efficiency may moderate severity. This is suggestive (n=11) but aligns with the intuition that concise, well-organized content produces less noise.
