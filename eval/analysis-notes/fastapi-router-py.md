# fastapi-router-py: Condition D Context Override Finding

## Summary

The fastapi-router-py skill (negative control, contamination score 0.00) behaves correctly as a control under Condition B (skill-only, B-A delta = -0.133) but shows significant degradation under Condition D (realistic context, D-A delta = -0.667). The degradation is concentrated in tasks where the user requests a non-FastAPI framework — the model overrides the user's request to match what it perceives as the project's existing framework.

## Condition B: Works Correctly as Control

B-A deltas by task:

| Task | Type | Language | B-A Delta |
|------|------|----------|-----------|
| 01 | direct_target | python | -0.500 (truncation) |
| 02 | cross_language | ruby | 0.000 |
| 03 | similar_syntax | python/Flask | 0.000 |
| 04 | grounded | python | 0.000 |
| 05 | adjacent_domain | python | -0.167 (minor) |

Task 01's -0.500 is from truncation (functional_correctness drops due to incomplete output), not contamination. Tasks 02-04 show perfect zero deltas. This is exactly what a negative control should produce.

## Condition D: Framework Override

D-A deltas by task:

| Task | Type | Language | D-A Delta | Issue |
|------|------|----------|-----------|-------|
| 01 | direct_target | python | -1.334 | Tool-calling XML tags in output |
| 02 | cross_language | ruby | -0.167 | Minor |
| 03 | similar_syntax | python/Flask | **-1.917** | Model generates FastAPI instead of Flask |
| 04 | grounded | python | -0.084 | Neutral |
| 05 | adjacent_domain | python | +0.167 | Slight improvement |

### Task 03 Detail (the main anomaly)

All 3 realistic-context runs for task 03 show the same pattern:
- The model explicitly states: "I notice this project uses FastAPI, not Flask"
- It then deliberately generates FastAPI code instead of the requested Flask code
- API idiomaticity drops to 1/5 in every realistic run
- Judge flags: FastAPI APIRouter instead of Flask Blueprint, Pydantic instead of marshmallow, Depends() instead of decorators

This does NOT happen under Condition B (delta = 0.0 for task 03).

### Task 01 Detail

Run 2 under realistic context scored 3/2/1/1 — the model generated XML tool-calling tags (`<read_file>`, `<write_file>`, `<list_dir>`) instead of actual Python code. This is an interaction between the CC system preamble (which describes tool usage) and the model's response mode.

## Root Cause

The Condition D system prompt includes a condensed Claude Code preamble with "Working directory: /Users/dev/project" and simulated codebase context. Combined with the FastAPI skill content, the model infers it's working in an existing FastAPI project and overrides the user's Flask request to match the perceived project context.

This is the **opposite** of the doc-coauthoring pattern: there, realistic context mitigated the skill effect. Here, realistic context amplifies it by giving the model a justification to ignore the user's request.

## Eval Design Considerations

The Condition D anomaly may be partially an eval artifact:

1. **Forced loading**: We append the skill to system context, bypassing activation triggers. In production, the FastAPI skill would only activate for FastAPI-relevant tasks, so a Flask request would likely never see it.

2. **Generic codebase context**: The simulated codebase snippet is selected by target language (Python), not by framework. The model gets a Python skill about FastAPI + a generic Python codebase context, and reasonably infers "this is a FastAPI project."

3. **Real-world skill activation**: Skill activation parameters (trigger conditions in the description frontmatter) would normally prevent the FastAPI skill from loading for a Flask task. Our eval bypasses this entirely.

However, the finding may still be relevant for scenarios where:
- A developer copies an entire skill repo into their project without selective activation
- A skill registry loads related skills broadly (e.g., all Python web framework skills)
- A company publishes a multi-framework skill that covers Flask, FastAPI, and Django

## Status

- **B-A analysis**: Valid as negative control, no changes needed
- **D-A analysis**: Flagged as eval design interaction, not representative of production behavior
- **Action**: None taken on exclusion — B-A data is clean. Condition D anomaly noted for context when interpreting realistic context mitigation results.

## Potential Framing

If we report the D-A finding, it could support a recommendation that:
- Skill activation triggers are important — indiscriminate skill loading can cause framework override
- Companies publishing multi-framework skill repos should ensure developers load only relevant skills
- Agent platforms should filter skills by project context, not just load everything available
- However, we cannot assume in a real-world scenario that the skill would get activated at all — activation parameters would likely prevent this specific interaction
