"""
Statistical analysis and figure generation for behavioral eval.

Reads scored results from eval/results/scores/, computes deltas between
baseline and with-skill conditions, runs statistical tests, and generates
figures for the paper.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from config import (
    BEHAVIORAL_OUTPUT,
    FIGURES_DIR,
    SCORES_DIR,
    SKILLS,
)

JUDGE_DIMS = ["language_correctness", "api_idiomaticity", "functional_correctness", "code_quality"]
TASK_TYPES = ["direct_target", "cross_language", "similar_syntax", "grounded", "adjacent_domain"]


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def load_all_scores() -> dict[str, dict]:
    """Load all scored results, keyed by skill name."""
    results = {}
    for path in sorted(SCORES_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        results[data["skill_name"]] = data
    return results


def extract_dim_scores(condition_data: dict, dim: str) -> float | None:
    """Extract a judge dimension score from a condition's scored data."""
    if condition_data is None:
        return None
    judge = condition_data.get("judge")
    if judge is None:
        return None
    val = judge.get(dim)
    if val is None:
        return None
    return float(val)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))


def cohens_d(group1: list[float], group2: list[float]) -> float:
    """Compute Cohen's d effect size."""
    if not group1 or not group2:
        return 0.0
    m1, m2 = mean(group1), mean(group2)
    s1, s2 = stdev(group1), stdev(group2)
    pooled = math.sqrt(((len(group1) - 1) * s1**2 + (len(group2) - 1) * s2**2) /
                        (len(group1) + len(group2) - 2)) if (len(group1) + len(group2)) > 2 else 1.0
    return (m1 - m2) / pooled if pooled > 0 else 0.0


def paired_t_stat(diffs: list[float]) -> tuple[float, float]:
    """Compute paired t-statistic and approximate two-tailed p-value."""
    n = len(diffs)
    if n < 2:
        return 0.0, 1.0
    m = mean(diffs)
    s = stdev(diffs)
    if s == 0:
        return 0.0, 1.0
    t = m / (s / math.sqrt(n))
    # Approximate p-value using normal distribution for large enough n
    # For small n this is imprecise but directionally correct
    p = 2 * (1 - _normal_cdf(abs(t)))
    return t, p


def _normal_cdf(x: float) -> float:
    """Approximate standard normal CDF."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def wilcoxon_approx(diffs: list[float]) -> tuple[float, float]:
    """Approximate Wilcoxon signed-rank test statistic and p-value."""
    nonzero = [(abs(d), 1 if d > 0 else -1) for d in diffs if d != 0]
    if len(nonzero) < 2:
        return 0.0, 1.0
    # Rank by absolute value
    nonzero.sort(key=lambda x: x[0])
    w_plus = sum(rank + 1 for rank, (_, sign) in enumerate(nonzero) if sign > 0)
    w_minus = sum(rank + 1 for rank, (_, sign) in enumerate(nonzero) if sign < 0)
    w = min(w_plus, w_minus)
    n = len(nonzero)
    # Normal approximation
    mu = n * (n + 1) / 4
    sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    if sigma == 0:
        return w, 1.0
    z = (w - mu) / sigma
    p = 2 * (1 - _normal_cdf(abs(z)))
    return w, p


def pearson_r(x: list[float], y: list[float]) -> float:
    """Compute Pearson correlation coefficient."""
    n = len(x)
    if n < 3 or len(y) != n:
        return 0.0
    mx, my = mean(x), mean(y)
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    if sx == 0 or sy == 0:
        return 0.0
    return cov / (sx * sy)


# ---------------------------------------------------------------------------
# Per-skill analysis
# ---------------------------------------------------------------------------

def analyze_skill(skill_name: str, score_data: dict) -> dict:
    """Compute deltas and stats for a single skill."""
    skill_results = {
        "skill_name": skill_name,
        "contamination_score": score_data.get("contamination_score", 0),
        "risk_level": score_data.get("risk_level", ""),
        "test_category": score_data.get("test_category", ""),
        "tasks": [],
    }

    all_baseline_scores = {d: [] for d in JUDGE_DIMS}
    all_skill_scores = {d: [] for d in JUDGE_DIMS}
    all_realistic_scores = {d: [] for d in JUDGE_DIMS}
    all_diffs = {d: [] for d in JUDGE_DIMS}
    all_diffs_realistic = {d: [] for d in JUDGE_DIMS}

    for task in score_data["tasks"]:
        task_analysis = {
            "task_id": task["task_id"],
            "task_type": task["task_type"],
            "target_language": task["target_language"],
            "deltas": {},
            "deltas_realistic": {},
            "baseline_means": {},
            "skill_means": {},
            "realistic_means": {},
            "pattern_results": {"baseline": [], "with_skill": [], "realistic": []},
        }

        task_baseline = {d: [] for d in JUDGE_DIMS}
        task_skill = {d: [] for d in JUDGE_DIMS}
        task_realistic = {d: [] for d in JUDGE_DIMS}

        for run in task["runs"]:
            for dim in JUDGE_DIMS:
                b_val = extract_dim_scores(run.get("baseline"), dim)
                s_val = extract_dim_scores(run.get("with_skill"), dim)
                r_val = extract_dim_scores(run.get("realistic"), dim)
                if b_val is not None:
                    task_baseline[dim].append(b_val)
                    all_baseline_scores[dim].append(b_val)
                if s_val is not None:
                    task_skill[dim].append(s_val)
                    all_skill_scores[dim].append(s_val)
                if r_val is not None:
                    task_realistic[dim].append(r_val)
                    all_realistic_scores[dim].append(r_val)
                if b_val is not None and s_val is not None:
                    all_diffs[dim].append(s_val - b_val)
                if b_val is not None and r_val is not None:
                    all_diffs_realistic[dim].append(r_val - b_val)

            # Pattern matching results
            for cond_key in ["baseline", "with_skill", "realistic"]:
                cond = run.get(cond_key, {})
                if cond is None:
                    continue
                patterns = cond.get("patterns")
                if patterns:
                    task_analysis["pattern_results"][cond_key].append(patterns)

        # Per-task deltas (skip when either side has no judge data)
        for dim in JUDGE_DIMS:
            has_baseline = len(task_baseline[dim]) > 0
            has_skill = len(task_skill[dim]) > 0
            has_realistic = len(task_realistic[dim]) > 0

            b_mean = mean(task_baseline[dim]) if has_baseline else None
            s_mean = mean(task_skill[dim]) if has_skill else None
            r_mean = mean(task_realistic[dim]) if has_realistic else None

            task_analysis["baseline_means"][dim] = round(b_mean, 3) if b_mean is not None else None
            task_analysis["skill_means"][dim] = round(s_mean, 3) if s_mean is not None else None
            if b_mean is not None and s_mean is not None:
                task_analysis["deltas"][dim] = round(s_mean - b_mean, 3)
            else:
                task_analysis["deltas"][dim] = None
            if b_mean is not None and r_mean is not None:
                task_analysis["realistic_means"][dim] = round(r_mean, 3)
                task_analysis["deltas_realistic"][dim] = round(r_mean - b_mean, 3)

        # Composite delta (B vs A) — only from dimensions with valid data
        dim_deltas = [task_analysis["deltas"][d] for d in JUDGE_DIMS
                      if task_analysis["deltas"][d] is not None]
        task_analysis["delta_composite"] = round(mean(dim_deltas), 3) if dim_deltas else None

        # Composite delta (D vs A)
        dim_deltas_r = [task_analysis["deltas_realistic"][d] for d in JUDGE_DIMS
                        if task_analysis["deltas_realistic"].get(d) is not None]
        task_analysis["delta_composite_realistic"] = round(mean(dim_deltas_r), 3) if dim_deltas_r else None

        # Anti-pattern summary
        baseline_anti = [p.get("anti_pattern_hit_rate", 0) for p in task_analysis["pattern_results"]["baseline"]]
        skill_anti = [p.get("anti_pattern_hit_rate", 0) for p in task_analysis["pattern_results"]["with_skill"]]
        realistic_anti = [p.get("anti_pattern_hit_rate", 0) for p in task_analysis["pattern_results"]["realistic"]]
        task_analysis["anti_pattern_rate_baseline"] = round(mean(baseline_anti), 3) if baseline_anti else 0
        task_analysis["anti_pattern_rate_skill"] = round(mean(skill_anti), 3) if skill_anti else 0
        task_analysis["anti_pattern_rate_realistic"] = round(mean(realistic_anti), 3) if realistic_anti else 0

        skill_results["tasks"].append(task_analysis)

    # Per-skill aggregates (exclude tasks with missing judge data)
    task_deltas = [t["delta_composite"] for t in skill_results["tasks"]
                   if t["delta_composite"] is not None]
    skill_results["mean_delta_composite"] = round(mean(task_deltas), 3) if task_deltas else None
    skill_results["stdev_delta_composite"] = round(stdev(task_deltas), 3) if task_deltas else None

    # Realistic context aggregates
    task_deltas_r = [t["delta_composite_realistic"] for t in skill_results["tasks"]
                     if t["delta_composite_realistic"] is not None]
    skill_results["mean_delta_composite_realistic"] = round(mean(task_deltas_r), 3) if task_deltas_r else None

    # Deltas by task type
    by_type = {}
    by_type_realistic = {}
    for t in skill_results["tasks"]:
        tt = t["task_type"]
        if t["delta_composite"] is not None:
            if tt not in by_type:
                by_type[tt] = []
            by_type[tt].append(t["delta_composite"])
        if t["delta_composite_realistic"] is not None:
            if tt not in by_type_realistic:
                by_type_realistic[tt] = []
            by_type_realistic[tt].append(t["delta_composite_realistic"])
    skill_results["delta_by_task_type"] = {
        tt: round(mean(vals), 3) for tt, vals in by_type.items()
    }
    skill_results["delta_by_task_type_realistic"] = {
        tt: round(mean(vals), 3) for tt, vals in by_type_realistic.items()
    }

    # Statistical tests across all runs
    composite_diffs = []
    for dim in JUDGE_DIMS:
        composite_diffs.extend(all_diffs[dim])

    all_composite_diffs = []
    all_composite_diffs_realistic = []
    for task in score_data["tasks"]:
        for run in task["runs"]:
            b_scores = [extract_dim_scores(run.get("baseline"), d) for d in JUDGE_DIMS]
            s_scores = [extract_dim_scores(run.get("with_skill"), d) for d in JUDGE_DIMS]
            r_scores = [extract_dim_scores(run.get("realistic"), d) for d in JUDGE_DIMS]
            b_valid = [v for v in b_scores if v is not None]
            s_valid = [v for v in s_scores if v is not None]
            r_valid = [v for v in r_scores if v is not None]
            if b_valid and s_valid:
                all_composite_diffs.append(mean(s_valid) - mean(b_valid))
            if b_valid and r_valid:
                all_composite_diffs_realistic.append(mean(r_valid) - mean(b_valid))

    t_stat, t_p = paired_t_stat(all_composite_diffs)
    w_stat, w_p = wilcoxon_approx(all_composite_diffs)

    # Cohen's d
    all_b_flat = []
    all_s_flat = []
    for d in JUDGE_DIMS:
        all_b_flat.extend(all_baseline_scores[d])
        all_s_flat.extend(all_skill_scores[d])
    d_effect = cohens_d(all_s_flat, all_b_flat)

    skill_results["statistics"] = {
        "n_comparisons": len(all_composite_diffs),
        "paired_t_stat": round(t_stat, 3),
        "paired_t_p": round(t_p, 4),
        "wilcoxon_w": round(w_stat, 3),
        "wilcoxon_p": round(w_p, 4),
        "cohens_d": round(d_effect, 3),
    }

    # Realistic context statistics
    if all_composite_diffs_realistic:
        t_stat_r, t_p_r = paired_t_stat(all_composite_diffs_realistic)
        all_r_flat = []
        for d in JUDGE_DIMS:
            all_r_flat.extend(all_realistic_scores[d])
        d_effect_r = cohens_d(all_r_flat, all_b_flat)

        # Mitigation ratio: how much of the skill-only effect is reduced
        skill_only_delta = mean(all_composite_diffs) if all_composite_diffs else 0
        realistic_delta = mean(all_composite_diffs_realistic)
        if skill_only_delta != 0:
            mitigation_ratio = 1 - (realistic_delta / skill_only_delta)
        else:
            mitigation_ratio = 0

        skill_results["statistics_realistic"] = {
            "n_comparisons": len(all_composite_diffs_realistic),
            "paired_t_stat": round(t_stat_r, 3),
            "paired_t_p": round(t_p_r, 4),
            "cohens_d": round(d_effect_r, 3),
            "mitigation_ratio": round(mitigation_ratio, 3),
        }

    # Hidden contamination analysis
    if SKILLS.get(skill_name, {}).get("hidden_contamination"):
        md_only_diffs = []
        full_diffs = []
        for task in score_data["tasks"]:
            for run in task["runs"]:
                b_scores = [extract_dim_scores(run.get("baseline"), d) for d in JUDGE_DIMS]
                s_scores = [extract_dim_scores(run.get("with_skill"), d) for d in JUDGE_DIMS]
                m_scores = [extract_dim_scores(run.get("skill_md_only"), d) for d in JUDGE_DIMS]
                b_valid = [v for v in b_scores if v is not None]
                s_valid = [v for v in s_scores if v is not None]
                m_valid = [v for v in m_scores if v is not None]
                if b_valid and m_valid:
                    md_only_diffs.append(mean(m_valid) - mean(b_valid))
                if b_valid and s_valid:
                    full_diffs.append(mean(s_valid) - mean(b_valid))

        skill_results["hidden_contamination"] = {
            "skill_md_only_delta": round(mean(md_only_diffs), 3) if md_only_diffs else None,
            "skill_plus_refs_delta": round(mean(full_diffs), 3) if full_diffs else None,
            "ref_attribution": round(
                (mean(full_diffs) - mean(md_only_diffs)), 3
            ) if md_only_diffs and full_diffs else None,
        }

    return skill_results


# ---------------------------------------------------------------------------
# Cross-skill analysis
# ---------------------------------------------------------------------------

def cross_skill_analysis(skill_analyses: list[dict]) -> dict:
    """Compute cross-skill correlations and comparisons."""
    # Filter to skills with valid deltas for aggregate statistics
    valid_analyses = [sa for sa in skill_analyses if sa.get("mean_delta_composite") is not None]

    # Correlation: structural score vs behavioral delta
    contam_scores = []
    behavioral_deltas = []
    for sa in valid_analyses:
        contam_scores.append(sa["contamination_score"])
        behavioral_deltas.append(sa["mean_delta_composite"])

    r = pearson_r(contam_scores, behavioral_deltas)

    # By risk level
    by_risk = {}
    for sa in valid_analyses:
        rl = sa["risk_level"]
        if rl not in by_risk:
            by_risk[rl] = []
        by_risk[rl].append(sa["mean_delta_composite"])

    risk_summary = {
        rl: {"mean_delta": round(mean(vals), 3), "n": len(vals)}
        for rl, vals in by_risk.items()
    }

    # By test category
    by_category = {}
    for sa in valid_analyses:
        cat = sa["test_category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(sa["mean_delta_composite"])

    category_summary = {
        cat: {"mean_delta": round(mean(vals), 3), "n": len(vals)}
        for cat, vals in by_category.items()
    }

    # By task type (across all skills)
    by_task_type = {}
    for sa in valid_analyses:
        for task in sa["tasks"]:
            if task["delta_composite"] is None:
                continue
            tt = task["task_type"]
            if tt not in by_task_type:
                by_task_type[tt] = []
            by_task_type[tt].append(task["delta_composite"])

    task_type_summary = {
        tt: {"mean_delta": round(mean(vals), 3), "n": len(vals)}
        for tt, vals in by_task_type.items()
    }

    # Net negative validation
    net_neg_skills = [sa for sa in valid_analyses if sa["test_category"] == "net_negative"]
    net_neg_summary = {
        "skills": [{"name": sa["skill_name"], "delta": sa["mean_delta_composite"]}
                    for sa in net_neg_skills],
        "mean_delta": round(mean([sa["mean_delta_composite"] for sa in net_neg_skills]), 3)
        if net_neg_skills else None,
    }

    # Hidden contamination
    hidden_skills = [sa for sa in skill_analyses if "hidden_contamination" in sa]
    hidden_summary = [
        {
            "name": sa["skill_name"],
            **sa["hidden_contamination"],
        }
        for sa in hidden_skills
    ]

    # Realistic context: aggregate mitigation stats
    realistic_skills = [sa for sa in valid_analyses if sa.get("mean_delta_composite_realistic") is not None]
    realistic_summary = {}
    if realistic_skills:
        skill_only_deltas = [sa["mean_delta_composite"] for sa in realistic_skills]
        realistic_deltas = [sa["mean_delta_composite_realistic"] for sa in realistic_skills]
        realistic_summary = {
            "n_skills": len(realistic_skills),
            "mean_delta_skill_only": round(mean(skill_only_deltas), 3),
            "mean_delta_realistic": round(mean(realistic_deltas), 3),
            "mean_mitigation_ratio": round(
                mean([sa["statistics_realistic"]["mitigation_ratio"]
                      for sa in realistic_skills if "statistics_realistic" in sa]),
                3
            ) if any("statistics_realistic" in sa for sa in realistic_skills) else None,
        }

        # Correlation: structural score vs realistic delta
        r_contam = [sa["contamination_score"] for sa in realistic_skills]
        r_deltas = [sa["mean_delta_composite_realistic"] for sa in realistic_skills]
        realistic_summary["correlation_structural_realistic"] = round(pearson_r(r_contam, r_deltas), 3)

    return {
        "correlation_structural_behavioral": round(r, 3),
        "n_skills": len(valid_analyses),
        "by_risk_level": risk_summary,
        "by_test_category": category_summary,
        "by_task_type": task_type_summary,
        "net_negative": net_neg_summary,
        "hidden_contamination": hidden_summary,
        "realistic_context": realistic_summary,
    }


# ---------------------------------------------------------------------------
# Figure generation
# ---------------------------------------------------------------------------

def fig_correlation(skill_analyses: list[dict]):
    """Scatter: structural contamination score vs behavioral delta."""
    skill_analyses = [sa for sa in skill_analyses if sa.get("mean_delta_composite") is not None]
    if not skill_analyses:
        print("  → behavioral_correlation.png (skipped, no valid data)")
        return

    fig, ax = plt.subplots(figsize=(8, 6))

    colors = {"high": "#e74c3c", "medium": "#f39c12", "control": "#2ecc71"}
    for sa in skill_analyses:
        c = colors.get(sa["risk_level"], "#3498db")
        ax.scatter(sa["contamination_score"], sa["mean_delta_composite"],
                   color=c, s=80, alpha=0.8, edgecolors="white", linewidth=0.5)
        ax.annotate(sa["skill_name"], (sa["contamination_score"], sa["mean_delta_composite"]),
                    fontsize=7, ha="left", va="bottom", alpha=0.7)

    # Add reference line at y=0
    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)

    # Legend
    for label, color in colors.items():
        ax.scatter([], [], color=color, s=80, label=label)
    ax.legend(title="Risk Level")

    ax.set_xlabel("Structural Contamination Score")
    ax.set_ylabel("Behavioral Delta (with-skill - baseline)")
    ax.set_title("Structural vs. Behavioral Contamination")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "behavioral_correlation.png", dpi=150)
    plt.close(fig)
    print("  → behavioral_correlation.png")


def fig_deltas_by_risk(skill_analyses: list[dict]):
    """Box plot: deltas grouped by risk level."""
    skill_analyses = [sa for sa in skill_analyses if sa.get("mean_delta_composite") is not None]

    fig, ax = plt.subplots(figsize=(8, 5))

    risk_groups = {}
    for sa in skill_analyses:
        rl = sa["risk_level"]
        if rl not in risk_groups:
            risk_groups[rl] = []
        risk_groups[rl].append(sa["mean_delta_composite"])

    order = ["high", "medium", "control"]
    data = [risk_groups.get(r, []) for r in order]
    labels = [f"{r}\n(n={len(risk_groups.get(r, []))})" for r in order]

    bp = ax.boxplot(data, labels=labels, patch_artist=True)
    colors = ["#e74c3c", "#f39c12", "#2ecc71"]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)

    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax.set_ylabel("Behavioral Delta (composite)")
    ax.set_title("Quality Delta by Risk Level")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "behavioral_deltas_by_risk.png", dpi=150)
    plt.close(fig)
    print("  → behavioral_deltas_by_risk.png")


def fig_task_types(skill_analyses: list[dict]):
    """Bar chart: mean delta by task type across risk levels."""
    fig, ax = plt.subplots(figsize=(10, 5))

    risk_levels = ["high", "medium", "control"]
    colors = {"high": "#e74c3c", "medium": "#f39c12", "control": "#2ecc71"}

    # Collect data
    data = {rl: {tt: [] for tt in TASK_TYPES} for rl in risk_levels}
    for sa in skill_analyses:
        rl = sa["risk_level"]
        if rl not in data:
            continue
        for task in sa["tasks"]:
            tt = task["task_type"]
            if tt in data[rl] and task["delta_composite"] is not None:
                data[rl][tt].append(task["delta_composite"])

    x = range(len(TASK_TYPES))
    width = 0.25
    offsets = {rl: i * width for i, rl in enumerate(risk_levels)}

    for rl in risk_levels:
        means = [mean(data[rl][tt]) if data[rl][tt] else 0 for tt in TASK_TYPES]
        positions = [xi + offsets[rl] for xi in x]
        ax.bar(positions, means, width, label=rl, color=colors[rl], alpha=0.7)

    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax.set_xticks([xi + width for xi in x])
    ax.set_xticklabels([t.replace("_", "\n") for t in TASK_TYPES], fontsize=9)
    ax.set_ylabel("Mean Behavioral Delta")
    ax.set_title("Quality Delta by Task Type and Risk Level")
    ax.legend(title="Risk Level")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "behavioral_task_types.png", dpi=150)
    plt.close(fig)
    print("  → behavioral_task_types.png")


def fig_hidden_contamination(skill_analyses: list[dict]):
    """Bar: SKILL-only vs SKILL+refs for hidden contamination skills."""
    hidden = [sa for sa in skill_analyses if "hidden_contamination" in sa]
    if not hidden:
        print("  → behavioral_hidden_contamination.png (skipped, no data)")
        return

    fig, ax = plt.subplots(figsize=(8, 5))

    names = [sa["skill_name"] for sa in hidden]
    md_only = [sa["hidden_contamination"]["skill_md_only_delta"] or 0 for sa in hidden]
    full = [sa["hidden_contamination"]["skill_plus_refs_delta"] or 0 for sa in hidden]

    x = range(len(names))
    width = 0.35
    ax.bar([xi - width / 2 for xi in x], md_only, width,
           label="SKILL.md only", color="#3498db", alpha=0.7)
    ax.bar([xi + width / 2 for xi in x], full, width,
           label="SKILL.md + refs", color="#e74c3c", alpha=0.7)

    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, rotation=15, ha="right")
    ax.set_ylabel("Behavioral Delta")
    ax.set_title("Hidden Contamination: SKILL-only vs SKILL+References")
    ax.legend()

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "behavioral_hidden_contamination.png", dpi=150)
    plt.close(fig)
    print("  → behavioral_hidden_contamination.png")


def fig_context_mitigation(skill_analyses: list[dict]):
    """Paired bar: skill-only delta vs realistic-context delta per skill."""
    # Only include skills that have both valid deltas and realistic data
    has_realistic = [sa for sa in skill_analyses
                     if sa.get("mean_delta_composite") is not None
                     and sa.get("mean_delta_composite_realistic") is not None]
    if not has_realistic:
        print("  → behavioral_context_mitigation.png (skipped, no data)")
        return

    # Sort by skill-only delta (most negative first)
    has_realistic.sort(key=lambda s: s["mean_delta_composite"])

    fig, ax = plt.subplots(figsize=(12, 6))

    names = [sa["skill_name"] for sa in has_realistic]
    skill_deltas = [sa["mean_delta_composite"] for sa in has_realistic]
    realistic_deltas = [sa["mean_delta_composite_realistic"] for sa in has_realistic]

    x = range(len(names))
    width = 0.35
    ax.bar([xi - width / 2 for xi in x], skill_deltas, width,
           label="B: Skill only", color="#e74c3c", alpha=0.7)
    ax.bar([xi + width / 2 for xi in x], realistic_deltas, width,
           label="D: Skill + realistic context", color="#3498db", alpha=0.7)

    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Behavioral Delta (vs baseline)")
    ax.set_title("Context Mitigation: Skill-Only vs Realistic Context")
    ax.legend()

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "behavioral_context_mitigation.png", dpi=150)
    plt.close(fig)
    print("  → behavioral_context_mitigation.png")


def fig_net_negative(skill_analyses: list[dict]):
    """Bar: deltas for net-negative skills."""
    net_neg = [sa for sa in skill_analyses
               if sa["test_category"] == "net_negative" and sa.get("mean_delta_composite") is not None]
    if not net_neg:
        print("  → behavioral_net_negative.png (skipped, no data)")
        return

    fig, ax = plt.subplots(figsize=(8, 5))

    names = [sa["skill_name"] for sa in net_neg]
    deltas = [sa["mean_delta_composite"] for sa in net_neg]

    bars = ax.bar(range(len(names)), deltas, color=["#e74c3c" if d < 0 else "#2ecc71" for d in deltas],
                  alpha=0.7)
    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=15, ha="right")
    ax.set_ylabel("Behavioral Delta (composite)")
    ax.set_title("Net Negative Skills: Loading Skill Degrades Output?")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "behavioral_net_negative.png", dpi=150)
    plt.close(fig)
    print("  → behavioral_net_negative.png")


# ---------------------------------------------------------------------------
# Main analysis pipeline
# ---------------------------------------------------------------------------

def run_analysis() -> dict:
    """Run full analysis pipeline and return unified results."""
    print("=== Behavioral Eval: Analysis ===")

    all_scores = load_all_scores()
    if not all_scores:
        print("  ERROR: No scored data found in results/scores/", file=sys.stderr)
        return {}

    print(f"  Found scores for {len(all_scores)} skills")

    # Per-skill analysis
    skill_analyses = []
    for name, score_data in all_scores.items():
        analysis = analyze_skill(name, score_data)
        skill_analyses.append(analysis)

    # Cross-skill analysis
    cross = cross_skill_analysis(skill_analyses)

    # Generate figures
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    print("\n  Generating figures...")
    fig_correlation(skill_analyses)
    fig_deltas_by_risk(skill_analyses)
    fig_task_types(skill_analyses)
    fig_hidden_contamination(skill_analyses)
    fig_context_mitigation(skill_analyses)
    fig_net_negative(skill_analyses)

    # Unified output
    unified = {
        "summary": cross,
        "skills": skill_analyses,
    }

    BEHAVIORAL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    BEHAVIORAL_OUTPUT.write_text(json.dumps(unified, indent=2))
    print(f"\n  → Saved {BEHAVIORAL_OUTPUT}")

    # Print summary
    print_summary(skill_analyses, cross)

    return unified


def print_summary(skill_analyses: list[dict], cross: dict):
    """Print summary statistics to stdout."""
    print("\n" + "=" * 60)
    print("BEHAVIORAL EVAL SUMMARY")
    print("=" * 60)

    print(f"\nCorrelation (structural vs behavioral): r = {cross['correlation_structural_behavioral']}")
    print(f"Skills analyzed: {cross['n_skills']}")

    print("\nBy risk level:")
    for rl, stats in cross["by_risk_level"].items():
        print(f"  {rl}: mean delta = {stats['mean_delta']:+.3f} (n={stats['n']})")

    print("\nBy task type:")
    for tt, stats in cross["by_task_type"].items():
        print(f"  {tt}: mean delta = {stats['mean_delta']:+.3f} (n={stats['n']})")

    print("\nPer-skill results:")
    valid_skills = [sa for sa in skill_analyses if sa.get("mean_delta_composite") is not None]
    skipped_skills = [sa for sa in skill_analyses if sa.get("mean_delta_composite") is None]
    sorted_skills = sorted(valid_skills, key=lambda s: s["mean_delta_composite"])
    for sa in sorted_skills:
        stats = sa["statistics"]
        sig = "*" if stats["paired_t_p"] < 0.05 else ""
        print(f"  {sa['skill_name']:40s} contam={sa['contamination_score']:.2f}  "
              f"delta={sa['mean_delta_composite']:+.3f}  "
              f"d={stats['cohens_d']:+.3f}  "
              f"p={stats['paired_t_p']:.3f}{sig}")
    for sa in skipped_skills:
        print(f"  {sa['skill_name']:40s} contam={sa['contamination_score']:.2f}  "
              f"delta=N/A (insufficient judge data)")

    if cross["hidden_contamination"]:
        print("\nHidden contamination:")
        for hc in cross["hidden_contamination"]:
            print(f"  {hc['name']}: SKILL-only delta={hc['skill_md_only_delta']}, "
                  f"SKILL+refs delta={hc['skill_plus_refs_delta']}, "
                  f"ref attribution={hc['ref_attribution']}")

    if cross.get("realistic_context"):
        rc = cross["realistic_context"]
        print(f"\nRealistic context mitigation (n={rc['n_skills']}):")
        print(f"  Mean delta (skill-only):       {rc['mean_delta_skill_only']:+.3f}")
        print(f"  Mean delta (realistic context): {rc['mean_delta_realistic']:+.3f}")
        if rc.get("mean_mitigation_ratio") is not None:
            print(f"  Mean mitigation ratio:          {rc['mean_mitigation_ratio']:.1%}")
        if rc.get("correlation_structural_realistic") is not None:
            print(f"  Correlation (structural vs realistic): r = {rc['correlation_structural_realistic']}")

    if cross["net_negative"]["skills"]:
        print("\nNet negative validation:")
        for nn in cross["net_negative"]["skills"]:
            direction = "DEGRADES" if nn["delta"] < -0.1 else "neutral" if abs(nn["delta"]) <= 0.1 else "improves"
            print(f"  {nn['name']}: delta={nn['delta']:+.3f} ({direction})")


if __name__ == "__main__":
    run_analysis()
