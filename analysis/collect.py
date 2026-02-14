#!/usr/bin/env python3
"""
Collect skill validator results into data/raw/.

Reads skills from git submodules in data/skills/ and runs skill-validator
on each skill directory, storing results in data/raw/{category}/.

Also records snapshot metadata (git commit, date, URL) for each source
submodule into data/processed/snapshot-metadata.json.

Sources are configured in SOURCES below. Each source maps a submodule
path to a validator category and describes how skills are laid out
within the submodule.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SKILLS_DIR = DATA_DIR / "skills"
PROCESSED_DIR = DATA_DIR / "processed"

VALIDATOR = Path("/Users/dachary/workspace/skill-validator/skill-validator")

# Source configuration
# Each entry describes one git submodule in data/skills/:
#   submodule: directory name under data/skills/
#   skill_root: relative path within submodule to the directory containing skills
#     Use "." for the submodule root itself
#   type: how skills are organized under skill_root
#     "collection" = each subdir of skill_root is a skill (skills/*/SKILL.md)
#     "single" = skill_root itself is a single skill directory
#     "nested-collection" = subdirs contain further subdirs that are skills
#     "plugins" = each subdir has a skills/ subdir containing skill dirs
#     "find" = recursively find all SKILL.md files under skill_root
#   category: which raw/ subdirectory to file results under
#   exclude: optional list of path fragments to skip (e.g. provider duplicates)
SOURCES = [
    # ── Original sources ──────────────────────────────────────────────
    {
        "submodule": "anthropic-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "anthropic",
    },
    {
        "submodule": "trailofbits-skills",
        "skill_root": "plugins",
        "type": "plugins",
        "category": "trail-of-bits",
    },
    {
        "submodule": "superpowers",
        "skill_root": "skills",
        "type": "collection",
        "category": "k-dense",
    },
    {
        "submodule": "superpowers-skills",
        "skill_root": "skills",
        "type": "nested-collection",
        "category": "k-dense",
    },
    {
        "submodule": "superpowers-lab",
        "skill_root": "skills",
        "type": "collection",
        "category": "k-dense",
    },
    {
        "submodule": "claude-d3js-skill",
        "skill_root": ".",
        "type": "single",
        "category": "community-individual",
    },
    {
        "submodule": "claudeskill-loki-mode",
        "skill_root": ".",
        "type": "find",
        "category": "community-individual",
    },
    {
        "submodule": "playwright-skill",
        "skill_root": "skills/playwright-skill",
        "type": "single",
        "category": "community-individual",
    },
    {
        "submodule": "web-asset-generator",
        "skill_root": "skills/web-asset-generator",
        "type": "single",
        "category": "community-individual",
    },
    {
        "submodule": "ffuf_claude_skill",
        "skill_root": "ffuf-skill",
        "type": "single",
        "category": "community-individual",
    },
    {
        "submodule": "ios-simulator-skill",
        "skill_root": "ios-simulator-skill",
        "type": "single",
        "category": "community-individual",
    },
    {
        "submodule": "claude-scientific-skills",
        "skill_root": "scientific-skills",
        "type": "collection",
        "category": "community-collection",
    },

    # ── Company-published skills ──────────────────────────────────────
    {
        "submodule": "microsoft-skills",
        "skill_root": ".",
        "type": "find",
        "category": "company",
        # Exclude test fixtures and docs-site content
        "exclude": ["tests/", "docs-site/", "docs/"],
    },
    {
        "submodule": "openai-skills",
        "skill_root": "skills",
        "type": "find",
        "category": "company",
    },
    {
        "submodule": "cloudflare-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "company",
    },
    {
        "submodule": "sentry-skills",
        "skill_root": "plugins",
        "type": "plugins",
        "category": "company",
    },
    {
        "submodule": "expo-skills",
        "skill_root": "plugins",
        "type": "plugins",
        "category": "company",
    },
    {
        "submodule": "huggingface-skills",
        "skill_root": ".",
        "type": "find",
        "category": "company",
    },
    {
        "submodule": "hashicorp-skills",
        "skill_root": ".",
        "type": "find",
        "category": "company",
        "exclude": ["scripts/"],
    },
    {
        "submodule": "wordpress-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "company",
    },
    {
        "submodule": "stripe-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "company",
        # Only use canonical skills/, not provider duplicates
    },
    {
        "submodule": "vercel-skills",
        "skill_root": "skills",
        "type": "find",
        "category": "company",
    },
    {
        "submodule": "supabase-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "company",
    },
    {
        "submodule": "google-gemini-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "company",
    },
    {
        "submodule": "google-stitch-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "company",
    },
    {
        "submodule": "vuejs-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "company",
    },
    {
        "submodule": "remotion-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "company",
    },
    {
        "submodule": "neon-skills",
        "skill_root": ".",
        "type": "find",
        "category": "company",
    },
    {
        "submodule": "better-auth-skills",
        "skill_root": ".",
        "type": "find",
        "category": "company",
    },
    {
        "submodule": "callstack-skills",
        "skill_root": ".",
        "type": "find",
        "category": "company",
    },
    {
        "submodule": "tinybird-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "company",
    },
    {
        "submodule": "ast-grep-skill",
        "skill_root": "ast-grep/skills/ast-grep",
        "type": "single",
        "category": "company",
    },
    {
        "submodule": "black-forest-labs-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "company",
    },
    {
        "submodule": "solana-skills",
        "skill_root": "skill",
        "type": "single",
        "category": "company",
    },

    # ── Community notable ─────────────────────────────────────────────
    {
        "submodule": "antfu-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "community-collection",
    },
    {
        "submodule": "obsidian-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "community-collection",
    },

    # ── Vertical / domain-specific ────────────────────────────────────
    {
        "submodule": "legal-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "vertical",
    },
    {
        "submodule": "protein-design-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "vertical",
    },
    {
        "submodule": "devops-skills",
        "skill_root": ".",
        "type": "find",
        "category": "vertical",
    },
    {
        "submodule": "zephyr-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "vertical",
    },

    # ── Security ──────────────────────────────────────────────────────
    {
        "submodule": "clawsec-skills",
        "skill_root": "skills",
        "type": "collection",
        "category": "security",
    },
]


def get_submodule_metadata(submodule_path: Path) -> dict:
    """Get git commit SHA, date, and remote URL for a submodule."""
    meta = {
        "commit": None,
        "commit_date": None,
        "remote_url": None,
        "snapshot_date": datetime.now(timezone.utc).isoformat(),
    }

    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H%n%aI"],
            capture_output=True, text=True, cwd=str(submodule_path),
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            meta["commit"] = lines[0]
            meta["commit_date"] = lines[1] if len(lines) > 1 else None
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=str(submodule_path),
        )
        if result.returncode == 0:
            meta["remote_url"] = result.stdout.strip()
    except Exception:
        pass

    return meta


def validate_skill(skill_dir: Path) -> dict | None:
    """Run skill-validator on a skill directory and return JSON result."""
    try:
        result = subprocess.run(
            [str(VALIDATOR), "-o", "json", str(skill_dir)],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout.strip():
            return json.loads(result.stdout)
        else:
            print(f"  WARNING: No output from validator for {skill_dir}", file=sys.stderr)
            if result.stderr:
                print(f"  stderr: {result.stderr.strip()}", file=sys.stderr)
            return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  ERROR validating {skill_dir}: {e}", file=sys.stderr)
        return None


# Tracks saved skills per category: {category: {skill_name: submodule}}
# Used to detect and resolve name collisions across submodules.
_saved_skills = {}


def save_result(result: dict, category: str, skill_name: str, submodule: str):
    """Save a single skill's validator result, resolving name collisions.

    If another submodule already saved a skill with the same name in this
    category, both are renamed to {submodule}--{skill_name} to avoid
    silent data loss.
    """
    out_dir = RAW_DIR / category
    out_dir.mkdir(parents=True, exist_ok=True)

    if category not in _saved_skills:
        _saved_skills[category] = {}

    if skill_name in _saved_skills[category]:
        existing_submodule = _saved_skills[category][skill_name]
        if existing_submodule != submodule:
            # Collision: rename the previously saved file
            old_path = out_dir / f"{skill_name}.json"
            renamed_path = out_dir / f"{existing_submodule}--{skill_name}.json"
            if old_path.exists() and not renamed_path.exists():
                old_path.rename(renamed_path)
                print(f"  COLLISION: '{skill_name}' in {category}/ — "
                      f"renamed {existing_submodule} copy, prefixing both",
                      file=sys.stderr)
            _saved_skills[category][skill_name] = None  # Mark as multi-source

            # Save new one with prefix
            out_path = out_dir / f"{submodule}--{skill_name}.json"
            with open(out_path, "w") as f:
                json.dump(result, f, indent=2)
            return

    if skill_name in _saved_skills[category] and _saved_skills[category][skill_name] is None:
        # Already known collision — always prefix
        out_path = out_dir / f"{submodule}--{skill_name}.json"
    else:
        # First time seeing this name in this category
        out_path = out_dir / f"{skill_name}.json"
        _saved_skills[category][skill_name] = submodule

    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)


def validate_and_save(skill_dir: Path, category: str, skill_name: str, submodule: str) -> int:
    """Validate a single skill directory, handle multi-skill results, save."""
    result = validate_skill(skill_dir)
    if result is None:
        return 0

    if "skills" in result:
        count = 0
        for skill_result in result["skills"]:
            sub_name = Path(skill_result["skill_dir"]).name
            save_result(skill_result, category, sub_name, submodule)
            count += 1
        return count
    else:
        save_result(result, category, skill_name, submodule)
        return 1


def has_skill_md(skill_dir: Path) -> bool:
    """Check if a directory is a skill or contains skills.

    Returns True if:
    - The directory itself contains a SKILL.md (single skill), or
    - Any immediate subdirectory contains a SKILL.md (multi-skill directory)

    This ensures we don't skip multi-skill directories (like document-skills/
    which contains xlsx/, pdf/, etc. each with their own SKILL.md) while still
    filtering out support directories (like scripts/, _shared/).
    """
    for child in skill_dir.iterdir():
        if child.is_file() and child.name.upper() == "SKILL.MD":
            return True
        if child.is_dir():
            for grandchild in child.iterdir():
                if grandchild.is_file() and grandchild.name.upper() == "SKILL.MD":
                    return True
    return False


def process_single_skill(skill_dir: Path, category: str, skill_name: str, submodule: str) -> int:
    """Validate a single skill and save results."""
    if not skill_dir.exists():
        print(f"  SKIP: {skill_dir} does not exist", file=sys.stderr)
        return 0
    return validate_and_save(skill_dir, category, skill_name, submodule)


def process_collection(base_dir: Path, category: str, submodule: str) -> int:
    """Process a directory containing skill subdirectories."""
    if not base_dir.exists():
        print(f"  SKIP: {base_dir} does not exist", file=sys.stderr)
        return 0

    count = 0
    for entry in sorted(base_dir.iterdir()):
        if entry.is_dir() and not entry.name.startswith("."):
            if not has_skill_md(entry):
                print(f"  SKIP: {entry.name}/ has no SKILL.md (not a skill)", file=sys.stderr)
                continue
            count += validate_and_save(entry, category, entry.name, submodule)
    return count


def process_nested_collection(base_dir: Path, category: str, submodule: str) -> int:
    """Process a directory of category subdirs, each containing skill subdirs."""
    if not base_dir.exists():
        print(f"  SKIP: {base_dir} does not exist", file=sys.stderr)
        return 0

    count = 0
    for cat_dir in sorted(base_dir.iterdir()):
        if cat_dir.is_dir() and not cat_dir.name.startswith("."):
            for entry in sorted(cat_dir.iterdir()):
                if entry.is_dir() and not entry.name.startswith("."):
                    if not has_skill_md(entry):
                        print(f"  SKIP: {cat_dir.name}/{entry.name}/ has no SKILL.md (not a skill)", file=sys.stderr)
                        continue
                    count += validate_and_save(entry, category, entry.name, submodule)
    return count


def process_plugins(base_dir: Path, category: str, submodule: str) -> int:
    """Process plugin directories: {base_dir}/{plugin}/skills/{skill}/SKILL.md"""
    if not base_dir.exists():
        print(f"  SKIP: {base_dir} does not exist", file=sys.stderr)
        return 0

    count = 0
    for plugin_dir in sorted(base_dir.iterdir()):
        if not plugin_dir.is_dir() or plugin_dir.name.startswith("."):
            continue
        skills_dir = plugin_dir / "skills"
        if not skills_dir.exists():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                if not has_skill_md(skill_dir):
                    print(f"  SKIP: {plugin_dir.name}/skills/{skill_dir.name}/ has no SKILL.md (not a skill)", file=sys.stderr)
                    continue
                count += validate_and_save(skill_dir, category, skill_dir.name, submodule)
    return count


def process_find(base_dir: Path, category: str, submodule: str, exclude: list[str] = None) -> int:
    """Recursively find all SKILL.md files and validate their parent directories.

    This handles repos with non-standard layouts by finding every SKILL.md
    and treating its parent directory as a skill.
    """
    if not base_dir.exists():
        print(f"  SKIP: {base_dir} does not exist", file=sys.stderr)
        return 0

    exclude = exclude or []

    # Find all SKILL.md files (case-insensitive)
    skill_dirs = set()
    for skill_md in base_dir.rglob("SKILL.[mM][dD]"):
        # Check exclusions
        rel_path = str(skill_md.relative_to(base_dir))
        if any(ex in rel_path for ex in exclude):
            continue
        skill_dirs.add(skill_md.parent)

    # Detect intra-submodule name collisions by checking for duplicate dir names
    sorted_dirs = sorted(skill_dirs)
    name_counts = {}
    for d in sorted_dirs:
        name_counts[d.name] = name_counts.get(d.name, 0) + 1

    count = 0
    for skill_dir in sorted_dirs:
        if name_counts[skill_dir.name] > 1:
            # Use grandparent--name to disambiguate (e.g. "iac-terraform--skills")
            skill_name = f"{skill_dir.parent.name}--{skill_dir.name}"
            print(f"  DISAMBIGUATE: {skill_dir.name} → {skill_name} "
                  f"(multiple dirs named '{skill_dir.name}' in {submodule})",
                  file=sys.stderr)
        else:
            skill_name = skill_dir.name
        count += validate_and_save(skill_dir, category, skill_name, submodule)
    return count


def main():
    if not VALIDATOR.exists():
        print(f"ERROR: skill-validator not found at {VALIDATOR}", file=sys.stderr)
        sys.exit(1)

    # Collect metadata for all submodules
    metadata = {
        "analysis_date": datetime.now(timezone.utc).isoformat(),
        "sources": {},
    }

    total = 0
    for source in SOURCES:
        submodule = source["submodule"]
        skill_root = source["skill_root"]
        stype = source["type"]
        category = source["category"]
        exclude = source.get("exclude", [])

        submodule_path = SKILLS_DIR / submodule
        if not submodule_path.exists():
            print(f"SKIP: submodule {submodule} not found at {submodule_path}", file=sys.stderr)
            continue

        # Record submodule metadata
        if submodule not in metadata["sources"]:
            meta = get_submodule_metadata(submodule_path)
            meta["category"] = category
            metadata["sources"][submodule] = meta

        # Resolve skill root
        root = submodule_path / skill_root if skill_root != "." else submodule_path

        print(f"Processing {submodule} ({stype}) → {category}/")

        if stype == "single":
            count = process_single_skill(root, category, submodule, submodule)
        elif stype == "collection":
            count = process_collection(root, category, submodule)
        elif stype == "nested-collection":
            count = process_nested_collection(root, category, submodule)
        elif stype == "plugins":
            count = process_plugins(root, category, submodule)
        elif stype == "find":
            count = process_find(root, category, submodule, exclude)
        else:
            print(f"  Unknown type: {stype}", file=sys.stderr)
            count = 0

        metadata["sources"][submodule]["skill_count"] = count
        print(f"  → {count} skills collected")
        total += count

    # Save metadata
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    metadata_path = PROCESSED_DIR / "snapshot-metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nTotal: {total} skills collected")
    print(f"Raw results: {RAW_DIR}")
    print(f"Snapshot metadata: {metadata_path}")


if __name__ == "__main__":
    main()
