# Synthetic Skills for Experiments

This directory contains synthetic skill variants created for specific eval experiments. These are **not** real company-published skills — they are modified versions of existing skills designed to test specific hypotheses about skill design and its effects on code generation quality.

## Experiment: Partial Knowledge Hypothesis

Tests whether providing API ground truth alongside pattern guidance reduces fabrication, and whether _more extensive_ documentation triggers over-engineering (architecture complexity).

**Baseline:** `upgrade-stripe` (pattern-only, SKILL.md with no reference files, ~1,500 tokens)

### upgrade-stripe-targeted (~7K tokens total)

**Level 1: Minimal ground truth.** Adds a single quick-reference file with just the correct API signatures, error class names, version constants, and webhook method names for each language. Contains the minimum information needed to prevent fabrication of non-existent APIs.

**Hypothesis:** Reduces fabrication signals without increasing architecture complexity.

### upgrade-stripe-comprehensive (~10K tokens total)

**Level 2: Full SDK documentation.** Adds four per-language reference files with extensive examples including pagination, object expansion, idempotency keys, metadata handling, retry patterns, and complete webhook handler implementations.

**Hypothesis:** May reduce fabrication further but could trigger over-engineering — the model may attempt to implement retry logic, idempotency, pagination, and other patterns not requested by the task, similar to the architecture complexity observed with other high-reference skills.

## Source Material

Reference files were sourced from official Stripe SDK repositories on GitHub:
- [stripe-python](https://github.com/stripe/stripe-python) (v14.3.0)
- [stripe-go](https://github.com/stripe/stripe-go) (v84.3.0)
- [stripe-node](https://github.com/stripe/stripe-node)
- [stripe-ruby](https://github.com/stripe/stripe-ruby)

All skills use an identical copy of `data/skills/stripe-skills/skills/upgrade-stripe/SKILL.md`.
