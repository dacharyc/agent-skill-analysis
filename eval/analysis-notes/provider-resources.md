# provider-resources Deep Dive

## Summary

provider-resources (HashiCorp, Terraform provider development) shows B-A = -0.317 (p=0.010), the third-largest degradation in our sample. Structural contamination score is 0.55 (high), categorized as app-to-aux (Go mixed with HCL, shell). The degradation is concentrated in two tasks and driven by two interacting mechanisms: **output inflation** (the skill's detailed Go patterns cause the model to generate substantially more verbose code that hits the 4096-token ceiling) and **pattern over-specification** (the model adopts AWS-provider-specific internal patterns from the skill that aren't appropriate for a generic provider resource).

Realistic context fully mitigates the degradation on the cross-language task and partially mitigates it on the grounded task.

## Per-Task Breakdown

| Task | Type | Lang | Baseline | With-skill | Realistic | B-A |
|------|------|------|----------|------------|-----------|-----|
| 01 | direct_target | Go | 3.583 | 3.333 | 3.583 | -0.250 |
| 02 | cross_language | Python | 3.833 | 3.250 | 3.917 | **-0.583** |
| 03 | similar_syntax | Go | 4.417 | 4.417 | 4.250 | 0.000 |
| 04 | grounded | Go | 4.667 | 3.917 | 4.083 | **-0.750** |
| 05 | adjacent_domain | HCL | 4.167 | 4.167 | 4.083 | 0.000 |

Mean B-A: -0.317. Two tasks (02, 04) drive all the degradation; three tasks (01, 03, 05) show zero or negligible effect.

## Mechanism 1: Output Inflation → Truncation

The dominant mechanism is that skill content causes the model to generate substantially longer, more elaborate outputs that hit the 4096-token ceiling and get truncated mid-implementation.

### Task 04 (grounded, Go): Complete Read/Update for partial provider code

| Condition | Output tokens | Truncated? | Functional correctness |
|-----------|--------------|------------|----------------------|
| Baseline run 0 | 1,832 | No | 4 |
| Baseline run 1 | 1,796 | No | 5 |
| Baseline run 2 | 1,739 | No | 5 |
| With-skill run 0 | 3,741 | No | 3 |
| With-skill run 1 | 4,096 | **Yes** | 2 |
| With-skill run 2 | 4,096 | **Yes** | 3 |

Baseline outputs are compact (~1,800 tokens) and functionally complete — they implement Read and Update operations directly without preamble. With-skill outputs are 2x longer (~3,900 tokens): the model adds a markdown header, full import blocks, reconstructs the entire resource struct with additional fields (ARN, Endpoint, LastUpdated), reimplements Create, and generates elaborate helper functions (finder patterns, waiter patterns, retry logic). Two of three runs hit the ceiling and are truncated mid-function.

The judge scores functional_correctness lower because the with-skill outputs are **cut off before completing the requested operations** — exactly the token budget competition mechanism seen in react-native-best-practices, but here the competition is between the skill's elaborate Go patterns and the task's core requirements.

### Task 02 (cross_language, Python): Pulumi dynamic provider

ALL 9 runs across all 3 conditions hit the 4096-token ceiling. But the with-skill outputs are structurally different from baseline:

- **Baseline**: Jumps directly into a single Python file implementing `DatabaseProvider(ResourceProvider)` with CRUD methods. Truncated mid-implementation but the core provider class and 2-3 CRUD methods are present.
- **With-skill**: Generates an elaborate project structure first (7 files: models.py, client.py, exceptions.py, tests/, etc.) before reaching the core provider implementation. The judge notes this is "over-engineered project structure more typical of enterprise Java/C# patterns." The core Pulumi provider class is never reached before truncation.

The skill's detailed Go provider package structure (service packages, models, client abstractions) bleeds into the Python output as an enterprise-style project layout, consuming tokens on scaffolding at the expense of the core implementation.

## Mechanism 2: Pattern Over-Specification

The skill teaches Terraform Plugin Framework patterns using detailed examples that closely follow the AWS provider's internal conventions. When loaded, the model adopts these specific patterns even when they're inappropriate:

**Task 04 with-skill contamination signals (from judge):**
- `r.Meta().S3StorageClient(ctx)` — AWS-provider-specific client access pattern
- `github.com/hashicorp/terraform-provider-aws/internal` imports
- `names.S3Storage`, `names.AttrTags`, `names.AttrTagsAll` — AWS-provider-internal constants
- Mixing `terraform-plugin-sdk/v2` (retry) with `terraform-plugin-framework` — an AWS provider convention
- `types` namespace collision between framework types and AWS S3 SDK types

The baseline generates clean, generic Plugin Framework code without any provider-specific patterns. The skill causes the model to over-specialize toward the AWS provider's conventions.

**Task 02 cross-language bleed:**
The Go provider package structure (separate models, client, exceptions, tests) bleeds into the Python Pulumi output. The judge identifies this as "enterprise Java/C#" patterns — the Go conventions don't translate as "Go patterns in Python" (which would be classic PLC) but rather as "over-engineered architecture" in a context that calls for a simple single-file implementation.

## Realistic Context Mitigation

| Task | B-A | D-A | Mitigation |
|------|-----|-----|-----------|
| 02 | -0.583 | +0.083 | >100% (fully reversed) |
| 04 | -0.750 | -0.583 | 22% (partial) |

Task 02's full mitigation suggests that the system preamble and conversation context help the model ignore the Go patterns when generating Python — the cross-language bleed is weak and easily overridden. Task 04's partial mitigation is consistent with the pattern being in the same language (Go → Go): the skill's AWS-specific patterns are harder to suppress when the task is also in Go.

## What This Adds to the Contamination Vector Taxonomy

provider-resources confirms the **output inflation** mechanism seen in react-native-best-practices but adds a new variant: **architectural pattern bleed**. The skill's Go package structure doesn't cause language confusion (the Python is syntactically correct) — instead, it causes structural over-engineering in a different language. This is distinct from:

- Template propagation (exact syntax copying, e.g., `//` comments in JSON)
- Textual frame leakage (skill identity in prose, e.g., "React Native best practices")
- API hallucination (fabricated methods, e.g., Stripe)
- Cross-language code bleed (wrong language syntax, e.g., `db.` in JSON)

The architectural pattern bleed is subtler: the model learns "a provider resource needs separate models, client, exceptions, tests" from the Go skill and applies this architecture when a simpler single-file approach would be more appropriate in Python/Pulumi. The contamination is at the design level, not the syntax level.

## Implications

1. **Output inflation is a recurring mechanism**: This is now the third skill (after react-native-best-practices and provider-resources task 04) where the token ceiling confound is a significant factor. Skills with detailed, pattern-heavy content consistently cause longer outputs that get truncated. This is partly an eval artifact (real usage doesn't have a fixed 4096-token ceiling) but also partly real — verbose outputs waste user attention even without truncation.

2. **Same-language over-specification is hard to mitigate**: Task 04 (Go → Go) shows only 22% mitigation from realistic context, compared to >100% for the cross-language task 02. When the skill's patterns are in the same language as the task, the model has less reason to ignore them. This is consistent with the framework-specificity finding from react-native: patterns that are in-domain but over-specific are the hardest to suppress.

3. **Structural contamination score partially works here**: Unlike most skills in our sample, provider-resources's structural score (0.55) does align directionally with its behavioral degradation (-0.317). The Go + HCL + shell mixing is a real contamination vector, even though the app-to-aux category should in theory be lower risk. The degradation mechanism isn't classic language confusion, though — it's pattern over-specification and architectural bleed.
