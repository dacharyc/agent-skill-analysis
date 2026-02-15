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

    print_summary_stats(data)
    print(f"\nFigures saved to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
