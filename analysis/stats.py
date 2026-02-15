#!/usr/bin/env python3
"""
Generate summary statistics and figures from combined.json for the white paper.

Produces figures in paper/figures/:
  - pass_fail_by_source.png: Pass/fail rates by source
  - token_distribution.png: Distribution of token counts
  - content_quality.png: Information density and instruction specificity distributions
  - contamination_distribution.png: Cross-contamination level distribution
  - contamination_by_source.png: Contamination score distribution by source
  - metrics_correlation.png: Correlation between key metrics
  - llm_scores_by_source.png: LLM judge scores by source category
  - llm_novelty_distribution.png: Novelty score distribution by source
  - llm_dimension_correlations.png: Correlations between LLM judge dimensions
  - llm_vs_heuristic.png: LLM judge scores vs heuristic metrics
  - llm_ref_vs_skill.png: Reference file quality vs SKILL.md quality
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

REPO_ROOT = Path(__file__).resolve().parent.parent
COMBINED = REPO_ROOT / "data" / "processed" / "combined.json"
FIGURES_DIR = REPO_ROOT / "paper" / "figures"

# Style
plt.rcParams.update({
    "figure.figsize": (8, 5),
    "figure.dpi": 150,
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})

COLORS = {
    "pass": "#2ecc71",
    "fail": "#e74c3c",
    "high": "#e74c3c",
    "medium": "#f39c12",
    "low": "#2ecc71",
    "anthropic": "#5B6ABF",
    "community-other": "#E67E22",
    "k-dense": "#1ABC9C",
    "trail-of-bits": "#9B59B6",
}


def load_data():
    with open(COMBINED) as f:
        return json.load(f)


def fig_pass_fail_by_source(data):
    """Bar chart: pass/fail counts by source."""
    fig, ax = plt.subplots()

    sources = sorted(data["by_source"].keys())
    passed = [data["by_source"][s]["passed"] for s in sources]
    failed = [data["by_source"][s]["failed"] for s in sources]

    x = range(len(sources))
    width = 0.35
    ax.bar([i - width/2 for i in x], passed, width, label="Passed", color=COLORS["pass"])
    ax.bar([i + width/2 for i in x], failed, width, label="Failed", color=COLORS["fail"])

    ax.set_xlabel("Source")
    ax.set_ylabel("Number of Skills")
    ax.set_title("Validation Pass/Fail by Source")
    ax.set_xticks(list(x))
    ax.set_xticklabels(sources, rotation=15, ha="right")
    ax.legend()
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "pass_fail_by_source.png")
    plt.close(fig)
    print("  → pass_fail_by_source.png")


def fig_token_distribution(data):
    """Histogram: distribution of total token counts."""
    fig, ax = plt.subplots()

    tokens = [s["total_tokens"] for s in data["skills"]]
    skill_md_tokens = [s["skill_md_tokens"] for s in data["skills"]]

    ax.hist(skill_md_tokens, bins=50, alpha=0.7, label="SKILL.md tokens", color="#3498db")
    ax.hist(tokens, bins=50, alpha=0.4, label="Total tokens (incl. assets)", color="#e74c3c")

    ax.set_xlabel("Token Count")
    ax.set_ylabel("Number of Skills")
    ax.set_title("Token Count Distribution")
    ax.legend()

    # Log scale for x-axis since some skills are very large
    ax.set_xscale("symlog", linthresh=100)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "token_distribution.png")
    plt.close(fig)
    print("  → token_distribution.png")


def fig_content_quality(data):
    """Scatter plot: information density vs instruction specificity."""
    fig, ax = plt.subplots()

    for source in sorted(set(s["source"] for s in data["skills"])):
        skills = [s for s in data["skills"] if s["source"] == source]
        x = [s["information_density"] for s in skills]
        y = [s["instruction_specificity"] for s in skills]
        ax.scatter(x, y, label=source, alpha=0.6, s=30,
                   color=COLORS.get(source, "#999"))

    ax.set_xlabel("Information Density")
    ax.set_ylabel("Instruction Specificity")
    ax.set_title("Content Quality: Density vs. Specificity")
    ax.legend(loc="lower right", fontsize=9)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "content_quality.png")
    plt.close(fig)
    print("  → content_quality.png")


def fig_contamination_distribution(data):
    """Donut chart: contamination level distribution."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Left: Pass/fail donut
    ax = axes[0]
    sizes = [data["summary"]["passed"], data["summary"]["failed"]]
    labels = [f"Passed ({sizes[0]})", f"Failed ({sizes[1]})"]
    colors = [COLORS["pass"], COLORS["fail"]]
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="%1.0f%%",
        startangle=90, pctdistance=0.75,
    )
    centre_circle = plt.Circle((0, 0), 0.50, fc="white")
    ax.add_artist(centre_circle)
    ax.set_title("Validation Results")

    # Right: Contamination level donut
    ax = axes[1]
    contamination = data["summary"]["contamination_distribution"]
    sizes = [contamination["high"], contamination["medium"], contamination["low"]]
    labels = [f"High ({contamination['high']})", f"Medium ({contamination['medium']})", f"Low ({contamination['low']})"]
    colors = [COLORS["high"], COLORS["medium"], COLORS["low"]]
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="%1.0f%%",
        startangle=90, pctdistance=0.75,
    )
    centre_circle = plt.Circle((0, 0), 0.50, fc="white")
    ax.add_artist(centre_circle)
    ax.set_title("Cross-Contamination")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "contamination_distribution.png")
    plt.close(fig)
    print("  → contamination_distribution.png")


def fig_contamination_by_source(data):
    """Box plot: contamination scores by source."""
    fig, ax = plt.subplots()

    sources = sorted(set(s["source"] for s in data["skills"]))
    contamination_data = []
    for source in sources:
        scores = [s["contamination_score"] for s in data["skills"] if s["source"] == source]
        contamination_data.append(scores)

    bp = ax.boxplot(contamination_data, tick_labels=sources, patch_artist=True)
    for patch, source in zip(bp["boxes"], sources):
        patch.set_facecolor(COLORS.get(source, "#999"))
        patch.set_alpha(0.7)

    ax.set_xlabel("Source")
    ax.set_ylabel("Contamination Score")
    ax.set_title("Cross-Contamination by Source")
    ax.set_xticklabels(sources, rotation=15, ha="right")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "contamination_by_source.png")
    plt.close(fig)
    print("  → contamination_by_source.png")


def fig_metrics_correlation(data):
    """Correlation matrix of key numeric metrics."""
    fig, ax = plt.subplots(figsize=(8, 7))

    metrics = [
        ("total_tokens", "Total Tokens"),
        ("errors", "Errors"),
        ("warnings", "Warnings"),
        ("information_density", "Info Density"),
        ("instruction_specificity", "Specificity"),
        ("code_block_ratio", "Code Ratio"),
        ("contamination_score", "Contamination"),
    ]

    # Build data matrix
    import numpy as np
    n = len(metrics)
    values = []
    for key, _ in metrics:
        values.append([s[key] for s in data["skills"]])

    # Compute correlation matrix
    corr = np.corrcoef(values)

    im = ax.imshow(corr, cmap="RdYlGn", vmin=-1, vmax=1)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels([m[1] for m in metrics], rotation=45, ha="right")
    ax.set_yticklabels([m[1] for m in metrics])

    # Add correlation values
    for i in range(n):
        for j in range(n):
            text = ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center",
                          fontsize=9, color="black" if abs(corr[i, j]) < 0.7 else "white")

    ax.set_title("Metric Correlations")
    fig.colorbar(im, ax=ax, shrink=0.8)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "metrics_correlation.png")
    plt.close(fig)
    print("  → metrics_correlation.png")


def fig_ref_language_distribution(data):
    """Horizontal bar chart: most common programming languages in reference files (top 15)."""
    from collections import Counter
    lang_counts = Counter()
    for s in data["skills"]:
        for lang in s.get("ref_code_languages", []):
            lang_counts[lang] += 1

    if not lang_counts:
        print("  → ref_language_distribution.png (skipped, no data)")
        return

    top = lang_counts.most_common(15)
    labels = [l for l, _ in reversed(top)]
    counts = [c for _, c in reversed(top)]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(labels, counts, color="#3498db")
    ax.set_xlabel("Number of Skills")
    ax.set_title("Most Common Languages in Reference Files (Top 15)")
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "ref_language_distribution.png")
    plt.close(fig)
    print("  → ref_language_distribution.png")


def fig_ref_token_ratio(data):
    """Histogram: reference token ratio (ref tokens / SKILL.md tokens)."""
    ratios = [s["ref_token_ratio"] for s in data["skills"] if s.get("ref_token_ratio", 0) > 0]

    if not ratios:
        print("  → ref_token_ratio.png (skipped, no data)")
        return

    fig, ax = plt.subplots()

    # Cap at 20x for histogram clarity, note outliers
    cap = 20
    capped = [min(r, cap) for r in ratios]
    outliers = sum(1 for r in ratios if r > cap)

    ax.hist(capped, bins=40, color="#e67e22", edgecolor="white", linewidth=0.5)
    ax.axvline(x=1, color="#e74c3c", linestyle="--", linewidth=1.5, label="1:1 (refs = SKILL.md)")
    ax.set_xlabel("Reference / SKILL.md Token Ratio")
    ax.set_ylabel("Number of Skills")
    title = "Reference File Size vs. SKILL.md"
    if outliers:
        title += f" ({outliers} skills >{cap}x not shown)"
    ax.set_title(title)
    ax.legend()

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "ref_token_ratio.png")
    plt.close(fig)
    print("  → ref_token_ratio.png")


def print_summary_stats(data):
    """Print summary statistics for the paper."""
    summary = data["summary"]
    total = data["total_skills"]

    print("\n=== Summary Statistics ===")
    print(f"Total skills: {total}")
    print(f"Passed: {summary['passed']} ({summary['passed']/total*100:.1f}%)")
    print(f"Failed: {summary['failed']} ({summary['failed']/total*100:.1f}%)")
    print(f"Total errors: {summary['total_errors']}")
    print(f"Total warnings: {summary['total_warnings']}")

    ts = summary.get("token_stats", {})
    print(f"\nToken counts:")
    print(f"  Min: {ts.get('min', 0):,}")
    print(f"  Max: {ts.get('max', 0):,}")
    print(f"  Mean: {ts.get('mean', 0):,}")
    print(f"  Median: {ts.get('median', 0):,}")

    ns = summary.get("nonstandard_stats", {})
    if ns:
        print(f"\nNonstandard token impact:")
        print(f"  Skills with nonstandard files: {ns['skills_with_nonstandard']}")
        print(f"  Mean effective tokens: {ns['mean_effective_tokens']:,}")
        print(f"  Median effective tokens: {ns['median_effective_tokens']:,}")
        print(f"  Inflation (mean): {ns['inflation_mean_pct']}%")
        print(f"  Inflation (median): {ns['inflation_median_pct']}%")
        print(f"  Skills where SKILL.md < 10% of total: {ns['skills_below_10pct_skill_md']}")

    contamination = summary["contamination_distribution"]
    print(f"\nContamination distribution:")
    print(f"  High: {contamination['high']} ({contamination['high']/total*100:.1f}%)")
    print(f"  Medium: {contamination['medium']} ({contamination['medium']/total*100:.1f}%)")
    print(f"  Low: {contamination['low']} ({contamination['low']/total*100:.1f}%)")

    hc = summary.get("hidden_contamination", {})
    if hc:
        print(f"\nHidden contamination (clean SKILL.md, contaminated refs):")
        print(f"  Total: {hc['total']} ({hc['high_ref']} high + {hc['medium_ref']} medium)")
        if hc.get("by_source"):
            for src, count in sorted(hc["by_source"].items(), key=lambda x: -x[1]):
                print(f"    {src}: {count}")

    print(f"\nContent metrics:")
    print(f"  Avg info density: {summary['avg_information_density']:.3f}")
    print(f"  Avg specificity: {summary['avg_instruction_specificity']:.3f}")

    lh = summary.get("link_health", {})
    if lh:
        print(f"\nLink health:")
        print(f"  Broken links: {lh.get('total_broken', 0)}")
        print(f"  Skills with broken links: {lh.get('skills_with_broken_links', 0)}")

    # Reference file stats
    rs = summary.get("reference_stats", {})
    if rs:
        print(f"\nReference files:")
        print(f"  Skills with references: {rs['skills_with_refs']} ({rs['skills_with_refs']/total*100:.0f}%)")
        print(f"  Total reference files: {rs['total_ref_files']}")
        print(f"  Avg ref info density: {rs['avg_ref_info_density']:.3f} (vs SKILL.md: {summary['avg_information_density']:.3f})")
        print(f"  Refs with contamination risk: {rs['refs_with_contamination']}")
        print(f"\nReference token stats:")
        print(f"  Median: {rs.get('median_ref_tokens', 0):,}")
        print(f"  P99: {rs.get('p99_ref_tokens', 0):,}")
        print(f"  Oversized refs (>50k tokens): {rs['oversized_refs']}")
        print(f"  Skills with refs >50k: {rs.get('skills_with_refs_over_50k', 0)}")
        print(f"  Refs larger than SKILL.md: {rs['refs_larger_than_skill']} ({rs.get('pct_refs_larger_than_skill', 0)}%)")

    print(f"\nBy source:")
    for source, stats in sorted(data["by_source"].items()):
        pct = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
        broken = stats.get("broken_link_count", 0)
        link_info = f", {broken} broken links" if broken > 0 else ""
        print(f"  {source}: {stats['total']} skills, {pct:.0f}% pass, avg {stats['avg_tokens']} tokens, avg contamination {stats['avg_contamination_score']:.3f}{link_info}")
        print(f"    Errors: {stats.get('total_errors', 0)}, Warnings: {stats.get('total_warnings', 0)}")
        print(f"    Avg info density: {stats.get('avg_information_density', 0):.3f}, Avg specificity: {stats.get('avg_instruction_specificity', 0):.3f}")
        tbc = stats.get("token_budget_composition", {})
        if tbc:
            print(f"    Token budget: SKILL.md {tbc['skill_md_pct']}%, refs {tbc['ref_pct']}%, assets {tbc['asset_pct']}%, nonstandard {tbc['nonstandard_pct']}%")


def fig_token_budget_composition(data):
    """Stacked bar chart: token budget composition by source (SKILL.md, refs, assets, nonstandard)."""
    from collections import defaultdict

    budget = defaultdict(lambda: {"skill_md": 0, "ref": 0, "asset": 0, "nonstandard": 0})
    for s in data["skills"]:
        src = s["source"]
        budget[src]["skill_md"] += s.get("skill_md_tokens", 0)
        budget[src]["ref"] += s.get("ref_tokens", 0)
        budget[src]["asset"] += s.get("asset_tokens", 0)
        budget[src]["nonstandard"] += s.get("nonstandard_tokens", 0)

    # Sort by total tokens descending
    sources = sorted(budget.keys(), key=lambda s: sum(budget[s].values()), reverse=True)

    # Compute percentages
    skill_md_pct, ref_pct, asset_pct, ns_pct = [], [], [], []
    for src in sources:
        total = sum(budget[src].values())
        if total == 0:
            total = 1
        skill_md_pct.append(100 * budget[src]["skill_md"] / total)
        ref_pct.append(100 * budget[src]["ref"] / total)
        asset_pct.append(100 * budget[src]["asset"] / total)
        ns_pct.append(100 * budget[src]["nonstandard"] / total)

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(sources))

    ax.bar(x, skill_md_pct, label="SKILL.md", color="#2ecc71")
    ax.bar(x, ref_pct, bottom=skill_md_pct, label="References", color="#3498db")
    ax.bar(x, asset_pct, bottom=[a + b for a, b in zip(skill_md_pct, ref_pct)],
           label="Assets", color="#9b59b6")
    ax.bar(x, ns_pct, bottom=[a + b + c for a, b, c in zip(skill_md_pct, ref_pct, asset_pct)],
           label="Nonstandard", color="#e74c3c", alpha=0.8)

    ax.set_xlabel("Source")
    ax.set_ylabel("Percentage of Total Tokens")
    ax.set_title("Token Budget Composition by Source")
    ax.set_xticks(list(x))
    ax.set_xticklabels(sources, rotation=15, ha="right")
    ax.legend(loc="upper right", fontsize=9)
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter())

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "token_budget_composition.png")
    plt.close(fig)
    print("  → token_budget_composition.png")


def fig_hidden_contamination(data):
    """Bar chart comparing SKILL.md vs reference contamination for skills with hidden contamination."""
    # Hidden contamination: low SKILL.md contamination but medium/high ref contamination
    hidden = [s for s in data["skills"]
              if s.get("ref_file_count", 0) > 0
              and s.get("contamination_level") == "low"
              and s.get("ref_contamination_level") in ("medium", "high")]

    if not hidden:
        print("  → hidden_contamination.png (skipped, no data)")
        return

    # Sort by ref contamination descending, take top 20
    hidden.sort(key=lambda s: s.get("ref_contamination_score", 0), reverse=True)
    top = hidden[:20]

    labels = [s["name"][:25] for s in top]
    skill_scores = [s["contamination_score"] for s in top]
    ref_scores = [s["ref_contamination_score"] for s in top]

    fig, ax = plt.subplots(figsize=(10, 7))

    y = range(len(labels))
    height = 0.35
    ax.barh([i + height / 2 for i in y], ref_scores, height,
            label="Reference files", color=COLORS["medium"], alpha=0.9)
    ax.barh([i - height / 2 for i in y], skill_scores, height,
            label="SKILL.md", color=COLORS["low"], alpha=0.9)

    ax.axvline(x=0.2, color="#999", linestyle=":", linewidth=1, alpha=0.7)
    ax.axvline(x=0.5, color="#999", linestyle=":", linewidth=1, alpha=0.7)
    ax.text(0.1, len(labels) - 0.5, "Low", ha="center", fontsize=8, color="#999")
    ax.text(0.35, len(labels) - 0.5, "Medium", ha="center", fontsize=8, color="#999")
    ax.text(0.65, len(labels) - 0.5, "High", ha="center", fontsize=8, color="#999")

    ax.set_yticks(list(y))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Contamination Score")
    ax.set_title("Hidden Contamination: Clean SKILL.md, Contaminated References (Top 20)")
    ax.legend(loc="lower right")
    ax.invert_yaxis()

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "hidden_contamination.png")
    plt.close(fig)
    print("  → hidden_contamination.png")


def fig_nonstandard_breakdown(data):
    """Pie chart: what types of files make up the nonstandard token waste."""
    import glob
    import os
    from collections import Counter

    category_tokens = Counter()
    for jf in sorted(glob.glob(str(REPO_ROOT / "data" / "raw" / "*" / "*.json"))):
        with open(jf) as f:
            raw = json.load(f)
        for finfo in raw.get("other_token_counts", {}).get("files", []):
            fname = finfo["file"]
            tokens = finfo.get("tokens", 0)
            upper = fname.upper()
            if "LICENSE" in upper or "LICENCE" in upper:
                category_tokens["LICENSE files"] += tokens
            elif ".xsd" in fname or "ooxml" in fname:
                category_tokens["OOXML schemas (XSD)"] += tokens
            elif "benchmark" in fname.lower() or "results" in fname.lower():
                category_tokens["Benchmarks & results"] += tokens
            elif fname.endswith((".js.map", "package-lock.json", ".pptx")):
                category_tokens["Build artifacts"] += tokens
            elif "README" in upper:
                category_tokens["README files"] += tokens
            elif fname.startswith("templates/") or "template" in fname.lower():
                category_tokens["Templates"] += tokens
            elif fname.endswith((".yaml", ".yml")) and "agents/" in fname:
                category_tokens["Agent configs (YAML)"] += tokens
            elif "dashboard" in fname.lower() or "vscode-extension" in fname.lower():
                category_tokens["UI/extension code"] += tokens
            elif fname.endswith(".skill"):
                category_tokens["Legacy .skill files"] += tokens
            else:
                category_tokens["Other"] += tokens

    if not category_tokens:
        print("  → nonstandard_breakdown.png (skipped, no data)")
        return

    # Sort by size, combine small categories into "Other"
    sorted_cats = category_tokens.most_common()
    total = sum(category_tokens.values())
    threshold = total * 0.03  # 3% minimum
    main_cats = [(k, v) for k, v in sorted_cats if v >= threshold]
    other_sum = sum(v for _, v in sorted_cats if v < threshold)
    # Merge with existing Other if present
    main_cats_dict = dict(main_cats)
    if "Other" in main_cats_dict:
        main_cats_dict["Other"] += other_sum
    else:
        main_cats_dict["Other"] = other_sum
    main_cats = sorted(main_cats_dict.items(), key=lambda x: -x[1])

    labels = [f"{k}\n({v:,.0f} tokens)" for k, v in main_cats]
    sizes = [v for _, v in main_cats]
    colors = ["#e74c3c", "#3498db", "#f39c12", "#9b59b6", "#1abc9c",
              "#e67e22", "#2ecc71", "#34495e", "#95a5a6", "#d35400"][:len(labels)]

    fig, ax = plt.subplots(figsize=(9, 6))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="%1.1f%%",
        startangle=90, pctdistance=0.8, textprops={"fontsize": 9},
    )
    for at in autotexts:
        at.set_fontsize(8)
    ax.set_title(f"Nonstandard Token Waste Breakdown\n({total:,.0f} tokens across {len(data['skills'])} skills)")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "nonstandard_breakdown.png")
    plt.close(fig)
    print("  → nonstandard_breakdown.png")


LLM_DIMS = [
    ("llm_clarity", "Clarity"),
    ("llm_actionability", "Actionability"),
    ("llm_token_efficiency", "Token Efficiency"),
    ("llm_scope_discipline", "Scope Discipline"),
    ("llm_directive_precision", "Directive Precision"),
    ("llm_novelty", "Novelty"),
]

REF_LLM_DIMS = [
    ("ref_llm_clarity", "Clarity"),
    ("ref_llm_instructional_value", "Instructional Value"),
    ("ref_llm_token_efficiency", "Token Efficiency"),
    ("ref_llm_novelty", "Novelty"),
    ("ref_llm_skill_relevance", "Skill Relevance"),
]


def _llm_scored_skills(data):
    """Return skills that have a non-null llm_overall score."""
    return [s for s in data["skills"] if s.get("llm_overall") is not None]


def fig_llm_scores_by_source(data):
    """Grouped bar chart: mean LLM judge scores by source category."""
    import numpy as np

    skills = _llm_scored_skills(data)
    if not skills:
        print("  → llm_scores_by_source.png (skipped, no LLM data)")
        return

    sources = sorted(set(s["source"] for s in skills))
    dims = LLM_DIMS

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(sources))
    width = 0.12
    offsets = np.arange(len(dims)) - (len(dims) - 1) / 2

    dim_colors = ["#3498db", "#2ecc71", "#e67e22", "#9b59b6", "#1abc9c", "#e74c3c"]

    for i, (key, label) in enumerate(dims):
        means = []
        for src in sources:
            vals = [s[key] for s in skills if s["source"] == src and s.get(key) is not None]
            means.append(sum(vals) / len(vals) if vals else 0)
        ax.bar(x + offsets[i] * width, means, width, label=label,
               color=dim_colors[i], alpha=0.85)

    ax.set_xlabel("Source")
    ax.set_ylabel("Mean Score (1-5)")
    ax.set_title("LLM Judge Scores by Source")
    ax.set_xticks(x)
    ax.set_xticklabels(sources, rotation=15, ha="right")
    ax.legend(loc="lower left", fontsize=8, ncol=3)
    ax.set_ylim(1, 5.3)
    ax.axhline(y=3, color="#ccc", linestyle=":", linewidth=0.8)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "llm_scores_by_source.png")
    plt.close(fig)
    print("  → llm_scores_by_source.png")


def fig_llm_novelty_distribution(data):
    """Stacked bar chart: novelty score distribution by source."""
    skills = _llm_scored_skills(data)
    novelty_skills = [s for s in skills if s.get("llm_novelty") is not None]
    if not novelty_skills:
        print("  → llm_novelty_distribution.png (skipped, no data)")
        return

    sources = sorted(set(s["source"] for s in novelty_skills))
    score_values = [1, 2, 3, 4, 5]
    score_colors = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#27ae60"]

    # Compute percentage distributions per source
    pcts = {score: [] for score in score_values}
    for src in sources:
        src_skills = [s for s in novelty_skills if s["source"] == src]
        total = len(src_skills)
        for score in score_values:
            count = sum(1 for s in src_skills if s["llm_novelty"] == score)
            pcts[score].append(100 * count / total if total else 0)

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(sources))
    bottom = [0] * len(sources)

    for score, color in zip(score_values, score_colors):
        ax.bar(x, pcts[score], bottom=bottom, label=f"Score {score}",
               color=color, alpha=0.85)
        bottom = [b + p for b, p in zip(bottom, pcts[score])]

    ax.set_xlabel("Source")
    ax.set_ylabel("Percentage of Skills")
    ax.set_title("Novelty Score Distribution by Source")
    ax.set_xticks(list(x))
    ax.set_xticklabels(sources, rotation=15, ha="right")
    ax.legend(loc="upper right", fontsize=9)
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter())

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "llm_novelty_distribution.png")
    plt.close(fig)
    print("  → llm_novelty_distribution.png")


def fig_llm_dimension_correlations(data):
    """Heatmap: correlations between LLM judge dimensions."""
    import numpy as np

    skills = _llm_scored_skills(data)
    if not skills:
        print("  → llm_dimension_correlations.png (skipped, no LLM data)")
        return

    dims = LLM_DIMS
    # Only use skills that have all dimensions
    complete = [s for s in skills
                if all(s.get(k) is not None for k, _ in dims)]
    if len(complete) < 10:
        print("  → llm_dimension_correlations.png (skipped, too few complete scores)")
        return

    values = []
    for key, _ in dims:
        values.append([s[key] for s in complete])

    corr = np.corrcoef(values)
    n = len(dims)

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(corr, cmap="RdYlGn", vmin=-1, vmax=1)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels([m[1] for m in dims], rotation=45, ha="right")
    ax.set_yticklabels([m[1] for m in dims])

    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center",
                    fontsize=10, color="black" if abs(corr[i, j]) < 0.7 else "white")

    ax.set_title("LLM Judge Dimension Correlations")
    fig.colorbar(im, ax=ax, shrink=0.8)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "llm_dimension_correlations.png")
    plt.close(fig)
    print("  → llm_dimension_correlations.png")


def fig_llm_vs_heuristic(data):
    """Heatmap: correlations between LLM dimensions and heuristic metrics."""
    import numpy as np

    skills = _llm_scored_skills(data)
    if not skills:
        print("  → llm_vs_heuristic.png (skipped, no LLM data)")
        return

    llm_dims = LLM_DIMS
    heuristics = [
        ("information_density", "Info Density"),
        ("instruction_specificity", "Specificity"),
        ("contamination_score", "Contamination"),
        ("skill_md_tokens", "SKILL.md Tokens"),
        ("word_count", "Word Count"),
        ("code_block_ratio", "Code Ratio"),
        ("imperative_ratio", "Imperative Ratio"),
    ]

    # Use skills with all LLM dims present
    complete = [s for s in skills
                if all(s.get(k) is not None for k, _ in llm_dims)]
    if len(complete) < 10:
        print("  → llm_vs_heuristic.png (skipped, too few complete scores)")
        return

    llm_values = [[s[k] for s in complete] for k, _ in llm_dims]
    heur_values = [[s.get(k, 0) for s in complete] for k, _ in heuristics]

    # Compute cross-correlation matrix (llm rows x heuristic cols)
    all_values = np.array(llm_values + heur_values)
    full_corr = np.corrcoef(all_values)
    n_llm = len(llm_dims)
    n_heur = len(heuristics)
    cross_corr = full_corr[:n_llm, n_llm:]

    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.imshow(cross_corr, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(n_heur))
    ax.set_yticks(range(n_llm))
    ax.set_xticklabels([m[1] for m in heuristics], rotation=45, ha="right")
    ax.set_yticklabels([m[1] for m in llm_dims])

    for i in range(n_llm):
        for j in range(n_heur):
            ax.text(j, i, f"{cross_corr[i, j]:.2f}", ha="center", va="center",
                    fontsize=9, color="black" if abs(cross_corr[i, j]) < 0.7 else "white")

    ax.set_title("LLM Judge vs. Heuristic Metric Correlations")
    fig.colorbar(im, ax=ax, shrink=0.8)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "llm_vs_heuristic.png")
    plt.close(fig)
    print("  → llm_vs_heuristic.png")


def fig_llm_ref_vs_skill(data):
    """Grouped bar chart: mean ref LLM scores vs SKILL.md LLM scores."""
    # Skills with both SKILL.md and ref LLM scores
    both = [s for s in data["skills"]
            if s.get("llm_overall") is not None
            and s.get("ref_llm_overall") is not None]
    if not both:
        print("  → llm_ref_vs_skill.png (skipped, no data)")
        return

    # Shared dimensions between skill and ref scoring
    shared = [
        ("clarity", "Clarity"),
        ("token_efficiency", "Token Efficiency"),
        ("novelty", "Novelty"),
    ]

    skill_means = []
    ref_means = []
    labels = []
    for dim, label in shared:
        sk = [s[f"llm_{dim}"] for s in both if s.get(f"llm_{dim}") is not None]
        rf = [s[f"ref_llm_{dim}"] for s in both if s.get(f"ref_llm_{dim}") is not None]
        if sk and rf:
            skill_means.append(sum(sk) / len(sk))
            ref_means.append(sum(rf) / len(rf))
            labels.append(label)

    # Add overall
    sk_overall = [s["llm_overall"] for s in both]
    rf_overall = [s["ref_llm_overall"] for s in both]
    skill_means.append(sum(sk_overall) / len(sk_overall))
    ref_means.append(sum(rf_overall) / len(rf_overall))
    labels.append("Overall")

    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(labels))
    width = 0.3
    ax.bar([i - width / 2 for i in x], skill_means, width,
           label="SKILL.md", color="#3498db", alpha=0.85)
    ax.bar([i + width / 2 for i in x], ref_means, width,
           label="Reference Files", color="#e67e22", alpha=0.85)

    ax.set_xlabel("Dimension")
    ax.set_ylabel("Mean Score (1-5)")
    ax.set_title(f"SKILL.md vs. Reference File Quality (n={len(both)})")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.legend()
    ax.set_ylim(1, 5.3)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "llm_ref_vs_skill.png")
    plt.close(fig)
    print("  → llm_ref_vs_skill.png")


def print_llm_stats(data):
    """Print LLM judge summary statistics."""
    skills = _llm_scored_skills(data)
    if not skills:
        return

    print(f"\n=== LLM Judge Statistics ===")
    print(f"Skills scored: {len(skills)}/{data['total_skills']}")

    # Null dimension counts
    all_skills = data["skills"]
    nulls = {}
    for key, label in LLM_DIMS:
        n = sum(1 for s in all_skills if s.get(key) is None)
        if n > 0:
            nulls[label] = n
    if nulls:
        print(f"Missing dimensions: {nulls}")

    # Global means
    print(f"\nGlobal means:")
    for key, label in LLM_DIMS:
        vals = [s[key] for s in skills if s.get(key) is not None]
        if vals:
            print(f"  {label}: {sum(vals)/len(vals):.3f} (n={len(vals)})")
    overalls = [s["llm_overall"] for s in skills]
    print(f"  Overall: {sum(overalls)/len(overalls):.3f}")

    # By source
    sources = sorted(set(s["source"] for s in skills))
    print(f"\nOverall score by source (ranked):")
    source_means = []
    for src in sources:
        vals = [s["llm_overall"] for s in skills if s["source"] == src]
        source_means.append((src, sum(vals) / len(vals), len(vals)))
    source_means.sort(key=lambda x: -x[1])
    for src, mean, n in source_means:
        print(f"  {src}: {mean:.3f} (n={n})")

    # Novelty by source
    print(f"\nNovelty by source (ranked):")
    novelty_means = []
    for src in sources:
        vals = [s["llm_novelty"] for s in skills
                if s["source"] == src and s.get("llm_novelty") is not None]
        if vals:
            novelty_means.append((src, sum(vals) / len(vals), len(vals)))
    novelty_means.sort(key=lambda x: -x[1])
    for src, mean, n in novelty_means:
        high_pct = 100 * sum(1 for s in skills
                             if s["source"] == src
                             and s.get("llm_novelty") is not None
                             and s["llm_novelty"] >= 4) / n
        print(f"  {src}: {mean:.3f} ({high_pct:.0f}% scoring >= 4, n={n})")

    # Top and bottom skills
    ranked = sorted(skills, key=lambda s: s["llm_overall"], reverse=True)
    print(f"\nTop 10 skills by overall LLM score:")
    for s in ranked[:10]:
        print(f"  {s['llm_overall']:.2f}  {s['source']}/{s['name']}")
    print(f"\nBottom 10 skills by overall LLM score:")
    for s in ranked[-10:]:
        print(f"  {s['llm_overall']:.2f}  {s['source']}/{s['name']}")

    # Structural validation vs LLM quality
    passed = [s["llm_overall"] for s in skills if s.get("passed")]
    failed = [s["llm_overall"] for s in skills if not s.get("passed")]
    if passed and failed:
        print(f"\nLLM overall by validation status:")
        print(f"  Passed: {sum(passed)/len(passed):.3f} (n={len(passed)})")
        print(f"  Failed: {sum(failed)/len(failed):.3f} (n={len(failed)})")

    # Reference file quality comparison
    both = [s for s in skills if s.get("ref_llm_overall") is not None]
    if both:
        sk = sum(s["llm_overall"] for s in both) / len(both)
        rf = sum(s["ref_llm_overall"] for s in both) / len(both)
        print(f"\nSKILL.md vs Reference file quality (n={len(both)}):")
        print(f"  SKILL.md overall: {sk:.3f}")
        print(f"  Reference overall: {rf:.3f}")
        print(f"  Delta: {rf - sk:+.3f}")

        for dim, label in [("clarity", "Clarity"), ("token_efficiency", "Token Efficiency"), ("novelty", "Novelty")]:
            sk_vals = [s[f"llm_{dim}"] for s in both if s.get(f"llm_{dim}") is not None]
            rf_vals = [s[f"ref_llm_{dim}"] for s in both if s.get(f"ref_llm_{dim}") is not None]
            if sk_vals and rf_vals:
                sk_m = sum(sk_vals) / len(sk_vals)
                rf_m = sum(rf_vals) / len(rf_vals)
                print(f"  {label}: SKILL.md {sk_m:.3f}, Refs {rf_m:.3f} (delta {rf_m - sk_m:+.3f})")


def print_craft_vs_content_stats(data):
    """Print per-dimension source profiles for craft vs. content analysis."""
    by_source = data.get("by_source", {})
    dims = [
        ("avg_llm_clarity", "Clarity"),
        ("avg_llm_actionability", "Actionability"),
        ("avg_llm_token_efficiency", "Token Efficiency"),
        ("avg_llm_scope_discipline", "Scope Discipline"),
        ("avg_llm_directive_precision", "Directive Precision"),
        ("avg_llm_novelty", "Novelty"),
    ]

    # Check if LLM data is present
    if not any(by_source[s].get("avg_llm_overall") is not None for s in by_source):
        return

    sources = sorted(by_source.keys())

    print(f"\n=== Craft vs. Content: Per-Dimension Source Profiles ===")

    # Per-dimension rankings
    print(f"\nPer-dimension means and rankings:")
    for key, label in dims:
        source_vals = []
        for src in sources:
            val = by_source[src].get(key)
            if val is not None:
                source_vals.append((src, val))
        source_vals.sort(key=lambda x: -x[1])
        high = source_vals[0][1] if source_vals else 0
        low = source_vals[-1][1] if source_vals else 0
        spread = high - low

        print(f"\n  {label} (spread: {spread:.2f}):")
        for rank, (src, val) in enumerate(source_vals, 1):
            print(f"    #{rank} {src}: {val:.3f}")

    # Dimension spread summary (most to least discriminating)
    print(f"\nDimension spread summary (most → least discriminating):")
    spreads = []
    for key, label in dims:
        vals = [by_source[s][key] for s in sources if by_source[s].get(key) is not None]
        if vals:
            spreads.append((label, max(vals) - min(vals)))
    spreads.sort(key=lambda x: -x[1])
    for label, spread in spreads:
        print(f"  {label}: {spread:.3f}")

    # Per-source strength/weakness
    print(f"\nPer-source relative strength and weakness:")
    for src in sources:
        rankings = []
        for key, label in dims:
            # Compute rank for this source on this dimension
            vals = [(s, by_source[s].get(key, 0)) for s in sources
                    if by_source[s].get(key) is not None]
            vals.sort(key=lambda x: -x[1])
            for rank, (s, _) in enumerate(vals, 1):
                if s == src:
                    rankings.append((label, rank))
                    break
        if rankings:
            best = min(rankings, key=lambda x: x[1])
            worst = max(rankings, key=lambda x: x[1])
            print(f"  {src}: strength = {best[0]} (#{best[1]}), "
                  f"weakness = {worst[0]} (#{worst[1]})")


def print_net_negative_stats(data):
    """Print net negative risk statistics (low novelty + high contamination)."""
    nn = data["summary"].get("net_negative_risk", {})
    if not nn:
        return

    print(f"\n=== Net Negative Risk (Low Novelty + High Contamination) ===")
    print(f"Strict (novelty <= 2, contamination >= 0.2): "
          f"{nn['strict_count']} skills ({nn['strict_pct']}%)")
    print(f"Broad  (novelty <= 3, contamination >= 0.2): "
          f"{nn['broad_count']} skills ({nn['broad_pct']}%)")

    print(f"\nNovelty-contamination correlation: r = {nn['novelty_contamination_corr']}")

    mc = nn.get("mean_novelty_contaminated_company")
    mnc = nn.get("mean_novelty_contaminated_non_company")
    if mc is not None and mnc is not None:
        print(f"Mean novelty among contaminated skills:")
        print(f"  Company: {mc}")
        print(f"  Non-company: {mnc}")

    print(f"\nBy source (strict):")
    for source, rates in sorted(nn.get("source_rates", {}).items(),
                                key=lambda x: -x[1]["strict_pct"]):
        if rates["strict_count"] > 0 or rates["broad_count"] > 0:
            print(f"  {source}: {rates['strict_count']}/{rates['total']} strict "
                  f"({rates['strict_pct']}%), "
                  f"{rates['broad_count']}/{rates['total']} broad "
                  f"({rates['broad_pct']}%)")

    offenders = nn.get("top_offenders", [])
    if offenders:
        print(f"\nTop offenders (strict, by contamination score):")
        for o in offenders:
            print(f"  {o['contamination_score']:.2f} contam, "
                  f"novelty {o['llm_novelty']}, "
                  f"overall {o['llm_overall']:.2f}  "
                  f"{o['source']}/{o['name']}")


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    data = load_data()

    print("Generating figures...")
    fig_pass_fail_by_source(data)
    fig_token_distribution(data)
    fig_content_quality(data)
    fig_contamination_distribution(data)
    fig_contamination_by_source(data)
    fig_metrics_correlation(data)
    fig_ref_language_distribution(data)
    fig_ref_token_ratio(data)
    fig_token_budget_composition(data)
    fig_hidden_contamination(data)
    fig_nonstandard_breakdown(data)

    fig_llm_scores_by_source(data)
    fig_llm_novelty_distribution(data)
    fig_llm_dimension_correlations(data)
    fig_llm_vs_heuristic(data)
    fig_llm_ref_vs_skill(data)

    print_summary_stats(data)
    print_llm_stats(data)
    print_craft_vs_content_stats(data)
    print_net_negative_stats(data)
    print(f"\nFigures saved to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
