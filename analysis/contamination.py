#!/usr/bin/env python3
"""
Cross-contamination risk detection for Agent Skills.

Detects skills where code examples in one language/framework could cause
incorrect code generation in another context. For example, a MongoDB skill
with shell examples could cause incorrect Node.js code generation.

Scoring dimensions:
  - multi_interface: Does the skill cover a tool with multiple language interfaces?
  - language_mismatch: Do code block languages differ from the skill's claimed scope?
  - scope_breadth: How many distinct technologies/languages are referenced?
  - risk_score: Overall cross-contamination risk (0-1)

Outputs → data/processed/contamination-risk.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "data" / "skills"
VALIDATION_SUMMARY = REPO_ROOT / "data" / "processed" / "validation-summary.json"
CONTENT_ANALYSIS = REPO_ROOT / "data" / "processed" / "content-analysis.json"
OUTPUT = REPO_ROOT / "data" / "processed" / "contamination-risk.json"

# Tools/platforms known to have multiple language interfaces
MULTI_INTERFACE_TOOLS = {
    "mongodb": ["javascript", "python", "java", "csharp", "go", "ruby", "rust", "shell", "bash", "mongosh"],
    "aws": ["python", "javascript", "typescript", "java", "go", "cli", "bash", "shell", "cloudformation", "terraform"],
    "docker": ["yaml", "bash", "shell", "dockerfile", "python", "javascript"],
    "kubernetes": ["yaml", "bash", "shell", "go", "python"],
    "redis": ["python", "javascript", "java", "go", "ruby", "bash", "shell"],
    "postgresql": ["sql", "python", "javascript", "java", "go", "ruby"],
    "mysql": ["sql", "python", "javascript", "java", "go", "ruby"],
    "elasticsearch": ["json", "python", "javascript", "java", "curl", "bash"],
    "firebase": ["javascript", "typescript", "python", "java", "swift", "kotlin", "dart"],
    "terraform": ["hcl", "bash", "shell", "json", "yaml"],
    "graphql": ["graphql", "javascript", "typescript", "python", "java", "go"],
    "grpc": ["protobuf", "python", "go", "java", "javascript", "csharp"],
    "kafka": ["java", "python", "go", "javascript", "scala"],
    "rabbitmq": ["python", "java", "javascript", "go", "ruby"],
    "stripe": ["python", "javascript", "ruby", "java", "go", "php", "curl"],
}

# Language/technology categories for detecting cross-contamination
LANGUAGE_CATEGORIES = {
    "shell": {"bash", "shell", "sh", "zsh", "fish", "powershell", "cmd", "bat"},
    "javascript": {"javascript", "js", "typescript", "ts", "jsx", "tsx", "node"},
    "python": {"python", "py", "python3"},
    "java": {"java", "kotlin", "scala", "groovy"},
    "systems": {"c", "cpp", "c++", "rust", "go", "zig"},
    "ruby": {"ruby", "rb"},
    "dotnet": {"csharp", "cs", "fsharp", "vb"},
    "config": {"yaml", "yml", "json", "toml", "ini", "xml", "hcl"},
    "query": {"sql", "graphql", "cypher", "sparql"},
    "markup": {"html", "css", "scss", "sass", "less", "markdown", "md"},
    "mobile": {"swift", "kotlin", "dart", "objective-c", "objc"},
}


def detect_multi_interface_tool(name: str, content: str) -> list[str]:
    """Detect if a skill covers a multi-interface tool."""
    matches = []
    name_lower = name.lower()
    content_lower = content.lower()

    for tool, _languages in MULTI_INTERFACE_TOOLS.items():
        if tool in name_lower or tool in content_lower:
            matches.append(tool)
    return matches


def get_language_categories(languages: list[str]) -> set[str]:
    """Map specific languages to broad categories."""
    categories = set()
    for lang in languages:
        lang_lower = lang.lower()
        for category, members in LANGUAGE_CATEGORIES.items():
            if lang_lower in members:
                categories.add(category)
                break
    return categories


def detect_technology_references(content: str) -> set[str]:
    """Detect technology/language references in skill content beyond code blocks."""
    refs = set()
    content_lower = content.lower()

    # Check for framework/runtime mentions
    tech_patterns = {
        "node.js": "javascript",
        "react": "javascript",
        "express": "javascript",
        "django": "python",
        "flask": "python",
        "fastapi": "python",
        "spring": "java",
        "rails": "ruby",
        "asp.net": "dotnet",
        ".net": "dotnet",
        "swift": "mobile",
        "flutter": "mobile",
    }

    for tech, category in tech_patterns.items():
        if tech in content_lower:
            refs.add(category)

    return refs


def analyze_skill(name: str, source: str, code_languages: list[str], skill_dir: str = "") -> dict | None:
    """Analyze cross-contamination risk for a single skill."""
    skill_md = Path(skill_dir) / "SKILL.md" if skill_dir else SKILLS_DIR / source / name / "SKILL.md"
    if not skill_md.exists():
        return None

    content = skill_md.read_text(encoding="utf-8", errors="replace")
    if not content.strip():
        return None

    # Detect multi-interface tools
    multi_tools = detect_multi_interface_tool(name, content)

    # Analyze code block language diversity
    lang_categories = get_language_categories(code_languages)

    # Detect additional technology references
    tech_refs = detect_technology_references(content)

    # Combine all scope indicators
    all_scopes = lang_categories | tech_refs
    scope_breadth = len(all_scopes)

    # Detect language mismatch: code examples in categories different from primary
    # Primary category = most common code block language category
    primary_category = None
    if code_languages:
        from collections import Counter
        lang_cat_list = []
        for lang in code_languages:
            for cat, members in LANGUAGE_CATEGORIES.items():
                if lang.lower() in members:
                    lang_cat_list.append(cat)
                    break
        if lang_cat_list:
            primary_category = Counter(lang_cat_list).most_common(1)[0][0]

    mismatched_categories = lang_categories - {primary_category} if primary_category else set()
    language_mismatch = len(mismatched_categories) > 0

    # Calculate risk score (0-1)
    risk_factors = []

    # Factor 1: Multi-interface tool (0.0 or 0.3)
    if multi_tools:
        risk_factors.append(0.3)

    # Factor 2: Language mismatch in code blocks (0.0-0.4)
    if language_mismatch:
        mismatch_severity = min(len(mismatched_categories) / 3.0, 1.0)
        risk_factors.append(0.4 * mismatch_severity)

    # Factor 3: Scope breadth (0.0-0.3)
    if scope_breadth > 2:
        breadth_score = min((scope_breadth - 2) / 4.0, 1.0)
        risk_factors.append(0.3 * breadth_score)

    risk_score = min(sum(risk_factors), 1.0)

    # Risk level
    if risk_score >= 0.5:
        risk_level = "high"
    elif risk_score >= 0.2:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "name": name,
        "source": source,
        "multi_interface_tools": multi_tools,
        "code_languages": code_languages,
        "language_categories": sorted(lang_categories),
        "primary_category": primary_category,
        "mismatched_categories": sorted(mismatched_categories),
        "language_mismatch": language_mismatch,
        "tech_references": sorted(tech_refs),
        "scope_breadth": scope_breadth,
        "risk_score": round(risk_score, 4),
        "risk_level": risk_level,
    }


def main():
    # Load validation summary
    with open(VALIDATION_SUMMARY) as f:
        summary = json.load(f)

    # Load content analysis for code languages
    with open(CONTENT_ANALYSIS) as f:
        content_data = json.load(f)

    # Build code languages lookup
    code_langs = {}
    for skill in content_data["skills"]:
        key = (skill["name"], skill["source"])
        code_langs[key] = skill.get("code_languages", [])

    results = []
    for skill in summary["skills"]:
        name = skill["name"]
        source = skill["source"]
        languages = code_langs.get((name, source), [])
        skill_dir = skill.get("skill_dir", "")
        analysis = analyze_skill(name, source, languages, skill_dir)
        if analysis:
            results.append(analysis)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump({"skills": results}, f, indent=2)

    # Stats
    high = sum(1 for r in results if r["risk_level"] == "high")
    medium = sum(1 for r in results if r["risk_level"] == "medium")
    low = sum(1 for r in results if r["risk_level"] == "low")

    print(f"Analyzed {len(results)} skills → {OUTPUT}")
    print(f"  Risk levels: {high} high, {medium} medium, {low} low")

    if high > 0:
        print(f"\n  High-risk skills:")
        for r in sorted(results, key=lambda x: x["risk_score"], reverse=True):
            if r["risk_level"] == "high":
                tools = ", ".join(r["multi_interface_tools"]) if r["multi_interface_tools"] else "N/A"
                print(f"    {r['source']}/{r['name']} (score={r['risk_score']}, tools={tools})")


if __name__ == "__main__":
    main()
