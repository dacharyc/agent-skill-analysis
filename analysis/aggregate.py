#!/usr/bin/env python3
"""
Aggregate raw validator JSON files into a single validation-summary.json.

Reads all data/raw/{category}/*.json files and produces
data/processed/validation-summary.json with one record per skill.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
OUTPUT = REPO_ROOT / "data" / "processed" / "validation-summary.json"


def extract_skill_record(filepath: Path, category: str) -> dict:
    """Extract a summary record from a single skill's validator JSON."""
    with open(filepath) as f:
        data = json.load(f)

    skill_name = filepath.stem
    skill_dir = data.get("skill_dir", "")

    # Count results by level
    results = data.get("results", [])
    level_counts = {}
    category_counts = {}
    for r in results:
        level = r.get("level", "unknown")
        cat = r.get("category", "unknown")
        level_counts[level] = level_counts.get(level, 0) + 1
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Token counts
    token_counts = data.get("token_counts", {})
    other_token_counts = data.get("other_token_counts", {})
    total_tokens = token_counts.get("total", 0) + other_token_counts.get("total", 0)
    skill_md_tokens = token_counts.get("total", 0)

    record = {
        "name": skill_name,
        "source": category,
        "skill_dir": skill_dir,
        "passed": data.get("passed", False),
        "errors": data.get("errors", 0),
        "warnings": data.get("warnings", 0),
        "passes": level_counts.get("pass", 0),
        "total_tokens": total_tokens,
        "skill_md_tokens": skill_md_tokens,
        "other_tokens": other_token_counts.get("total", 0),
        "result_levels": level_counts,
        "result_categories": category_counts,
        "token_files": [
            f["file"] for f in token_counts.get("files", [])
        ] + [
            f["file"] for f in other_token_counts.get("files", [])
        ],
    }

    # Content analysis (from skill-validator check -o json)
    ca = data.get("content_analysis")
    if ca:
        record["content_analysis"] = ca

    # Risk analysis (from skill-validator check -o json)
    ra = data.get("risk_analysis")
    if ra:
        record["risk_analysis"] = ra

    return record


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    records = []
    for category_dir in sorted(RAW_DIR.iterdir()):
        if not category_dir.is_dir():
            continue
        category = category_dir.name
        for filepath in sorted(category_dir.glob("*.json")):
            record = extract_skill_record(filepath, category)
            records.append(record)

    # Summary stats
    total = len(records)
    passed = sum(1 for r in records if r["passed"])
    failed = total - passed
    total_errors = sum(r["errors"] for r in records)
    total_warnings = sum(r["warnings"] for r in records)

    # Load snapshot metadata if available
    metadata_path = OUTPUT.parent / "snapshot-metadata.json"
    snapshot_metadata = None
    if metadata_path.exists():
        with open(metadata_path) as f:
            snapshot_metadata = json.load(f)

    summary = {
        "total_skills": total,
        "passed": passed,
        "failed": failed,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "snapshot": snapshot_metadata,
        "by_source": {},
        "skills": records,
    }

    # Per-source breakdown
    sources = sorted(set(r["source"] for r in records))
    for source in sources:
        source_records = [r for r in records if r["source"] == source]
        summary["by_source"][source] = {
            "total": len(source_records),
            "passed": sum(1 for r in source_records if r["passed"]),
            "failed": sum(1 for r in source_records if not r["passed"]),
            "errors": sum(r["errors"] for r in source_records),
            "warnings": sum(r["warnings"] for r in source_records),
        }

    with open(OUTPUT, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Aggregated {total} skills → {OUTPUT}")
    print(f"  Passed: {passed}, Failed: {failed}")
    print(f"  Total errors: {total_errors}, Total warnings: {total_warnings}")
    for source in sources:
        s = summary["by_source"][source]
        print(f"  {source}: {s['total']} skills ({s['passed']} passed, {s['failed']} failed)")


if __name__ == "__main__":
    main()
