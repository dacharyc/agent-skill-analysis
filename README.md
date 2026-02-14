# Agent Skill Analysis

Formal analysis of 673 Agent Skills from 41 repositories against the [agentskills.io](https://agentskills.io) specification. Covers structural validation, content quality analysis, and cross-contamination risk assessment across Anthropic official, company-published, community, vertical/domain-specific, and security skill sources.

## Project Structure

- **`data/skills/`** — Git submodules pointing to each skill source repo, pinned to specific commits
- **`data/raw/`** — Validator JSON output per skill (one file per skill)
- **`data/processed/`** — Analysis pipeline outputs (`combined.json` is the unified dataset)
- **`analysis/`** — Python data pipeline (collect → aggregate → analyze → combine)
- **`paper/`** — White paper source (Markdown + Pandoc → PDF)
- **`site/`** — Interactive web report (plain HTML/CSS/JS + Chart.js)

## Getting Started

### 1. Clone with submodules

The skill source repos are tracked as git submodules under `data/skills/`. To clone the full project with all skill data:

```bash
git clone --recurse-submodules https://github.com/dacharyc/agent-skill-analysis.git
cd agent-skill-analysis
```

If you already cloned without `--recurse-submodules`, initialize them after the fact:

```bash
git submodule update --init --recursive
```

### 2. Install dependencies

```bash
pip install -r analysis/requirements.txt
```

You also need the [skill-validator](https://github.com/dacharyc/skill-validator) binary. Build it from source or download a release, then update the `VALIDATOR` path in `analysis/collect.py` if it's not at `~/workspace/skill-validator/skill-validator`.

### 3. Run the data pipeline

```bash
python analysis/collect.py          # Validate + analyze skills → data/raw/
python analysis/aggregate.py        # Aggregate → validation-summary.json
python analysis/combine.py          # Merge all → combined.json
python analysis/stats.py            # Generate figures → paper/figures/
cp data/processed/combined.json site/data.json  # Update interactive report
```

Optionally, if you have an `ANTHROPIC_API_KEY` set, run LLM-as-judge scoring before `combine.py`:

```bash
export ANTHROPIC_API_KEY=your-key-here
python analysis/llm_judge.py        # Score skills via Claude API (~$5-15)
```

### 4. View results

```bash
# Interactive report (needs a local server for fetch)
python -m http.server -d site

# Build the white paper PDF (requires Pandoc)
cd paper && make pdf
```

## Skill Sources (41 Submodules)

Each source repo is a git submodule pinned to the commit that was analyzed. The `snapshot-metadata.json` file in `data/processed/` records the exact commit SHA, date, and URL for each source.

### Anthropic Official

| Submodule | Repo | Skills |
|-----------|------|--------|
| `anthropic-skills` | [anthropics/skills](https://github.com/anthropics/skills) | 16 |

### Company-Published

| Submodule | Repo |
|-----------|------|
| `microsoft-skills` | [microsoft/skills](https://github.com/microsoft/skills) |
| `openai-skills` | [openai/skills](https://github.com/openai/skills) |
| `cloudflare-skills` | [cloudflare/skills](https://github.com/cloudflare/skills) |
| `sentry-skills` | [getsentry/skills](https://github.com/getsentry/skills) |
| `expo-skills` | [expo/skills](https://github.com/expo/skills) |
| `huggingface-skills` | [huggingface/skills](https://github.com/huggingface/skills) |
| `hashicorp-skills` | [hashicorp/agent-skills](https://github.com/hashicorp/agent-skills) |
| `wordpress-skills` | [WordPress/agent-skills](https://github.com/WordPress/agent-skills) |
| `stripe-skills` | [stripe/ai](https://github.com/stripe/ai) |
| `vercel-skills` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) |
| `supabase-skills` | [supabase/agent-skills](https://github.com/supabase/agent-skills) |
| `google-gemini-skills` | [google-gemini/gemini-skills](https://github.com/google-gemini/gemini-skills) |
| `google-stitch-skills` | [google-labs-code/stitch-skills](https://github.com/google-labs-code/stitch-skills) |
| `vuejs-skills` | [vuejs-ai/skills](https://github.com/vuejs-ai/skills) |
| `remotion-skills` | [remotion-dev/skills](https://github.com/remotion-dev/skills) |
| `neon-skills` | [neondatabase/agent-skills](https://github.com/neondatabase/agent-skills) |
| `better-auth-skills` | [better-auth/skills](https://github.com/better-auth/skills) |
| `callstack-skills` | [callstackincubator/agent-skills](https://github.com/callstackincubator/agent-skills) |
| `tinybird-skills` | [tinybirdco/tinybird-agent-skills](https://github.com/tinybirdco/tinybird-agent-skills) |
| `ast-grep-skill` | [ast-grep/agent-skill](https://github.com/ast-grep/agent-skill) |
| `black-forest-labs-skills` | [black-forest-labs/skills](https://github.com/black-forest-labs/skills) |
| `solana-skills` | [solana-foundation/solana-dev-skill](https://github.com/solana-foundation/solana-dev-skill) |

### Community Collections

| Submodule | Repo |
|-----------|------|
| `trailofbits-skills` | [trailofbits/skills](https://github.com/trailofbits/skills) |
| `superpowers` | [obra/superpowers](https://github.com/obra/superpowers) |
| `superpowers-skills` | [obra/superpowers-skills](https://github.com/obra/superpowers-skills) |
| `superpowers-lab` | [obra/superpowers-lab](https://github.com/obra/superpowers-lab) |
| `claude-scientific-skills` | [K-Dense-AI/claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills) |
| `antfu-skills` | [antfu/skills](https://github.com/antfu/skills) |
| `obsidian-skills` | [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) |

### Community Individual

| Submodule | Repo |
|-----------|------|
| `claude-d3js-skill` | [chrisvoncsefalvay/claude-d3js-skill](https://github.com/chrisvoncsefalvay/claude-d3js-skill) |
| `claudeskill-loki-mode` | [asklokesh/claudeskill-loki-mode](https://github.com/asklokesh/claudeskill-loki-mode) |
| `playwright-skill` | [lackeyjb/playwright-skill](https://github.com/lackeyjb/playwright-skill) |
| `web-asset-generator` | [alonw0/web-asset-generator](https://github.com/alonw0/web-asset-generator) |
| `ffuf_claude_skill` | [jthack/ffuf_claude_skill](https://github.com/jthack/ffuf_claude_skill) |
| `ios-simulator-skill` | [conorluddy/ios-simulator-skill](https://github.com/conorluddy/ios-simulator-skill) |

### Vertical / Domain-Specific

| Submodule | Repo |
|-----------|------|
| `legal-skills` | [lawvable/awesome-legal-skills](https://github.com/lawvable/awesome-legal-skills) |
| `protein-design-skills` | [adaptyvbio/protein-design-skills](https://github.com/adaptyvbio/protein-design-skills) |
| `devops-skills` | [ahmedasmar/devops-claude-skills](https://github.com/ahmedasmar/devops-claude-skills) |
| `zephyr-skills` | [beriberikix/zephyr-agent-skills](https://github.com/beriberikix/zephyr-agent-skills) |

### Security

| Submodule | Repo |
|-----------|------|
| `clawsec-skills` | [prompt-security/clawsec](https://github.com/prompt-security/clawsec) |

### Updating submodules for a new analysis run

To re-run the analysis against the latest upstream commits:

```bash
# Update all submodules to their latest remote commits
git submodule update --remote

# Or update a specific one
git submodule update --remote data/skills/trailofbits-skills

# Re-run the pipeline — new commit SHAs are captured automatically
python analysis/collect.py
python analysis/aggregate.py
python analysis/combine.py
python analysis/stats.py
cp data/processed/combined.json site/data.json

# Commit the submodule pointer updates
git add data/skills/
git commit -m "Update skill submodules to latest commits"
```

The snapshot metadata in `data/processed/snapshot-metadata.json` will reflect the new commit SHAs, so you can always tell exactly which version of each source was analyzed.

## Data Pipeline

```
collect.py → data/raw/          (skill-validator check -o json per skill)
aggregate.py → validation-summary.json (includes content + risk analysis)
llm_judge.py → llm-scores.json (optional, Claude API scoring)
combine.py → combined.json     (unified dataset)
stats.py → paper/figures/      (charts for the paper)
```

Content analysis and contamination risk metrics are computed by the `skill-validator` CLI (Go) and included in the raw JSON output. The Python scripts `content_analyzer.py` and `contamination.py` have been removed — their logic is now in the CLI's `internal/content/` and `internal/risk/` packages.

## Tools

- [skill-validator](https://github.com/dacharyc/skill-validator) — Go CLI for structural validation, content analysis, and contamination risk
- Python 3.9+ with `anthropic`, `tiktoken`, `matplotlib`
- Pandoc for PDF generation
