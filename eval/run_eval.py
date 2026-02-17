#!/usr/bin/env python3
"""
Orchestrator for behavioral eval pipeline.

Usage:
    python eval/run_eval.py                          # Run all 20 skills
    python eval/run_eval.py --skill upgrade-stripe   # Run specific skill
    python eval/run_eval.py --skill upgrade-stripe --skill gemini-api-dev
    python eval/run_eval.py --stage generate         # Only generate
    python eval/run_eval.py --stage judge            # Only judge (needs generation data)
    python eval/run_eval.py --stage analyze          # Only analyze (needs scored data)
    python eval/run_eval.py --list                   # List available skills
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure eval/ is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import SKILLS, get_skill_path


def validate_skills(skill_names: list[str]) -> list[str]:
    """Validate that skill paths exist, return valid names."""
    valid = []
    for name in skill_names:
        if name not in SKILLS:
            print(f"  WARNING: Unknown skill '{name}', skipping")
            continue
        path = get_skill_path(name)
        skill_md = path / "SKILL.md"
        if not skill_md.exists():
            print(f"  WARNING: SKILL.md not found at {skill_md}, skipping")
            continue
        valid.append(name)
    return valid


def list_skills():
    """Print available skills with metadata."""
    print(f"\n{'Name':40s} {'Score':>6s} {'Risk':>8s} {'Category'}")
    print("-" * 80)
    for name, cfg in sorted(SKILLS.items(), key=lambda x: -x[1]["contamination_score"]):
        print(f"  {name:38s} {cfg['contamination_score']:6.2f} {cfg['risk_level']:>8s} "
              f"{cfg['test_category']}")
    print(f"\n  Total: {len(SKILLS)} skills")


def main():
    parser = argparse.ArgumentParser(
        description="Behavioral eval for cross-contamination validation"
    )
    parser.add_argument(
        "--skill", action="append", dest="skills",
        help="Specific skill(s) to run (can be repeated)"
    )
    parser.add_argument(
        "--stage", choices=["generate", "judge", "analyze"],
        help="Run only a specific pipeline stage"
    )
    parser.add_argument(
        "--task", action="append", dest="tasks",
        help="Specific task ID(s) to run (can be repeated). "
             "Only the specified tasks are re-generated/re-judged; "
             "others retain results from previous runs."
    )
    parser.add_argument(
        "--patterns-only", action="store_true",
        help="Re-run only deterministic pattern matching (no LLM judge calls). "
             "Preserves existing judge scores. Useful for iterating on expected/anti patterns."
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available skills and exit"
    )
    args = parser.parse_args()

    if args.list:
        list_skills()
        return

    # Resolve skill list (exclude experimental skills unless explicitly named)
    skill_names = args.skills or [
        name for name, cfg in SKILLS.items() if not cfg.get("experimental")
    ]
    valid_skills = validate_skills(skill_names)

    if not valid_skills and args.stage != "analyze":
        print("ERROR: No valid skills to process", file=sys.stderr)
        sys.exit(1)

    task_ids = args.tasks

    print("=" * 60)
    print("BEHAVIORAL EVAL PIPELINE")
    print("=" * 60)
    if args.stage:
        print(f"Stage: {args.stage}")
    print(f"Skills: {len(valid_skills)}")
    if task_ids:
        print(f"Tasks: {', '.join(task_ids)}")
    print()

    # Stage 1: Generate (skipped in patterns-only mode)
    if (args.stage is None or args.stage == "generate") and not args.patterns_only:
        print("--- Stage 1: Generation ---")
        from runner import run_all
        run_all(valid_skills, task_ids=task_ids)
        print()

    # Stage 2: Judge
    if args.stage is None or args.stage == "judge":
        if args.patterns_only:
            print("--- Stage 2: Pattern Matching Only (no LLM calls) ---")
        else:
            print("--- Stage 2: Judging ---")
        from judge import judge_all
        judge_all(valid_skills, patterns_only=args.patterns_only, task_ids=task_ids)
        print()

    # Stage 3: Analyze (always reads all available data)
    if args.stage is None or args.stage == "analyze":
        print("--- Stage 3: Analysis ---")
        from analyze import run_analysis
        run_analysis()
        print()

    print("Pipeline complete.")


if __name__ == "__main__":
    main()
