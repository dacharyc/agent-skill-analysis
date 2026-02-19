// Agent Skill Analysis — Interactive Report
// Loads combined.json, renders charts and filterable table.

let DATA = null;
let sortCol = "name";
let sortAsc = true;

// Hardcoded behavioral evaluation data (19 skills, excluding experimental)
const BEHAVIORAL_DATA = [
    { name: "azure-containerregistry-py", contamination_score: 0.33, ba_delta: -0.117, da_delta: -0.092, risk: "medium" },
    { name: "azure-identity-dotnet", contamination_score: 0.33, ba_delta: -0.017, da_delta: 0.034, risk: "medium" },
    { name: "azure-identity-java", contamination_score: 0.52, ba_delta: 0.05, da_delta: 0.233, risk: "high" },
    { name: "azure-security-keyvault-secrets-java", contamination_score: 0.52, ba_delta: 0.0, da_delta: 0.384, risk: "high" },
    { name: "claude-settings-audit", contamination_score: 0.63, ba_delta: -0.483, da_delta: -0.3, risk: "high" },
    { name: "copilot-sdk", contamination_score: 0.63, ba_delta: -0.1, da_delta: 0.15, risk: "high" },
    { name: "fastapi-router-py", contamination_score: 0.0, ba_delta: -0.133, da_delta: -0.667, risk: "control" },
    { name: "gemini-api-dev", contamination_score: 0.55, ba_delta: 0.2, da_delta: 0.2, risk: "high" },
    { name: "monitoring-observability", contamination_score: 0.5, ba_delta: -0.233, da_delta: -0.167, risk: "medium" },
    { name: "neon-postgres", contamination_score: 0.0, ba_delta: 0.0, da_delta: -0.05, risk: "medium" },
    { name: "ossfuzz", contamination_score: 0.53, ba_delta: 0.017, da_delta: 0.267, risk: "high" },
    { name: "pdf", contamination_score: 0.33, ba_delta: -0.05, da_delta: 0.05, risk: "medium" },
    { name: "prompt-agent", contamination_score: 0.48, ba_delta: 0.0, da_delta: 0.067, risk: "medium" },
    { name: "provider-resources", contamination_score: 0.55, ba_delta: -0.317, da_delta: -0.15, risk: "high" },
    { name: "react-native-best-practices", contamination_score: 0.075, ba_delta: -0.384, da_delta: 0.117, risk: "medium" },
    { name: "sharp-edges", contamination_score: 0.62, ba_delta: -0.083, da_delta: -0.067, risk: "high" },
    { name: "skill-creator", contamination_score: 0.46, ba_delta: 0.05, da_delta: 0.0, risk: "medium" },
    { name: "upgrade-stripe", contamination_score: 0.93, ba_delta: -0.117, da_delta: -0.383, risk: "high" },
    { name: "wiki-agents-md", contamination_score: 0.57, ba_delta: 0.2, da_delta: -0.067, risk: "high" },
];

const COLORS = {
    pass: "#2ecc71",
    fail: "#e74c3c",
    high: "#e74c3c",
    medium: "#f39c12",
    low: "#2ecc71",
    sources: {
        anthropic: "#5B6ABF",
        "community-other": "#E67E22",
        "k-dense": "#1ABC9C",
        "trail-of-bits": "#9B59B6",
    },
};

// Dark mode: check localStorage, fall back to OS preference
function getTheme() {
    const stored = localStorage.getItem("theme");
    if (stored === "dark" || stored === "light") return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme) {
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.classList.toggle("light", theme === "light");
    const btn = document.getElementById("theme-toggle");
    if (btn) btn.textContent = theme === "dark" ? "\u2600\uFE0F" : "\uD83C\uDF19";
}

const currentTheme = getTheme();
applyTheme(currentTheme);
const isDark = currentTheme === "dark";

if (isDark) {
    Chart.defaults.color = "#b0b0b0";
    Chart.defaults.borderColor = "rgba(255, 255, 255, 0.1)";
    Chart.defaults.plugins.legend.labels.color = "#b0b0b0";
    Chart.defaults.plugins.title.color = "#e0e0e0";
}

// Toggle handler — reload to re-render charts with correct colors
document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("theme-toggle");
    if (btn) {
        btn.addEventListener("click", () => {
            const next = getTheme() === "dark" ? "light" : "dark";
            localStorage.setItem("theme", next);
            applyTheme(next);
            location.reload();
        });
    }

    // Nav scroll fade indicators
    const fadeLeft = document.querySelector(".nav-fade-left");
    const fadeRight = document.querySelector(".nav-fade-right");
    const nav = document.querySelector("nav");
    if (fadeLeft && fadeRight && nav) {
        function updateNavFades() {
            const scrollLeft = nav.scrollLeft;
            const maxScroll = nav.scrollWidth - nav.clientWidth;
            fadeLeft.classList.toggle("visible", scrollLeft > 4);
            fadeRight.classList.toggle("visible", maxScroll - scrollLeft > 4);
        }
        nav.addEventListener("scroll", updateNavFades, { passive: true });
        window.addEventListener("resize", updateNavFades);
        updateNavFades();
    }
});

// Load data
async function loadData() {
    try {
        const resp = await fetch("data.json");
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        DATA = await resp.json();
        render();
    } catch (err) {
        document.querySelector("main").innerHTML =
            `<p style="color:red;padding:2rem;">Error loading data.json: ${err.message}<br>
            Make sure data.json exists in the site/ directory (copy or symlink from data/processed/combined.json).</p>`;
    }
}

function render() {
    renderStats();
    renderCharts();
    renderBehavioral();
    renderLLMCharts();
    renderCraftNoveltyScatter();
    renderHighRisk();
    renderHiddenContamination();
    renderNetNegative();
    populateFilters();
    renderTable();
    bindEvents();
}

// Stats cards
function renderStats() {
    document.getElementById("stat-total").textContent = DATA.total_skills;
    document.getElementById("stat-passed").textContent = DATA.summary.passed;
    document.getElementById("stat-failed").textContent = DATA.summary.failed;
    document.getElementById("stat-high-risk").textContent = DATA.summary.contamination_distribution.high;

    // Compute context window waste percentage
    let totalTokens = 0, nonstandardTokens = 0;
    DATA.skills.forEach(s => {
        totalTokens += s.total_tokens || 0;
        nonstandardTokens += s.nonstandard_tokens || 0;
    });
    const wastePct = totalTokens > 0 ? Math.round(100 * nonstandardTokens / totalTokens) : 0;
    document.getElementById("stat-waste").textContent = wastePct + "%";

    // LLM overall mean
    const llmScored = DATA.skills.filter(s => s.llm_overall != null);
    if (llmScored.length > 0) {
        const mean = llmScored.reduce((sum, s) => sum + s.llm_overall, 0) / llmScored.length;
        document.getElementById("stat-llm-overall").textContent = mean.toFixed(2);
    }

    // Hidden contamination count
    const hiddenContam = DATA.skills.filter(s =>
        s.ref_file_count > 0
        && s.contamination_level === "low"
        && (s.ref_contamination_level === "medium" || s.ref_contamination_level === "high")
    ).length;
    document.getElementById("stat-hidden-contam").textContent = hiddenContam;

    // Net negative count
    const nn = DATA.summary.net_negative_risk;
    if (nn) {
        document.getElementById("stat-net-negative").textContent = nn.strict_count;
    }
}

// Charts
function renderCharts() {
    // Pass/Fail donut
    new Chart(document.getElementById("chart-pass-fail"), {
        type: "doughnut",
        data: {
            labels: ["Passed", "Failed"],
            datasets: [{
                data: [DATA.summary.passed, DATA.summary.failed],
                backgroundColor: [COLORS.pass, COLORS.fail],
            }],
        },
        options: {
            maintainAspectRatio: window.innerWidth > 768,
            plugins: {
                title: { display: true, text: "Validation Results" },
                legend: { position: "bottom" },
            },
        },
    });

    // Contamination donut
    const contamination = DATA.summary.contamination_distribution;
    new Chart(document.getElementById("chart-risk"), {
        type: "doughnut",
        data: {
            labels: ["High", "Medium", "Low"],
            datasets: [{
                data: [contamination.high, contamination.medium, contamination.low],
                backgroundColor: [COLORS.high, COLORS.medium, COLORS.low],
            }],
        },
        options: {
            maintainAspectRatio: window.innerWidth > 768,
            plugins: {
                title: { display: true, text: "Cross-Contamination" },
                legend: { position: "bottom" },
            },
        },
    });

    // By source bar chart
    const sources = Object.keys(DATA.by_source).sort();
    new Chart(document.getElementById("chart-by-source"), {
        type: "bar",
        data: {
            labels: sources,
            datasets: [
                {
                    label: "Passed",
                    data: sources.map(s => DATA.by_source[s].passed),
                    backgroundColor: COLORS.pass,
                },
                {
                    label: "Failed",
                    data: sources.map(s => DATA.by_source[s].failed),
                    backgroundColor: COLORS.fail,
                },
            ],
        },
        options: {
            maintainAspectRatio: window.innerWidth > 768,
            plugins: { title: { display: true, text: "Pass/Fail by Source" } },
            scales: {
                x: { stacked: false },
                y: { beginAtZero: true, title: { display: true, text: "Skills" } },
            },
        },
    });

    // Token distribution histogram
    const tokens = DATA.skills.map(s => s.skill_md_tokens).filter(t => t > 0);
    const maxToken = Math.min(Math.max(...tokens), 50000);
    const binSize = 2000;
    const bins = [];
    const binLabels = [];
    for (let i = 0; i <= maxToken; i += binSize) {
        bins.push(0);
        binLabels.push(`${(i / 1000).toFixed(0)}k`);
    }
    tokens.forEach(t => {
        const idx = Math.min(Math.floor(t / binSize), bins.length - 1);
        bins[idx]++;
    });

    new Chart(document.getElementById("chart-tokens"), {
        type: "bar",
        data: {
            labels: binLabels,
            datasets: [{
                label: "Skills",
                data: bins,
                backgroundColor: "#3498db",
            }],
        },
        options: {
            maintainAspectRatio: window.innerWidth > 768,
            plugins: { title: { display: true, text: "SKILL.md Token Distribution (capped at 50k)" } },
            scales: {
                x: { title: { display: true, text: "Tokens" } },
                y: { beginAtZero: true, title: { display: true, text: "Count" } },
            },
        },
    });

    // Density distribution
    const densities = DATA.skills.map(s => s.information_density);
    const densityBins = new Array(20).fill(0);
    densities.forEach(d => {
        const idx = Math.min(Math.floor(d * 20), 19);
        densityBins[idx]++;
    });

    new Chart(document.getElementById("chart-density"), {
        type: "bar",
        data: {
            labels: densityBins.map((_, i) => (i * 0.05).toFixed(2)),
            datasets: [{
                label: "Skills",
                data: densityBins,
                backgroundColor: "#9b59b6",
            }],
        },
        options: {
            maintainAspectRatio: window.innerWidth > 768,
            plugins: { title: { display: true, text: "Information Density Distribution" } },
            scales: {
                x: { title: { display: true, text: "Density" } },
                y: { beginAtZero: true },
            },
        },
    });

    // Specificity distribution
    const specs = DATA.skills.map(s => s.instruction_specificity);
    const specBins = new Array(20).fill(0);
    specs.forEach(s => {
        const idx = Math.min(Math.floor(s * 20), 19);
        specBins[idx]++;
    });

    new Chart(document.getElementById("chart-specificity"), {
        type: "bar",
        data: {
            labels: specBins.map((_, i) => (i * 0.05).toFixed(2)),
            datasets: [{
                label: "Skills",
                data: specBins,
                backgroundColor: "#e67e22",
            }],
        },
        options: {
            maintainAspectRatio: window.innerWidth > 768,
            plugins: { title: { display: true, text: "Instruction Specificity Distribution" } },
            scales: {
                x: { title: { display: true, text: "Specificity" } },
                y: { beginAtZero: true },
            },
        },
    });

    // Contamination by source scatter chart (with jitter)
    const contaminationDatasets = sources.map(source => {
        const skills = DATA.skills.filter(s => s.source === source);
        return {
            label: source,
            data: skills.map((s, i) => ({
                x: sources.indexOf(source) + (Math.random() - 0.5) * 0.3,
                y: s.contamination_score,
            })),
            backgroundColor: COLORS.sources[source] || "#999",
            pointRadius: 3,
        };
    });

    new Chart(document.getElementById("chart-risk-detail"), {
        type: "scatter",
        data: { datasets: contaminationDatasets },
        options: {
            maintainAspectRatio: window.innerWidth > 768,
            plugins: {
                title: { display: true, text: "Contamination Score by Source" },
                legend: { position: "bottom" },
            },
            scales: {
                x: {
                    type: "linear",
                    ticks: {
                        callback: (val) => sources[Math.round(val)] || "",
                        stepSize: 1,
                    },
                    min: -0.5,
                    max: sources.length - 0.5,
                },
                y: { beginAtZero: true, max: 1, title: { display: true, text: "Contamination Score" } },
            },
        },
    });

    // Token Budget Composition (stacked bar by source)
    const budgetBySource = {};
    sources.forEach(s => { budgetBySource[s] = { skill_md: 0, ref: 0, asset: 0, nonstandard: 0 }; });
    DATA.skills.forEach(s => {
        const b = budgetBySource[s.source];
        if (!b) return;
        b.skill_md += s.skill_md_tokens || 0;
        b.ref += s.ref_tokens || 0;
        b.asset += s.asset_tokens || 0;
        b.nonstandard += s.nonstandard_tokens || 0;
    });

    const budgetSources = sources;
    const toPct = (src, key) => {
        const b = budgetBySource[src];
        const total = b.skill_md + b.ref + b.asset + b.nonstandard;
        return total > 0 ? (100 * b[key] / total) : 0;
    };

    new Chart(document.getElementById("chart-token-budget"), {
        type: "bar",
        data: {
            labels: budgetSources,
            datasets: [
                { label: "SKILL.md", data: budgetSources.map(s => toPct(s, "skill_md")), backgroundColor: "#2ecc71" },
                { label: "References", data: budgetSources.map(s => toPct(s, "ref")), backgroundColor: "#3498db" },
                { label: "Assets", data: budgetSources.map(s => toPct(s, "asset")), backgroundColor: "#9b59b6" },
                { label: "Nonstandard", data: budgetSources.map(s => toPct(s, "nonstandard")), backgroundColor: "rgba(231, 76, 60, 0.8)" },
            ],
        },
        options: {
            maintainAspectRatio: window.innerWidth > 768,
            plugins: { title: { display: true, text: "Token Budget Composition by Source (%)" } },
            scales: {
                x: { stacked: true },
                y: { stacked: true, beginAtZero: true, max: 100, title: { display: true, text: "% of Total Tokens" } },
            },
        },
    });
}

// LLM Quality charts
function renderLLMCharts() {
    const sources = Object.keys(DATA.by_source).sort();
    const dims = [
        { key: "avg_llm_clarity", label: "Clarity", color: "#3498db" },
        { key: "avg_llm_actionability", label: "Actionability", color: "#2ecc71" },
        { key: "avg_llm_token_efficiency", label: "Token Efficiency", color: "#e67e22" },
        { key: "avg_llm_scope_discipline", label: "Scope Discipline", color: "#9b59b6" },
        { key: "avg_llm_directive_precision", label: "Directive Precision", color: "#1abc9c" },
        { key: "avg_llm_novelty", label: "Novelty", color: "#e74c3c" },
    ];

    // Check if LLM data is available
    if (DATA.by_source[sources[0]].avg_llm_overall == null) return;

    // Grouped bar: LLM scores by source
    new Chart(document.getElementById("chart-llm-by-source"), {
        type: "bar",
        data: {
            labels: sources,
            datasets: dims.map(d => ({
                label: d.label,
                data: sources.map(s => DATA.by_source[s][d.key]),
                backgroundColor: d.color,
            })),
        },
        options: {
            maintainAspectRatio: window.innerWidth > 768,
            plugins: {
                title: { display: true, text: "LLM Judge Scores by Source (1-5)" },
                legend: { position: "bottom" },
            },
            scales: {
                y: { beginAtZero: false, min: 1, max: 5.3, title: { display: true, text: "Mean Score" } },
            },
        },
    });

    // Stacked bar: Novelty distribution by source
    const scoreValues = [1, 2, 3, 4, 5];
    const scoreColors = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#27ae60"];
    const noveltyDatasets = scoreValues.map((score, i) => ({
        label: "Score " + score,
        data: sources.map(src => {
            const srcSkills = DATA.skills.filter(s => s.source === src && s.llm_novelty != null);
            const count = srcSkills.filter(s => s.llm_novelty === score).length;
            return srcSkills.length > 0 ? (100 * count / srcSkills.length) : 0;
        }),
        backgroundColor: scoreColors[i],
    }));

    new Chart(document.getElementById("chart-novelty-dist"), {
        type: "bar",
        data: { labels: sources, datasets: noveltyDatasets },
        options: {
            maintainAspectRatio: window.innerWidth > 768,
            plugins: {
                title: { display: true, text: "Novelty Score Distribution by Source" },
                legend: { position: "bottom" },
            },
            scales: {
                x: { stacked: true, ticks: { maxRotation: 45 } },
                y: { stacked: true, beginAtZero: true, max: 100, title: { display: true, text: "% of Skills" } },
            },
        },
    });

    // Horizontal bar: Dimension spread (max - min across sources)
    const spreadData = dims.map(d => {
        const vals = sources.map(s => DATA.by_source[s][d.key]).filter(v => v != null);
        return { label: d.label, spread: Math.max(...vals) - Math.min(...vals), color: d.color };
    }).sort((a, b) => b.spread - a.spread);

    new Chart(document.getElementById("chart-llm-spread"), {
        type: "bar",
        data: {
            labels: spreadData.map(d => d.label),
            datasets: [{
                label: "Spread (max - min across sources)",
                data: spreadData.map(d => d.spread),
                backgroundColor: spreadData.map(d => d.color),
            }],
        },
        options: {
            indexAxis: "y",
            maintainAspectRatio: window.innerWidth > 768,
            plugins: { title: { display: true, text: "Dimension Spread Across Sources" }, legend: { display: false } },
            scales: {
                x: { beginAtZero: true, title: { display: true, text: "Spread (points)" } },
            },
        },
    });
}

// Net negative risk
function renderNetNegative() {
    const nn = DATA.summary.net_negative_risk;
    if (!nn || !nn.strict_count) return;

    // Summary callout
    const summaryEl = document.getElementById("net-negative-summary");
    const sourceRows = Object.entries(nn.source_rates || {})
        .filter(([, r]) => r.strict_count > 0)
        .sort((a, b) => b[1].strict_pct - a[1].strict_pct)
        .map(([src, r]) => `<tr><td>${src}</td><td>${r.strict_count}/${r.total}</td><td>${r.strict_pct}%</td></tr>`)
        .join("");

    summaryEl.innerHTML = `
        <div class="callout-stats">
            <div><strong>${nn.strict_count}</strong> skills (${nn.strict_pct}%) in low value-add quadrant</div>
            <div>Novelty-contamination correlation: <strong>r = ${nn.novelty_contamination_corr}</strong> (independent)</div>
            <div>Mean novelty among contaminated skills: company <strong>${nn.mean_novelty_contaminated_company}</strong> vs non-company <strong>${nn.mean_novelty_contaminated_non_company}</strong></div>
        </div>
        <table class="callout-table">
            <thead><tr><th>Source</th><th>Count</th><th>Rate</th></tr></thead>
            <tbody>${sourceRows}</tbody>
        </table>
    `;

    // Highest-risk net-negative cards
    const container = document.getElementById("net-negative-cards");
    const offenders = nn.top_offenders || [];
    container.innerHTML = '<h4>Lowest Value-Add Skills</h4>' + offenders.map(o => {
        const skill = DATA.skills.find(s => s.name === o.name && s.source === o.source);
        const link = skill && skill.github_url
            ? `<a href="${skill.github_url}" target="_blank" class="gh-link">View on GitHub</a>` : "";
        return `<div class="risk-card net-neg-card">
            <h4>${o.name}</h4>
            <div class="risk-meta">
                <div>Source: ${o.source}</div>
                <div>Contamination: ${o.contamination_score.toFixed(2)}</div>
                <div>Novelty: ${o.llm_novelty} / 5</div>
                <div>LLM Overall: ${o.llm_overall.toFixed(2)}</div>
                ${link}
            </div>
        </div>`;
    }).join("");
}

// High risk cards
function renderHighRisk() {
    const container = document.getElementById("high-risk-cards");
    const highRisk = DATA.skills
        .filter(s => s.contamination_level === "high")
        .sort((a, b) => b.contamination_score - a.contamination_score);

    container.innerHTML = highRisk.map(s => {
        const link = s.github_url ? '<a href="' + s.github_url + '" target="_blank" class="gh-link">View on GitHub</a>' : "";
        return '<div class="risk-card">'
            + '<h4>' + s.name + '</h4>'
            + '<div class="risk-meta">'
            + '<div>Source: ' + s.source + '</div>'
            + '<div>Contamination Score: ' + s.contamination_score.toFixed(2) + '</div>'
            + '<div>Multi-interface tools: ' + (s.multi_interface_tools.length > 0 ? s.multi_interface_tools.join(", ") : "N/A") + '</div>'
            + '<div>Mismatched categories: ' + (s.mismatched_categories.length > 0 ? s.mismatched_categories.join(", ") : "none") + '</div>'
            + '<div>Scope breadth: ' + s.scope_breadth + ' categories</div>'
            + link
            + '</div></div>';
    }).join("");
}

// Hidden contamination cards
function renderHiddenContamination() {
    const container = document.getElementById("hidden-contamination-cards");
    const hidden = DATA.skills
        .filter(s => s.ref_file_count > 0
            && s.contamination_level === "low"
            && (s.ref_contamination_level === "medium" || s.ref_contamination_level === "high"))
        .sort((a, b) => b.ref_contamination_score - a.ref_contamination_score);

    if (hidden.length === 0) {
        container.innerHTML = "<p>No hidden contamination detected.</p>";
        return;
    }

    container.innerHTML = hidden.map(s => {
        const barWidth = Math.max(Math.round(s.ref_contamination_score * 120), 8);
        const skillBarWidth = Math.max(Math.round(s.contamination_score * 120), 8);
        const isHigh = s.ref_contamination_level === "high";
        const link = s.github_url ? '<a href="' + s.github_url + '" target="_blank" class="gh-link">View on GitHub</a>' : "";
        return `
            <div class="hidden-card">
                <h4>${s.name}</h4>
                <div class="hidden-meta">
                    <div>Source: ${s.source}</div>
                    <div class="score-bar">
                        SKILL.md: ${s.contamination_score.toFixed(2)}
                        <span class="bar bar-skill" style="width:${skillBarWidth}px"></span>
                    </div>
                    <div class="score-bar">
                        Refs: ${s.ref_contamination_score.toFixed(2)}
                        <span class="bar bar-ref${isHigh ? " high" : ""}" style="width:${barWidth}px"></span>
                        <span class="badge badge-${s.ref_contamination_level}">${s.ref_contamination_level}</span>
                    </div>
                    <div>Ref files: ${s.ref_file_count} (${s.ref_total_tokens.toLocaleString()} tokens)</div>
                    ${link}
                </div>
            </div>
        `;
    }).join("");
}

// Behavioral scatter: contamination score vs B-A delta
function renderBehavioral() {
    const canvas = document.getElementById("chart-behavioral-scatter");
    if (!canvas) return;

    const riskColors = {
        high: "#e74c3c",
        medium: "#f39c12",
        control: "#3498db",
    };

    const datasets = [];
    const byRisk = {};
    BEHAVIORAL_DATA.forEach(d => {
        if (!byRisk[d.risk]) byRisk[d.risk] = [];
        byRisk[d.risk].push(d);
    });

    for (const [risk, skills] of Object.entries(byRisk)) {
        datasets.push({
            label: risk,
            data: skills.map(s => ({ x: s.contamination_score, y: s.ba_delta })),
            backgroundColor: riskColors[risk] || "#999",
            pointRadius: 6,
            pointHoverRadius: 8,
        });
    }

    new Chart(canvas, {
        type: "scatter",
        data: { datasets },
        options: {
            maintainAspectRatio: window.innerWidth > 768,
            plugins: {
                title: { display: true, text: "Structural Contamination vs. Behavioral Delta (B-A)" },
                legend: { position: "bottom" },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const risk = ctx.dataset.label;
                            const all = BEHAVIORAL_DATA.filter(d => d.risk === risk);
                            const match = all[ctx.dataIndex];
                            return match ? `${match.name}: contam=${match.contamination_score}, delta=${match.ba_delta}` : "";
                        },
                    },
                },
                annotation: undefined,
            },
            scales: {
                x: { title: { display: true, text: "Structural Contamination Score" }, min: -0.05, max: 1.0 },
                y: { title: { display: true, text: "B-A Delta (negative = degradation)" } },
            },
        },
        plugins: [{
            afterDraw: (chart) => {
                const ctx = chart.ctx;
                ctx.save();
                ctx.font = "10px -apple-system, sans-serif";
                ctx.fillStyle = isDark ? "#a0a0b0" : "#666";
                BEHAVIORAL_DATA.forEach(d => {
                    const xPixel = chart.scales.x.getPixelForValue(d.contamination_score);
                    const yPixel = chart.scales.y.getPixelForValue(d.ba_delta);
                    const short = d.name.length > 20 ? d.name.slice(0, 18) + "..." : d.name;
                    ctx.fillText(short, xPixel + 6, yPixel - 4);
                });
                // Draw trend line
                const xs = BEHAVIORAL_DATA.map(d => d.contamination_score);
                const ys = BEHAVIORAL_DATA.map(d => d.ba_delta);
                const n = xs.length;
                const mx = xs.reduce((a, b) => a + b, 0) / n;
                const my = ys.reduce((a, b) => a + b, 0) / n;
                let num = 0, den = 0;
                for (let i = 0; i < n; i++) {
                    num += (xs[i] - mx) * (ys[i] - my);
                    den += (xs[i] - mx) * (xs[i] - mx);
                }
                const slope = den !== 0 ? num / den : 0;
                const intercept = my - slope * mx;
                const x0 = 0, x1 = 1;
                const y0 = intercept, y1 = slope + intercept;
                const px0 = chart.scales.x.getPixelForValue(x0);
                const py0 = chart.scales.y.getPixelForValue(y0);
                const px1 = chart.scales.x.getPixelForValue(x1);
                const py1 = chart.scales.y.getPixelForValue(y1);
                ctx.beginPath();
                ctx.strokeStyle = isDark ? "rgba(255,255,255,0.25)" : "rgba(0,0,0,0.25)";
                ctx.lineWidth = 1.5;
                ctx.setLineDash([6, 4]);
                ctx.moveTo(px0, py0);
                ctx.lineTo(px1, py1);
                ctx.stroke();
                // Label
                ctx.setLineDash([]);
                ctx.fillStyle = isDark ? "#8a8a9a" : "#999";
                ctx.font = "11px -apple-system, sans-serif";
                ctx.fillText("r = 0.077 (no correlation)", px1 - 150, py1 - 8);
                ctx.restore();
            },
        }],
    });
}

// Craft vs Novelty scatter
function renderCraftNoveltyScatter() {
    const canvas = document.getElementById("chart-craft-novelty");
    if (!canvas || !DATA) return;

    const scored = DATA.skills.filter(s => s.llm_overall != null && s.llm_novelty != null);
    if (scored.length === 0) return;

    const sources = Object.keys(DATA.by_source).sort();
    const datasets = sources.map(source => {
        const skills = scored.filter(s => s.source === source);
        return {
            label: source,
            data: skills.map(s => {
                const craft = (
                    (s.llm_clarity || 0) +
                    (s.llm_actionability || 0) +
                    (s.llm_token_efficiency || 0) +
                    (s.llm_scope_discipline || 0) +
                    (s.llm_directive_precision || 0)
                ) / 5;
                return { x: craft, y: s.llm_novelty };
            }),
            backgroundColor: COLORS.sources[source] || "#999",
            pointRadius: 4,
            pointHoverRadius: 6,
        };
    });

    new Chart(canvas, {
        type: "scatter",
        data: { datasets },
        options: {
            maintainAspectRatio: window.innerWidth > 768,
            plugins: {
                title: { display: true, text: "Craft Composite vs. Novelty by Source" },
                legend: { position: "bottom" },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const source = ctx.dataset.label;
                            const skills = scored.filter(s => s.source === source);
                            const skill = skills[ctx.dataIndex];
                            return skill ? `${skill.name}: craft=${ctx.parsed.x.toFixed(2)}, novelty=${ctx.parsed.y}` : "";
                        },
                    },
                },
            },
            scales: {
                x: { title: { display: true, text: "Craft Composite (mean of 5 non-novelty dims)" }, min: 1, max: 5 },
                y: { title: { display: true, text: "Novelty Score" }, min: 0.5, max: 5.5 },
            },
        },
    });
}

// Filters
function populateFilters() {
    const sourceSelect = document.getElementById("filter-source");
    const sources = [...new Set(DATA.skills.map(s => s.source))].sort();
    sources.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s;
        opt.textContent = s;
        sourceSelect.appendChild(opt);
    });
}

function getFilteredSkills() {
    const source = document.getElementById("filter-source").value;
    const status = document.getElementById("filter-status").value;
    const risk = document.getElementById("filter-risk").value;
    const search = document.getElementById("filter-search").value.toLowerCase();

    return DATA.skills.filter(s => {
        if (source && s.source !== source) return false;
        if (status === "passed" && !s.passed) return false;
        if (status === "failed" && s.passed) return false;
        if (risk && s.contamination_level !== risk) return false;
        if (search && !s.name.toLowerCase().includes(search)) return false;
        return true;
    });
}

function renderTable() {
    const skills = getFilteredSkills();

    // Sort
    skills.sort((a, b) => {
        let va = a[sortCol];
        let vb = b[sortCol];
        if (typeof va === "string") {
            va = va.toLowerCase();
            vb = (vb || "").toLowerCase();
        }
        if (typeof va === "boolean") {
            va = va ? 1 : 0;
            vb = vb ? 1 : 0;
        }
        if (va == null) va = 0;
        if (vb == null) vb = 0;
        if (va < vb) return sortAsc ? -1 : 1;
        if (va > vb) return sortAsc ? 1 : -1;
        return 0;
    });

    const tbody = document.getElementById("skills-tbody");
    tbody.innerHTML = skills.map(s => `
        <tr data-name="${s.name}" data-source="${s.source}">
            <td>${s.github_url ? '<a href="' + s.github_url + '" target="_blank" class="skill-link">' + s.name + '</a>' : '<strong>' + s.name + '</strong>'}</td>
            <td>${s.source}</td>
            <td><span class="badge badge-${s.passed ? "pass" : "fail"}">${s.passed ? "Pass" : "Fail"}</span></td>
            <td>${s.errors}</td>
            <td>${s.warnings}</td>
            <td>${s.total_tokens.toLocaleString()}</td>
            <td>${s.information_density.toFixed(3)}</td>
            <td>${s.instruction_specificity.toFixed(3)}</td>
            <td><span class="badge badge-${s.contamination_level}">${s.contamination_level} (${s.contamination_score.toFixed(2)})</span></td>
            <td>${s.llm_overall != null ? s.llm_overall.toFixed(2) : "—"}${s.llm_novelty != null && s.llm_novelty <= 2 && s.contamination_score >= 0.2 ? ' <span class="badge badge-net-neg">evaluate</span>' : ""}</td>
            <td>${s.llm_novelty != null ? s.llm_novelty : "—"}</td>
        </tr>
    `).join("");
}

function showDetail(name, source) {
    const skill = DATA.skills.find(s => s.name === name && s.source === source);
    if (!skill) return;

    const panel = document.getElementById("skill-detail");
    const content = document.getElementById("detail-content");

    const rows = [
        ["Name", skill.github_url ? '<a href="' + skill.github_url + '" target="_blank">' + skill.name + '</a>' : skill.name],
        ["Source", skill.source],
        ["Status", skill.passed ? "Passed" : "Failed"],
        ["Errors", skill.errors],
        ["Warnings", skill.warnings],
        ["Total Tokens", skill.total_tokens.toLocaleString()],
        ["SKILL.md Tokens", skill.skill_md_tokens.toLocaleString()],
        ["Ref Tokens", (skill.ref_tokens || 0).toLocaleString()],
        ["Nonstandard Tokens", (skill.nonstandard_tokens || 0).toLocaleString()],
        ["Word Count", skill.word_count],
        ["Code Blocks", skill.code_block_count],
        ["Code Block Ratio", skill.code_block_ratio.toFixed(3)],
        ["Code Languages", (skill.code_languages || []).join(", ") || "none"],
        ["Sections", skill.section_count],
        ["List Items", skill.list_item_count],
        ["Info Density", skill.information_density.toFixed(4)],
        ["Specificity", skill.instruction_specificity.toFixed(4)],
        ["Contamination Score", skill.contamination_score.toFixed(4)],
        ["Contamination Level", skill.contamination_level],
        ["Multi-Interface Tools", (skill.multi_interface_tools || []).join(", ") || "none"],
        ["Language Mismatch", skill.language_mismatch ? "Yes" : "No"],
        ["Scope Breadth", skill.scope_breadth],
    ];

    if (skill.llm_overall != null) {
        rows.push(
            ["LLM Overall", skill.llm_overall],
            ["LLM Clarity", skill.llm_clarity],
            ["LLM Actionability", skill.llm_actionability],
            ["LLM Token Efficiency", skill.llm_token_efficiency],
            ["LLM Scope Discipline", skill.llm_scope_discipline],
            ["LLM Directive Precision", skill.llm_directive_precision],
            ["LLM Novelty", skill.llm_novelty],
            ["LLM Assessment", skill.llm_assessment],
        );
    }

    if (skill.ref_llm_overall != null) {
        rows.push(
            ["Ref LLM Overall", skill.ref_llm_overall],
            ["Ref LLM Clarity", skill.ref_llm_clarity],
            ["Ref LLM Token Efficiency", skill.ref_llm_token_efficiency],
            ["Ref LLM Novelty", skill.ref_llm_novelty],
        );
    }

    // Check for net negative risk
    let alertHtml = "";
    if (skill.llm_novelty != null && skill.llm_novelty <= 2 && skill.contamination_score >= 0.2) {
        alertHtml += '<div class="detail-alert alert-high">'
            + 'Low value-add risk: Low novelty (' + skill.llm_novelty
            + '/5) combined with elevated structural complexity ('
            + skill.contamination_score.toFixed(2) + ') without novel information.</div>';
    }

    // Check for hidden contamination
    if (skill.ref_file_count > 0 && skill.contamination_level === "low"
        && (skill.ref_contamination_level === "medium" || skill.ref_contamination_level === "high")) {
        const isHigh = skill.ref_contamination_level === "high";
        const cls = isHigh ? "detail-alert alert-high" : "detail-alert";
        alertHtml = '<div class="' + cls + '">'
            + 'Hidden contamination: SKILL.md is low-risk (' + skill.contamination_score.toFixed(2)
            + ') but reference files are <strong>' + skill.ref_contamination_level
            + '</strong>-risk (' + skill.ref_contamination_score.toFixed(2) + ').</div>';
    }

    content.innerHTML = `
        <h3>${skill.name}</h3>
        ${alertHtml}
        ${rows.map(([label, value]) => `
            <div class="detail-row">
                <span class="label">${label}</span>
                <span class="value">${value}</span>
            </div>
        `).join("")}
    `;

    panel.classList.remove("hidden");
}

function bindEvents() {
    // Filter changes
    ["filter-source", "filter-status", "filter-risk"].forEach(id => {
        document.getElementById(id).addEventListener("change", renderTable);
    });
    document.getElementById("filter-search").addEventListener("input", renderTable);

    // Sort
    document.querySelectorAll("#skills-table th[data-sort]").forEach(th => {
        th.addEventListener("click", () => {
            const col = th.dataset.sort;
            if (sortCol === col) {
                sortAsc = !sortAsc;
            } else {
                sortCol = col;
                sortAsc = true;
            }
            renderTable();
        });
    });

    // Row click → detail
    document.getElementById("skills-tbody").addEventListener("click", (e) => {
        const tr = e.target.closest("tr");
        if (tr) showDetail(tr.dataset.name, tr.dataset.source);
    });

    // Close detail
    document.getElementById("close-detail").addEventListener("click", () => {
        document.getElementById("skill-detail").classList.add("hidden");
    });

    // Download CSV
    document.getElementById("btn-download-csv").addEventListener("click", downloadCSV);
}

function downloadCSV() {
    const skills = getFilteredSkills();
    const headers = [
        "name", "source", "passed", "errors", "warnings",
        "total_tokens", "skill_md_tokens", "word_count",
        "code_block_count", "code_block_ratio", "information_density",
        "instruction_specificity", "contamination_score", "contamination_level",
        "llm_overall", "llm_clarity", "llm_actionability", "llm_token_efficiency",
        "llm_scope_discipline", "llm_directive_precision", "llm_novelty",
    ];
    const rows = skills.map(s => headers.map(h => {
        const v = s[h];
        if (typeof v === "string" && v.includes(",")) return `"${v}"`;
        return v;
    }));

    const csv = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "agent-skill-analysis.csv";
    a.click();
    URL.revokeObjectURL(url);
}

// Force all charts to resize when viewport changes
// Chart.js can shrink but won't grow back without this
let resizeTimeout;
window.addEventListener("resize", () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        const canvases = document.querySelectorAll(".chart-container canvas");
        canvases.forEach(canvas => {
            const chart = Chart.getChart(canvas);
            if (chart) chart.resize();
        });
    }, 100);
});

// Initialize
loadData();
