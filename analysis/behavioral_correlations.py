#!/usr/bin/env python3
"""
Compute correlations between structural LLM quality scores and behavioral eval deltas.

Reads:
  - data/processed/llm-scores.json  (structural LLM judge scores)
  - data/processed/behavioral-eval.json  (behavioral eval deltas)
  - data/processed/combined.json  (for contamination scores + full corpus stats)

Outputs a summary table to stdout showing:
  - Per-dimension correlations with behavioral deltas (B-A, |B-A|, D-A, |D-A|)
  - Novelty amplification headline (novelty vs |B-A|)
  - Per-task-type novelty correlations
  - Novelty-contamination independence
  - LLM dimension intercorrelations
  - Reference vs SKILL.md quality gap
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
LLM_SCORES = REPO_ROOT / "data" / "processed" / "llm-scores.json"
BEHAVIORAL = REPO_ROOT / "data" / "processed" / "behavioral-eval.json"
COMBINED = REPO_ROOT / "data" / "processed" / "combined.json"

SKILL_DIMS = [
    "clarity", "actionability", "token_efficiency",
    "scope_discipline", "directive_precision", "novelty",
]
CRAFT_DIMS = [d for d in SKILL_DIMS if d != "novelty"]
REF_DIMS = ["clarity", "instructional_value", "token_efficiency", "novelty", "skill_relevance"]


def pearson_r(x: list[float], y: list[float]) -> float:
    """Pearson correlation coefficient. Returns NaN if n < 3."""
    n = len(x)
    if n < 3 or len(y) != n:
        return float("nan")
    mx, my = mean(x), mean(y)
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    if sx == 0 or sy == 0:
        return float("nan")
    return cov / (sx * sy)


def load_data():
    """Load and join LLM scores with behavioral eval data."""
    llm_data = json.loads(LLM_SCORES.read_text())
    behav_data = json.loads(BEHAVIORAL.read_text())
    combined_data = json.loads(COMBINED.read_text())

    # LLM scores lookup by name
    llm_lookup: dict[str, dict] = {}
    for s in llm_data["skills"]:
        if s.get("llm_scores"):
            llm_lookup[s["name"]] = s["llm_scores"]

    # Behavioral eval lookup (excluding experimental / overridden)
    excluded = set(
        e["name"] for e in behav_data["summary"].get("excluded_from_aggregates", [])
    )
    behav_lookup: dict[str, dict] = {}
    for s in behav_data["skills"]:
        if s["skill_name"] not in excluded:
            behav_lookup[s["skill_name"]] = s

    # Contamination scores from combined.json
    contam_lookup: dict[str, float] = {}
    for s in combined_data["skills"]:
        if "contamination_score" in s:
            contam_lookup[s["name"]] = s["contamination_score"]

    return llm_lookup, behav_lookup, contam_lookup, combined_data


def print_section(title: str):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def main():
    llm_lookup, behav_lookup, contam_lookup, combined_data = load_data()

    # Match skills present in both LLM scores and behavioral eval
    matched = [name for name in behav_lookup if name in llm_lookup]
    unmatched = [name for name in behav_lookup if name not in llm_lookup]

    print(f"Matched skills: {len(matched)} / {len(behav_lookup)} behavioral eval skills")
    if unmatched:
        print(f"  Unmatched: {', '.join(unmatched)}")

    # Extract delta vectors
    ba_deltas = [behav_lookup[n]["mean_delta_composite"] for n in matched]
    abs_ba = [abs(d) for d in ba_deltas]
    da_deltas = [behav_lookup[n]["mean_delta_composite_realistic"] for n in matched]
    abs_da = [abs(d) for d in da_deltas]

    # ---- 1. Dimension correlations with behavioral deltas ----
    print_section("1. DIMENSION CORRELATIONS WITH BEHAVIORAL DELTAS")
    print(f"{'Dimension':<25} {'r vs B-A':>10} {'r vs |B-A|':>10} {'r vs D-A':>10} {'r vs |D-A|':>10}")
    print("-" * 70)

    for dim in SKILL_DIMS:
        vals = [llm_lookup[n][dim] for n in matched]
        print(
            f"{dim:<25} "
            f"{pearson_r(vals, ba_deltas):>+10.3f} "
            f"{pearson_r(vals, abs_ba):>+10.3f} "
            f"{pearson_r(vals, da_deltas):>+10.3f} "
            f"{pearson_r(vals, abs_da):>+10.3f}"
        )

    # Craft composite
    craft = [mean([llm_lookup[n][d] for d in CRAFT_DIMS]) for n in matched]
    print(
        f"{'craft_composite':<25} "
        f"{pearson_r(craft, ba_deltas):>+10.3f} "
        f"{pearson_r(craft, abs_ba):>+10.3f} "
        f"{pearson_r(craft, da_deltas):>+10.3f} "
        f"{pearson_r(craft, abs_da):>+10.3f}"
    )

    # Overall composite
    overall = [llm_lookup[n]["overall"] for n in matched]
    print(
        f"{'overall_composite':<25} "
        f"{pearson_r(overall, ba_deltas):>+10.3f} "
        f"{pearson_r(overall, abs_ba):>+10.3f} "
        f"{pearson_r(overall, da_deltas):>+10.3f} "
        f"{pearson_r(overall, abs_da):>+10.3f}"
    )

    # ---- 2. Headline: novelty vs |B-A| ----
    novelty_vals = [llm_lookup[n]["novelty"] for n in matched]
    r_headline = pearson_r(novelty_vals, abs_ba)
    print_section("2. HEADLINE: NOVELTY AMPLIFICATION")
    print(f"  novelty vs |B-A| = {r_headline:+.3f}")

    # ---- 3. Per-task-type novelty correlations ----
    print_section("3. NOVELTY vs DELTA BY TASK TYPE")
    task_types = ["direct_target", "cross_language", "similar_syntax", "adjacent_domain", "grounded"]
    for tt in task_types:
        tt_d, tt_n = [], []
        for n in matched:
            dbt = behav_lookup[n].get("delta_by_task_type", {})
            if tt in dbt:
                tt_d.append(dbt[tt])
                tt_n.append(llm_lookup[n]["novelty"])
        if len(tt_n) >= 3:
            print(
                f"  {tt:<20} r={pearson_r(tt_n, tt_d):+.3f}  "
                f"r(abs)={pearson_r(tt_n, [abs(d) for d in tt_d]):+.3f}  "
                f"n={len(tt_n)}"
            )
        else:
            print(f"  {tt:<20} n={len(tt_n)} (too few)")

    # ---- 4. Structural contamination vs behavioral ----
    print_section("4. STRUCTURAL CONTAMINATION vs BEHAVIORAL DELTA")
    contam_matched = [n for n in matched if n in contam_lookup]
    if contam_matched:
        c_vals = [contam_lookup[n] for n in contam_matched]
        c_ba = [behav_lookup[n]["mean_delta_composite"] for n in contam_matched]
        print(f"  contamination vs B-A: r = {pearson_r(c_vals, c_ba):+.3f}  n={len(contam_matched)}")
    else:
        print("  No contamination scores available for matched skills")

    # ---- 5. Novelty-contamination independence (full corpus) ----
    # combined.json uses flat keys (llm_novelty, contamination_score)
    print_section("5. NOVELTY-CONTAMINATION INDEPENDENCE (FULL CORPUS)")
    novelty_all, contam_all = [], []
    novelty_co, contam_co = [], []
    for s in combined_data["skills"]:
        nov = s.get("llm_novelty")
        contam = s.get("contamination_score")
        if nov is not None and contam is not None:
            novelty_all.append(nov)
            contam_all.append(contam)
            if s["source"] == "company":
                novelty_co.append(nov)
                contam_co.append(contam)

    if novelty_all:
        print(f"  All sources:  r = {pearson_r(novelty_all, contam_all):+.3f}  n={len(novelty_all)}")
    if novelty_co:
        print(f"  Company only: r = {pearson_r(novelty_co, contam_co):+.3f}  n={len(novelty_co)}")

    # ---- 6. LLM dimension intercorrelations (full corpus) ----
    print_section("6. LLM DIMENSION INTERCORRELATIONS (FULL CORPUS)")
    all_scores: dict[str, list[float]] = {d: [] for d in SKILL_DIMS}
    for s in combined_data["skills"]:
        llm_keys = {d: s.get(f"llm_{d}") for d in SKILL_DIMS}
        if all(v is not None for v in llm_keys.values()):
            for d in SKILL_DIMS:
                all_scores[d].append(llm_keys[d])

    n_scored = len(all_scores["clarity"]) if all_scores["clarity"] else 0
    print(f"  n = {n_scored} skills with full LLM scores")
    print()
    # Craft-craft correlations
    print("  Craft cluster (non-novelty):")
    for i, d1 in enumerate(CRAFT_DIMS):
        for d2 in CRAFT_DIMS[i + 1:]:
            r = pearson_r(all_scores[d1], all_scores[d2])
            print(f"    {d1} vs {d2}: r = {r:+.3f}")

    print()
    print("  Novelty vs craft dimensions:")
    for d in CRAFT_DIMS:
        r = pearson_r(all_scores["novelty"], all_scores[d])
        print(f"    novelty vs {d}: r = {r:+.3f}")

    # ---- 7. Reference vs SKILL.md quality gap ----
    # combined.json uses flat keys: llm_clarity, ref_llm_clarity, etc.
    print_section("7. REFERENCE vs SKILL.md QUALITY GAP")
    shared_dims = ["clarity", "token_efficiency", "novelty"]
    for dim in shared_dims:
        skill_vals = [
            s[f"llm_{dim}"]
            for s in combined_data["skills"]
            if s.get(f"llm_{dim}") is not None
        ]
        ref_vals = [
            s[f"ref_llm_{dim}"]
            for s in combined_data["skills"]
            if s.get(f"ref_llm_{dim}") is not None
        ]
        if skill_vals and ref_vals:
            print(
                f"  {dim}: SKILL.md={mean(skill_vals):.2f}, "
                f"Ref={mean(ref_vals):.2f}, "
                f"gap={mean(ref_vals) - mean(skill_vals):+.2f}"
            )

    # Overall gap
    skill_ov = [
        s["llm_overall"]
        for s in combined_data["skills"]
        if s.get("llm_overall") is not None
    ]
    ref_ov = [
        s["ref_llm_overall"]
        for s in combined_data["skills"]
        if s.get("ref_llm_overall") is not None
    ]
    if skill_ov and ref_ov:
        print(
            f"  overall: SKILL.md={mean(skill_ov):.2f}, "
            f"Ref={mean(ref_ov):.2f}, "
            f"gap={mean(ref_ov) - mean(skill_ov):+.2f}"
        )

    # ---- 8. Global dimension means ----
    print_section("8. GLOBAL DIMENSION MEANS")
    print("  SKILL.md:")
    for d in SKILL_DIMS:
        vals = [
            s[f"llm_{d}"]
            for s in combined_data["skills"]
            if s.get(f"llm_{d}") is not None
        ]
        if vals:
            print(f"    {d}: {mean(vals):.2f}  (n={len(vals)})")

    print("  References:")
    ref_key_map = {
        "clarity": "ref_llm_clarity",
        "instructional_value": "ref_llm_instructional_value",
        "token_efficiency": "ref_llm_token_efficiency",
        "novelty": "ref_llm_novelty",
        "skill_relevance": "ref_llm_skill_relevance",
    }
    for d in REF_DIMS:
        key = ref_key_map[d]
        vals = [s[key] for s in combined_data["skills"] if s.get(key) is not None]
        if vals:
            print(f"    {d}: {mean(vals):.2f}  (n={len(vals)})")

    # ---- 9. Source rankings ----
    print_section("9. SOURCE RANKINGS BY OVERALL LLM SCORE")
    from collections import defaultdict
    source_scores: dict[str, list[float]] = defaultdict(list)
    for s in combined_data["skills"]:
        if s.get("llm_overall") is not None:
            source_scores[s["source"]].append(s["llm_overall"])

    for src, vals in sorted(source_scores.items(), key=lambda x: -mean(x[1])):
        print(f"  {src}: {mean(vals):.2f}  (n={len(vals)})")

    # ---- 10. Novelty 4+ by source ----
    print_section("10. NOVELTY DISTRIBUTION: % SCORING 4+ BY SOURCE")
    source_novelty: dict[str, list[float]] = defaultdict(list)
    for s in combined_data["skills"]:
        if s.get("llm_novelty") is not None:
            source_novelty[s["source"]].append(s["llm_novelty"])

    for src, vals in sorted(source_novelty.items(), key=lambda x: -sum(1 for v in x[1] if v >= 4) / len(x[1])):
        pct = sum(1 for v in vals if v >= 4) / len(vals) * 100
        print(f"  {src}: {pct:.1f}%  (n={len(vals)}, mean={mean(vals):.2f})")


if __name__ == "__main__":
    main()
