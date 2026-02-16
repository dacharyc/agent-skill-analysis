# claude-settings-audit: Template-Taught Bad Patterns

## Summary

The claude-settings-audit skill (contamination score 0.63, high risk, Sentry-internal) produces the second-largest negative B-A delta in the dataset (-0.483, p=0.019, d=-1.01). The degradation is driven by a specific, identifiable defect: the skill's output template contains JavaScript-style `//` comments in JSON, which the model faithfully reproduces, producing syntactically invalid JSON in every with_skill run for tasks 01 and 04.

## Per-Task Breakdown

| Task | Type | Base | Skill | B-A | D-A | Failure Mode |
|------|------|------|-------|-----|-----|--------------|
| 01 | direct_target | 4.50 | 3.33 | **-1.17** | -1.25 | JS comments in JSON, Sentry write ops included despite read-only requirement |
| 02 | cross_language (Rust) | 3.08 | 2.83 | -0.25 | -0.08 | Modest. Baseline already mediocre |
| 03 | similar_syntax (pnpm) | 2.67 | 3.17 | **+0.50** | +0.33 | Skill teaches correct schema. Baseline invents wrong format |
| 04 | grounded | 4.58 | 3.17 | **-1.42** | -0.33 | JS comments in JSON, scope creep (markdown docs, unrequested .mcp.json) |
| 05 | adjacent_domain (MCP) | 4.50 | 4.42 | -0.08 | -0.17 | Mostly neutral |

**Overall: B-A = -0.483, D-A = -0.300**

## Root Cause: Skill Template Contains Invalid JSON

Lines 260-269 of the SKILL.md output template:

```markdown
\`\`\`json
{
"permissions": {
"allow": [
// ... grouped by category with comments
],
"deny": []
}
}
\`\`\`
```

The `// ... grouped by category with comments` line teaches the model that JSON output should include `//` comments for readability. Every with_skill run for tasks 01 and 04 reproduces this pattern, producing syntactically invalid JSON.

The judge consistently flags this:
- "JSON does not support comments (// style comments used throughout the file), which is a pattern from JavaScript/TypeScript"
- "JSON with comments (// style comments) - this is not valid JSON; comments are a JavaScript/TypeScript pattern"
- language_correctness drops from 5 to 2-3 across all affected runs

## Secondary Failure Mode: Sentry-Specific Content Bleed

The skill is an internal Sentry tool. It includes:
- A hardcoded list of Sentry skills to whitelist (`Skill(sentry-skills:commit)`, etc.)
- Sentry-specific WebFetch domains (`docs.sentry.io`, `develop.sentry.dev`)
- Sentry MCP server configuration

When the eval tasks request settings for non-Sentry projects, the model still includes Sentry-specific entries. The judge flags: "Sentry Skills entries appear to be Sentry's internal development tools rather than generic Sentry error tracking integration."

This is organization-specific content contaminating generic outputs — a different contamination mode from cross-language PLC.

## Task 03: Why the Skill Helps

The similar_syntax task (pnpm/TypeScript/Vite) is the exception — the skill improves output. The reason is clear from the baseline assessments:

- **Baseline** doesn't know the correct Claude Code settings.json schema. It invents a different format: `"allowList"` with objects containing `"command"` and `"description"` fields. The judge flags: "Claude Code settings.json uses 'permissions' with 'allow' array of strings, not 'allowList' with objects."
- **With skill** uses the correct schema (`permissions.allow` array of strings like `Bash(pnpm list:*)`) but adds `//` comments.

The skill teaches genuinely novel schema knowledge (correct settings.json format), but also teaches the invalid JSON comment pattern. For task 03, the schema improvement outweighs the comment issue. For tasks 01 and 04, the baseline already uses the correct schema, so the comment issue dominates.

**This mirrors the gemini-api-dev pattern**: the skill helps when the model lacks knowledge (task 03: wrong schema), but hurts when the model already knows the answer (tasks 01, 04: correct schema) because the skill's defects become the dominant signal.

## Statistical Detail

| Metric | B-A | D-A |
|--------|-----|-----|
| Mean delta | -0.483 | -0.300 |
| Cohen's d | -1.01 | — |
| Wilcoxon p | 0.019 | — |
| Statistically significant | Yes | — |

## Implications

### 1. Template Quality as Contamination Vector

This is a distinct contamination mode: **the skill teaches syntactically incorrect patterns through its output template.** Unlike cross-language PLC (where Python syntax bleeds into Go), this is the skill's own example output containing an error that the model propagates faithfully.

This is arguably the most actionable finding for skill authors: review your example output for syntactic correctness, because the model will reproduce errors in templates with high fidelity.

### 2. Organization-Specific Content

Internal skills (Sentry skills, Sentry domains, Sentry MCP) contaminate generic outputs. Skill authors publishing internal tools should consider whether organization-specific content will cause problems when the skill is loaded in non-organizational contexts.

### 3. Novelty Effect Confirmed

Task 03's improvement confirms the pattern from gemini-api-dev and wiki-agents-md: the skill helps when it provides genuinely novel knowledge (correct settings.json schema), but the benefit is offset by defects in the skill content (invalid JSON comments). A higher-quality skill — same schema knowledge without the template error — would likely show positive delta across all tasks.

## Remediation

If the skill author fixed the output template to use valid JSON (removing `//` comments, or using JSONC format explicitly), the degradation on tasks 01 and 04 would likely disappear. The skill would then potentially show the same positive-delta pattern as gemini-api-dev, since it provides genuinely novel Claude Code settings.json knowledge.
