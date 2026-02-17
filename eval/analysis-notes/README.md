# Behavioral Eval Analysis Notes

Detailed analysis notes from the behavioral evaluation of 19 Agent Skills. These notes document the reasoning behind findings reported in the paper's Behavioral Evaluation: Mechanism Identification section and provide per-skill and cross-cutting analyses that go deeper than the paper itself.

## High-Level Results

| Metric | Value |
|--------|-------|
| Structural-behavioral correlation | r = 0.077 (n=19) |
| Mean B-A delta (skill-only) | -0.080 |
| Mean D-A delta (realistic context) | -0.029 |
| Mean mitigation ratio | -67.8% |
| Statistically significant skills (p<0.05) | 6 of 19 |

The central finding is that **structural contamination scores do not predict behavioral degradation** in this sample. The actual interference mechanisms — template propagation, textual frame leakage, API hallucination, token budget competition, and cross-language code bleed — are content-specific rather than language-mixing artifacts. Preliminary evidence suggests that realistic agentic context may substantially attenuate measured degradation.

## Per-Skill Deep Dives

| File | Skill | Key Finding |
|------|-------|-------------|
| [doc-coauthoring.md](doc-coauthoring.md) | doc-coauthoring | Behavioral override, not contamination. Model follows skill's collaborative workflow instead of generating code. Excluded from aggregates. |
| [fastapi-router-py.md](fastapi-router-py.md) | fastapi-router-py | B-A near-zero (good control). D-A shows framework override — model detects FastAPI skill and refuses Flask tasks. Eval artifact. |
| [upgrade-stripe.md](upgrade-stripe.md) | upgrade-stripe | Highest structural risk (0.93) but modest B-A (-0.117). Failure mode is API hallucination, not language confusion. Realistic context amplifies rather than mitigates. |
| [claude-settings-audit.md](claude-settings-audit.md) | claude-settings-audit | Largest B-A (-0.483). Template propagation: `// comments` in JSON templates reproduced verbatim. Also demonstrates novelty pattern — helps on tasks where model lacks knowledge. |
| [positive-delta-skills.md](positive-delta-skills.md) | gemini-api-dev, wiki-agents-md | Skills with genuinely post-training knowledge produce net-positive effects. Positive deltas concentrated on tasks requiring novel knowledge. |
| [react-native-best-practices.md](react-native-best-practices.md) | react-native-best-practices | Largest degradation (B-A=-0.384) despite near-zero structural risk (0.07). Two mechanisms: textual frame leakage and token budget competition. Contrasted with sharp-edges. |
| [provider-resources.md](provider-resources.md) | provider-resources | Third-largest degradation (B-A=-0.317). Output inflation (2x longer outputs hit token ceiling) and architectural pattern bleed (Go package structure causes over-engineering in Python). |
| [template-propagation.md](template-propagation.md) | Multiple | Cross-cutting analysis of template and pattern propagation across skills. |

## Cross-Cutting Analyses

| File | Topic | Key Finding |
|------|-------|-------------|
| [skill-size-vs-degradation.md](skill-size-vs-degradation.md) | Token overhead vs. behavioral delta | Weak correlation (r=-0.188), confounded by selective reference loading measurement artifact. Prior "internal dilution" hypothesis retracted. |
| [quality-dimensions-vs-degradation.md](quality-dimensions-vs-degradation.md) | LLM-judge quality dimensions vs. behavioral delta | No single dimension predicts degradation (all \|r\| < 0.25). **Novelty amplification**: novelty vs \|B-A\| r=+0.327 — high-novelty skills have larger effects in both directions. |
| [code-block-labels-vs-degradation.md](code-block-labels-vs-degradation.md) | Code block language labels vs. behavioral delta | **Negative result**: 100% labeled skills show *worse* mean degradation (-0.105) than partially labeled (-0.052). Labels don't address the actual interference mechanisms found. |
| [judge-signals-analysis.md](judge-signals-analysis.md) | LLM judge contamination signals & assessments | Pervasive truncation confound (63.9% of baseline assessments). Three patterns: copilot-sdk pre-existing hallucination, upgrade-stripe fabrication escalation (1→12→32), gemini-api-dev error shift. |

## Eval Design

For methodology details (task design, scoring, conditions, selective reference loading), see the main [eval README](../README.md).

### Skills Tested

20 skills sampled across the contamination score range (0.00–0.93), all source categories, and multiple content types. One skill (doc-coauthoring) was excluded from aggregates due to behavioral override. Each skill was evaluated on 5 tasks spanning 5 interference categories (direct_target, cross_language, similar_syntax, grounded, adjacent_domain) under 3 conditions (baseline, with-skill, realistic) with 3 runs each at temperature 0.3.

### Uninvestigated Signals

Some findings were noted during analysis but not pursued in depth:

- **azure-identity-java** and **azure-security-keyvault-secrets-java**: Both show B-A near zero but positive D-A deltas (+0.233, +0.384). Realistic context somehow helps these skills — mechanism unknown.
- **Contamination density** (contamination score / token count): Not computed. Likely low value given r near 0 for both component metrics.
