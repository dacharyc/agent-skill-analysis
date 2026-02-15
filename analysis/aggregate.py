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

    # Token counts — split token_counts.files into SKILL.md / references / assets
    # token_counts contains spec-compliant files: "SKILL.md body", "references/*", "assets/*"
    # other_token_counts contains everything else (non-standard dirs, root-level files)
    token_counts = data.get("token_counts", {})
    other_token_counts = data.get("other_token_counts", {})

    skill_md_tokens = 0
    ref_tokens = 0
    asset_tokens = 0
    ref_file_tokens = []    # per-file tokens for references/
    asset_file_tokens = []  # per-file tokens for assets/
    for f in token_counts.get("files", []):
        name = f.get("file", "")
        tokens = f.get("tokens", 0)
        if name == "SKILL.md body":
            skill_md_tokens = tokens
        elif name.startswith("references/"):
            ref_tokens += tokens
            ref_file_tokens.append(tokens)
        elif name.startswith("assets/"):
            asset_tokens += tokens
            asset_file_tokens.append(tokens)
        else:
            # Unexpected entry in token_counts — count toward SKILL.md
            skill_md_tokens += tokens

    nonstandard_tokens = other_token_counts.get("total", 0)
    total_tokens = skill_md_tokens + ref_tokens + asset_tokens + nonstandard_tokens

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
        "ref_tokens": ref_tokens,
        "asset_tokens": asset_tokens,
        "nonstandard_tokens": nonstandard_tokens,
        "result_levels": level_counts,
        "result_categories": category_counts,
        "token_files": [
            f["file"] for f in token_counts.get("files", [])
        ] + [
            f["file"] for f in other_token_counts.get("files", [])
        ],
    }

    # Link health (separated from structural pass/fail)
    link_results = data.get("link_results", [])
    link_errors = data.get("link_errors", 0)
    link_warnings = data.get("link_warnings", 0)
    broken_links = []
    for r in link_results:
        if r.get("level") == "error":
            # Extract URL from message (format: "URL (error details)")
            msg = r.get("message", "")
            url = msg.split(" (")[0] if " (" in msg else msg
            broken_links.append(url)

    record["link_errors"] = link_errors
    record["link_warnings"] = link_warnings
    record["broken_links"] = broken_links

    # Content analysis (from skill-validator check -o json)
    ca = data.get("content_analysis")
    if ca:
        record["content_analysis"] = ca

    # Contamination analysis (from skill-validator check -o json)
    ra = data.get("contamination_analysis")
    if ra:
        record["contamination_analysis"] = ra

    # Reference file analysis (aggregate and per-file)
    rca = data.get("references_content_analysis")
    if rca:
        record["references_content_analysis"] = rca
    rcr = data.get("references_contamination_analysis")
    if rcr:
        record["references_contamination_analysis"] = rcr
    ref_reports = data.get("reference_reports")
    if ref_reports:
        record["reference_reports"] = ref_reports

    # Derived reference fields
    ref_report_list = ref_reports or []
    record["ref_file_count"] = len(ref_report_list)
    record["ref_total_tokens"] = ref_tokens

    if skill_md_tokens > 0 and ref_tokens > 0:
        record["ref_token_ratio"] = round(ref_tokens / skill_md_tokens, 2)
    else:
        record["ref_token_ratio"] = 0

    record["ref_max_file_tokens"] = max(ref_file_tokens, default=0)

    record["ref_word_count"] = rca.get("word_count", 0) if rca else 0
    record["ref_code_block_count"] = rca.get("code_block_count", 0) if rca else 0
    record["ref_information_density"] = rca.get("information_density", 0) if rca else 0
    record["ref_contamination_score"] = rcr.get("contamination_score", 0) if rcr else 0
    record["ref_contamination_level"] = rcr.get("contamination_level", "low") if rcr else "low"

    # Count reference files with medium+ contamination
    record["refs_with_contamination"] = sum(
        1 for r in ref_report_list
        if r.get("contamination_analysis", {}).get("contamination_level", "low") in ("medium", "high")
    )

    # Deduplicated sorted list of languages across all reference files
    all_langs = set()
    for r in ref_report_list:
        for lang in r.get("content_analysis", {}).get("code_languages", []):
            all_langs.add(lang)
    record["ref_code_languages"] = sorted(all_langs)

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

    # Link health summary
    total_link_errors = sum(r["link_errors"] for r in records)
    skills_with_broken_links = sum(1 for r in records if r["link_errors"] > 0)
    summary["link_health"] = {
        "total_link_errors": total_link_errors,
        "total_link_warnings": sum(r["link_warnings"] for r in records),
        "skills_with_broken_links": skills_with_broken_links,
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
            "broken_link_count": sum(r["link_errors"] for r in source_records),
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
