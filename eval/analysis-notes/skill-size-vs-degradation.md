# Skill Size vs. Degradation: Weak Correlation, Confounded by Measurement Artifact

## Summary

Token overhead (skill input tokens minus baseline input tokens) shows a weak negative correlation with behavioral degradation (r=-0.188), revised upward from near-zero (r=0.047) after correcting a measurement artifact in the 4 largest skills. Content composition — specifically the density of multi-language API examples — remains the stronger predictor.

**Key revision (2026-02-16):** The prior analysis found zero correlation and a monotonic "smallest skills degrade most" pattern that supported an "internal dilution" hypothesis. This was partially an artifact of loading all reference files for skills with many references, which produced near-identical outputs (effectively n=1) and compressed variance to zero. After switching to selective reference loading (2-3 refs per task), the 4 previously-largest skills dropped from 24k-48k tokens to 8k-14k and revealed real degradation signals.

## Correlation Data

### Current (selective reference loading)

| Analysis level | r | n |
|---------------|---|---|
| Per-skill overhead vs B-A delta | -0.188 | 19 |
| Per-skill overhead vs D-A delta | +0.202 | 19 |
| Per-skill log(overhead) vs B-A delta | -0.184 | 19 |
| Per-skill log(overhead) vs D-A delta | +0.253 | 19 |
| Per-run input_tokens vs B-A delta | -0.074 | 285 |
| Per-run log(input_tokens) vs B-A delta | -0.073 | 285 |

### Previous (all references loaded) — for comparison

| Analysis level | r | n |
|---------------|---|---|
| Per-skill overhead vs B-A delta | 0.047 | 19 |
| Per-skill overhead vs D-A delta | 0.054 | 19 |
| Per-skill log(overhead) vs B-A delta | 0.064 | 19 |
| Per-skill log(overhead) vs D-A delta | 0.132 | 19 |
| Per-run input_tokens vs B-A delta | 0.015 | 283 |
| Per-run log(input_tokens) vs B-A delta | 0.021 | 283 |

The B-A correlation flipped from near-zero positive to weak negative. The D-A correlation strengthened in the positive direction. Neither is strong enough to be a reliable predictor at n=19.

## Quartile Analysis (B-A delta by skill token overhead)

### Current

| Quartile | Token range | Mean B-A delta | n |
|----------|-------------|----------------|---|
| Q1 (smallest) | 1,527 – 3,596 | -0.050 | 5 |
| Q2 | 4,445 – 5,247 | -0.097 | 5 |
| Q3 | 5,281 – 8,069 | -0.027 | 5 |
| Q4 (largest) | 8,095 – 13,991 | -0.163 | 4 |

### Previous — for comparison

| Quartile | Token range | Mean B-A delta | n |
|----------|-------------|----------------|---|
| Q1 (smallest) | 1,527 – 3,249 | -0.112 | 4 |
| Q2 | 3,596 – 4,743 | -0.042 | 4 |
| Q3 | 4,946 – 5,336 | -0.033 | 4 |
| Q4 (largest) | 6,403 – 48,192 | -0.022 | 7 |

The old pattern was monotonically decreasing degradation (Q1=-0.112 → Q4=-0.022). The new pattern is non-monotonic: Q4 now shows the second-worst degradation at -0.163.

## The Measurement Artifact: What Changed

Four skills with many reference files were regenerated with selective reference loading (2-3 refs per task instead of all ~10). This is what happened:

| Skill | Old overhead | New overhead | Old B-A | New B-A |
|-------|-------------|-------------|---------|---------|
| react-native-best-practices | 48,192 | 9,035 | -0.067 | **-0.383** (p=0.001) |
| monitoring-observability | 43,294 | 13,991 | -0.067 | **-0.233** (p=0.000) |
| sharp-edges | 37,981 | 8,095 | -0.033 | -0.083 (p=0.337) |
| neon-postgres | 24,590 | 7,917 | +0.083 | 0.000 (p=1.000) |

When all references were loaded, the model produced near-identical outputs across runs (~127-token unique content, effectively n=1 per task — see MongoDB case study in `claude-context.md`). This compressed variance to near-zero, making it look like large skills were safe. Selective loading restored output diversity and revealed that react-native-best-practices and monitoring-observability carry statistically significant degradation.

## Revised Interpretation

### What was right in the prior analysis
- **Content composition matters more than volume.** claude-settings-audit (3,249 tokens) still shows the worst delta (-0.483). react-native-best-practices (contam=0.075) degrades more than sharp-edges (contam=0.62). The content, not the score or the size, drives the effect.
- **Small concentrated skills can be potent.** upgrade-stripe (1,527 tokens, contam=0.93) and provider-resources (4,719 tokens, contam=0.55) still show meaningful degradation.

### What was wrong
- **"Large skills are safe via internal dilution"** — this was confounded by the measurement artifact. The 4 largest skills appeared safe because they produced degenerate outputs, not because their size buffered against contamination.
- **The monotonic quartile pattern** — an artifact of the same confound. With corrected measurements, Q4 shows degradation comparable to Q1-Q2.

### What's new
- **The weak negative B-A correlation (r=-0.188)** suggests that, if anything, larger skills degrade slightly more — the opposite of internal dilution. But this is driven primarily by react-native-best-practices and monitoring-observability and is not strong enough to be a reliable predictor.
- **The weak positive D-A correlation (r=+0.253)** hints that larger skills may benefit more from realistic context mitigation. Tentative; n=19 is insufficient.
- **neon-postgres is a true null** — zero degradation before and after the methodology fix, consistent with its zero contamination score. This is the clearest "clean skill, clean behavior" data point.

## Token Counts Across Conditions

Full data for reference (sorted by skill token overhead, descending):

| Skill | Contam | Overhead | B-A Δ | D-A Δ |
|-------|--------|----------|-------|-------|
| monitoring-observability | 0.50 | 13,991 | -0.233 | -0.167 |
| azure-identity-java | 0.52 | 10,777 | +0.050 | +0.233 |
| react-native-best-practices | 0.07 | 9,035 | -0.383 | +0.117 |
| sharp-edges | 0.62 | 8,095 | -0.083 | -0.067 |
| azure-security-keyvault-secrets-java | 0.52 | 8,069 | +0.000 | +0.384 |
| neon-postgres | 0.00 | 7,917 | +0.000 | -0.050 |
| azure-containerregistry-py | 0.33 | 6,403 | -0.117 | -0.092 |
| azure-identity-dotnet | 0.33 | 5,336 | -0.017 | +0.034 |
| prompt-agent | 0.48 | 5,281 | +0.000 | +0.067 |
| fastapi-router-py | 0.00 | 5,247 | -0.133 | -0.667 |
| ossfuzz | 0.53 | 4,946 | +0.017 | +0.267 |
| skill-creator | 0.46 | 4,743 | +0.050 | -0.000 |
| provider-resources | 0.55 | 4,719 | -0.317 | -0.150 |
| copilot-sdk | 0.63 | 4,445 | -0.100 | +0.150 |
| wiki-agents-md | 0.57 | 3,596 | +0.200 | -0.067 |
| claude-settings-audit | 0.63 | 3,249 | -0.483 | -0.300 |
| pdf | 0.33 | 2,530 | -0.050 | +0.050 |
| gemini-api-dev | 0.55 | 1,817 | +0.200 | +0.200 |
| upgrade-stripe | 0.93 | 1,527 | -0.117 | -0.500 |

## Future Investigation Areas

### Content Composition Deep Dive
- What fraction of each skill's tokens are multi-language code examples vs. prose vs. single-language code?
- Does the ratio of app-to-app language mixing to total content predict degradation better than total size?
- Can we compute a "contamination density" metric (contamination score / token count) that better predicts behavioral impact?

### Content Quality vs. Size
- Do the LLM-as-judge quality scores (from the main paper analysis) correlate with behavioral deltas?
  - Novelty: do high-novelty skills show different degradation patterns than low-novelty ones?
  - Token efficiency: do skills scored as concise/efficient show more or less contamination?
  - Directive precision: do strongly-directive skills anchor the model better against contamination?
- Does the information density heuristic (code-to-prose ratio) interact with contamination risk?
- Skills with high information density may concentrate contaminating content more effectively than prose-heavy skills

### Structural Patterns
- Does the presence of explicit language labels on code blocks correlate with reduced degradation?
  - The PLC literature (Moumoula et al. 2025) identifies explicit language keywords as the most effective mitigation
- Do skills with structured formats (tables, labeled sections) show less contamination than prose-heavy skills?
- Does reference file structure matter — is contamination from references diluted differently than from SKILL.md?

### Practical Recommendations
- The prior recommendation of "if you must include multi-language content, ensure it's a small fraction of the total" still holds, but not because large skills are inherently safer — rather because diluting contaminating content within relevant single-language content reduces its proportional influence
- Skill authors should consider splitting multi-language skills into per-language versions (eliminating contamination) rather than relying on volume to buffer
- Selective reference loading is both a methodological improvement (more valid measurements) and a practical recommendation (don't load irrelevant references — it wastes context and masks problems)
