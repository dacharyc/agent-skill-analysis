# Template Pattern Propagation: Documentation Quality and LLM Output

## Core Finding

When an LLM receives documentation containing syntactically incorrect patterns in code examples (e.g., `//` comments in JSON), it reproduces those patterns in its output with near-deterministic fidelity — even though the model demonstrably "knows" the syntax is invalid (baseline outputs are correct).

This has direct implications for documentation teams whose content is consumed by LLMs via skills, RAG, or copy-paste.

## Evidence: claude-settings-audit

### Quantitative Data

The claude-settings-audit skill's output template (SKILL.md line 264) contains `// ... grouped by category with comments` inside a JSON code block.

| Condition | Runs with `//` in JSON | Comment count per run | Notes |
|-----------|----------------------|----------------------|-------|
| Baseline (no skill) | **0/15** (0%) | 0 | Model knows JSON has no comments |
| With skill, tasks 01-04 | **12/12** (100%) | 7-30 | Perfect reproduction |
| Realistic, tasks 01-03 | **9/9** (100%) | 4-9 | Reduced count, not eliminated |
| Realistic, task 04 (grounded) | **0/3** (0%) | 0 | Concrete input JSON suppresses |
| Any condition, task 05 (different format) | **0/9** (0%) | 0 | Different output format not affected |

### Key Properties of the Effect

1. **Deterministic, not stochastic**: 0% baseline → 100% with-skill for matching formats. Not a tendency; a near-certain reproduction across 3 runs × 4 tasks.

2. **Overrides trained knowledge**: The model knows JSON doesn't support comments (proved by baseline). The template overrides this knowledge.

3. **Format-specific propagation**: The pattern propagates when the model produces the same type of output (settings.json → settings.json). It does NOT propagate to structurally different JSON files (task 05, .mcp.json).

4. **Mitigation hierarchy**:
   - Competing system instructions (CC preamble in realistic context): reduces comment count ~60% but doesn't eliminate
   - Concrete input code to transform (grounded context): fully suppresses
   - Different output format: fully suppresses

### Prevalence in the Skill Ecosystem

46 SKILL.md files across 9 unique skills contain `//` comments inside JSON code blocks. This is widespread, particularly in:
- **turborepo** (26+ instances) — extensive WRONG/CORRECT pattern examples with inline comments
- **docx-processing-lawvable** (14+ instances) — API examples with inline field explanations
- **pptx/xlsx processing skills** (multiple instances) — schema examples with field type comments
- **claude-settings-audit** (1 instance) — the template we evaluated

None of the other 8 skills with commented JSON are in our behavioral eval, so we cannot confirm the propagation effect generalizes across skills — but the mechanism is clear and the effect within claude-settings-audit is deterministic.

## Open Questions for Further Investigation

### 1. Placeholder Templates in JSON

MongoDB documentation uses placeholder syntax in JSON examples:

**Quoted placeholders (valid JSON):**
```json
{
  "analyzer": "<analyzer-for-index>",
  "mappings": {
    "fields": {
      "<string-field-name>": {
        "type": "string",
        "analyzer": "<analyzer-for-field>"
      }
    }
  }
}
```

**Unquoted placeholders (invalid JSON):**
```json
{
  "searchAnalyzer": "<analyzer-for-query>",
  "mappings": {
    "dynamic": <boolean>,
    "fields": { <field-definition> }
  }
}
```

Questions:
- Does the model reproduce `<boolean>` (unquoted) and `<field-definition>` (unquoted) as template placeholders in its output, or does it resolve them to actual values?
- When both quoted and unquoted placeholders appear in the same document, does the model learn the inconsistency?
- Unquoted `<boolean>` is technically valid template syntax in some contexts but invalid JSON — does this cause the same kind of "override trained knowledge" effect as `//` comments?
- Does the model produce invalid JSON with unquoted placeholders, or does it "fix" them to valid JSON while still using placeholder names?

### 2. Mislabeled Code Block Languages

MongoDB skill examples include:

**JavaScript labeled as `shell`:**
```shell
db.movies.createSearchIndex(
    "example-index",
    { mappings: { dynamic: true } }
)
```

**JavaScript objects labeled as `json`:**
```json
[
   {
      id: '648b4ad4d697b73bf9d2e5e0',
      name: 'default',
      status: 'READY',
      queryable: true,
      latestDefinition: { mappings: { dynamic: true } }
   }
]
```

The second example is particularly interesting: it uses unquoted keys (`id`, `name`, `status`) and single-quoted strings — JavaScript object literal syntax, not JSON. When labeled as `json`, this teaches the model that "JSON" includes JS object notation.

Questions:
- Does mislabeling cause the model to produce JavaScript object literals when asked for JSON? (e.g., unquoted keys, single-quoted strings)
- Does the `shell` label on JavaScript code affect the model's ability to identify the language when producing similar code?
- The PLC literature (Moumoula et al. 2025) identifies explicit language labels as the most effective contamination mitigation — does *incorrect* labeling have the opposite effect, actively teaching wrong associations?
- Is mislabeled code a contamination vector distinct from cross-language examples in the same document?

### 3. Context Size and Template Propagation

From the broader skill-size analysis (see `skill-size-vs-degradation.md`), we found the "internal dilution" hypothesis: large skills buffer against their own contaminating content. Does this apply to template propagation?

#### What We Found

**Within claude-settings-audit, token counts vs comment propagation:**

| Condition | Mean input tokens | Mean comments (tasks 01-04) | Comments as % reduction from with_skill |
|-----------|------------------|---------------------------|----------------------------------------|
| Baseline | 82 | 0 | N/A |
| With skill | 3,331 | 12.6 | — |
| Realistic | 3,616 (+285 over with_skill) | 5.5 | -56% |

The realistic condition adds only ~285 tokens (8.5% more context) but reduces comments by 56%. For the grounded task specifically, realistic context (same +285 tokens) produces 0 comments vs 7.7 for with_skill — full suppression.

**Comment density within JSON blocks (with_skill):**

| Task | Comment density range | Absolute comment count |
|------|---------------------|----------------------|
| 01 (direct_target) | 8.8-24.6% | 9-30 |
| 02 (cross_language) | 18.1-25.0% | 13-19 |
| 03 (similar_syntax) | 5.2-10.9% | 6-7 |
| 04 (grounded) | 7.4-9.1% | 7-8 |

Comment count does NOT scale proportionally with output length. Tasks 03-04 have 6-8 comments whether the output is 64 or 115 JSON lines. The model learns a discrete structural pattern ("add section header comments to JSON"), not a per-line behavior.

#### Interpretation

**Content type matters more than content volume for suppressing template propagation.** The 285-token CC preamble contains competing formatting instructions that reduce (but don't eliminate) the pattern. The concrete JSON input in the grounded task provides an anchoring code example that fully suppresses it.

Pure token volume — adding more context without adding competing instructions or anchoring code — is untested. From the broader internal dilution data, we know Q1 skills (1,527-3,249 tokens, including claude-settings-audit at 3,249) show worst mean B-A deltas (-0.112) while Q4 skills (6,403-48,192 tokens) show near-zero deltas (-0.022). But we cannot isolate template propagation from general contamination in that cross-skill comparison.

**Open question**: If a 48k-token skill contained one commented-JSON template line buried among 100 valid JSON examples, would the valid examples serve as implicit competing templates? This is plausible but unproven. The mechanism would be different from explicit competing instructions — the model would need to weight the many valid examples over the single invalid one rather than following an explicit instruction.

### 4. Interaction Effects

Multiple documentation quality issues may interact:
- Commented JSON + mislabeled code blocks + placeholder templates in the same document
- Does the model degrade gracefully (each issue independently affects output) or catastrophically (issues compound)?
- The claude-settings-audit data suggests the effect is additive: `//` comments are the primary issue, and Sentry-specific content bleed is a secondary independent issue

## Practical Recommendations (Preliminary)

Based on current evidence, for documentation teams whose content will be LLM-consumed:

1. **Move explanatory text outside code fences.** Instead of inline `//` comments in JSON, use surrounding prose, tables, or callout boxes. The model will reproduce patterns inside code fences with high fidelity.

2. **Ensure code block language labels are accurate.** Label JavaScript as `javascript` (or `js`), not `shell` or `json`. Mislabeling may teach wrong language associations.

3. **Use valid syntax in code examples.** If the code block is labeled `json`, ensure the content is valid JSON — no unquoted keys, no single-quoted strings, no `//` comments.

4. **Be consistent with placeholder notation.** If using template placeholders, choose a consistent format (e.g., always `"<placeholder>"` with quotes) rather than mixing quoted and unquoted forms.

5. **Consider output format context.** The propagation is strongest when the model's output format matches the template format. A commented JSON config example is more likely to contaminate config output than prose output.

These are preliminary — investigation items 1-4 above would strengthen or refine these recommendations.

## Prevalence Scan: Ecosystem-Wide Pattern Issues

### `//` Comments in JSON Blocks

Scanned all 673 SKILL.md files across 41 skill repositories. Found **46 instances across 9 unique skills**:

| Skill | Comment instances | Pattern |
|-------|-----------------|---------|
| turborepo | 26+ | WRONG/CORRECT examples with inline explanations |
| docx-processing-lawvable | 14+ | API response field explanations |
| pptx-processing-anthropic | 14+ | Schema field type annotations |
| xlsx/xlsx-processing-anthropic | 8+ | Validation result field explanations |
| claude-settings-audit | 1 | Output template section comment |
| expo-tailwind-setup | 1 | Package.json comment |
| claude-scientific-skills (multiple) | 4+ | Document processing field annotations |

**None of the other 8 skills (besides claude-settings-audit) are in the behavioral eval**, so we cannot confirm propagation generalizes. However, the turborepo skill (26+ instances of WRONG/CORRECT pattern comments) would be a particularly strong test case given the volume.

### Mislabeled Code Block Languages

Scanned for JSON blocks containing JavaScript object syntax (unquoted keys, single-quoted strings). Found **4 instances across 4 skills** — low prevalence in the current ecosystem. The MongoDB-style mislabeling described in the investigation questions is not well-represented in the current skill corpus.

Scanned for shell/bash blocks containing obvious JavaScript or Python syntax. Found **35 instances across ~15 skills**, but most are false positives (shell commands that invoke `node -e` or `python -c`, or tools like ImageMagick's `import` command). Genuine mislabeling is less common than the scan suggests.

### Unquoted Placeholders in JSON

Found only **2 instances** of unquoted placeholder templates in JSON blocks (in devcontainer-setup and docx-processing-lawvable). This pattern is rare in the current ecosystem but may be more common in documentation-derived skills (like the MongoDB Search example).
