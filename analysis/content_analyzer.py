#!/usr/bin/env python3
"""
Content analysis of SKILL.md files.

Computes per-skill metrics:
  - information_density: ratio of code blocks + imperative sentences to total content
  - instruction_specificity: scoring based on language markers (must/always vs may/consider)
  - code_block_count: number of fenced code blocks
  - code_block_ratio: proportion of content that is code blocks
  - imperative_ratio: proportion of sentences starting with imperative verbs
  - word_count: total words in SKILL.md

Outputs → data/processed/content-analysis.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "data" / "skills"
VALIDATION_SUMMARY = REPO_ROOT / "data" / "processed" / "validation-summary.json"
OUTPUT = REPO_ROOT / "data" / "processed" / "content-analysis.json"

# Strong directive language markers
STRONG_MARKERS = [
    r"\bmust\b", r"\balways\b", r"\bnever\b", r"\bshall\b",
    r"\brequired\b", r"\bdo not\b", r"\bdon't\b", r"\bensure\b",
    r"\bcritical\b", r"\bmandatory\b",
]

# Weak/advisory language markers
WEAK_MARKERS = [
    r"\bmay\b", r"\bconsider\b", r"\bcould\b", r"\bmight\b",
    r"\boptional\b", r"\bpossibly\b", r"\bsuggested\b",
    r"\bprefer\b", r"\btry to\b", r"\bif possible\b",
]

# Common imperative verbs for instructions
IMPERATIVE_VERBS = [
    "use", "run", "create", "add", "set", "install", "configure",
    "write", "read", "check", "verify", "make", "build", "test",
    "ensure", "include", "remove", "delete", "update", "call",
    "import", "export", "define", "implement", "return", "pass",
    "handle", "parse", "generate", "format", "validate", "convert",
    "follow", "apply", "start", "stop", "avoid", "keep", "do",
    "execute", "open", "close", "save", "load", "send", "receive",
]


def extract_code_blocks(content: str) -> list[str]:
    """Extract fenced code blocks from markdown content."""
    pattern = r"```[\w]*\n(.*?)```"
    return re.findall(pattern, content, re.DOTALL)


def get_code_block_languages(content: str) -> list[str]:
    """Extract language identifiers from fenced code blocks."""
    pattern = r"```(\w+)"
    return re.findall(pattern, content)


def count_sentences(text: str) -> list[str]:
    """Split text into sentences (rough approximation)."""
    # Remove code blocks first
    text = re.sub(r"```[\w]*\n.*?```", "", text, flags=re.DOTALL)
    # Remove inline code
    text = re.sub(r"`[^`]+`", "", text)
    # Split on sentence boundaries
    sentences = re.split(r"[.!?]\s+|[.!?]$|\n\n+", text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]


def count_imperative_sentences(sentences: list[str]) -> int:
    """Count sentences that start with imperative verbs."""
    count = 0
    for sentence in sentences:
        # Get first word, stripping markdown formatting
        cleaned = re.sub(r"^[#*\->\s]+", "", sentence).split()
        first_word = cleaned[0].lower() if cleaned else ""
        if first_word in IMPERATIVE_VERBS:
            count += 1
    return count


def count_marker_matches(text: str, patterns: list[str]) -> int:
    """Count total matches for a list of regex patterns."""
    total = 0
    text_lower = text.lower()
    for pattern in patterns:
        total += len(re.findall(pattern, text_lower))
    return total


def analyze_skill(name: str, source: str, skill_dir: str) -> dict | None:
    """Analyze a single skill's SKILL.md content."""
    skill_md = Path(skill_dir) / "SKILL.md"
    if not skill_md.exists():
        return None

    content = skill_md.read_text(encoding="utf-8", errors="replace")
    if not content.strip():
        return None

    # Basic metrics
    words = content.split()
    word_count = len(words)

    # Code block analysis
    code_blocks = extract_code_blocks(content)
    code_block_count = len(code_blocks)
    code_block_words = sum(len(block.split()) for block in code_blocks)
    code_block_ratio = code_block_words / word_count if word_count > 0 else 0

    code_languages = get_code_block_languages(content)

    # Sentence analysis
    sentences = count_sentences(content)
    sentence_count = len(sentences)
    imperative_count = count_imperative_sentences(sentences)
    imperative_ratio = imperative_count / sentence_count if sentence_count > 0 else 0

    # Information density: code + imperative content as proportion of total
    information_density = (code_block_ratio * 0.5) + (imperative_ratio * 0.5)

    # Language marker analysis
    strong_count = count_marker_matches(content, STRONG_MARKERS)
    weak_count = count_marker_matches(content, WEAK_MARKERS)
    total_markers = strong_count + weak_count

    # Instruction specificity: proportion of strong markers
    if total_markers > 0:
        instruction_specificity = strong_count / total_markers
    else:
        instruction_specificity = 0.0

    # Section count (H2+ headers)
    sections = re.findall(r"^#{2,}\s+", content, re.MULTILINE)
    section_count = len(sections)

    # List item count
    list_items = re.findall(r"^[\s]*[-*+]\s+|^\s*\d+\.\s+", content, re.MULTILINE)
    list_item_count = len(list_items)

    return {
        "name": name,
        "source": source,
        "skill_dir": skill_dir,
        "word_count": word_count,
        "code_block_count": code_block_count,
        "code_block_ratio": round(code_block_ratio, 4),
        "code_languages": code_languages,
        "sentence_count": sentence_count,
        "imperative_count": imperative_count,
        "imperative_ratio": round(imperative_ratio, 4),
        "information_density": round(information_density, 4),
        "strong_markers": strong_count,
        "weak_markers": weak_count,
        "instruction_specificity": round(instruction_specificity, 4),
        "section_count": section_count,
        "list_item_count": list_item_count,
    }


def main():
    # Load validation summary to get skill list
    with open(VALIDATION_SUMMARY) as f:
        summary = json.load(f)

    results = []
    missing = 0
    for skill in summary["skills"]:
        name = skill["name"]
        source = skill["source"]
        skill_dir = skill.get("skill_dir", "")
        analysis = analyze_skill(name, source, skill_dir)
        if analysis:
            results.append(analysis)
        else:
            missing += 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump({"skills": results}, f, indent=2)

    print(f"Analyzed {len(results)} skills → {OUTPUT}")
    if missing:
        print(f"  {missing} skills had no SKILL.md file available")

    # Quick stats
    if results:
        avg_density = sum(r["information_density"] for r in results) / len(results)
        avg_specificity = sum(r["instruction_specificity"] for r in results) / len(results)
        avg_words = sum(r["word_count"] for r in results) / len(results)
        print(f"  Avg information density: {avg_density:.3f}")
        print(f"  Avg instruction specificity: {avg_specificity:.3f}")
        print(f"  Avg word count: {avg_words:.0f}")


if __name__ == "__main__":
    main()
