#!/usr/bin/env python3
"""
LLM-as-judge content quality scoring for Agent Skills.

Performs two scoring passes:

1. SKILL.md scoring — 6 dimensions (1-5 each):
   - clarity, actionability, token_efficiency, scope_discipline,
     directive_precision, novelty

2. Reference file scoring — 5 dimensions (1-5 each), per file:
   - clarity, instructional_value, token_efficiency, novelty,
     skill_relevance
   Provides parent skill context (name + description) so the judge can
   assess relevance to the parent skill's purpose.

Reads skill list from data/processed/validation-summary.json.
Outputs → data/processed/llm-scores.json
Caches results in analysis/.llm_cache/ to avoid re-scoring on re-runs.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "data" / "skills"
VALIDATION_SUMMARY = REPO_ROOT / "data" / "processed" / "validation-summary.json"
OUTPUT = REPO_ROOT / "data" / "processed" / "llm-scores.json"
CACHE_DIR = Path(__file__).resolve().parent / ".llm_cache"

# ---------------------------------------------------------------------------
# SKILL.md judge prompt
# ---------------------------------------------------------------------------

SKILL_JUDGE_PROMPT = """You are evaluating the quality of an "Agent Skill" — a markdown document that instructs an AI coding agent how to perform a specific task. Score this skill on 6 dimensions, each from 1 (worst) to 5 (best).

**Scoring dimensions:**

1. **Clarity** (1-5): How clear and unambiguous are the instructions? Are there vague or confusing passages?
   - 1: Mostly vague, unclear instructions
   - 3: Generally clear with some ambiguities
   - 5: Crystal clear, no room for misinterpretation

2. **Actionability** (1-5): How actionable are the instructions for an AI agent? Can an agent follow them step-by-step?
   - 1: Abstract advice, no concrete steps
   - 3: Mix of concrete and abstract guidance
   - 5: Highly specific, step-by-step instructions an agent can execute

3. **Token Efficiency** (1-5): How concise is the skill? Does every token earn its place in the context window, or is there redundant prose, boilerplate, or filler that could be trimmed without losing instructional value?
   - 1: Extremely verbose, heavy boilerplate, much content could be cut
   - 3: Reasonably concise with some unnecessary verbosity
   - 5: Maximally concise — every sentence carries essential information

4. **Scope Discipline** (1-5): Does the skill stay tightly focused on its stated purpose and primary language/technology, or does it sprawl into adjacent domains, languages, or concerns that risk confusing the agent?
   - 1: Sprawling scope, mixes many unrelated languages or domains
   - 3: Mostly focused with some tangential content
   - 5: Tightly scoped to a single purpose and technology

5. **Directive Precision** (1-5): Does the skill use precise, unambiguous directives (must, always, never, ensure) or does it hedge with vague suggestions (consider, may, could, possibly)?
   - 1: Mostly vague suggestions and hedged language
   - 3: Mix of precise directives and vague guidance
   - 5: Consistently precise, imperative directives throughout

6. **Novelty** (1-5): How much of this skill's content provides information beyond what you would already know from training data? Does it convey project-specific conventions, proprietary APIs, internal workflows, or non-obvious domain knowledge — or does it mostly restate common programming knowledge you already have?
   - 1: Almost entirely common knowledge any LLM would already know
   - 3: Mix of common knowledge and genuinely new information
   - 5: Predominantly novel information not available in training data

Respond with ONLY a JSON object in this exact format:
{
  "clarity": <1-5>,
  "actionability": <1-5>,
  "token_efficiency": <1-5>,
  "scope_discipline": <1-5>,
  "directive_precision": <1-5>,
  "novelty": <1-5>,
  "brief_assessment": "<1-2 sentence summary>"
}"""

SKILL_DIMS = ["clarity", "actionability", "token_efficiency", "scope_discipline",
              "directive_precision", "novelty"]

# ---------------------------------------------------------------------------
# Reference file judge prompt
# ---------------------------------------------------------------------------

REF_JUDGE_PROMPT = """You are evaluating the quality of a **reference file** that accompanies an Agent Skill. Reference files are supplementary documents (examples, API docs, patterns, etc.) loaded alongside the main SKILL.md into an AI coding agent's context window.

The parent skill's purpose is provided below so you can judge whether this reference supports it.

**Parent skill:** {skill_name}
**Parent description:** {skill_description}

Score this reference file on 5 dimensions, each from 1 (worst) to 5 (best).

**Scoring dimensions:**

1. **Clarity** (1-5): How clear and well-written is this reference? Can an AI agent easily parse and apply the information?
   - 1: Confusing, poorly formatted, hard to extract useful information
   - 3: Generally clear with some ambiguities or formatting issues
   - 5: Crystal clear, well-structured, easy for an agent to consume

2. **Instructional Value** (1-5): Does this reference provide concrete, directly-applicable examples, patterns, or API signatures that an agent can use — or is it abstract and theoretical?
   - 1: Abstract descriptions with no concrete examples or patterns
   - 3: Mix of concrete examples and abstract explanations
   - 5: Rich with directly-applicable code examples, patterns, and signatures

3. **Token Efficiency** (1-5): Does every token in this reference earn its place in the context window? Is the content concise, or bloated with redundant explanations, excessive boilerplate, or content that could be significantly compressed?
   - 1: Extremely verbose, much content could be cut or compressed
   - 3: Reasonably concise with some unnecessary verbosity
   - 5: Maximally concise — every section carries essential information

4. **Novelty** (1-5): How much of this reference provides information beyond what you would already know from training data? Does it document proprietary APIs, internal conventions, non-obvious gotchas, or uncommon patterns — or does it mostly restate standard documentation you already have access to?
   - 1: Almost entirely common knowledge (standard library docs, well-known patterns, basic tutorials)
   - 3: Mix of common knowledge and genuinely new information
   - 5: Predominantly novel — proprietary APIs, internal specifics, or rare domain knowledge

5. **Skill Relevance** (1-5): How directly does this reference file support the parent skill's stated purpose? Does every section contribute to what the skill is trying to teach the agent, or does it include tangential content?
   - 1: Mostly unrelated to the parent skill's purpose
   - 3: Generally relevant with some tangential sections
   - 5: Every section directly supports the parent skill's purpose

Respond with ONLY a JSON object in this exact format:
{{
  "clarity": <1-5>,
  "instructional_value": <1-5>,
  "token_efficiency": <1-5>,
  "novelty": <1-5>,
  "skill_relevance": <1-5>,
  "brief_assessment": "<1-2 sentence summary>"
}}"""

REF_DIMS = ["clarity", "instructional_value", "token_efficiency", "novelty", "skill_relevance"]


def get_cache_key(content: str, prefix: str = "") -> str:
    """Generate a cache key from content with an optional prefix."""
    raw = f"{prefix}:{content}" if prefix else content
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get_cached_result(cache_key: str) -> dict | None:
    """Check if a cached result exists."""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    return None


def save_cache(cache_key: str, result: dict):
    """Save a result to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    with open(cache_file, "w") as f:
        json.dump(result, f, indent=2)


def compute_overall(scores: dict, dims: list[str]) -> float | None:
    """Compute the mean of dimension scores ourselves, not the LLM."""
    values = [scores[d] for d in dims if d in scores and isinstance(scores[d], (int, float))]
    return round(sum(values) / len(values), 2) if values else None


def call_judge(prompt: str, content: str, client, max_tokens: int = 500) -> dict | None:
    """Send a judge prompt + content to the API and parse the JSON response."""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\n---\n\nCONTENT TO EVALUATE:\n\n{content[:8000]}",
                }
            ],
        )
        text = response.content[0].text.strip()
        if text.startswith("{"):
            return json.loads(text)
        match = re.search(r"\{[^{}]+\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        print(f"  WARNING: Could not parse JSON from response: {text[:100]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  ERROR: API call failed: {e}", file=sys.stderr)
        return None


def extract_frontmatter(content: str) -> tuple[str, str]:
    """Extract name and description from SKILL.md YAML frontmatter."""
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return "", ""
    fm_text = fm_match.group(1)
    name = ""
    description = ""
    for line in fm_text.split("\n"):
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip()
        elif line.startswith("description:"):
            description = line.split(":", 1)[1].strip()
    return name, description


def score_reference_files(skill_dir: Path, skill_content: str, client) -> list[dict]:
    """Score all reference files for a skill. Returns list of per-file score dicts."""
    refs_dir = skill_dir / "references"
    if not refs_dir.is_dir():
        return []

    ref_files = sorted(refs_dir.iterdir())
    if not ref_files:
        return []

    skill_name, skill_description = extract_frontmatter(skill_content)
    if not skill_name:
        skill_name = skill_dir.name
    if not skill_description:
        skill_description = "(no description provided)"

    prompt = REF_JUDGE_PROMPT.format(
        skill_name=skill_name,
        skill_description=skill_description,
    )

    results = []
    for ref_path in ref_files:
        if not ref_path.is_file() or ref_path.suffix.lower() != ".md":
            continue

        try:
            ref_content = ref_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        if not ref_content.strip():
            continue

        cache_key = get_cache_key(ref_content, prefix=f"ref:{skill_name}")
        cached = get_cached_result(cache_key)
        if cached:
            cached["overall"] = compute_overall(cached, REF_DIMS)
            results.append({"file": ref_path.name, "scores": cached, "cached": True})
            continue

        print(f"    Scoring ref {ref_path.name}...")
        result = call_judge(prompt, ref_content, client)
        if result:
            result.pop("overall", None)
            result["overall"] = compute_overall(result, REF_DIMS)
            save_cache(cache_key, result)
            results.append({"file": ref_path.name, "scores": result, "cached": False})
        else:
            results.append({"file": ref_path.name, "scores": None, "cached": False})

        time.sleep(0.5)

    return results


def aggregate_ref_scores(ref_results: list[dict]) -> dict | None:
    """Compute mean scores across all reference files for a skill."""
    scored = [r for r in ref_results if r.get("scores")]
    if not scored:
        return None

    agg = {}
    for dim in REF_DIMS:
        values = [r["scores"][dim] for r in scored if dim in r["scores"]]
        agg[dim] = round(sum(values) / len(values), 2) if values else None

    agg["overall"] = compute_overall(agg, REF_DIMS)
    agg["files_scored"] = len(scored)
    agg["files_total"] = len(ref_results)

    return agg


def main():
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        print("Set it with: export ANTHROPIC_API_KEY=your-key-here", file=sys.stderr)
        print("\nSkipping LLM judge scoring. Run again with API key to add quality scores.")
        sys.exit(0)

    try:
        import anthropic
    except ImportError:
        print("ERROR: anthropic package not installed. Run: pip install anthropic", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Load validation summary for skill list
    with open(VALIDATION_SUMMARY) as f:
        summary = json.load(f)

    scores = []
    skill_scored = 0
    skill_cached = 0
    skill_failed = 0
    skill_skipped = 0
    ref_files_scored = 0
    ref_files_cached = 0
    ref_skills_scored = 0

    for skill in summary["skills"]:
        name = skill["name"]
        source = skill["source"]

        skill_dir = skill.get("skill_dir", "")
        skill_dir_path = Path(skill_dir) if skill_dir else SKILLS_DIR / source / name
        skill_md = skill_dir_path / "SKILL.md"
        if not skill_md.exists():
            skill_skipped += 1
            continue

        content = skill_md.read_text(encoding="utf-8", errors="replace")

        # --- Pass 1: Score SKILL.md ---
        cache_key = get_cache_key(content)
        result = get_cached_result(cache_key)
        if result:
            # Recompute overall from dimension scores (cache may predate this logic)
            result["overall"] = compute_overall(result, SKILL_DIMS)
            skill_cached += 1
        else:
            print(f"  Scoring {source}/{name}...")
            result = score_skill_md(content, client)
            if result:
                save_cache(cache_key, result)
                skill_scored += 1
            else:
                skill_failed += 1

        entry = {"name": name, "source": source, "llm_scores": result}

        # --- Pass 2: Score reference files ---
        ref_results = score_reference_files(skill_dir_path, content, client)
        if ref_results:
            ref_skills_scored += 1
            for r in ref_results:
                if r.get("cached"):
                    ref_files_cached += 1
                elif r.get("scores"):
                    ref_files_scored += 1

            entry["ref_llm_scores"] = [
                {"file": r["file"], "scores": r["scores"]}
                for r in ref_results
            ]
            entry["ref_llm_aggregate"] = aggregate_ref_scores(ref_results)

        scores.append(entry)

    # Save LLM scores
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump({"skills": scores}, f, indent=2)

    print(f"\nLLM Judge scoring complete → {OUTPUT}")
    print(f"  SKILL.md — Scored: {skill_scored}, Cached: {skill_cached}, "
          f"Failed: {skill_failed}, Skipped: {skill_skipped}")
    print(f"  References — Skills with refs scored: {ref_skills_scored}, "
          f"Files scored: {ref_files_scored}, Files cached: {ref_files_cached}")


def score_skill_md(content: str, client) -> dict | None:
    """Score a SKILL.md using the skill judge prompt."""
    result = call_judge(SKILL_JUDGE_PROMPT, content, client)
    if result:
        result.pop("overall", None)  # discard if LLM included it anyway
        result["overall"] = compute_overall(result, SKILL_DIMS)
    return result


if __name__ == "__main__":
    main()
