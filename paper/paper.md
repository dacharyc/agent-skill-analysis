---
title: "Quality and Safety in the Agent Skills Ecosystem: A Structural, Content, and Cross-Contamination Analysis of 673 Skills"
author: "Dachary Carey"
date: "February 2026"
abstract: |
  Agent Skills — modular instruction sets that extend AI coding agents — are emerging as a key primitive in the developer toolchain. As adoption grows, quality standards have not kept pace. We present the first systematic analysis of the Agent Skills ecosystem, evaluating 673 skills from 41 source repositories across eight categories: platform publisher (Anthropic), company-published (Microsoft, OpenAI, Stripe, Cloudflare, and 18 others), community collections, individual community skills, security-focused (Trail of Bits, Prompt Security), development methodology (K-Dense/Superpowers), and vertical/domain-specific (legal, biotech, DevOps, embedded). We assess four dimensions: structural compliance with the agentskills.io specification, content quality metrics, cross-contamination risk — where mixed-language skill content may induce incorrect code generation in unrelated contexts — and context window efficiency. Our analysis finds that 22.0% of skills fail structural validation (including internal link integrity), with company-published skills (79.2% pass rate) performing worse than community collections (94.0%). We identify 10 skills with high cross-contamination risk, 66 skills with "hidden contamination" visible only in reference files, and demonstrate through a case study how multi-interface tool examples can degrade code generation. A token budget analysis reveals that 52% of all tokens across the ecosystem are nonstandard files (LICENSE texts, build artifacts, XML schemas) that waste context window space. The ecosystem extends well beyond our sample: we catalog over 80 additional repositories containing an estimated 800+ skills, suggesting these quality concerns are industry-wide. We propose quality criteria for skill authors and recommendations for specification maintainers.
bibliography: references.bib
---

# Introduction

The emergence of AI coding agents — tools like Claude Code, GitHub Copilot, and Cursor — has shifted software development toward human-AI collaboration. These agents operate in agentic loops: they read code, plan modifications, write implementations, and run tests, with the human developer providing guidance and oversight.

Agent Skills [@agentskills-spec] extend this model by allowing developers and organizations to package domain expertise as modular instruction sets. A skill is a structured directory — primarily a `SKILL.md` markdown file plus optional reference materials — that an agent loads into its context window to gain specialized knowledge. Skills cover domains from specific tools (Playwright, Docker) to development methodologies (test-driven development, code review).

The Agent Skills ecosystem has grown rapidly. As of February 2026, the agentskills.io specification is supported by over 27 agent platforms including Claude Code, GitHub Copilot, Cursor, Windsurf, OpenAI Codex, and Gemini CLI. Companies from Microsoft and OpenAI to Stripe and Cloudflare publish official skills for their platforms. Community contributors have built skills for security analysis (Trail of Bits), scientific computing (K-Dense), and development workflows (Superpowers). We catalog 673 skills from 41 source repositories in our primary analysis, with an additional 800+ skills identified across the broader ecosystem.

However, this growth has outpaced quality assurance. No prior work has systematically evaluated skill quality. We identified three concerns:

1. **Structural compliance**: Many skills deviate from the specification, potentially confusing agents about which files to load and how to use them.
2. **Content quality**: Skills vary enormously in how clearly and specifically they instruct agents, from highly structured step-by-step guides to vague advisory text.
3. **Cross-contamination risk**: Skills for multi-interface tools (databases, cloud services, container runtimes) may include examples in one language that interfere with the agent's code generation in another language — a concern supported by research on Programming Language Confusion [@moumoula2025plc], copy bias in in-context learning [@ali2024copybias], and the demonstrated susceptibility of LLMs to irrelevant context [@shi2023distracted].

This paper presents a systematic analysis across all three dimensions, using automated validation, content metrics, and cross-contamination detection. Our key contributions are:

- The first comprehensive structural audit of the Agent Skills ecosystem using the `skill-validator` tool [@skill-validator], covering 673 skills from 41 repositories, with a two-pass validation approach that separates deterministic structural checks from environment-dependent link validation
- Content quality metrics (information density, instruction specificity) applied at ecosystem scale
- Identification and taxonomy of cross-contamination risk in multi-interface skills, including the discovery of "hidden contamination" in reference files (66 skills with clean instruction files but contaminated references)
- A token budget composition analysis revealing that 52% of all tokens across the ecosystem are nonstandard files wasting context window space
- An ecosystem survey cataloging 1,400+ skills across 120+ repositories, contextualizing our findings as industry-wide
- Concrete recommendations for skill authors and specification maintainers

# Methodology

## Dataset

We collected 673 skills from 41 source repositories, organized into eight analytical categories:

| Category | Skills | Repos | Description |
|----------|--------|-------|-------------|
| Anthropic | 16 | 1 | Official skills from the spec authors |
| Company | 288 | 22 | Skills published by companies for their own APIs/products |
| Community collections | 167 | 3 | Multi-skill community repositories |
| Community individual | 9 | 6 | Single-skill community repositories |
| Trail of Bits | 52 | 1 | Security-focused vulnerability analysis skills |
| K-Dense (Superpowers) | 48 | 3 | Development workflow and methodology skills |
| Security | 7 | 1 | Security tooling skills (Prompt Security) |
| Vertical | 86 | 4 | Domain-specific: legal, biotech, DevOps, embedded |

The company category includes skills from Microsoft (143), OpenAI (32), Sentry (16), HashiCorp (13), WordPress (13), Cloudflare (9), Expo (9), Hugging Face (9), Vue.js (8), Google (7), Better Auth (6), Vercel (5), Callstack (4), Tinybird (3), Neon (3), Black Forest Labs (2), Stripe (2), and others.

Each source repository is tracked as a git submodule pinned to a specific commit, ensuring reproducibility. Snapshot metadata (commit SHA, date, remote URL) is recorded for every source.

Skills were validated using `skill-validator` v1.0 [@skill-validator], a Go CLI tool that checks skills against the agentskills.io specification [@agentskills-spec].

## Structural Validation

Each skill was evaluated against the specification's requirements:

- **Structure**: Presence of `SKILL.md`, correct directory layout, no unexpected files
- **Frontmatter**: Valid YAML frontmatter with required fields (name, description, version)
- **Content**: Markdown body completeness and formatting
- **Token budget**: Total context window usage

The validator produces a pass/fail result per skill along with categorized errors and warnings. We run the validator in two passes: first with structural checks only (`--only structure`), then with all other checks (`--skip structure`) for content analysis, contamination detection, and link validation. Link results are split into two categories: **internal links** (references to files within the skill directory, e.g. `references/api_guide.md`) are treated as structural failures since they indicate missing files, while **external links** (HTTP/HTTPS URLs) are reported separately as link health metadata. External URL validation is environment-dependent — URLs may be temporarily unreachable due to DNS failures, rate limiting, or transient outages — so excluding them from the pass/fail determination ensures reproducible structural compliance results across runs.

## Content Analysis

We developed two automated content metrics:

**Information density** measures the proportion of a skill's content that consists of actionable material (code blocks and imperative sentences) versus prose. It is computed as:

$$\text{density} = 0.5 \times \frac{\text{code block words}}{\text{total words}} + 0.5 \times \frac{\text{imperative sentences}}{\text{total sentences}}$$

**Instruction specificity** measures the strength of a skill's language, based on the ratio of strong directive markers ("must", "always", "never", "ensure") to weak advisory markers ("may", "consider", "could", "possibly"):

$$\text{specificity} = \frac{\text{strong markers}}{\text{strong markers} + \text{weak markers}}$$

## Cross-Contamination Detection

Cross-contamination occurs when a skill designed for one context leaks information that influences agent behavior in another context. Research has established that code LLMs exhibit "Programming Language Confusion" — systematically generating code in unintended languages despite explicit instructions, with strong defaults toward Python and shifts between syntactically similar language pairs [@moumoula2025plc]. LLMs also exhibit a "copy bias" where they replicate patterns from in-context examples rather than reasoning independently about the task [@ali2024copybias], and in-context code examples have been shown to bias the style and characteristics of generated code [@li2023lail]. These findings suggest that mixed-language code examples in skill files could induce cross-language interference.

We developed a detection heuristic to estimate cross-contamination risk based on three structural factors:

1. **Multi-interface tool detection**: Does the skill reference a tool known to have multiple language SDKs (e.g., MongoDB, AWS, Docker)?
2. **Language mismatch**: Do code block languages differ from the skill's primary language category? Mismatches are weighted by syntactic similarity: mixing application languages (e.g., Python and JavaScript) carries higher weight than mixing an application language with auxiliary languages (shell, config, markup), reflecting research showing that Programming Language Confusion occurs primarily between syntactically similar language pairs [@moumoula2025plc].
3. **Scope breadth**: How many distinct technology categories does the skill reference?

These factors combine into a risk score from 0 to 1, classified as low (< 0.2), medium (0.2–0.5), or high (≥ 0.5). This score measures the *structural* potential for cross-contamination based on the presence of mixed-language content, not the measured behavioral impact on agent output — validating the behavioral effect is an important direction for future work (see Limitations).

An important distinction underlies the scoring: the research literature supports two different mechanisms by which multi-language content can degrade code generation, with different risk profiles:

- **Language confusion** — the model generates code using patterns from the wrong language. Research shows this primarily affects syntactically similar language pairs (C#/Java, JavaScript/TypeScript) and is driven by syntactic overlap in training data [@moumoula2025plc]. Skills mixing multiple application-language SDKs (e.g., Python and JavaScript examples for the same API) carry the highest risk.
- **Context dilution** — additional content of any type consumes context window budget and reduces the model's attention to the user's actual task [@tian2024spa; @hong2025contextrot]. This affects all multi-language content equally, regardless of syntactic similarity, and is addressed separately in our token budget analysis.

Many skills in our dataset mix an application language with bash scripts, YAML configuration, or SQL queries — a common and often necessary pattern for infrastructure and DevOps skills. Our scoring weights these auxiliary-language mismatches lower than application-to-application mismatches, since the syntactic dissimilarity between (for example) bash and Python makes language confusion less likely than between Python and JavaScript.

# Findings

## Structural Compliance

Of 673 skills evaluated, **525 (78.0%) passed** structural validation and **148 (22.0%) failed**. Structural validation includes internal link integrity (references to files within the skill directory) but excludes external URL checks, which are environment-dependent and reported separately (see Methodology).

![Pass/fail rates by source](figures/pass_fail_by_source.png)

Pass rates varied dramatically by source category:

| Category | Skills | Pass Rate | Errors | Warnings |
|----------|--------|-----------|--------|----------|
| Community collections | 167 | 94.0% | 30 | 209 |
| Anthropic | 16 | 87.5% | 7 | 39 |
| Trail of Bits | 52 | 86.5% | 15 | 73 |
| Company | 288 | 79.2% | 96 | 539 |
| Vertical | 86 | 66.3% | 41 | 154 |
| Community individual | 9 | 55.6% | 7 | 68 |
| K-Dense | 48 | 37.5% | 62 | 116 |
| Security | 7 | 14.3% | 6 | 23 |

Community collections lead at 94.0%, followed by Anthropic (87.5%) and Trail of Bits (86.5%). **Company-published skills have a lower pass rate (79.2%) than community collections (94.0%)**, inverting the common assumption that official company skills would be higher quality. The primary drivers:

- **Microsoft** (143 skills): Many skills use non-standard directory structures, placing skills under `.github/skills/` rather than the spec-standard layout. While functional within their GitHub Copilot integration, they generate structural validation errors.
- **Several companies** published skills before the spec was finalized and have not updated them to current requirements.

The K-Dense (Superpowers) skills had a low pass rate (37.5%), primarily because they use an alternative directory structure optimized for their development workflow rather than the agentskills.io specification.

Common errors across all sources included:
- Missing or malformed YAML frontmatter
- Unexpected files at the skill root (should be in `references/` or `assets/`)
- Missing required frontmatter fields

### Token Usage

Token counts varied by several orders of magnitude:

![Token count distribution](figures/token_distribution.png)

- Minimum: 0 tokens (empty skill placeholders)
- Maximum: 3,098,484 tokens (a scientific computing skill with large reference datasets)
- Median: 5,236 tokens
- Mean: 16,711 tokens

Company-published skills tend to be more concise (average 6,790 tokens) than community collections (22,900 tokens). The most focused skills — from Anthropic (8,189 avg) and K-Dense (3,592 avg) — demonstrate that effective skills can be compact.

### Token Budget Composition

Breaking total token counts into their constituent parts — SKILL.md body, reference files, asset files, and nonstandard files — reveals a striking pattern: **52% of all tokens across the ecosystem are nonstandard files** that fall outside the specification's defined structure.

![Token budget composition by source](figures/token_budget_composition.png)

The agentskills.io specification defines three categories of skill content: the primary `SKILL.md` instruction file, supplementary `references/` files, and binary `assets/` files. Any file outside these categories (placed at the skill root or in non-standard directories) is loaded into the agent's context window but provides no instructional value — and research demonstrates that irrelevant context actively degrades LLM task performance [@shi2023distracted; @liu2024lost]. We term these **nonstandard tokens**.

| Category | SKILL.md | References | Assets | Nonstandard |
|----------|----------|------------|--------|-------------|
| Community collections | 15.2% | 54.1% | 6.8% | 23.9% |
| Community individual | 0.9% | 2.6% | 0.1% | 96.4% |
| Company | 23.5% | 46.9% | 0.6% | 29.1% |
| Vertical | 10.8% | 26.0% | 3.2% | 60.0% |
| Trail of Bits | 32.6% | 31.1% | 0.0% | 36.3% |
| K-Dense | 37.0% | 0.0% | 0.0% | 63.0% |
| Anthropic | 24.4% | 0.4% | 0.0% | 75.1% |
| Security | 11.4% | 0.0% | 0.0% | 88.6% |
| **Overall** | **13.1%** | **32.1%** | **2.9%** | **52.0%** |

Of 673 skills, 185 (27.5%) contain nonstandard files. The impact is substantial: the mean token count is inflated 108% by nonstandard files (mean effective tokens = 8,027 vs. mean total = 16,711). Even at the median, nonstandard files add 41% overhead.

![Breakdown of nonstandard token waste](figures/nonstandard_breakdown.png)

Analyzing the 5.8 million nonstandard tokens reveals several distinct categories of waste:

- **OOXML schemas** (1.3M tokens, 22.4%): Four document-processing skills (docx, pptx, and their Anthropic variants) ship raw ISO-IEC 29500-4 XML Schema Definition files. A single schema file (`sml.xsd`, the SpreadsheetML schema) consumes 298,868 tokens — larger than most entire skills.
- **Benchmarks and results** (1.3M tokens, 22.4%): One skill (loki-mode) includes SWE-bench evaluation results and prediction logs, consuming over 500k tokens of JSON benchmark data.
- **Build artifacts** (434k tokens, 7.4%): Source maps (`.js.map`), lockfiles (`package-lock.json`), and compiled presentations (`.pptx`) that are development artifacts, not instructional content.
- **LICENSE files** (274k tokens, 4.7%): 89 skills include LICENSE.txt files at the skill root. While legally appropriate, each consumes ~2,700 tokens of context window space that provides no value to the agent.
- **UI/extension code** (415k tokens, 7.1%): VS Code extension source code and dashboard HTML/JavaScript shipped alongside skills.

The practical consequence is significant. An agent loading one of these skills receives a context window filled with XML schemas, benchmark JSON, or license text instead of the user's code. Research on LLM agent trajectories has shown that 40–60% of input tokens in agentic systems can be classified as useless, redundant, or expired information that is safely removable without performance loss [@xiao2025agentdiet]. For the 82 skills where SKILL.md represents less than 10% of total tokens, the instruction file risks being drowned out by supplementary material — consistent with findings that LLM performance degrades when relevant information is surrounded by irrelevant context [@liu2024lost; @shi2023distracted].

Notably, even Anthropic's own skills — the reference implementation from the spec authors — have the highest percentage of nonstandard tokens (75.1%) of any source category, driven primarily by LICENSE.txt files and template directories. This suggests the problem is structural rather than a matter of author diligence: the specification does not currently warn against or penalize nonstandard files, so authors have no signal that these files consume context window budget.

## Content Quality

![Information density vs. instruction specificity](figures/content_quality.png)

Content quality metrics revealed significant variation:

- **Information density**: Mean 0.206 (range 0.0–0.56). Most skills are prose-heavy with relatively few code examples or imperative instructions.
- **Instruction specificity**: Mean 0.616 (range 0.0–1.0). The expanded dataset shows a lower average specificity than our initial sample, driven by company skills that use more advisory language.

Anthropic skills cluster in the moderate-density, high-specificity quadrant — they are well-structured with clear directives but are not code-heavy. Company skills show the broadest distribution, ranging from highly specific API reference skills to vague best-practices guides.

## Cross-Contamination Risk

![Validation and contamination overview](figures/contamination_distribution.png)

Our cross-contamination analysis identified:

- **10 high-risk skills** (1.5%) — significant structural potential for cross-language interference, driven primarily by application-to-application language mixing
- **147 medium-risk skills** (21.8%) — some multi-language or multi-technology mixing
- **516 low-risk skills** (76.7%) — focused on a single technology or language

![Contamination scores by source](figures/contamination_by_source.png)

The security category had the highest average risk score (0.344), followed by Trail of Bits (0.151) and company-published skills (0.127). Security tools inherently operate across multiple languages and environments, making this expected. Company skills — particularly those for cloud platforms (Azure, AWS, Terraform) — scored higher because they often cover multiple language SDKs within a single skill.

### High-Risk Skills

The 10 high-risk skills cluster around two primary patterns, with the similarity-weighted scoring concentrating high-risk flags on skills with genuine application-to-application language mixing:

1. **Multi-SDK platform skills** (highest language confusion risk): Azure, AWS, and Terraform skills that cover multiple application language bindings (Python, Java, TypeScript, .NET, Rust) within one skill. These represent the strongest contamination concern because they mix syntactically similar languages for the same API — exactly the pattern that Programming Language Confusion research identifies as most problematic [@moumoula2025plc].
2. **Infrastructure-as-code skills** (moderate risk): Skills mixing shell commands, configuration languages (HCL, YAML), and application code. The language confusion risk here is lower due to syntactic dissimilarity between auxiliary and application languages, though context dilution remains a concern.
3. **Security analysis skills** (mixed risk): Tools that inherently operate across language boundaries, combining both application-to-application mixing (higher risk) and application-to-auxiliary mixing (lower risk).

Key examples:
- **upgrade-stripe** (Stripe, risk: 0.93): Covers SDK upgrades across multiple application languages (Python, Ruby, JavaScript) with mixed code examples — the highest-risk pattern, as examples for the same Stripe API in multiple syntactically similar languages create direct confusion potential
- **copilot-sdk** (Microsoft, risk: 0.63): Multi-SDK skill mixing application languages with shared API patterns
- **provider-resources** (HashiCorp, risk: 0.55): Terraform provider development mixing Go with HCL and shell — the Go application code mixed with infrastructure references drives the score, while the HCL/shell auxiliary mixing is appropriately down-weighted
- **ossfuzz** (Trail of Bits, risk: 0.53): Combines Docker, shell, Python, and C/C++ for fuzz testing — the Python/C++ application language mixing is the primary risk factor

Notably, **monitoring-observability** (DevOps vertical) — previously scored as high-risk (0.72) under uniform weighting — now scores as medium (0.50) because its multi-language content is primarily bash, YAML, and configuration alongside infrastructure tool references, not application-to-application language mixing. This reclassification better reflects the actual language confusion risk.

### Case Study: MongoDB Cross-Contamination

During development of this analysis, we observed an illustrative case of cross-contamination: a MongoDB skill containing `mongosh` (shell) examples caused Claude Code to generate incorrect Node.js driver code. The agent produced queries using shell syntax (`db.collection.find({})`) instead of the Node.js driver API (`collection.find({})`), and it embedded shell-specific operators in JavaScript contexts.

This is consistent with documented LLM behaviors: code LLMs exhibit Programming Language Confusion, systematically defaulting to patterns from syntactically similar languages [@moumoula2025plc], and in-context examples bias the style of generated code toward reproducing the patterns present in the examples [@li2023lail]. The MongoDB case is particularly illustrative because the shell examples are syntactically valid JavaScript (MongoDB's shell is JavaScript-based), making the interference subtle — the generated code *looks* correct but uses the wrong API for a Node.js application. Research on attention dilution in code generation further suggests that as skill file content grows, the model pays less attention to the user's actual intent [@tian2024spa].

While this case study is a single observation rather than a controlled experiment, it illustrates a pattern that the research literature predicts: irrelevant context with high surface-level similarity to the target task is especially likely to degrade LLM output [@shi2023distracted; @jain2024apidoc].

### Illustrative Example: Gemini API Multi-Language Skill

The **gemini-api-dev** skill (Google, risk: 0.55) provides a concrete illustration of the API shape differences that make cross-contamination particularly insidious. The skill demonstrates a single operation — `generateContent` — in four languages, each with a subtly different API shape:

**Python** — keyword arguments, snake_case method:
```python
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Explain quantum computing"
)
print(response.text)
```

**JavaScript** — options object, camelCase method:
```javascript
const response = await ai.models.generateContent({
  model: "gemini-3-flash-preview",
  contents: "Explain quantum computing"
});
console.log(response.text);
```

**Go** — positional parameters, PascalCase method, explicit context:
```go
resp, err := client.Models.GenerateContent(ctx,
    "gemini-3-flash-preview",
    genai.Text("Explain quantum computing"), nil)
```

**Java** — positional parameters, camelCase method, null config:
```java
GenerateContentResponse response =
    client.models.generateContent(
        "gemini-3-flash-preview",
        "Explain quantum computing",
        null);
System.out.println(response.text());
```

The differences are subtle but consequential: Python uses keyword arguments while Java uses positional parameters; Go wraps content in `genai.Text()` while others pass raw strings; Java accesses the result via a method call (`response.text()`) while Python and JavaScript use a property (`response.text`). An agent working on a Python project but primed with the JavaScript or Go patterns from this skill might generate code using positional arguments, or omit the keyword parameter names — code that would fail at runtime. This is exactly the kind of syntactically plausible but semantically incorrect output that Programming Language Confusion research predicts for syntactically similar languages sharing the same API surface [@moumoula2025plc].

## Company vs. Community: Quality Comparison

A key question motivating this expanded analysis was whether company-published skills demonstrate higher quality than community contributions. The answer is nuanced:

| Dimension | Company (288) | Community Collections (167) | Anthropic (16) |
|-----------|--------------|---------------------------|----------------|
| Pass rate | 79.2% | 94.0% | 87.5% |
| Avg tokens | 6,790 | 22,900 | 8,189 |
| Avg info density | 0.266 | 0.174 | 0.148 |
| Avg specificity | 0.585 | 0.579 | 0.725 |
| Avg contamination score | 0.127 | 0.091 | 0.078 |

Companies produce more **informationally dense** skills (higher code-to-prose ratio) but score lower on **structural compliance** (79.2% vs 94.0% for community collections) and **instruction specificity**. This suggests companies prioritize API reference content over the instructional framing that helps agents use the information effectively.

Anthropic's own skills, while small in number, set a benchmark for instruction specificity (0.725) — their skills use strong directive language that leaves less room for agent misinterpretation. Community collections fall between company and Anthropic skills on most dimensions.

## Metric Correlations

![Correlation between key metrics](figures/metrics_correlation.png)

Notable correlations:
- Token count shows weak positive correlation with error count, suggesting larger skills tend to have more structural issues
- Information density and code block ratio are strongly correlated (by construction)
- Risk score correlates with warnings, as structurally complex skills tend to have broader technology scopes

## Reference File Analysis

Beyond the primary `SKILL.md` file, the agentskills.io specification allows skills to include reference files — supplementary documents placed in a `references/` directory. These files provide additional context (API documentation, code examples, configuration templates) that agents load alongside the skill instructions. Our analysis reveals that reference files represent a significant and underexamined dimension of skill quality.

### Prevalence and Scale

Of 673 skills analyzed, **412 (61%) include reference files**, totaling 1,877 files across the dataset. Reference file usage varies by source: company-published skills and community collections are the heaviest users, while methodology-focused skills (K-Dense) and security skills rarely include references.

### Token Budget Impact

Reference files have a dramatic impact on context window consumption. Among skills with references:

- **81% have more reference tokens than SKILL.md tokens** — the references outweigh the primary instruction file
- The median reference token count is 4,729, but the distribution has a heavy tail: p99 reaches 44k tokens
- **4 skills have reference totals exceeding 50,000 tokens**, prime candidates for context window degradation — controlled experiments show 13.9–85% performance loss as input length increases, even when models can perfectly retrieve all evidence [@du2025context]
- Extreme outliers exist: vueuse-functions (153k reference tokens, 18x the SKILL.md) and security-best-practices (91k reference tokens, 57x the SKILL.md)

![Reference file size relative to SKILL.md](figures/ref_token_ratio.png)

These findings have practical implications. Agent platforms typically operate within context windows of 100k–200k tokens, though research suggests that effective context lengths are often less than half the advertised training length due to undertrained positional encodings [@an2025effective]. A single oversized reference file can consume a significant fraction of this budget, potentially crowding out the user's code context and degrading agent performance — an effect documented across 18 state-of-the-art models, where performance degrades non-uniformly as context grows [@hong2025contextrot; @yoran2024robust]. Skill authors should be mindful that reference files are not "free" — they compete directly with the user's code for context window space [@salim2026tokenomics].

### Content Quality

Reference files tend to have **higher information density** than their corresponding SKILL.md files. This is expected: references are typically code-heavy (API examples, configuration templates, type definitions) rather than prose-heavy instruction documents. The higher density reflects their role as reference material rather than instructional content.

### Contamination Risk and Hidden Contamination

Reference files introduce a distinct contamination vector. Because references often contain code examples for specific language SDKs, they may interfere with the agent's code generation when the user is working in a different language — a concern grounded in research showing that in-context code examples bias generated output toward the patterns present in those examples [@li2023lail; @ali2024copybias]. Our analysis found that reference contamination patterns differ from SKILL.md contamination:

- Reference files are more likely to contain **multiple programming languages** within a single skill, especially for platform SDK skills that provide examples across Python, TypeScript, Java, and .NET
- Skills with contaminated reference files sometimes have clean SKILL.md files — the contamination is hidden in the supplementary material

Among the 412 skills with reference files, contamination scores diverge between the SKILL.md and references in the majority of cases:

- **32.3%** have higher contamination in references than in SKILL.md
- **66.3%** have higher contamination in SKILL.md than in references
- **1.5%** have equal scores

The most concerning pattern is what we term **hidden contamination**: skills where the SKILL.md file scores as low-risk but the reference files carry medium or high contamination. We identified **66 skills** (16.0% of skills with references) exhibiting hidden contamination — 12 with high-risk references and 54 with medium-risk references.

![Hidden contamination: clean SKILL.md with contaminated references](figures/hidden_contamination.png)

Community collections account for the majority of hidden contamination cases (31 of 66), which is expected given their heavy reliance on reference files (88% adoption rate, averaging 6.9 files per skill). Company-published skills contribute 23 cases, and vertical/domain-specific skills contribute 6.

Illustrative examples of hidden contamination:

- **neon-postgres** (company): SKILL.md contamination 0.00 (low), reference contamination 0.83 (high). The SKILL.md provides clean PostgreSQL-focused instructions, but reference files include examples spanning JavaScript, Python, CSS, TSX, and Bash — with the JavaScript/Python application-language mixing driving the high reference score.
- **react-native-best-practices** (company): SKILL.md contamination 0.07 (low), reference contamination 1.0 (high). Reference files contain code in 14 different languages including Kotlin, Swift, Objective-C, Groovy, and C++ — a mix of application and mobile language categories that produces the maximum contamination score.
- **alphafold-database** (community collection): SKILL.md contamination 0.03 (low), reference contamination 0.21 (medium). Reference files mix Python with Bash and configuration languages for the protein structure prediction pipeline — the similarity-weighted scoring appropriately reduces this from high to medium, as the Python/bash mixing is primarily an auxiliary mismatch.
- **clinical-decision-support** (community collection): SKILL.md contamination 0.00 (low), reference contamination 0.41 (medium). A perfectly clean instruction file is paired with references containing mixed-language code examples.

Hidden contamination has important implications for quality assessment. **Any contamination analysis that examines only the SKILL.md file will miss 66 cases** — a 30% undercount relative to the 223 total skills with medium or high contamination across either their SKILL.md or references. Skill validation tools and quality gates should evaluate reference files alongside the primary instruction file.

### Language Distribution

![Most common languages in reference files](figures/ref_language_distribution.png)

The language distribution across reference files reveals how authors use references in practice. The most common languages reflect the ecosystem's emphasis on web development and cloud platform integration. Shell scripts, configuration languages (YAML, HCL, TOML), and type definition files appear frequently, confirming that references serve as practical implementation guides rather than conceptual documentation.

# Recommendations for Skill Authors

Based on our findings, we recommend the following practices:

1. **Validate before publishing**: Run `skill-validator` on your skill and fix all errors. Currently, 22.0% of published skills fail structural validation — including 21% of company-published skills.

2. **Scope skills tightly**: Skills covering multi-interface tools should target a specific language SDK. A "MongoDB for Node.js" skill is safer than a generic "MongoDB" skill. Research shows code LLMs systematically confuse syntactically similar languages [@moumoula2025plc] and copy patterns from in-context examples [@ali2024copybias], and we identified 10 high-risk skills where broad scope creates the structural conditions for this interference.

3. **Label code blocks explicitly**: Always specify the language in fenced code blocks (` ```javascript ` rather than ` ``` `). This helps agents disambiguate code contexts.

4. **Use strong directive language**: Skills with higher instruction specificity (using "must", "always", "never") provide clearer guidance to agents. Company skills in particular tend toward advisory language ("consider", "might") where directive language would be more effective.

5. **Minimize token usage**: Keep skills focused. The median effective skill uses ~5,200 tokens. Skills exceeding 50,000 tokens likely include material that should be external references.

6. **Separate language-specific examples**: If a skill must cover multiple languages, use clearly delineated sections with explicit context-switching markers. Consider publishing separate skills per language SDK.

7. **Audit nonstandard files**: Check that your skill directory contains only `SKILL.md`, `references/`, and `assets/`. Nonstandard files (LICENSE.txt, README.md, build artifacts, schemas) consume context window budget without providing instructional value. We found 52% of all tokens ecosystem-wide are nonstandard. Move license text to a reference or remove it; relocate build artifacts and schemas outside the skill directory.

8. **Validate reference files for contamination**: A clean SKILL.md does not guarantee a clean skill. We identified 66 skills with hidden contamination in reference files. Run contamination analysis on the full skill directory, not just the instruction file.

# Recommendations for Spec Maintainers

1. **Add a `languages` frontmatter field**: Skills should explicitly declare which programming languages they target. This enables agents to filter skills by context and would help mitigate cross-contamination.

2. **Define quality tiers**: Introduce a quality score based on structural compliance, content metrics, and contamination risk. Published skill registries could use these tiers for ranking.

3. **Require code block language annotations**: Make unlabeled code blocks a validation error, not just a warning. Research shows that explicit language keywords provide the most effective mitigation for Programming Language Confusion in code LLMs [@moumoula2025plc], making language annotations a low-cost safeguard against cross-contamination.

4. **Provide multi-language skill guidelines**: Publish guidance for skills that necessarily cover multiple languages (CI/CD, infrastructure, cross-platform tools). With 10 high-risk and 147 medium-risk skills in our sample, this is an important need.

5. **Add contamination risk assessment**: Include cross-contamination detection in the specification's recommended validation pipeline. Critically, this assessment should cover reference files as well as SKILL.md — our analysis found 66 cases of hidden contamination visible only in references.

6. **Engage company publishers**: Company-published skills have a lower structural compliance rate (79.2%) than community collections (94.0%). Given their high visibility and adoption, bringing these into compliance would significantly improve ecosystem quality.

7. **Warn on or penalize nonstandard files**: The specification should explicitly warn against files outside the defined structure (`SKILL.md`, `references/`, `assets/`). Currently, 52% of all tokens in the ecosystem come from nonstandard files. A validation warning or error for unexpected root-level files would significantly reduce context window waste. At minimum, agent platforms should consider filtering out nonstandard files when loading skills.

8. **Set token budget guidelines**: Provide recommended maximum token counts for SKILL.md, individual reference files, and total skill size. Our analysis shows that the median effective skill is ~4,000 tokens, yet 17 skills exceed 50% of a 128k context window. Guidelines would help authors understand the practical limits of context window consumption.

# Limitations and Future Work

**Limitations:**

- Our content metrics (information density, instruction specificity) are heuristic and may not capture all aspects of skill quality
- Cross-contamination risk scoring measures structural indicators (multi-language content, multi-interface tools, scope breadth) using keyword matching rather than semantic analysis. While research on Programming Language Confusion [@moumoula2025plc], copy bias [@ali2024copybias], and irrelevant context effects [@shi2023distracted] provides a strong theoretical basis for the risk, we have not conducted controlled experiments to measure the actual behavioral impact of specific skills on agent code generation. Our risk scores should be interpreted as indicators of structural potential for interference, not as measured effect sizes
- The scoring weights mismatches by language type (application-to-application vs. application-to-auxiliary), but the specific weights (1.0, 0.25, 0.1) are informed by the research direction rather than empirically calibrated. The PLC research [@moumoula2025plc] establishes that syntactically similar languages cause more confusion, but does not quantify the exact risk ratio between, for example, Python/JavaScript confusion and Python/bash confusion. Future work could calibrate these weights through behavioral experiments
- We analyze the skill text only, not the actual agent behavior when using skills — behavioral validation is the most important direction for future work
- The dataset represents a point-in-time snapshot; the ecosystem evolves rapidly
- Some skill name collisions occur across sources within the same category

**Future work:**

- **Behavioral testing**: Measure actual agent code generation quality with and without high-risk skills across domains, to validate whether our structural risk scores predict real performance degradation. Controlled experiments comparing code correctness with and without mixed-language skill content would establish the causal link that our structural analysis and the existing literature [@moumoula2025plc; @shi2023distracted; @ali2024copybias] predict but that has not been directly tested in the skill file context. Of particular interest is comparing the effect of application-to-application language mixing (e.g., Python + JavaScript for the same API) against application-to-auxiliary mixing (e.g., Python + bash + YAML) to calibrate the similarity weights in our risk scoring
- **LLM-as-judge quality scoring**: Use Claude to evaluate skill quality on dimensions including clarity, actionability, token efficiency, scope discipline, directive precision, and novelty (infrastructure built, awaiting execution)
- **Longitudinal analysis**: Track skill quality trends as the ecosystem matures and companies update their skills
- **Skill composition analysis**: Study how multiple active skills interact and potentially conflict
- **Expanded coverage**: Our ecosystem survey (Appendix A) identifies 800+ additional skills; analyzing the full set would strengthen statistical power

# Conclusion

The Agent Skills ecosystem is young and growing rapidly. Our analysis of 673 skills from 41 repositories reveals meaningful variation in structural compliance (78.0% pass rate), content quality, cross-contamination risk (10 high-risk skills), and context window efficiency (52% token waste). Company-published skills — from Microsoft, OpenAI, Stripe, and others — have a *lower* structural compliance rate (79.2%) than community collections (94.0%), inverting the assumption that official sources produce higher-quality skills.

Two findings stand out as particularly actionable. First, the context window waste problem: over half of all tokens loaded from skills are nonstandard files — LICENSE texts, build artifacts, XML schemas, benchmark data — that provide no instructional value to the agent. This is both the largest quality issue by magnitude and the easiest to fix. Second, hidden contamination in reference files: 66 skills appear clean when only the SKILL.md is analyzed but carry medium or high contamination risk in their reference files, meaning contamination assessments that ignore references undercount risk by 30%.

The cross-contamination risk is grounded in established LLM behaviors: Programming Language Confusion causes code LLMs to systematically generate code in unintended languages [@moumoula2025plc], in-context examples bias generated code toward the patterns they contain [@li2023lail; @ali2024copybias], and irrelevant context actively degrades LLM reasoning [@shi2023distracted]. Our MongoDB case study illustrates how these effects manifest in practice, and our structural analysis identifies 1.5% of skills at high risk and 21.8% at medium risk for triggering them. With the ecosystem growing rapidly (we estimate 1,400+ skills exist across 120+ repositories), systematic behavioral validation of these risk scores is an important next step.

Quality standards, validation tooling, and authoring guidelines can address these issues. As skills become a core part of the AI development workflow, the community benefits from treating them as first-class software artifacts deserving of the same quality discipline we apply to libraries and APIs.

\newpage

# Appendix A: Ecosystem Survey {.unnumbered}

Beyond the 673 skills we analyzed in depth, we conducted a broad survey of the Agent Skills ecosystem to estimate the total scope and identify patterns in adoption. This appendix documents our findings.

## Scale of the Ecosystem

As of February 2026, we identified **120+ repositories** containing Agent Skills, with an estimated **1,400+ individual skills** across the ecosystem. The agentskills.io specification is supported by **27+ agent platforms**.

Our analyzed sample of 673 skills represents approximately 48% of the estimated total. The quality patterns we observe — particularly the 22.0% structural failure rate and 1.5% high contamination risk — likely extend to the broader ecosystem.

## Adoption by Category

**Platform publishers** (3 repos, ~50 skills): Anthropic (16 skills), OpenAI (32 skills for Codex), Vercel (5 skills). These serve as reference implementations.

**Company-published** (22+ repos, ~300+ skills): The largest segment. Microsoft alone publishes 143 skills covering Azure SDKs across five languages. Other major publishers include Sentry (16), HashiCorp (13), WordPress (13), Expo (9), Hugging Face (9), Cloudflare (9), and Vue.js (8). Companies publish skills to reduce integration friction for developers using their products.

**Community collections** (10+ repos, ~400+ skills): Multi-skill repositories from community maintainers. K-Dense-AI publishes 145+ scientific computing skills. Anthony Fu maintains 17 skills for the Vue/Nuxt/Vite ecosystem. Obsidian's CEO publishes 5 skills for the knowledge management tool. The K-Dense/Superpowers family covers development methodology.

**Individual community skills** (60+ repos, ~100+ skills): Single-purpose skills covering niche use cases: D3.js visualization, Playwright testing, ffuf security scanning, Home Assistant automation, video editing, and more.

**Security-focused** (5+ repos, ~65+ skills): Trail of Bits (52+ skills) dominates this space with vulnerability scanning, fuzzing, and audit skills. Prompt Security (7 skills) and Cisco AI Defense provide security scanning skills. Snyk publishes an agent security scanner.

**Vertical/domain-specific** (10+ repos, ~100+ skills):

- *Legal* (lawvable): 38 skills for contract review, compliance, and legal document drafting
- *Biotech* (Adaptyv Bio): 21 skills for protein design, AlphaFold, and computational biology
- *Embedded/IoT* (Zephyr): 21 skills for RTOS development, BLE, and board bringup
- *DevOps*: 6 skills for Terraform, Kubernetes, CI/CD, and monitoring
- *Business strategy* (wondelai): 25 skills covering Blue Ocean Strategy, Design Sprint, and similar frameworks

## Ecosystem Infrastructure

Several supporting tools have emerged:

- **skills.sh**: Web registry with 58,000+ installations, providing search and discovery
- **Vercel `npx skills` CLI**: One-command installation of skills from any GitHub repository
- **SkillsMP**: Marketplace with quality indicators and category filtering
- **skill-validator** [@skill-validator]: Structural validation tool (used in this analysis)
- **Cisco AI Defense skill-scanner**: Security scanner for detecting malicious skill patterns
- **Snyk agent-scan**: Security scanner for AI agents and skills

## Implications for Our Findings

If the quality patterns we observe in our 673-skill sample hold across the full 1,400+ skill ecosystem:

- **~308 skills** may fail structural validation
- **~21 skills** may have structural indicators of high cross-contamination risk
- **~305 skills** may have structural indicators of medium contamination risk

These estimates underscore the urgency of quality standards and validation tooling. The ecosystem has reached a scale where manual review is impractical — automated quality gates are necessary.

## Source Repositories Not Included in Primary Analysis

For completeness, we list additional repositories identified during our survey that were not included in our primary analysis. These represent opportunities for future expansion:

- **OthmanAdi/planning-with-files** (13,888 stars): 13 planning workflow skills
- **blader/humanizer** (4,798 stars): AI text humanization
- **antfu/skills** (3,403 stars): Vue/Nuxt ecosystem (partially included)
- **blader/Claudeception** (1,624 stars): Autonomous skill extraction
- **CharlesWiltgen/Axiom** (465 stars): 144 Apple xOS development skills
- **daymade/claude-code-skills** (579 stars): 37 production-ready skills
- **Aaronontheweb/dotnet-skills** (327 stars): 33 .NET ecosystem skills
- **wondelai/skills** (104 stars): 25 business strategy skills
- **sundial-org/skills** (142 stars): 11 research-oriented skills
- Multiple awesome-lists curating 300-800+ skills each

# References
