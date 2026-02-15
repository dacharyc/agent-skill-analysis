// Agent Skill Analysis — Interactive Report
// Loads combined.json, renders charts and filterable table.

let DATA = null;
let sortCol = "name";
let sortAsc = true;

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
    renderHighRisk();
    renderHiddenContamination();
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
            plugins: { title: { display: true, text: "Contamination Score by Source" } },
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
            plugins: { title: { display: true, text: "Token Budget Composition by Source (%)" } },
            scales: {
                x: { stacked: true },
                y: { stacked: true, beginAtZero: true, max: 100, title: { display: true, text: "% of Total Tokens" } },
            },
        },
    });
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
        ["Other Tokens", skill.other_tokens.toLocaleString()],
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
            ["LLM Coherence", skill.llm_coherence],
            ["LLM Relevance", skill.llm_relevance],
            ["LLM Actionability", skill.llm_actionability],
            ["LLM Completeness", skill.llm_completeness],
            ["LLM Assessment", skill.llm_assessment],
        );
    }

    // Check for hidden contamination
    let alertHtml = "";
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

// Initialize
loadData();
