#!/usr/bin/env python3
"""
Merge all analysis outputs into a single combined.json.

Combines:
  - data/processed/validation-summary.json
  - data/processed/content-analysis.json
  - data/processed/contamination-risk.json

Produces → data/processed/combined.json
One record per skill with all metrics.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = REPO_ROOT / "data" / "processed"
OUTPUT = PROCESSED / "combined.json"


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def main():
    validation = load_json(PROCESSED / "validation-summary.json")
    content = load_json(PROCESSED / "content-analysis.json")
    contamination = load_json(PROCESSED / "contamination-risk.json")

    # Index content and contamination by (name, source)
    content_index = {}
    for skill in content.get("skills", []):
        key = (skill["name"], skill["source"])
        content_index[key] = skill

    contam_index = {}
    for skill in contamination.get("skills", []):
        key = (skill["name"], skill["source"])
        contam_index[key] = skill

    # Build combined records
    combined_skills = []
    for skill in validation["skills"]:
        key = (skill["name"], skill["source"])

        record = {
            # Validation data
            "name": skill["name"],
            "source": skill["source"],
            "passed": skill["passed"],
            "errors": skill["errors"],
            "warnings": skill["warnings"],
            "passes": skill["passes"],
            "total_tokens": skill["total_tokens"],
            "skill_md_tokens": skill["skill_md_tokens"],
            "other_tokens": skill["other_tokens"],
        }

        # Content analysis data
        ca = content_index.get(key, {})
        record["word_count"] = ca.get("word_count", 0)
        record["code_block_count"] = ca.get("code_block_count", 0)
        record["code_block_ratio"] = ca.get("code_block_ratio", 0)
        record["code_languages"] = ca.get("code_languages", [])
        record["sentence_count"] = ca.get("sentence_count", 0)
        record["imperative_ratio"] = ca.get("imperative_ratio", 0)
        record["information_density"] = ca.get("information_density", 0)
        record["instruction_specificity"] = ca.get("instruction_specificity", 0)
        record["section_count"] = ca.get("section_count", 0)
        record["list_item_count"] = ca.get("list_item_count", 0)

        # LLM judge scores (if available)
        llm = ca.get("llm_scores", {})
        record["llm_clarity"] = llm.get("clarity")
        record["llm_coherence"] = llm.get("coherence")
        record["llm_relevance"] = llm.get("relevance")
        record["llm_actionability"] = llm.get("actionability")
        record["llm_completeness"] = llm.get("completeness")
        record["llm_overall"] = llm.get("overall")
        record["llm_assessment"] = llm.get("brief_assessment")

        # Contamination risk data
        cr = contam_index.get(key, {})
        record["multi_interface_tools"] = cr.get("multi_interface_tools", [])
        record["language_mismatch"] = cr.get("language_mismatch", False)
        record["scope_breadth"] = cr.get("scope_breadth", 0)
        record["risk_score"] = cr.get("risk_score", 0)
        record["risk_level"] = cr.get("risk_level", "low")
        record["mismatched_categories"] = cr.get("mismatched_categories", [])

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
            "risk_distribution": {
                "high": sum(1 for s in combined_skills if s["risk_level"] == "high"),
                "medium": sum(1 for s in combined_skills if s["risk_level"] == "medium"),
                "low": sum(1 for s in combined_skills if s["risk_level"] == "low"),
            },
            "has_llm_scores": sum(1 for s in combined_skills if s["llm_overall"] is not None),
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
            "avg_risk_score": round(sum(s["risk_score"] for s in source_skills) / len(source_skills), 3),
        }

    with open(OUTPUT, "w") as f:
        json.dump(combined, f, indent=2)

    print(f"Combined {len(combined_skills)} skills → {OUTPUT}")
    print(f"  Passed: {combined['summary']['passed']}, Failed: {combined['summary']['failed']}")
    print(f"  Avg tokens: {combined['summary']['avg_tokens']}")
    print(f"  LLM scores available: {combined['summary']['has_llm_scores']}")
    print(f"  Risk: {combined['summary']['risk_distribution']}")


if __name__ == "__main__":
    main()
