"""
LLM-as-judge contamination scoring for behavioral eval.

Scores each generated output on 4 dimensions:
  1. Language Correctness (1-5)
  2. API Idiomaticity (1-5)
  3. Functional Correctness (1-5)
  4. Code Quality (1-5)

Also runs deterministic pattern matching (expected/anti patterns).
Uses a different model (Opus) than generation (Sonnet) to avoid self-preference bias.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path

import anthropic

from config import (
    CACHE_DIR,
    GENERATIONS_DIR,
    MAX_JUDGE_TOKENS,
    MODEL_JUDGE,
    SCORES_DIR,
    SKILLS,
)

JUDGE_PROMPT = """You are evaluating AI-generated code for signs of cross-language contamination.
The user requested code in {target_language} for the following task:

{task_prompt}

Score the generated code on these dimensions (1-5 each):

1. **Language Correctness** (1-5): Is the code entirely in the requested language?
   - 1: Significant portions in wrong language or mixed syntax
   - 3: Correct language but with some foreign idioms or syntax patterns
   - 5: Entirely correct language with no foreign patterns

2. **API Idiomaticity** (1-5): Does the code use the correct, idiomatic API for the
   target language and framework? Or does it use API patterns from a different SDK/interface?
   - 1: Uses API patterns from a clearly different language SDK
   - 3: Mostly correct API but some patterns borrowed from other SDKs
   - 5: Fully idiomatic API usage for the target language

3. **Functional Correctness** (1-5): Ignoring language/API issues, would this code
   accomplish the stated task if the APIs were correct?
   - 1: Would not accomplish the task
   - 3: Partially accomplishes the task with significant gaps
   - 5: Would fully accomplish the task

4. **Code Quality** (1-5): Overall quality of the generated code.
   - 1: Poor quality, many issues
   - 3: Acceptable quality
   - 5: Production-quality code

Respond with ONLY a JSON object:
{{
  "language_correctness": <1-5>,
  "api_idiomaticity": <1-5>,
  "functional_correctness": <1-5>,
  "code_quality": <1-5>,
  "contamination_signals": ["list of specific patterns from other languages/APIs detected, or empty"],
  "brief_assessment": "<1-2 sentence summary>"
}}"""

JUDGE_DIMS = ["language_correctness", "api_idiomaticity", "functional_correctness", "code_quality"]


def judge_cache_key(output: str, target_language: str, task_prompt: str) -> str:
    """Hash-based cache key for a judge call."""
    raw = json.dumps({
        "model": MODEL_JUDGE,
        "output": output,
        "target_language": target_language,
        "task_prompt": task_prompt,
    }, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def get_cached(key: str) -> dict | None:
    path = CACHE_DIR / f"judge_{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_cache(key: str, result: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"judge_{key}.json"
    path.write_text(json.dumps(result, indent=2))


def call_judge(
    client: anthropic.Anthropic,
    output: str,
    target_language: str,
    task_prompt: str,
) -> dict | None:
    """Score a single generated output using the LLM judge."""
    key = judge_cache_key(output, target_language, task_prompt)
    cached = get_cached(key)
    if cached is not None:
        return {**cached, "cached": True}

    prompt = JUDGE_PROMPT.format(
        target_language=target_language,
        task_prompt=task_prompt,
    )

    try:
        response = client.messages.create(
            model=MODEL_JUDGE,
            max_tokens=MAX_JUDGE_TOKENS,
            messages=[{
                "role": "user",
                "content": f"{prompt}\n\n---\n\nCODE TO EVALUATE:\n\n{output[:6000]}",
            }],
        )
        text = response.content[0].text.strip()

        # Parse JSON from response
        if text.startswith("{"):
            result = json.loads(text)
        else:
            match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                print(f"    WARNING: Could not parse judge JSON: {text[:100]}", file=sys.stderr)
                return None

        # Validate required dimensions
        missing = [d for d in JUDGE_DIMS if d not in result]
        if missing:
            print(f"    WARNING: Judge missing dims {missing}", file=sys.stderr)
            return None

        save_cache(key, result)
        return {**result, "cached": False}

    except Exception as e:
        print(f"    ERROR in judge: {e}", file=sys.stderr)
        return None


def _pattern_matches(pattern: str, output: str) -> bool:
    """Test whether a pattern matches anywhere in the output using regex."""
    try:
        return re.search(pattern, output) is not None
    except re.error:
        # Fall back to literal substring match if pattern is invalid regex
        return pattern in output


def pattern_match(output: str, expected: list[str], anti: list[str]) -> dict:
    """Deterministic pattern matching layer.

    Returns per-pattern results for both expected and anti-patterns,
    plus compound metrics for summary use.
    """
    # Per-pattern expected results: list of {pattern, matched} dicts
    expected_results = [
        {"pattern": p, "matched": _pattern_matches(p, output)}
        for p in expected
    ]
    expected_hits = [r["pattern"] for r in expected_results if r["matched"]]
    expected_misses = [r["pattern"] for r in expected_results if not r["matched"]]

    # Per-pattern anti-pattern results
    anti_results = [
        {"pattern": p, "matched": _pattern_matches(p, output)}
        for p in anti
    ]
    anti_hits = [r["pattern"] for r in anti_results if r["matched"]]

    return {
        # Expected patterns: per-match detail + compound metric
        "expected_results": expected_results,
        "expected_hits": expected_hits,
        "expected_misses": expected_misses,
        "expected_hit_count": len(expected_hits),
        "expected_total": len(expected),
        "expected_hit_rate": len(expected_hits) / len(expected) if expected else 0,
        # Anti-patterns: per-match detail + pass/fail
        "anti_results": anti_results,
        "anti_pattern_hits": anti_hits,
        "anti_pattern_hit_count": len(anti_hits),
        "anti_pattern_total": len(anti),
        "anti_pattern_hit_rate": len(anti_hits) / len(anti) if anti else 0,
        "contamination_detected": len(anti_hits) > 0,
    }


def score_condition(
    client: anthropic.Anthropic,
    output: str,
    target_language: str,
    task_prompt: str,
    expected_patterns: list[str],
    anti_patterns: list[str],
) -> dict:
    """Score a single condition's output (judge + pattern matching)."""
    if not output or output.strip() == "":
        return {"error": "empty output", "judge": None, "patterns": None}

    judge_scores = call_judge(client, output, target_language, task_prompt)
    patterns = pattern_match(output, expected_patterns, anti_patterns)

    return {
        "judge": judge_scores,
        "patterns": patterns,
    }


def load_generation(skill_name: str) -> dict | None:
    """Load generation results for a skill."""
    gen_file = GENERATIONS_DIR / f"{skill_name}.json"
    if not gen_file.exists():
        return None
    return json.loads(gen_file.read_text())


def load_tasks(skill_name: str) -> dict | None:
    """Load original task definitions to get prompts."""
    from config import TASKS_DIR
    task_file = TASKS_DIR / f"{skill_name}.json"
    if not task_file.exists():
        return None
    return json.loads(task_file.read_text())


def judge_skill(client: anthropic.Anthropic, skill_name: str) -> dict | None:
    """Score all generated outputs for a skill."""
    gen_data = load_generation(skill_name)
    if gen_data is None:
        print(f"  WARNING: No generation data for {skill_name}", file=sys.stderr)
        return None

    tasks_data = load_tasks(skill_name)
    if tasks_data is None:
        print(f"  WARNING: No task definitions for {skill_name}", file=sys.stderr)
        return None

    # Build prompt lookup from task definitions
    prompt_lookup = {t["id"]: t["prompt"] for t in tasks_data["tasks"]}

    print(f"  Judging {skill_name} ({len(gen_data['tasks'])} tasks)...")

    scored_tasks = []
    for task in gen_data["tasks"]:
        task_id = task["task_id"]
        task_prompt = prompt_lookup.get(task_id, "")
        target_lang = task["target_language"]
        expected = task.get("expected_patterns", [])
        anti = task.get("anti_patterns", [])

        print(f"    Task: {task_id}")

        scored_runs = []
        for run in task["runs"]:
            run_scores = {"run_index": run["run_index"]}

            # Score baseline
            baseline_out = run["baseline"].get("output", "")
            run_scores["baseline"] = score_condition(
                client, baseline_out, target_lang, task_prompt, expected, anti
            )

            # Score with-skill
            skill_out = run["with_skill"].get("output", "")
            run_scores["with_skill"] = score_condition(
                client, skill_out, target_lang, task_prompt, expected, anti
            )

            # Score skill-md-only (hidden contamination)
            if run.get("skill_md_only") and run["skill_md_only"].get("output"):
                md_out = run["skill_md_only"]["output"]
                run_scores["skill_md_only"] = score_condition(
                    client, md_out, target_lang, task_prompt, expected, anti
                )
            else:
                run_scores["skill_md_only"] = None

            # Score realistic context (Condition D)
            if run.get("realistic") and run["realistic"].get("output"):
                realistic_out = run["realistic"]["output"]
                run_scores["realistic"] = score_condition(
                    client, realistic_out, target_lang, task_prompt, expected, anti
                )
            else:
                run_scores["realistic"] = None

            scored_runs.append(run_scores)
            time.sleep(0.3)

        scored_tasks.append({
            "task_id": task_id,
            "task_type": task["task_type"],
            "target_language": target_lang,
            "runs": scored_runs,
        })

    result = {
        "skill_name": skill_name,
        "scored_at": gen_data.get("generated_at", ""),
        "model_judge": MODEL_JUDGE,
        "model_generation": gen_data.get("model", ""),
        "contamination_score": gen_data.get("contamination_score", 0),
        "risk_level": gen_data.get("risk_level", ""),
        "test_category": gen_data.get("test_category", ""),
        "tasks": scored_tasks,
    }

    SCORES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SCORES_DIR / f"{skill_name}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"  → Saved {out_path}")
    return result


def judge_all(skill_names: list[str] | None = None) -> list[dict]:
    """Score all generated outputs for specified skills (or all with data)."""
    client = anthropic.Anthropic()
    names = skill_names or list(SKILLS.keys())
    results = []

    for name in names:
        if not (GENERATIONS_DIR / f"{name}.json").exists():
            print(f"  Skipping {name}: no generation data")
            continue
        result = judge_skill(client, name)
        if result:
            results.append(result)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run behavioral eval judging")
    parser.add_argument("--skill", action="append", help="Specific skill(s) to judge")
    args = parser.parse_args()

    print("=== Behavioral Eval: Judging ===")
    judge_all(args.skill)
    print("Done.")
