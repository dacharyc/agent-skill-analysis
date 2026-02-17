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

Score the generated code on these dimensions (1-5 each). Use the full range — reserve
5 for genuinely excellent output and do not round up:

1. **Language Correctness** (1-5): Is the code entirely in the requested language?
   - 1: Significant portions in wrong language or mixed syntax
   - 2: Mostly wrong language with some correct sections
   - 3: Correct language but with some foreign idioms or syntax patterns
   - 4: Correct language with only minor foreign influences
   - 5: Entirely correct language with no foreign patterns whatsoever

2. **API Idiomaticity** (1-5): Does the code use the correct, idiomatic API for the
   target language and framework? Or does it use API patterns from a different SDK/interface?
   If you identify any contamination signals, this score must be 3 or lower.
   - 1: Uses API patterns from a clearly different language SDK
   - 2: Mostly foreign API patterns with some correct usage
   - 3: Mostly correct API but some patterns borrowed from other SDKs
   - 4: Correct API with only trivial deviations from idiomatic usage
   - 5: Fully idiomatic API usage for the target language with zero foreign patterns

3. **Functional Correctness** (1-5): Ignoring language/API issues, would this code
   accomplish the stated task if the APIs were correct?
   If the code is truncated or incomplete (e.g. cut off mid-function, missing required
   methods/endpoints), score based on what fraction of the task is actually implemented.
   - 1: Would not accomplish the task
   - 2: Accomplishes less than half the task
   - 3: Partially accomplishes the task with significant gaps
   - 4: Accomplishes most of the task with minor omissions
   - 5: Would fully accomplish the task with all requested features present

4. **Code Quality** (1-5): Overall quality of the generated code.
   - 1: Poor quality, many issues
   - 2: Below average, notable issues
   - 3: Acceptable quality
   - 4: Good quality with minor issues
   - 5: Production-quality code

Respond with ONLY a JSON object:
{{
  "language_correctness": <1-5>,
  "api_idiomaticity": <1-5>,
  "functional_correctness": <1-5>,
  "code_quality": <1-5>,
  "contamination_signals": ["list of specific patterns from other languages/APIs detected, or empty"],
  "brief_assessment": "<2-4 sentence assessment covering: what the code does well, any contamination or foreign patterns detected, and any completeness issues>"
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


def _parse_judge_json(text: str) -> dict | None:
    """Parse JSON from judge response with multiple fallback strategies."""
    # Strategy 1: Direct parse (response is pure JSON)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract JSON from markdown code fence or surrounding text.
    # Use a greedy brace-matching approach that handles nested objects/arrays.
    json_match = re.search(r"\{", text)
    if json_match:
        start = json_match.start()
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break

    # Strategy 3: Single-quoted Python dict → JSON conversion
    # Replace single quotes with double quotes (handles the common LLM failure mode)
    try:
        fixed = text
        # Strip markdown code fence if present
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", fixed, re.DOTALL)
        if fence_match:
            fixed = fence_match.group(1).strip()
        # Extract outermost braces using depth counting
        brace_start = fixed.find("{")
        if brace_start >= 0:
            depth = 0
            for i in range(brace_start, len(fixed)):
                if fixed[i] == "{":
                    depth += 1
                elif fixed[i] == "}":
                    depth -= 1
                    if depth == 0:
                        fixed = fixed[brace_start:i + 1]
                        break
        # Replace single quotes with double quotes
        fixed = fixed.replace("'", '"')
        return json.loads(fixed)
    except (json.JSONDecodeError, ValueError):
        pass

    # Strategy 4: Truncated JSON recovery — the judge response was cut off by
    # max_tokens before the closing brace.  The four numeric scores appear first,
    # so we can often salvage them even when the trailing fields are incomplete.
    # Approach: strip to the last complete key-value pair, close any open arrays
    # and the object, then parse.
    fence = re.search(r"```(?:json)?\s*\n?(.*)", text, re.DOTALL)
    fragment = fence.group(1) if fence else text
    brace_start = fragment.find("{")
    if brace_start >= 0:
        fragment = fragment[brace_start:]
        # Strip any trailing incomplete value (partial string, dangling comma, etc.)
        # by keeping up to the last complete key-value line.
        lines = fragment.split("\n")
        kept: list[str] = []
        for line in lines:
            kept.append(line)
            stripped = line.strip()
            # If the line is just a closing brace/bracket we already have it
            if stripped in ("}", "},", "]", "],"):
                continue
            # A complete key-value pair ends with a comma or with a closing bracket
            if stripped.endswith(",") or stripped.endswith("]") or stripped.endswith("],"):
                continue
            # The opening brace
            if stripped == "{":
                continue
            # Otherwise this line may be the truncated one — keep it only if
            # it looks like a complete value (ends with a number or quoted string + optional comma)
            if not re.search(r'([\d"\]]})\s*,?\s*$', stripped):
                # Truncated mid-value — drop this line
                kept.pop()
                break
        rebuilt = "\n".join(kept).rstrip().rstrip(",")
        # Close any unclosed array brackets
        open_brackets = rebuilt.count("[") - rebuilt.count("]")
        rebuilt += "]" * open_brackets
        # Close the object
        open_braces = rebuilt.count("{") - rebuilt.count("}")
        rebuilt += "}" * open_braces
        try:
            return json.loads(rebuilt)
        except json.JSONDecodeError:
            pass

    return None


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

        # Parse JSON from response, with multiple fallback strategies
        result = _parse_judge_json(text)
        if result is None:
            print(f"    WARNING: Could not parse judge JSON: {text[:200]}", file=sys.stderr)
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


def judge_skill(
    client: anthropic.Anthropic,
    skill_name: str,
    task_ids: list[str] | None = None,
) -> dict | None:
    """Score all generated outputs for a skill.

    Args:
        client: Anthropic API client.
        skill_name: Name of the skill to judge.
        task_ids: Optional list of task IDs to judge. When set, only matching
            tasks are re-scored; other tasks retain their existing scores from
            a previous run (if any).
    """
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

    # Load existing scores for merge when filtering by task
    existing_scored: dict[str, dict] = {}
    if task_ids is not None:
        score_path = SCORES_DIR / f"{skill_name}.json"
        if score_path.exists():
            existing_data = json.loads(score_path.read_text())
            for t in existing_data.get("tasks", []):
                existing_scored[t["task_id"]] = t

    print(f"  Judging {skill_name} ({len(gen_data['tasks'])} tasks)...")

    scored_tasks = []
    for task in gen_data["tasks"]:
        task_id = task["task_id"]

        # Skip tasks not in the filter list; preserve existing scores
        if task_ids is not None and task_id not in task_ids:
            if task_id in existing_scored:
                scored_tasks.append(existing_scored[task_id])
                print(f"    Task: {task_id} (preserved from previous run)")
            else:
                print(f"    Task: {task_id} (skipped, no previous scores)")
            continue

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


def judge_skill_patterns_only(
    skill_name: str,
    task_ids: list[str] | None = None,
) -> dict | None:
    """Re-run only deterministic pattern matching for a skill.

    Loads generation data to get outputs, loads current task definitions
    to get patterns, and preserves any existing LLM judge scores from
    a prior full judge run. No API calls are made.

    Args:
        skill_name: Name of the skill to judge.
        task_ids: Optional list of task IDs to re-score. When set, only
            matching tasks are re-scored; others are preserved from the
            existing score file.
    """
    gen_data = load_generation(skill_name)
    if gen_data is None:
        print(f"  WARNING: No generation data for {skill_name}", file=sys.stderr)
        return None

    tasks_data = load_tasks(skill_name)
    if tasks_data is None:
        print(f"  WARNING: No task definitions for {skill_name}", file=sys.stderr)
        return None

    # Load existing scored data to preserve judge scores
    existing_scores = None
    score_path = SCORES_DIR / f"{skill_name}.json"
    if score_path.exists():
        existing_scores = json.loads(score_path.read_text())

    # Build lookups from task definitions
    task_defs = {t["id"]: t for t in tasks_data["tasks"]}

    # Build lookup from existing scores: (task_id, run_index, condition) -> judge dict
    existing_judge: dict[tuple[str, int, str], dict | None] = {}
    existing_scored_tasks: dict[str, dict] = {}
    if existing_scores:
        for task in existing_scores["tasks"]:
            existing_scored_tasks[task["task_id"]] = task
            for run in task["runs"]:
                ri = run["run_index"]
                for cond in ["baseline", "with_skill", "skill_md_only", "realistic"]:
                    cond_data = run.get(cond)
                    if cond_data is not None and isinstance(cond_data, dict):
                        existing_judge[(task["task_id"], ri, cond)] = cond_data.get("judge")

    print(f"  Patterns-only: {skill_name} ({len(gen_data['tasks'])} tasks)")

    scored_tasks = []
    for task in gen_data["tasks"]:
        task_id = task["task_id"]

        # Skip tasks not in the filter list; preserve existing scores
        if task_ids is not None and task_id not in task_ids:
            if task_id in existing_scored_tasks:
                scored_tasks.append(existing_scored_tasks[task_id])
                print(f"    Task: {task_id} (preserved from previous run)")
            else:
                print(f"    Task: {task_id} (skipped, no previous scores)")
            continue

        task_def = task_defs.get(task_id, {})
        target_lang = task["target_language"]
        expected = task_def.get("expected_patterns", task.get("expected_patterns", []))
        anti = task_def.get("anti_patterns", task.get("anti_patterns", []))

        print(f"    Task: {task_id}")

        scored_runs = []
        for run in task["runs"]:
            ri = run["run_index"]
            run_scores = {"run_index": ri}

            for cond_key, gen_key in [
                ("baseline", "baseline"),
                ("with_skill", "with_skill"),
                ("skill_md_only", "skill_md_only"),
                ("realistic", "realistic"),
            ]:
                cond_gen = run.get(gen_key)
                if cond_gen is None or not cond_gen.get("output"):
                    run_scores[cond_key] = None
                    continue

                output = cond_gen["output"]
                patterns = pattern_match(output, expected, anti)
                judge = existing_judge.get((task_id, ri, cond_key))

                run_scores[cond_key] = {
                    "judge": judge,
                    "patterns": patterns,
                }

            scored_runs.append(run_scores)

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


def judge_all(
    skill_names: list[str] | None = None,
    *,
    patterns_only: bool = False,
    task_ids: list[str] | None = None,
) -> list[dict]:
    """Score all generated outputs for specified skills (or all with data).

    Args:
        skill_names: Skills to judge (default: all with generation data).
        patterns_only: If True, only re-run deterministic pattern matching.
        task_ids: Optional task ID filter passed through to judge functions.
    """
    names = skill_names or list(SKILLS.keys())
    results = []

    if patterns_only:
        for name in names:
            if not (GENERATIONS_DIR / f"{name}.json").exists():
                print(f"  Skipping {name}: no generation data")
                continue
            result = judge_skill_patterns_only(name, task_ids=task_ids)
            if result:
                results.append(result)
        return results

    client = anthropic.Anthropic()
    for name in names:
        if not (GENERATIONS_DIR / f"{name}.json").exists():
            print(f"  Skipping {name}: no generation data")
            continue
        result = judge_skill(client, name, task_ids=task_ids)
        if result:
            results.append(result)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run behavioral eval judging")
    parser.add_argument("--skill", action="append", help="Specific skill(s) to judge")
    parser.add_argument("--task", action="append", help="Specific task ID(s) to judge")
    parser.add_argument("--patterns-only", action="store_true",
                        help="Re-run only deterministic pattern matching (no LLM calls)")
    args = parser.parse_args()

    print("=== Behavioral Eval: Judging ===")
    if args.patterns_only:
        print("  Mode: patterns-only (no LLM calls)")
    judge_all(args.skill, patterns_only=args.patterns_only, task_ids=args.task)
    print("Done.")
