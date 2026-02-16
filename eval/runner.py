"""
Generation engine for behavioral eval.

Runs baseline vs with-skill code generation experiments.
For each task, generates code under two (or more) conditions:
  A) Baseline — no skill loaded
  B) With skill — SKILL.md + references in system prompt
  C) SKILL-only (hidden contamination skills) — SKILL.md without references
  D) Realistic context — skill + Claude Code system preamble + codebase context

Caches all API responses by content hash to avoid redundant calls.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import anthropic

from config import (
    CACHE_DIR,
    GENERATIONS_DIR,
    MAX_GENERATION_TOKENS,
    MODEL_GENERATION,
    RUNS_PER_CONDITION,
    SKILLS,
    TASKS_DIR,
    TEMPERATURE,
    get_full_skill_content,
    get_skill_md,
    build_realistic_system,
    build_realistic_messages,
)


def cache_key(prompt: str, system: str | None, run_index: int) -> str:
    """Hash-based cache key for a generation call."""
    raw = json.dumps({
        "model": MODEL_GENERATION,
        "prompt": prompt,
        "system": system or "",
        "run_index": run_index,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_GENERATION_TOKENS,
    }, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def get_cached(key: str) -> dict | None:
    path = CACHE_DIR / f"gen_{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_cache(key: str, result: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"gen_{key}.json"
    path.write_text(json.dumps(result, indent=2))


def generate(
    client: anthropic.Anthropic,
    prompt: str,
    system: str | None = None,
    run_index: int = 0,
    messages: list[dict] | None = None,
) -> dict:
    """Generate code with optional skill content as system prompt.

    Args:
        prompt: User prompt (used for cache key and as the user message if messages is None).
        system: Optional system prompt content.
        run_index: Run index for cache differentiation.
        messages: Optional full message list. If provided, overrides the default
                  single-user-message construction (used by Condition D to inject
                  codebase context as prior assistant/tool turns).

    Returns cached if available.
    """
    key = cache_key(prompt, system, run_index)
    cached = get_cached(key)
    if cached is not None:
        return {**cached, "cached": True}

    kwargs: dict = {
        "model": MODEL_GENERATION,
        "max_tokens": MAX_GENERATION_TOKENS,
        "temperature": TEMPERATURE,
        "messages": messages or [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    try:
        response = client.messages.create(**kwargs)
        output = response.content[0].text
        result = {
            "output": output,
            "model": MODEL_GENERATION,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
        save_cache(key, result)
        return {**result, "cached": False}
    except Exception as e:
        print(f"    ERROR generating: {e}", file=sys.stderr)
        return {"output": "", "error": str(e), "cached": False}


def load_tasks(skill_name: str) -> dict | None:
    """Load task definitions for a skill."""
    task_file = TASKS_DIR / f"{skill_name}.json"
    if not task_file.exists():
        print(f"  WARNING: No task file for {skill_name}", file=sys.stderr)
        return None
    return json.loads(task_file.read_text())


def run_skill(client: anthropic.Anthropic, skill_name: str) -> dict | None:
    """Run all tasks for a single skill, returning results dict."""
    skill_config = SKILLS[skill_name]
    tasks_data = load_tasks(skill_name)
    if tasks_data is None:
        return None

    # Load skill content
    full_content = get_full_skill_content(skill_name)
    skill_md_only = get_skill_md(skill_name) if skill_config["hidden_contamination"] else None

    if full_content is None:
        print(f"  WARNING: Could not load SKILL.md for {skill_name}", file=sys.stderr)
        return None

    print(f"  Running {skill_name} ({len(tasks_data['tasks'])} tasks, "
          f"{RUNS_PER_CONDITION} runs/condition)...")

    task_results = []
    for task in tasks_data["tasks"]:
        task_id = task["id"]
        target_lang = task["target_language"]
        print(f"    Task: {task_id}")

        runs = []
        for run_idx in range(RUNS_PER_CONDITION):
            # Condition A: Baseline (no skill)
            baseline = generate(client, task["prompt"], system=None, run_index=run_idx)
            cached_b = "cached" if baseline.get("cached") else "new"

            # Condition B: With full skill content
            with_skill = generate(client, task["prompt"], system=full_content, run_index=run_idx)
            cached_s = "cached" if with_skill.get("cached") else "new"

            # Condition C: SKILL.md only (hidden contamination skills)
            skill_md_result = None
            if skill_config["hidden_contamination"] and skill_md_only:
                skill_md_result = generate(
                    client, task["prompt"], system=skill_md_only, run_index=run_idx
                )
                cached_m = "cached" if skill_md_result.get("cached") else "new"

            # Condition D: Realistic context (skill + CC preamble + codebase context)
            realistic_system = build_realistic_system(full_content)
            realistic_msgs = build_realistic_messages(task["prompt"], target_lang)
            realistic_result = generate(
                client, task["prompt"],
                system=realistic_system,
                run_index=run_idx,
                messages=realistic_msgs,
            )
            cached_r = "cached" if realistic_result.get("cached") else "new"

            # Progress logging
            parts = [f"baseline({cached_b})", f"skill({cached_s})"]
            if skill_md_result is not None:
                parts.append(f"skill_md_only({cached_m})")
            parts.append(f"realistic({cached_r})")
            print(f"      Run {run_idx}: {' '.join(parts)}")

            runs.append({
                "run_index": run_idx,
                "baseline": baseline,
                "with_skill": with_skill,
                "skill_md_only": skill_md_result,
                "realistic": realistic_result,
            })

            # Small delay between non-cached calls to avoid rate limits
            if not baseline.get("cached") or not with_skill.get("cached"):
                time.sleep(0.5)

        task_results.append({
            "task_id": task_id,
            "task_type": task["type"],
            "target_language": task["target_language"],
            "expected_patterns": task.get("expected_patterns", []),
            "anti_patterns": task.get("anti_patterns", []),
            "pattern_sources": task.get("pattern_sources", []),
            "runs": runs,
        })

    result = {
        "skill_name": skill_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": MODEL_GENERATION,
        "temperature": TEMPERATURE,
        "runs_per_condition": RUNS_PER_CONDITION,
        "contamination_score": skill_config["contamination_score"],
        "risk_level": skill_config["risk_level"],
        "test_category": skill_config["test_category"],
        "tasks": task_results,
    }

    # Save to disk
    GENERATIONS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = GENERATIONS_DIR / f"{skill_name}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"  → Saved {out_path}")
    return result


def run_all(skill_names: list[str] | None = None) -> list[dict]:
    """Run generation for specified skills (or all)."""
    client = anthropic.Anthropic()
    names = skill_names or list(SKILLS.keys())
    results = []

    for name in names:
        if name not in SKILLS:
            print(f"  WARNING: Unknown skill '{name}', skipping", file=sys.stderr)
            continue
        result = run_skill(client, name)
        if result:
            results.append(result)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run behavioral eval generation")
    parser.add_argument("--skill", action="append", help="Specific skill(s) to run")
    args = parser.parse_args()

    print("=== Behavioral Eval: Generation ===")
    run_all(args.skill)
    print("Done.")
