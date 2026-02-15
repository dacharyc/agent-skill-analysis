#!/usr/bin/env python3
"""
Merge all analysis outputs into a single combined.json.

Combines:
  - data/processed/validation-summary.json (includes content_analysis and contamination_analysis)
  - data/processed/llm-scores.json (optional, from llm_judge.py)

Produces → data/processed/combined.json
One record per skill with all metrics.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = REPO_ROOT / "data" / "processed"
SKILLS_DIR = REPO_ROOT / "data" / "skills"
OUTPUT = PROCESSED / "combined.json"


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _compute_reference_stats(skills: list[dict]) -> dict:
    """Compute aggregate reference file statistics."""
    with_refs = [s for s in skills if s["ref_file_count"] > 0]
    total_ref_files = sum(s["ref_file_count"] for s in skills)

    if with_refs:
        avg_ref_info_density = round(sum(s["ref_information_density"] for s in with_refs) / len(with_refs), 3)
        avg_ref_contamination = round(sum(s["ref_contamination_score"] for s in with_refs) / len(with_refs), 3)
    else:
        avg_ref_info_density = 0
        avg_ref_contamination = 0

    return {
        "skills_with_refs": len(with_refs),
        "total_ref_files": total_ref_files,
        "avg_ref_info_density": avg_ref_info_density,
        "avg_ref_contamination_score": avg_ref_contamination,
        "refs_with_contamination": sum(s["refs_with_contamination"] for s in skills),
        "oversized_refs": sum(1 for s in skills if s["ref_max_file_tokens"] > 50000),
        "refs_larger_than_skill": sum(1 for s in skills if s["ref_token_ratio"] > 1),
    }


def _build_github_url_index(snapshot: dict) -> dict[str, tuple[str, str]]:
    """Build a mapping from submodule directory name to (github_base_url, commit_sha)."""
    index = {}
    for submodule_name, info in snapshot.get("sources", {}).items():
        remote = info.get("remote_url", "")
        commit = info.get("commit", "")
        # Convert git remote URL to GitHub browse URL
        base = re.sub(r"\.git$", "", remote)
        index[submodule_name] = (base, commit)
    return index


def _compute_github_url(skill_dir: str, url_index: dict[str, tuple[str, str]]) -> str:
    """Compute a GitHub URL for a skill given its local skill_dir path."""
    skills_dir_str = str(SKILLS_DIR)
    if not skill_dir.startswith(skills_dir_str):
        return ""

    # skill_dir looks like: .../data/skills/<submodule>/<path_within_repo>
    rel = skill_dir[len(skills_dir_str):].lstrip("/")
    parts = rel.split("/", 1)
    submodule = parts[0]
    path_in_repo = parts[1] if len(parts) > 1 else ""

    if submodule not in url_index:
        return ""

    base_url, commit = url_index[submodule]
    ref = commit if commit else "main"
    if path_in_repo:
        return f"{base_url}/tree/{ref}/{path_in_repo}"
    return f"{base_url}/tree/{ref}"


def main():
    validation = load_json(PROCESSED / "validation-summary.json")

    # LLM scores are optional — the pipeline works without them
    llm_scores_path = PROCESSED / "llm-scores.json"
    llm_index = {}
    if llm_scores_path.exists():
        llm_data = load_json(llm_scores_path)
        for skill in llm_data.get("skills", []):
            key = (skill["name"], skill["source"])
            llm_index[key] = skill.get("llm_scores", {})

    # Build GitHub URL index from snapshot metadata
    url_index = _build_github_url_index(validation.get("snapshot", {}))

    # Build combined records
    combined_skills = []
    for skill in validation["skills"]:
        key = (skill["name"], skill["source"])

        # Content analysis from skill-validator check (embedded in validation-summary)
        ca = skill.get("content_analysis", {})
        # Contamination analysis from skill-validator check (embedded in validation-summary)
        cr = skill.get("contamination_analysis", {})

        record = {
            # Validation data
            "name": skill["name"],
            "source": skill["source"],
            "github_url": _compute_github_url(skill.get("skill_dir", ""), url_index),
            "passed": skill["passed"],
            "errors": skill["errors"],
            "warnings": skill["warnings"],
            "passes": skill["passes"],
            "total_tokens": skill["total_tokens"],
            "skill_md_tokens": skill["skill_md_tokens"],
            "ref_tokens": skill.get("ref_tokens", 0),
            "asset_tokens": skill.get("asset_tokens", 0),
            "nonstandard_tokens": skill.get("nonstandard_tokens", 0),

            # Content analysis data
            "word_count": ca.get("word_count", 0),
            "code_block_count": ca.get("code_block_count", 0),
            "code_block_ratio": ca.get("code_block_ratio", 0),
            "code_languages": ca.get("code_languages", []),
            "sentence_count": ca.get("sentence_count", 0),
            "imperative_ratio": ca.get("imperative_ratio", 0),
            "information_density": ca.get("information_density", 0),
            "instruction_specificity": ca.get("instruction_specificity", 0),
            "section_count": ca.get("section_count", 0),
            "list_item_count": ca.get("list_item_count", 0),

            # Contamination analysis data
            "multi_interface_tools": cr.get("multi_interface_tools", []),
            "language_mismatch": cr.get("language_mismatch", False),
            "scope_breadth": cr.get("scope_breadth", 0),
            "contamination_score": cr.get("contamination_score", 0),
            "contamination_level": cr.get("contamination_level", "low"),
            "mismatched_categories": cr.get("mismatched_categories", []),

            # Link health (separate from structural pass/fail)
            "link_errors": skill.get("link_errors", 0),
            "broken_links": skill.get("broken_links", []),

            # Reference file metrics
            "ref_file_count": skill.get("ref_file_count", 0),
            "ref_total_tokens": skill.get("ref_total_tokens", 0),
            "ref_token_ratio": skill.get("ref_token_ratio", 0),
            "ref_max_file_tokens": skill.get("ref_max_file_tokens", 0),
            "ref_word_count": skill.get("ref_word_count", 0),
            "ref_code_block_count": skill.get("ref_code_block_count", 0),
            "ref_information_density": skill.get("ref_information_density", 0),
            "ref_contamination_score": skill.get("ref_contamination_score", 0),
            "ref_contamination_level": skill.get("ref_contamination_level", "low"),
            "refs_with_contamination": skill.get("refs_with_contamination", 0),
            "ref_code_languages": skill.get("ref_code_languages", []),
        }

        # LLM judge scores (if available)
        llm = llm_index.get(key, {})
        record["llm_clarity"] = llm.get("clarity")
        record["llm_coherence"] = llm.get("coherence")
        record["llm_relevance"] = llm.get("relevance")
        record["llm_actionability"] = llm.get("actionability")
        record["llm_completeness"] = llm.get("completeness")
        record["llm_overall"] = llm.get("overall")
        record["llm_assessment"] = llm.get("brief_assessment")

        combined_skills.append(record)

    combined = {
        "total_skills": len(combined_skills),
        "snapshot": validation.get("snapshot"),
        "summary": {
            "passed": sum(1 for s in combined_skills if s["passed"]),
            "failed": sum(1 for s in combined_skills if not s["passed"]),
            "total_errors": sum(s["errors"] for s in combined_skills),
            "total_warnings": sum(s["warnings"] for s in combined_skills),
            "avg_tokens": round(sum(s["total_tokens"] for s in combined_skills) / len(combined_skills)) if combined_skills else 0,
            "avg_information_density": round(sum(s["information_density"] for s in combined_skills) / len(combined_skills), 3) if combined_skills else 0,
            "avg_instruction_specificity": round(sum(s["instruction_specificity"] for s in combined_skills) / len(combined_skills), 3) if combined_skills else 0,
            "contamination_distribution": {
                "high": sum(1 for s in combined_skills if s["contamination_level"] == "high"),
                "medium": sum(1 for s in combined_skills if s["contamination_level"] == "medium"),
                "low": sum(1 for s in combined_skills if s["contamination_level"] == "low"),
            },
            "has_llm_scores": sum(1 for s in combined_skills if s["llm_overall"] is not None),
            "link_health": {
                "total_broken": sum(s["link_errors"] for s in combined_skills),
                "skills_with_broken_links": sum(1 for s in combined_skills if s["link_errors"] > 0),
            },
            "reference_stats": _compute_reference_stats(combined_skills),
        },
        "by_source": {},
        "skills": combined_skills,
    }

    # Per-source breakdown
    sources = sorted(set(s["source"] for s in combined_skills))
    for source in sources:
        source_skills = [s for s in combined_skills if s["source"] == source]
        combined["by_source"][source] = {
            "total": len(source_skills),
            "passed": sum(1 for s in source_skills if s["passed"]),
            "failed": sum(1 for s in source_skills if not s["passed"]),
            "avg_tokens": round(sum(s["total_tokens"] for s in source_skills) / len(source_skills)),
            "avg_contamination_score": round(sum(s["contamination_score"] for s in source_skills) / len(source_skills), 3),
            "avg_ref_contamination_score": round(sum(s["ref_contamination_score"] for s in source_skills) / len(source_skills), 3),
            "broken_link_count": sum(s["link_errors"] for s in source_skills),
        }

    with open(OUTPUT, "w") as f:
        json.dump(combined, f, indent=2)

    print(f"Combined {len(combined_skills)} skills → {OUTPUT}")
    print(f"  Passed: {combined['summary']['passed']}, Failed: {combined['summary']['failed']}")
    print(f"  Avg tokens: {combined['summary']['avg_tokens']}")
    print(f"  LLM scores available: {combined['summary']['has_llm_scores']}")
    print(f"  Contamination: {combined['summary']['contamination_distribution']}")
    lh = combined['summary']['link_health']
    print(f"  Link health: {lh['total_broken']} broken links across {lh['skills_with_broken_links']} skills")
    rs = combined['summary']['reference_stats']
    print(f"  References: {rs['skills_with_refs']} skills with refs, {rs['total_ref_files']} total files, {rs['oversized_refs']} oversized (>50k tokens)")


if __name__ == "__main__":
    main()
