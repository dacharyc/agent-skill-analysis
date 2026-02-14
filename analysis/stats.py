#!/usr/bin/env python3
"""
Generate summary statistics and figures from combined.json for the white paper.

Produces figures in paper/figures/:
  - pass_fail_by_source.png: Pass/fail rates by source
  - token_distribution.png: Distribution of token counts
  - content_quality.png: Information density and instruction specificity distributions
  - risk_distribution.png: Cross-contamination risk by level
  - risk_by_source.png: Risk score distribution by source
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


def fig_risk_distribution(data):
    """Donut chart: risk level distribution."""
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

    # Right: Risk level donut
    ax = axes[1]
    risk = data["summary"]["risk_distribution"]
    sizes = [risk["high"], risk["medium"], risk["low"]]
    labels = [f"High ({risk['high']})", f"Medium ({risk['medium']})", f"Low ({risk['low']})"]
    colors = [COLORS["high"], COLORS["medium"], COLORS["low"]]
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="%1.0f%%",
        startangle=90, pctdistance=0.75,
    )
    centre_circle = plt.Circle((0, 0), 0.50, fc="white")
    ax.add_artist(centre_circle)
    ax.set_title("Cross-Contamination Risk")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "risk_distribution.png")
    plt.close(fig)
    print("  → risk_distribution.png")


def fig_risk_by_source(data):
    """Box plot: risk scores by source."""
    fig, ax = plt.subplots()

    sources = sorted(set(s["source"] for s in data["skills"]))
    risk_data = []
    for source in sources:
        scores = [s["risk_score"] for s in data["skills"] if s["source"] == source]
        risk_data.append(scores)

    bp = ax.boxplot(risk_data, tick_labels=sources, patch_artist=True)
    for patch, source in zip(bp["boxes"], sources):
        patch.set_facecolor(COLORS.get(source, "#999"))
        patch.set_alpha(0.7)

    ax.set_xlabel("Source")
    ax.set_ylabel("Risk Score")
    ax.set_title("Cross-Contamination Risk by Source")
    ax.set_xticklabels(sources, rotation=15, ha="right")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "risk_by_source.png")
    plt.close(fig)
    print("  → risk_by_source.png")


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
        ("risk_score", "Risk Score"),
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


def print_summary_stats(data):
    """Print summary statistics for the paper."""
    print("\n=== Summary Statistics ===")
    print(f"Total skills: {data['total_skills']}")
    print(f"Passed: {data['summary']['passed']} ({data['summary']['passed']/data['total_skills']*100:.1f}%)")
    print(f"Failed: {data['summary']['failed']} ({data['summary']['failed']/data['total_skills']*100:.1f}%)")
    print(f"Total errors: {data['summary']['total_errors']}")
    print(f"Total warnings: {data['summary']['total_warnings']}")

    tokens = [s["total_tokens"] for s in data["skills"]]
    print(f"\nToken counts:")
    print(f"  Min: {min(tokens)}")
    print(f"  Max: {max(tokens)}")
    print(f"  Mean: {sum(tokens)/len(tokens):.0f}")
    print(f"  Median: {sorted(tokens)[len(tokens)//2]}")

    risk = data["summary"]["risk_distribution"]
    print(f"\nRisk distribution:")
    print(f"  High: {risk['high']} ({risk['high']/data['total_skills']*100:.1f}%)")
    print(f"  Medium: {risk['medium']} ({risk['medium']/data['total_skills']*100:.1f}%)")
    print(f"  Low: {risk['low']} ({risk['low']/data['total_skills']*100:.1f}%)")

    print(f"\nContent metrics:")
    print(f"  Avg info density: {data['summary']['avg_information_density']:.3f}")
    print(f"  Avg specificity: {data['summary']['avg_instruction_specificity']:.3f}")

    print(f"\nBy source:")
    for source, stats in sorted(data["by_source"].items()):
        pct = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  {source}: {stats['total']} skills, {pct:.0f}% pass, avg {stats['avg_tokens']} tokens, avg risk {stats['avg_risk_score']:.3f}")


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    data = load_data()

    print("Generating figures...")
    fig_pass_fail_by_source(data)
    fig_token_distribution(data)
    fig_content_quality(data)
    fig_risk_distribution(data)
    fig_risk_by_source(data)
    fig_metrics_correlation(data)

    print_summary_stats(data)
    print(f"\nFigures saved to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
