# Proposed SKILL.md Template

This template is derived from empirical analysis of 673 agent skills scored by an LLM-as-judge across six quality dimensions (clarity, actionability, token efficiency, scope discipline, directive precision, novelty). It codifies the structural patterns that distinguish top-scoring skills from bottom-scoring ones.

See the companion paper for full methodology and findings:
[paper/paper.md](../paper/paper.md)

## Relationship to Existing Guidance

Anthropic provides three levels of skill authoring guidance:

1. **The official template** ([anthropics/skills/template/SKILL.md](https://github.com/anthropics/skills/tree/main/template/SKILL.md)) — three lines of scaffolding with no structural guidance.
2. **The skill-creator skill** ([anthropics/skills/skills/skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator)) — sound *principles* including context window efficiency, progressive disclosure, and novelty over repetition.
3. **The agentskills.io specification** ([agentskills.io/specification](https://agentskills.io/specification.md)) — structural requirements for directory layout, frontmatter fields, and file organization.

The skill-creator provides good advice on *what to prioritize* (conciseness, novelty, progressive disclosure) but does not prescribe *what structure to use* — it says "write instructions" without specifying which sections to include or in what order. This template fills that gap: it operationalizes Anthropic's principles into a concrete section architecture derived from empirical patterns in the highest-scoring skills.

### What this template adds beyond existing guidance

| Pattern | In Anthropic's Guidance? | Empirical Signal |
|---------|--------------------------|------------------|
| Tables as primary information vehicle | No — skill-creator is itself prose-heavy | 90% of top-20 skills vs. 40% of bottom-10 |
| Quick Reference section near top | No | 80% of top-20 vs. 0% of bottom-10 |
| Anti-patterns / negative guidance | No | 60% of top-20 vs. 0% of bottom-10 |
| "Out of Scope" negative scope gate | No | 50% of top-20 vs. 0% of bottom-10 |
| Troubleshooting section | No | Present in top skills, absent from bottom |
| Specific section architecture | No — no prescribed ordering | Convergent in top-scoring skills |
| 4:1 structured-to-prose ratio | No | Derived from top vs. bottom comparison |

### What this template validates from existing guidance

Several principles in this template echo guidance from Anthropic's skill-creator. Our data provides the first ecosystem-wide evidence for these recommendations — and quantifies how widely they are ignored:

- **Novelty over repetition**: The skill-creator says "only add context Claude doesn't already have." Our data: novelty is the weakest dimension ecosystem-wide (mean 3.52/5); community collections score just 3.19.
- **Context window efficiency**: The skill-creator calls the context window "a public good." Our data: 52% of all tokens ecosystem-wide are nonstandard files with no instructional value.
- **Progressive disclosure**: The skill-creator provides detailed patterns for splitting content into references. Our data: reference files outscore SKILL.md by +0.39 overall and +0.52 on token efficiency.
- **No extraneous files**: The skill-creator warns against README.md, CHANGELOG.md, etc. Our data: 185 skills (27.5%) contain nonstandard files, inflating mean token counts by 108%.

### A note on "When to Use" placement

The skill-creator explicitly advises that "when to use" information belongs in the frontmatter `description` field, not the body, because the body is only loaded after the skill triggers. This is correct for *triggering*. The "Scope" and "Out of Scope" sections in this template serve a different purpose: **scope discipline once the skill is activated**. The agent has already loaded the skill; these body sections help it decide whether to *apply* the skill's patterns to the current subtask, or recognize when the task is out of scope. We deliberately avoid naming these "When to Use" to prevent confusion with triggering semantics. Authors should include triggering information in the frontmatter description *and* scope guidance in the body — these are complementary, not redundant.

## Empirical Basis

We compared structural patterns in the top 20 skills (overall LLM score 5.00) against the bottom 10 (scores 1.83–2.33). Key contrasts:

| Structural Pattern | Top 20 | Bottom 10 |
|--------------------|--------|-----------|
| Markdown tables | 18/20 (90%) | 4/10 (40%) |
| Quick Reference section near top | 16/20 (80%) | 0/10 (0%) |
| Strong directives (MUST/ALWAYS/NEVER) | 15/20 (75%) | 2/10 (20%) |
| Copy-paste-ready code blocks | 17/20 (85%) | 3/10 (30%) |
| Anti-patterns / negative guidance | 12/20 (60%) | 0/10 (0%) |
| Explicit scope / out-of-scope sections | 10/20 (50%) | 0/10 (0%) |
| References section | 15/20 (75%) | 5/10 (50%) |
| Prose-heavy content | 1/20 (5%) | 6/10 (60%) |

Bottom-scoring skills fall into identifiable failure modes: stub/pointer files with no actionable content, hundreds of lines of installation scripts, over-broad scope without depth, vague philosophical prose, and self-promotional content.

## Template Design Principles

The seven structural principles encoded in this template. Principles 1, 3, 5, and 7 align with guidance from Anthropic's skill-creator; principles 2, 4, and 6 are new patterns identified by our analysis.

1. **Scope discipline.** Explicit scope and out-of-scope sections in the body prevent misapplication once a skill is activated. Top skills narrowly define their purpose and — critically — their boundaries. *(Complements the skill-creator's advice to put triggering information in the frontmatter description.)*

2. **Tables as the primary information vehicle.** Decision matrices, quick references, command cheatsheets, and option comparisons are rendered as tables. This makes skills parseable by agents without requiring sequential reading of prose. *(Not mentioned in existing guidance — the skill-creator's own content is prose-heavy.)*

3. **Progressive disclosure.** Keep SKILL.md concise (100–300 lines) and delegate detailed material to `references/`. Bottom skills either dump everything into SKILL.md or put nothing there. *(Aligns with the skill-creator's progressive disclosure patterns and the spec's recommendation to keep SKILL.md under 500 lines.)*

4. **Copy-paste-ready code blocks.** Complete, runnable examples that an agent can immediately use. Not illustrations, not pseudocode, not installation scripts. *(The skill-creator mentions examples but does not emphasize runnability or distinguish from pseudocode.)*

5. **Strategic directives.** Use MUST/ALWAYS/NEVER at high-consequence decision points — security boundaries, common failure modes, prerequisite checks. Not scattered throughout, and not as emphasis for routine instructions. *(Extends the skill-creator's advice to use "imperative/infinitive form" with data-driven specificity on when and where to use strong markers.)*

6. **Negative guidance.** Explicitly document what NOT to do and WHY (anti-patterns section). This is absent from every bottom-10 skill in our analysis. *(Not mentioned in existing guidance.)*

7. **Actionable content, not meta-content.** Every token should teach the agent how to accomplish a task. Installation scripts, self-promotion, and pointer-only stubs waste context window budget. *(Aligns with the skill-creator's emphasis on context window efficiency and novelty.)*

## Guidelines

- **Target 100–300 lines** for SKILL.md. Skills scoring 5/5 on token efficiency tend to be under 200 lines.
- **Include at least 2 tables** — quick reference and anti-patterns at minimum.
- **Include at least 1 copy-paste-ready code block** with real flags and parameters.
- **Write a rich frontmatter description** (50–200 words) that naturally incorporates relevant keywords in prose. The description is how agents decide whether to load your skill — the skill-creator correctly identifies this as the primary triggering mechanism. Describe what the skill does and when to use it; avoid bare keyword lists or explicit `Triggers: "term1", "term2"` patterns. The spec says descriptions "should include specific keywords that help agents identify relevant tasks" — but woven into prose, not as a separate list.
- **Use strong directives sparingly** and only at high-consequence decision points.
- **Favor structured content over prose** at roughly a 4:1 ratio (tables + lists + code vs. paragraphs).
- **Focus on novel content** — information the LLM doesn't already have from training data. As Anthropic's skill-creator advises: "only add context Claude doesn't already have." Our data shows this is the most-ignored principle in the ecosystem.
