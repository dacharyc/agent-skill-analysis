# Behavioral Eval System for Cross-Contamination Validation

Tests whether structural cross-contamination risk scores predict actual code generation degradation when skills are loaded into an LLM's context.

## How It Works

For each skill, the system generates code under multiple conditions:

- **A) Baseline** — no skill loaded (just the task prompt)
- **B) With skill** — SKILL.md + references injected as system prompt
- **C) SKILL-only** — SKILL.md without reference files (hidden contamination skills only: neon-postgres, react-native-best-practices)
- **D) Realistic context** — skill + condensed Claude Code system preamble + simulated codebase context

Each skill has 5 tasks probing different contamination vectors:

| Task Type | What It Tests |
|-----------|---------------|
| `direct_target` | Primary language of the skill (should benefit or be neutral) |
| `cross_language` | Same domain, different language (tests bleed) |
| `similar_syntax` | Syntactically similar language (highest PLC risk) |
| `grounded` | Includes existing code context (tests contamination with grounding) |
| `adjacent_domain` | Related task (tests scope bleed) |

Each condition runs 3 times at temperature 0.3. Outputs are scored by an LLM judge (Opus) on 4 dimensions plus deterministic pattern matching. Deltas between conditions reveal whether loading the skill degrades output quality.

### Condition D: Realistic Context

Conditions A–C test whether cross-contamination *can* occur in isolation. Condition D tests whether it *persists* under realistic usage conditions, where the skill is a smaller proportion of the total context.

In real Claude Code usage, the model sees a large system prompt, tool definitions, conversation history, explore agent summaries, and file reads — not just a skill and a task. The skill content that dominates context in Condition B might represent only 10–30% of the total context in production.

Condition D simulates this by:

1. **System prompt**: A condensed Claude Code preamble (tool list, key instructions, environment info) prepended to the skill content — mirroring how skills sit alongside the CC system prompt in production.
2. **Conversation history**: A multi-turn exchange where the assistant reports explore agent findings and a file read before the user provides the task. The codebase snippet is language-appropriate (selected by `target_language`) and contains generic infrastructure code (base services, loggers, API clients) unrelated to the API under test.

Comparing B vs D measures **context mitigation** — how much of the skill-only effect is diluted by surrounding context. The analysis computes a per-skill mitigation ratio: `1 - (D_delta / B_delta)`. A value of 0.6 means 60% of the skill-only degradation is mitigated by realistic context.

## Skill Selection (20 skills)

- **10 high-risk** (contamination ≥ 0.5): upgrade-stripe, sharp-edges, claude-settings-audit, copilot-sdk, wiki-agents-md, gemini-api-dev, provider-resources, ossfuzz, azure-identity-java, azure-security-keyvault-secrets-java
- **8 medium-risk** (pattern diversity): monitoring-observability, skill-creator, pdf, neon-postgres, react-native-best-practices, azure-containerregistry-py, azure-identity-dotnet, prompt-agent
- **2 negative controls**: fastapi-router-py (single-language, expect ~zero delta), doc-coauthoring (non-code, expect ~zero delta)

## Usage

```bash
# List available skills
venv/bin/python3 eval/run_eval.py --list

# Run full pipeline (all 20 skills)
venv/bin/python3 eval/run_eval.py

# Run specific skill(s)
venv/bin/python3 eval/run_eval.py --skill upgrade-stripe
venv/bin/python3 eval/run_eval.py --skill upgrade-stripe --skill gemini-api-dev

# Run individual pipeline stages
venv/bin/python3 eval/run_eval.py --stage generate --skill upgrade-stripe
venv/bin/python3 eval/run_eval.py --stage judge --skill upgrade-stripe
venv/bin/python3 eval/run_eval.py --stage analyze

# Re-run deterministic pattern matching only (no LLM calls)
venv/bin/python3 eval/run_eval.py --patterns-only
venv/bin/python3 eval/run_eval.py --patterns-only --skill upgrade-stripe
```

The `--stage` flag runs a single stage. The `analyze` stage always reads all available results, so partial runs still produce aggregate statistics.

### `--patterns-only` mode

The `--patterns-only` flag re-runs deterministic pattern matching against generation outputs without making any LLM API calls. This is useful when iterating on `expected_patterns` or `anti_patterns` in task JSON files — you can edit the patterns, re-run, and inspect results immediately.

When used:
- Generation is skipped entirely (existing outputs in `results/generations/` are reused)
- Pattern matching runs against the current task definitions in `tasks/*.json`
- Any existing LLM judge scores from a prior full run are preserved in the output
- The analysis stage runs normally afterward, so figures and statistics update

This flag also works when running `judge.py` directly: `venv/bin/python3 eval/judge.py --patterns-only`

## Pipeline Stages

1. **Generate** (`runner.py`) — calls Sonnet to produce code under each condition (A/B/D for all skills, plus C for hidden contamination skills). Cached by content hash in `.eval_cache/`.
2. **Judge** (`judge.py`) — scores each output with Opus on 4 dimensions (language correctness, API idiomaticity, functional correctness, code quality) plus deterministic per-pattern matching. Also cached.
3. **Analyze** (`analyze.py`) — computes per-skill deltas for both B-vs-A and D-vs-A, runs statistical tests (paired t-test, Wilcoxon signed-rank, Cohen's d), calculates Pearson correlation between structural and behavioral scores, computes mitigation ratios, and generates figures.

## Output

| Path | Contents |
|------|----------|
| `eval/results/generations/*.json` | Raw LLM outputs per skill |
| `eval/results/scores/*.json` | Judge scores per skill |
| `data/processed/behavioral-eval.json` | Unified analysis results |
| `paper/figures/behavioral_correlation.png` | Structural score vs behavioral delta scatter |
| `paper/figures/behavioral_deltas_by_risk.png` | Box plot of deltas by risk level |
| `paper/figures/behavioral_task_types.png` | Mean delta by task type and risk level |
| `paper/figures/behavioral_hidden_contamination.png` | SKILL-only vs SKILL+refs comparison |
| `paper/figures/behavioral_context_mitigation.png` | Skill-only vs realistic context delta per skill |
| `paper/figures/behavioral_net_negative.png` | Net negative skill validation |

## File Structure

```
eval/
├── config.py              # Skill registry, model config, content loaders
├── runner.py              # Generation engine with caching
├── judge.py               # LLM-as-judge + pattern matching with caching
├── analyze.py             # Statistical analysis + figure generation
├── run_eval.py            # CLI orchestrator
├── tasks/                 # 20 JSON files, 5 tasks each
├── results/
│   ├── generations/       # Raw outputs (created at runtime)
│   └── scores/            # Judge scores (created at runtime)
└── .eval_cache/           # Hash-based API response cache (created at runtime)
```

## Task Selection Methodology

Claude Opus 4.6 selected a range of 5 tasks for each skill under test. The tasks were designed to elicit code gen outputs where cross-contamination may occur based on the contents of the skill files, or should not generate cross-contamination in the case of controls. Without direct domain expertise in these technologies, I can only verify that they seem logically consistent with a theoretical propensity to generate incorrect code due to cross-contamination. I make no assumptions or assertions about the "correctness" of code gen outputs from a product usage or best practices standpoint, or of any expertise or lack thereof demonstrated in the task prompt.

## Pattern Derivation Methodology

Each task definition includes `expected_patterns` (strings/regexes that should appear in correct output) and `anti_patterns` (strings that indicate cross-language contamination). These were derived by reading each skill's SKILL.md and reference files to identify the specific languages, SDKs, and API surfaces present in the skill content.

Claude Opus 4.6 suggested the `expected_patterns` and `anti_patterns`.

### Expected patterns

Expected patterns are SDK-specific API calls, language idioms, and framework conventions that a correct answer in the target language **must** use. They are derived from official documentation for the target language's ecosystem, not from the skill content itself. For example, a task asking for Go Stripe code expects `stripe.Key =` (the stripe-go idiom), not any pattern from the skill.

The primary focus is on key APIs present in either the correct source or a conflicting source, but we do assert some general language-development patterns for the purpose of detecting language drift due to cross-contamination.

### Anti-patterns: three derivation strategies

**1. Cross-SDK API bleed.** When a skill contains examples in multiple languages for the same API, each language's SDK has distinct method naming conventions. Anti-patterns are the method names/calling conventions from the **other** languages present in the skill. For example, `upgrade-stripe` contains Python (`stripe.Customer.create`), Ruby (`Stripe::Customer`), and JavaScript (`new Stripe(`, `apiVersion:`) examples. A task requesting Go code uses these as anti-patterns — their presence indicates the model mixed SDK idioms across languages.

| Skill | Languages in Skill | Example Anti-Pattern | What It Catches |
|-------|-------------------|---------------------|----------------|
| upgrade-stripe | Python, Ruby, JS | `Stripe::Webhook` in JS output | Ruby webhook pattern bleeding into JavaScript |
| gemini-api-dev | Python, JS, Go, cURL | `google-generativeai` in new code | Deprecated Python SDK name bleeding into current code |
| copilot-sdk | TS, Python, Go, C# | `create_copilot` in C# output | Python snake_case method bleeding into PascalCase C# |
| azure-identity-java | Java | `.build()` in Python output | Java builder pattern bleeding into Python |

**2. Skill-specific vocabulary leakage.** For skills with proprietary APIs or domain-specific tooling, anti-patterns are the skill's unique identifiers that should not appear in output for unrelated frameworks. For example, `neon-postgres` tasks that use standard `pg` check for `@neondatabase/serverless` and `neon(` — the Neon-specific driver imports that should only appear when Neon is explicitly requested. This strategy is especially important for hidden contamination tests, where reference files contain SDK-specific patterns across languages.

| Skill | Proprietary Identifier | Anti-Pattern Context |
|-------|----------------------|---------------------|
| neon-postgres | `@neondatabase/serverless`, `neon(` | Should not appear in standard pg/asyncpg tasks |
| react-native-best-practices | `FlashList`, `StyleSheet.create` | Should not appear in pure Swift/Kotlin tasks |
| provider-resources | `schema.Schema{`, `d.Set(` | SDKv2 patterns that should not appear in Plugin Framework code |

**3. Negative control jargon detection.** For the two negative control skills, anti-patterns are the skill's internal jargon and workflow terminology. Since these skills should produce zero contamination (one is single-language Python, the other is non-code), any appearance of skill-specific terms in code output would indicate unexpected leakage.

- **fastapi-router-py** (code control): Anti-patterns in cross-language tasks are FastAPI-specific (`APIRouter`, `Depends(`, `response_model`, `BaseModel`) — these should not appear in Ruby/Flask/Go output
- **doc-coauthoring** (non-code control): Anti-patterns across all tasks are the skill's workflow concepts (`str_replace`, `create_file`, `Reader Claude`, `Stage 1/2/3`, `brainstorm`, `curation`) — these are internal methodology terms that should never appear in generated code

### Documentation provenance

Every task includes a `pattern_sources` field listing the official documentation pages consulted when deriving its expected and anti-patterns. This ensures full transparency — each pattern can be traced back to a specific SDK reference page. For example:

```json
{
  "pattern_sources": [
    {
      "url": "https://docs.stripe.com/api/customers/create?lang=python",
      "description": "Stripe Python SDK - Customer.create API reference, source of expected Python calling convention"
    },
    {
      "url": "https://docs.stripe.com/api/customers/create?lang=ruby",
      "description": "Stripe Ruby SDK - source of anti-pattern Stripe::Customer syntax"
    }
  ]
}
```

Sources typically include:
- **Target SDK docs** — the official API reference for the language requested in the task (expected patterns)
- **Other-language SDK docs** — API references for the languages present in the skill but not requested (anti-patterns)
- **Framework migration guides** — for tasks testing deprecated-to-current API transitions
- **Language style guides** — for patterns testing idiomatic naming conventions (snake_case vs camelCase vs PascalCase)

Source identification involved a range of techniques, including:

- Claude Sonnet 4.5 attempted to load relevant documentation URLs and check the content to ensure the listed URL correctly demonstrated the patterns claimed in the description
- For pages that Claude was unable to access, we searched for alternate LLM-friendly versions of the documentation or example files
- For patterns that were too general or where we could not trace the provenance of the patterns to a specific documentation source, I removed the patterns from the experiment

The goal of the rigorous pattern provenance documentation is to ensure that the LLM-generated patterns provided by Claude Opus 4.6 do not reflect stale or outdated APIs, and do not themselves reflect cross-contamination. Without domain expertise across the entirety of the skill subject areas, the deterministic pattern data set is the weakest part of the experiment, so provenance tracing is an attempt to support the validity of the deterministic validation.

You can find artifacts from the pattern provenance iteration in [pattern-artifacts](pattern-artifacts/)

### Pattern matching in the scoring pipeline

Pattern matching runs as a deterministic pre-judge layer in `judge.py`. Patterns are matched using `re.search()` (with fallback to literal substring match for invalid regex), so task patterns can use full regex syntax including alternation (`|`), escaped metacharacters (`\.`), and character classes.

#### Per-pattern expected results

Each expected pattern is scored individually as matched/unmatched, producing a list of `{"pattern": "...", "matched": true/false}` entries in `expected_results`. This enables inspection of exactly which patterns a given output satisfies and which it misses (available in `expected_misses`). A compound metric (`expected_hit_rate`) summarizes overall coverage:

- `expected_results` = per-pattern `{pattern, matched}` list
- `expected_hits` = patterns that matched
- `expected_misses` = patterns that did not match
- `expected_hit_rate` = count of hits / total expected patterns

#### Anti-pattern pass/fail

Anti-patterns use the same per-pattern structure (`anti_results`) for inspectability, but the compound metric is a simple pass/fail — any anti-pattern match is a failure:

- `anti_results` = per-pattern `{pattern, matched}` list
- `anti_pattern_hits` = patterns that matched (the specific contamination signals detected)
- `contamination_detected` = boolean, true if any anti-pattern matches

These metrics are computed independently for all conditions (baseline, with-skill, realistic context), enabling delta analysis. A skill that increases anti-pattern hit rate relative to baseline provides direct evidence that loading the skill introduces cross-language contamination. The pattern matching layer complements the LLM judge — it catches specific, known contamination vectors while the judge catches subtler idiom mixing that can't be expressed as string patterns.

## Cost Estimate

Condition D adds a third generation + judge call for every task (alongside A and B), and hidden contamination skills add a fourth (C). Approximate call counts: 20 skills × 5 tasks × 3 runs × 3 conditions = ~900 generation calls, ~900 judge calls. Hidden contamination skills add ~30 more of each.

- **Generation** (Sonnet): ~930 calls × ~$0.05–0.10 = ~$45–95
- **Judging** (Opus): ~930 calls × ~$0.10–0.15 = ~$95–140
- **Total**: ~$140–235

All API calls are cached, so re-runs are free.

## Configuration

Key settings in `config.py`:

| Setting | Value | Purpose |
|---------|-------|---------|
| `MODEL_GENERATION` | claude-sonnet-4-5-20250929 | Generation model |
| `MODEL_JUDGE` | claude-opus-4-6 | Judge model (different to avoid self-preference bias) |
| `TEMPERATURE` | 0.3 | Low but non-zero for variance measurement |
| `RUNS_PER_CONDITION` | 3 | Repetitions per task/condition pair |
| `MAX_GENERATION_TOKENS` | 2048 | Output token limit for generation |
| `MAX_JUDGE_TOKENS` | 1000 | Output token limit for judge |

### Increasing the number of runs

To run each task more times (e.g. for stronger statistical power), increase `RUNS_PER_CONDITION` in `config.py`. The cache is keyed on `run_index`, so previously completed runs are served from cache — only the new run indices trigger API calls. For example, changing from 3 to 6 re-uses runs 0–2 from cache and only generates/judges runs 3–5. The analysis pipeline reads whatever runs exist dynamically; no other code changes are needed.

### Changing models

`MODEL_GENERATION` and `MODEL_JUDGE` can be changed independently. Note that the generation and judge caches include the model name in their hash keys, so switching models triggers fresh API calls (the old model's cached results remain untouched in `.eval_cache/` and will be reused if you switch back).
