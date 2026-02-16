# Pattern Provenance Sourcing - Context State (Artifact)

The pattern provenance sourcing occurred over several Claude sessions and through many auto-compaction events. I asked Claude to use this document to preserve context across compaction events. Preserving as an artifact for anyone interested in the pattern sourcing process, and also as a point-in-time reference reflecting the state of LLM documentation usage as of February 15, 2026.

## Current Task
Systematically finding and adding verified provenance sources for all expected_patterns in the eval framework task files. This is a HARD REQUIREMENT - all patterns used for deterministic scoring must have traceable provenance to validate results.

## Progress Status
**Completed: 20/20 skills (100%)** ✅

### ✅ Verified Skills:
1. azure-containerregistry-py (30 patterns)
2. azure-identity-dotnet (30 patterns)
3. azure-identity-java (30 patterns)
4. azure-security-keyvault-secrets-java (30 patterns)
5. claude-settings-audit (24 patterns)
6. copilot-sdk (26 patterns)
7. doc-coauthoring (29 patterns) - NEGATIVE CONTROL B
8. fastapi-router-py (30 patterns) - NEGATIVE CONTROL A
9. gemini-api-dev (13 patterns)
10. monitoring-observability (35 patterns)
11. neon-postgres (31 patterns)
12. ossfuzz (37 patterns)
13. pdf (34 patterns)
14. prompt-agent (30 patterns)
15. provider-resources (23 patterns)
16. react-native-best-practices (28 patterns)
17. sharp-edges (25 patterns)
18. skill-creator (30 patterns)
19. upgrade-stripe (26 patterns)
20. wiki-agents-md (25 patterns)

**All skills verified!** Pattern provenance sourcing complete for eval data quality.

## Key Learnings

### Successful Patterns:
1. **GitHub raw URLs work best**: `https://raw.githubusercontent.com/owner/repo/refs/heads/main/path/to/file.md`
2. **llms.txt is gold**: Neon's https://neon.com/docs/llms.txt provided markdown versions of all docs
3. **Scaffolding/example repos**: Better than API docs - real working code with all patterns
4. **Anti-patterns need sources too**: Show what NOT to use to prevent cross-contamination
5. **Stripe markdown URLs**: `https://docs.stripe.com/api/endpoint.md?lang=python` provides LLM-friendly markdown format
6. **GitHub over npmjs.com**: For npm packages, use `https://github.com/owner/package` instead of npmjs.com (gray-matter worked perfectly)
7. **GitHub manual/examples**: When official docs fail, use GitHub `manual/` or `examples/` dirs (Prawn: manual/table/table.rb, manual/text/text.rb)
8. **React.dev works great**: react.dev/reference/react/* docs are LLM-accessible (lazy, useState, useEffect, useCallback, memo, Suspense all work!)
9. **Android guides over API refs**: developer.android.com/guide/* pages with code examples work better than bare API references
10. **SME validation for missing patterns**: When official docs lack code examples (Apple UIKit), use SME validation for basic patterns (import statements, class syntax) while API docs verify class names
11. **agentskills.io is authoritative**: agentskills.io/specification.md is the definitive source for Agent Skills format, replacing older docs.anthropic.com URLs with comprehensive SKILL.md structure, frontmatter validation rules, and best practices
12. **Document transitional states**: When APIs/packages transition (Linear MCP: API key → OAuth), document both old and new sources without asserting expected output. This allows observing which pattern emerges in eval runs and tracking consistency across multiple runs, revealing how models handle outdated vs current documentation
13. **Python docs are excellent**: docs.python.org is consistently accessible and well-structured for LLM consumption (hashlib, json, argparse, re all work perfectly with code examples)
14. **POSIX specs work well**: pubs.opengroup.org POSIX specifications for shell and utilities are accessible and contain the needed patterns (crontab, shell scripting patterns)
15. **Linux man pages over GNU docs**: man7.org/linux/man-pages and linux.die.net provide accessible alternatives to rate-limited gnu.org. Simplify patterns by removing flags (grep -E → grep) to reduce brittleness when utilities have many option combinations
16. **Generic security sources for conceptual patterns**: For security analysis concepts (not SDK-specific), use OWASP cheat sheets, CWE database, and security design principles. These contain keywords like "pit of success", "secure by default", "timing attack", "dangerous defaults" that validate conceptual understanding rather than specific API usage
17. **Remove patterns without sources**: During verification, if patterns can't be sourced from accessible documentation, remove them rather than keeping unsourced assertions. Examples: Removed AGENTS.md section headers (no Anthropic spec found, generic agents.md spec doesn't prescribe sections), removed CLAUDE.md "Generated" patterns (not in docs). Removed 9 patterns total from wiki-agents-md.
18. **Always verify URLs immediately**: Adding URLs without verification is a critical error. GNU make (gnu.org → 429), npm docs (wrong path → 404) caught during systematic verification. Use WebFetch on every URL before adding to task files.
19. **Language syntax in framework docs**: Framework documentation often explicitly shows language syntax. Rails ActionController docs show Ruby class/def syntax, FastAPI WebSocket docs show Python async/await - no need for separate language sources when framework docs are comprehensive.
20. **FastAPI GitHub raw URLs work perfectly**: raw.githubusercontent.com URLs for FastAPI docs are reliable and contain all patterns (APIRouter, dependencies, WebSocket, status codes).

### Failed/Blocked Sources:
1. **HashiCorp developer.hashicorp.com** - Rate limited (429), use GitHub repos instead
2. **npmjs.com packages** - Rate limited (403), use GitHub repos instead
3. **google.github.io/oss-fuzz** - 404s, use github.com/google/oss-fuzz instead
4. **Some scraped HTML** - Low content density, prefer markdown/raw files
5. **Apple Developer docs** - Require JavaScript, not LLM-accessible (developer.apple.com/documentation/*)
6. **Swift.org docs** - Require JavaScript, not LLM-accessible (docs.swift.org/*)
7. **GNU Bash/Coreutils manuals** - Rate limited (429), use user verification when needed (gnu.org/software/bash/manual/bash.html works but rate-limits)

## Source Discovery Strategy

### Step 1: Find Official Docs
- Check for llms.txt (e.g., https://example.com/docs/llms.txt)
- Look for /docs or /documentation directories
- Check official GitHub repositories

### Step 2: Try Markdown Versions
- Append `.md` to documentation URLs
- Use raw.githubusercontent.com for GitHub files
- Check for `/docs` folder in repos

### Step 3: Find Examples
- Look for `examples/` directories in repos
- Find scaffolding/template repositories
- Check `projects/` for reference implementations

### Step 4: Verify Accessibility
- Test URLs with curl or WebFetch
- Verify content density (not just 404/403)
- Check that patterns are actually present in content

## Pattern Inclusion Criteria (CRITICAL for Eval Validity)

The eval framework measures **cross-language contamination** - when an agent provided code examples in the "wrong" language produces output with patterns from the example language instead of the requested language.

### When to Include a Pattern:

**INCLUDE** a pattern in `expected_patterns` if it **MUST be present** for a valid interpretation of the prompt:
- Language syntax that is mandatory for the target language (e.g., `package main` for Go, `def` for Python functions)
- Standard library imports/functions explicitly required by the prompt (e.g., "output as JSON" requires json.Marshal in Go)
- SDK/framework methods explicitly requested (e.g., "list repositories" requires list_repository_names)

**REMOVE** a pattern if there are multiple valid interpretations where it might not appear:
- Optional implementation details not specified in the prompt
- Alternative approaches that are equally valid (e.g., multiple ways to read a file)
- Patterns that might appear in some valid solutions but not others

### The Standard Language Pattern Test:

**Absence of required language patterns may indicate contamination.** For example:
- A Go program missing `package main` or `func main()` likely has Python/JavaScript contamination
- A Python script missing `def` for functions might have contamination from languages without explicit function definitions
- JSON output requirement missing `json.Marshal` (Go) or `json.dumps` (Python) suggests the model didn't understand the language context

### Sources for Standard Patterns:

- **Language syntax**: Reference official language specifications (go.dev, python.org)
- **Standard library**: Reference official stdlib documentation (go.dev/pkg, docs.python.org/3/library)
- **SDK/Framework**: Reference official API documentation

### URL Verification Requirement (CRITICAL - HARD REQUIREMENT):

**EVERY source URL MUST be verified to actually contain the pattern before adding it to a task file.**

This is non-negotiable for deterministic pattern matching data quality. The eval results will be published and scrutinized. Invalid URLs or sources that don't contain the claimed patterns could contaminate the data and interfere with accurate analysis.

**Verification Process:**
1. **Use WebFetch** to load each URL and verify it contains the expected pattern
2. **If pattern is NOT found**, search for alternate documentation that does contain it
3. **Update the URL** to the verified source
4. **Document verification** in sources_todo.md with ✅ marks

**Never assume:**
- Language spec URLs contain specific patterns (they often don't - use tutorial/guide docs instead)
- Standard library docs have the exact function (verify it's actually there)
- URLs haven't changed due to documentation reorganization

**Example Corrections Made:**
- ❌ go.dev/ref/spec#Package_clause - Did NOT contain "package main" explicitly
- ✅ go.dev/doc/code - DOES contain "package main" and "func main()" with examples
- ❌ Assumed docs.python.org/3/library/os.html had os.walk - verified via curl that it does ✅

**Workflow:**
1. Add source URL to JSON
2. Immediately verify with WebFetch (or curl if WebFetch fails)
3. If verification fails, find correct URL before proceeding
4. Mark as verified in sources_todo.md

## Critical Files

### Main Tracking Doc:
- `eval/sources_todo.md` - Comprehensive TODO with all unsourced patterns organized by skill

### Task Files (Update These):
- `eval/tasks/*.json` - Add pattern_sources with verified URLs

## Key Repository Patterns

### GitHub Copilot SDK
- Base: `https://github.com/github/copilot-sdk`
- Docs: `docs/getting-started.md`, `docs/hooks/*.md`, `docs/mcp/*.md`
- Language SDKs: `dotnet/README.md`, `python/README.md`, `go/README.md`

### OSS-Fuzz
- Base: `https://github.com/google/oss-fuzz`
- Docs: `docs/getting-started/new_project_guide.md`
- Language guides: `docs/getting-started/new-project-guide/{language}_lang.md`
- Examples: `projects/ujson/*.py`, `projects/ujson/Dockerfile`

### Terraform Provider Scaffolding
- Base: `https://github.com/hashicorp/terraform-provider-scaffolding-framework`
- Code: `internal/provider/example_resource.go`, `internal/provider/example_resource_test.go`
- HCL: `examples/resources/scaffolding_example/resource.tf`

### Neon
- llms.txt: `https://neon.com/docs/llms.txt` - Lists all markdown docs
- Guides: `https://neon.com/docs/guides/{topic}.md`
- Serverless: `https://neon.com/docs/serverless/serverless-driver.md`

## URL Template Patterns

```
GitHub raw:
https://raw.githubusercontent.com/{owner}/{repo}/refs/heads/{branch}/{path}

Neon markdown:
https://neon.com/docs/{category}/{page}.md

Drizzle ORM:
https://orm.drizzle.team/docs/{topic}

FastAPI:
https://fastapi.tiangolo.com/{section}/

jq manual:
https://jqlang.org/manual/ (redirects from jqlang.github.io/jq/manual/)

Python docs:
https://docs.python.org/3/library/{module}.html

POSIX specs:
https://pubs.opengroup.org/onlinepubs/9699919799/utilities/{utility}.html
https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html (shell)
```

## Anti-Pattern Strategy

For each task, we need sources for BOTH expected patterns AND anti-patterns:
- **Expected**: Show correct usage from official docs
- **Anti-patterns**: Show incorrect usage from OTHER language/framework docs

Example: For a Python task, use TypeScript SDK docs as anti-pattern source to show what NOT to do.

## Verification Commands

Test URL accessibility:
```bash
curl -I -s "https://example.com/path/to/doc.md" | head -1
```

Run verification script:
```bash
cd /tmp && python3 /tmp/verify_sources.py
```

Analyze coverage:
```bash
cd /tmp && python3 /tmp/analyze_pattern_coverage.py
```
