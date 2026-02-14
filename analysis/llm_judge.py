#!/usr/bin/env python3
"""
LLM-as-judge content quality scoring for Agent Skills.

Uses Claude API to score each skill on:
  - clarity (1-5): How clear and unambiguous are the instructions?
  - coherence (1-5): How well-organized and logically structured?
  - relevance (1-5): How relevant is the content to the skill's stated purpose?
  - actionability (1-5): How actionable are the instructions for an LLM agent?
  - completeness (1-5): How complete is the skill in covering its domain?

Outputs → merges into data/processed/content-analysis.json
Caches results in analysis/.llm_cache/ to avoid re-scoring on re-runs.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "data" / "skills"
CONTENT_ANALYSIS = REPO_ROOT / "data" / "processed" / "content-analysis.json"
CACHE_DIR = Path(__file__).resolve().parent / ".llm_cache"

JUDGE_PROMPT = """You are evaluating the quality of an "Agent Skill" — a markdown document that instructs an AI coding agent how to perform a specific task. Score this skill on 5 dimensions, each from 1 (worst) to 5 (best).

**Scoring dimensions:**

1. **Clarity** (1-5): How clear and unambiguous are the instructions? Are there vague or confusing passages?
   - 1: Mostly vague, unclear instructions
   - 3: Generally clear with some ambiguities
   - 5: Crystal clear, no room for misinterpretation

2. **Coherence** (1-5): How well-organized and logically structured is the document? Does it flow logically?
   - 1: Disorganized, no clear structure
   - 3: Reasonably organized with some structural issues
   - 5: Excellently structured with clear progression

3. **Relevance** (1-5): How relevant is all content to the skill's stated purpose? Is there irrelevant filler?
   - 1: Mostly irrelevant content
   - 3: Mostly relevant with some tangential content
   - 5: Every section directly supports the skill's purpose

4. **Actionability** (1-5): How actionable are the instructions for an AI agent? Can an agent follow them step-by-step?
   - 1: Abstract advice, no concrete steps
   - 3: Mix of concrete and abstract guidance
   - 5: Highly specific, step-by-step instructions an agent can execute

5. **Completeness** (1-5): How thoroughly does the skill cover its domain? Are there obvious gaps?
   - 1: Major gaps, barely covers the topic
   - 3: Covers main points but missing some important aspects
   - 5: Comprehensive coverage of the skill's domain

Respond with ONLY a JSON object in this exact format:
{
  "clarity": <1-5>,
  "coherence": <1-5>,
  "relevance": <1-5>,
  "actionability": <1-5>,
  "completeness": <1-5>,
  "overall": <1-5 average>,
  "brief_assessment": "<1-2 sentence summary>"
}"""


def get_cache_key(content: str) -> str:
    """Generate a cache key from skill content."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


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


def score_skill(content: str, client) -> dict | None:
    """Score a skill using Claude API."""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": f"{JUDGE_PROMPT}\n\n---\n\nSKILL CONTENT:\n\n{content[:8000]}",
                }
            ],
        )
        text = response.content[0].text.strip()
        # Extract JSON from response
        if text.startswith("{"):
            return json.loads(text)
        # Try to find JSON in the response
        import re
        match = re.search(r"\{[^{}]+\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        print(f"  WARNING: Could not parse JSON from response: {text[:100]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  ERROR: API call failed: {e}", file=sys.stderr)
        return None


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

    # Load content analysis
    with open(CONTENT_ANALYSIS) as f:
        content_data = json.load(f)

    scored = 0
    cached = 0
    failed = 0

    for skill in content_data["skills"]:
        name = skill["name"]
        source = skill["source"]

        skill_dir = skill.get("skill_dir", "")
        skill_md = Path(skill_dir) / "SKILL.md" if skill_dir else SKILLS_DIR / source / name / "SKILL.md"
        if not skill_md.exists():
            continue

        content = skill_md.read_text(encoding="utf-8", errors="replace")
        cache_key = get_cache_key(content)

        # Check cache
        result = get_cached_result(cache_key)
        if result:
            skill["llm_scores"] = result
            cached += 1
            continue

        # Score via API
        print(f"  Scoring {source}/{name}...")
        result = score_skill(content, client)
        if result:
            save_cache(cache_key, result)
            skill["llm_scores"] = result
            scored += 1
        else:
            failed += 1

        # Rate limit: ~1 request per second
        time.sleep(0.5)

    # Save updated content analysis
    with open(CONTENT_ANALYSIS, "w") as f:
        json.dump(content_data, f, indent=2)

    print(f"\nLLM Judge scoring complete → {CONTENT_ANALYSIS}")
    print(f"  Scored: {scored}, Cached: {cached}, Failed: {failed}")


if __name__ == "__main__":
    main()
