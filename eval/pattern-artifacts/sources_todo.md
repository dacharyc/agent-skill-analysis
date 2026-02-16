# Pattern Sources Verification - Systematic Review (Artifact)

Given that Claude Opus 4.6 generated the patterns used for deterministic testing, for the sake of rigor, Sonnet 4.5 with human oversight is systematically verifying that EVERY pattern in EVERY task has a valid source that actually contains that pattern. The human author of this paper has watched, guided, and participated in every single check. None of this was completed with background agents or autonomously with a human out of the loop.

This document has been cleared and rewritten over several passes as we have validated sources and removed unverifiable patterns to ensure clean deterministic expectations. It is intentionally preserved as an artifact of the final check pass.

Final pass completed February 15, 2026.

## Verification Checklist

- [x] azure-containerregistry-py
- [x] azure-identity-dotnet
- [x] azure-identity-java
- [x] azure-security-keyvault-secrets-java
- [x] claude-settings-audit
- [x] copilot-sdk
- [x] doc-coauthoring
- [x] fastapi-router-py
- [x] gemini-api-dev
- [x] monitoring-observability
- [x] neon-postgres
- [x] ossfuzz
- [x] pdf
- [x] prompt-agent
- [x] provider-resources
- [x] react-native-best-practices
- [x] sharp-edges
- [x] skill-creator
- [x] upgrade-stripe
- [x] wiki-agents-md

## Verification Process

For each skill:
1. List all tasks and their patterns
2. For each pattern, identify which source(s) should contain it
3. Verify that at least one source actually contains the pattern
4. Document any patterns that lack valid sources
5. Either add missing sources or remove unsourced patterns

---

## Detailed Verification Notes

### ✅ azure-containerregistry-py - VERIFIED (30 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 01: Added Python argparse docs for --dry-run/--delete CLI flags
- Task 02: Added Go documentation (package main, func main), Go stdlib (encoding/json, flag package)
- Task 04: Added Python exception handling docs for try/except blocks
- Task 05: Added Python stdlib docs (os.walk, hashlib) for directory traversal and MD5 hashing

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ docs.python.org/3/library/argparse.html - argparse module
- ✅ go.dev/doc/code - package main, func main() executable entry point
- ✅ pkg.go.dev/encoding/json - json.Marshal, json.NewEncoder
- ✅ pkg.go.dev/flag - flag parsing
- ✅ docs.python.org/3/tutorial/errors.html - try/except exception handling
- ✅ docs.python.org/3/library/os.html - os.walk() directory traversal
- ✅ docs.python.org/3/library/hashlib.html - hashlib, MD5 hashing

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- SDK patterns: Azure Container Registry, Azure Identity, Azure Blob Storage, Docker SDK ✅
- Language syntax: Go package/func declarations, Python try/except ✅
- Standard library: Python (argparse, os.walk, hashlib), Go (encoding/json, flag) ✅

---

### ✅ azure-identity-dotnet - VERIFIED (30 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 01: Added ASP.NET Core Minimal APIs for builder.Services and app.Map endpoint mapping
- Task 02: Added Python asyncio docs for import asyncio, async def, await keywords; Python function definition docs for def keyword
- Task 03: Added Spring Framework docs for @RestController, @GetMapping, @Bean annotations; Java tutorial for public class syntax
- Task 04: Added C# field modifiers docs for private, readonly, static; ASP.NET Core configuration docs for IConfiguration
- Task 05: Added JwtBearerDefaults API reference for JwtBearerDefaults class; ASP.NET Core Minimal APIs for builder.Services and app.UseAuthentication

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ learn.microsoft.com/en-us/aspnet/core/fundamentals/minimal-apis - builder.Services, app.MapGet/MapPost/Map
- ✅ docs.python.org/3/library/asyncio.html - import asyncio, async def, await
- ✅ docs.python.org/3/tutorial/controlflow.html#defining-functions - def keyword
- ✅ docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-requestmapping.html - @RestController, @GetMapping
- ✅ docs.spring.io/spring-framework/reference/core/beans/java/bean-annotation.html - @Bean
- ✅ docs.oracle.com/javase/tutorial/java/javaOO/classes.html - public class
- ✅ learn.microsoft.com/en-us/dotnet/csharp/programming-guide/classes-and-structs/fields - private, readonly, static
- ✅ learn.microsoft.com/en-us/aspnet/core/fundamentals/configuration - IConfiguration, Environment
- ✅ learn.microsoft.com/en-us/dotnet/api/microsoft.aspnetcore.authentication.jwtbearer.jwtbearerdefaults - JwtBearerDefaults

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- SDK patterns: Azure Identity (.NET, Python, Java), Key Vault Secrets, JWT Bearer ✅
- Language syntax: C# using/private/readonly/static, Python def/async def, Java public class ✅
- Framework patterns: ASP.NET Core (builder.Services, app.Map, IConfiguration, environments), Spring (annotations), Python asyncio ✅

---

### ✅ azure-identity-java - VERIFIED (30 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 02: Added Python exception handling docs for except keyword and Error exception handling
- Task 04: Added Java exception handling tutorial for try/catch blocks and throws keyword

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ docs.python.org/3/tutorial/errors.html - except keyword, Error exception handling
- ✅ docs.oracle.com/javase/tutorial/essential/exceptions/catch.html - try/catch blocks, throws keyword

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- SDK patterns: Azure Identity Java (DefaultAzureCredentialBuilder, WorkloadIdentityCredentialBuilder, ChainedTokenCredentialBuilder), Azure Storage (BlobServiceClientBuilder), Azure Key Vault (KeyClientBuilder, SecretClientBuilder), Azure Cosmos DB (CosmosClient) ✅
- Language syntax: Java (public class, try/catch, throws), Python (def, except) ✅
- Builder patterns: All Java SDK builders use .build() pattern consistently ✅

---

### ✅ azure-security-keyvault-secrets-java - VERIFIED (30 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 01: Added DefaultAzureCredentialBuilder source (required by prompt "Use SecretClient with DefaultAzureCredential")
- Task 03: Updated Reactor Mono/Flux source description to explicitly include subscribe() consumption pattern

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ learn.microsoft.com/en-us/java/api/com.azure.identity.defaultazurecredentialbuilder - DefaultAzureCredentialBuilder
- ✅ projectreactor.io/docs/core/release/api/reactor/core/publisher/Mono.html - subscribe(), onErrorResume, doOnError

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- SDK patterns: Key Vault Secrets (SecretClient, SecretAsyncClient, SecretClientBuilder), Key Vault Keys (KeyClient, CryptographyClient), Azure Identity (DefaultAzureCredentialBuilder), Core (SyncPoller, ResourceNotFoundException, HttpResponseException) ✅
- Reactive patterns: Project Reactor (Mono, Flux, subscribe, onErrorResume, doOnError, buildAsyncClient) ✅
- CRUD operations: setSecret, getSecret, updateSecretProperties, beginDeleteSecret, listDeletedSecrets, beginRecoverDeletedSecret ✅

---

### ✅ claude-settings-audit - VERIFIED (24 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 01: Added python --version, make command, git status sources
- Task 02: Added rustc --version, git status sources
- Task 03: Added node --version source
- Task 04: Added git status/log, npm list, tsc --version, node --version sources

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ docs.python.org/3/using/cmdline.html - python --version, python3 --version
- ✅ man7.org/linux/man-pages/man1/make.1.html - make with flags (corrected from gnu.org which rate limits)
- ✅ git-scm.com/docs/git-status - git status command
- ✅ doc.rust-lang.org/rustc/command-line-arguments.html - rustc --version
- ✅ nodejs.org/api/cli.html - node --version
- ✅ docs.npmjs.com/cli/v10/commands/npm-ls - npm list/npm ls (corrected URL from 404)

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- Claude Code settings: permissions.allow, Bash(command), WebFetch(domain:), Skill() syntax ✅
- Stack detection CLI tools: python, poetry, make, git, docker, rustc, cargo, node, pnpm, tsc, npm ✅
- MCP configuration: mcpServers, sentry, linear MCP servers ✅

---

### ✅ copilot-sdk - VERIFIED (26 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 02: Added Java language syntax sources (public class, public static void main) - required for Java application even though no official Java Copilot SDK exists

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ docs.oracle.com/javase/tutorial/java/javaOO/classes.html - Java class definitions
- ✅ docs.oracle.com/javase/tutorial/getStarted/application/index.html - Java main method signature

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- Copilot SDK patterns: Node.js/TypeScript (CopilotClient, createSession, defineTool, streaming, onPreToolUse), Python (await client.start/stop, create_session, send_and_wait), .NET (CreateSessionAsync, SendAndWaitAsync, DisposeAsync), Go (copilot.NewClient, Start, CreateSession) ✅
- Language syntax: Java (class, public static void main), C# (await using), Python (asyncio.run, await) ✅
- MCP integration: mcpServers configuration for remote HTTP and local stdio servers ✅

---

### ✅ doc-coauthoring - VERIFIED (29 patterns, all sourced)

**Added missing sources:**
- Task 01: Added Python function definition docs for def keyword
- Task 02: Added Go package main source
- Task 03: Added TypeScript function syntax docs

**Note:** This is NEGATIVE CONTROL B - a non-code skill about documentation workflows. All tasks test whether non-code workflow jargon (str_replace, create_file, Reader Claude, Stage 1/2/3, brainstorm, curation) bleeds into code generation.

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- Document processing libraries: Python-Markdown, PyYAML, Jinja2, gray-matter, unified/remark ✅
- Language syntax: Python (def, import, with open), Go (package main, func), TypeScript (function, async function, interface, export) ✅
- Standard library: Python (argparse, re, datetime, enumerate, os, pathlib), Go (net/http, encoding/json) ✅

---

### ✅ fastapi-router-py - VERIFIED (30 patterns, all sourced, URLs verified)

**No missing sources!** All patterns already had complete coverage.

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ FastAPI GitHub docs (raw.githubusercontent.com) - APIRouter, response_model, Depends, status codes, WebSocket
- ✅ guides.rubyonrails.org/action_controller_overview.html - Ruby class inheritance, def methods
- ✅ flask.palletsprojects.com - Blueprint, jsonify patterns
- ✅ marshmallow.readthedocs.io - Schema validation patterns

**Note:** This is NEGATIVE CONTROL A - a Python-only skill (score 0.00) testing whether FastAPI patterns contaminate other languages (Ruby) and frameworks (Flask).

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- FastAPI patterns: APIRouter, response_model, Depends, status.HTTP_201_CREATED, status.HTTP_204_NO_CONTENT, WebSocket, WebSocketDisconnect ✅
- Language syntax: Ruby (class < ApplicationController, def methods), Python (async def, await) ✅
- Alternative frameworks: Flask Blueprint, jsonify, Marshmallow Schema (testing no FastAPI contamination) ✅

---

### ✅ gemini-api-dev - VERIFIED (13 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 02: Added Rust reqwest HTTP client library source (no official Rust SDK exists, REST API required)
- Task 05: Added Go func main() entry point source

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ ai.google.dev/gemini-api/docs/quickstart.md.txt - Python SDK (genai.Client, generate_content), Node.js SDK (GoogleGenAI), Go SDK (genai.NewClient), REST API endpoint patterns
- ✅ ai.google.dev/gemini-api/docs/models.md.txt - Model names (gemini-3-flash-preview, gemini-3-pro-preview)
- ✅ ai.google.dev/gemini-api/docs/structured-output.md.txt - Python structured JSON output patterns
- ✅ ai.google.dev/gemini-api/docs/function-calling.md.txt - TypeScript function calling patterns
- ✅ ai.google.dev/gemini-api/docs/embeddings.md.txt - Go embeddings API patterns
- ✅ ai.google.dev/gemini-api/docs/migrate.md.txt - Migration guide showing deprecated patterns
- ✅ docs.rs/reqwest/latest/reqwest/ - Rust reqwest HTTP client (reqwest::Client, .post(), .json(), .send().await)
- ✅ go.dev/doc/code - Go func main() entry point

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- Gemini SDK patterns: Python (from google import genai, genai.Client(), client.models.generate_content, response.text), TypeScript (GoogleGenAI, ai.models.generateContent, functionDeclarations), Go (google.golang.org/genai, genai.NewClient, client.Models.GenerateContent) ✅
- REST API patterns: generativelanguage.googleapis.com, v1beta endpoint, generateContent ✅
- Language syntax: Go (func main), Rust HTTP clients (reqwest, hyper, ureq) ✅
- Model names: gemini-3-flash-preview, gemini-3-pro-preview (current), anti-patterns detect deprecated gemini-1.5/2.0/2.5 ✅
- Migration patterns: google-generativeai → google-genai SDK transition, old vs new model names ✅

---

### ✅ monitoring-observability - VERIFIED (35 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 02: Added Go language syntax sources (package main, func) and net/http source for http.Handle
- Task 03: Added Node.js module.exports/export source and crypto.randomUUID() source for correlation IDs
- Task 05: Added Python asyncio and function definition sources, urllib3 Retry class for retry logic

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ raw.githubusercontent.com/open-telemetry/opentelemetry.io - OpenTelemetry Python docs (TracerProvider, OTLPSpanExporter, set_attribute, start_as_current_span)
- ✅ raw.githubusercontent.com/open-telemetry/opentelemetry-python-contrib - FlaskInstrumentor class and instrument_app() method
- ✅ raw.githubusercontent.com/prometheus/client_golang - Go Prometheus client (NewCounterVec, NewHistogramVec, promhttp.Handler)
- ✅ raw.githubusercontent.com/prometheus/docs - Prometheus guides (Go application patterns, alerting best practices, histogram_quantile)
- ✅ go.dev/doc/code - Go package main and func syntax
- ✅ pkg.go.dev/net/http - Go http.Handle function
- ✅ raw.githubusercontent.com/winstonjs/winston - Winston logger (JSON format, transports)
- ✅ raw.githubusercontent.com/expressjs/expressjs.com - Express middleware (req.headers, middleware patterns)
- ✅ nodejs.org/api/modules.html - Node.js module.exports documentation
- ✅ nodejs.org/api/crypto.html - Node.js crypto.randomUUID() for UUID generation
- ✅ raw.githubusercontent.com/prometheus/prometheus - Prometheus alerting rules (for:, labels:, annotations:, severity:)
- ✅ raw.githubusercontent.com/fastapi/fastapi - FastAPI patterns (@app.get, async def)
- ✅ raw.githubusercontent.com/encode/httpx - HTTPX async client (AsyncClient, timeout configuration)
- ✅ raw.githubusercontent.com/aio-libs/aiohttp - aiohttp client (ClientSession, ClientTimeout)
- ✅ docs.python.org/3/library/asyncio.html - Python asyncio (import asyncio, async def, event loop)
- ✅ urllib3.readthedocs.io - urllib3 Retry class (total, backoff_factor retry configuration)

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- OpenTelemetry patterns: Python (from opentelemetry, TracerProvider, OTLPSpanExporter, FlaskInstrumentor, set_attribute, start_as_current_span) ✅
- Prometheus patterns: Go (NewHistogramVec, NewCounterVec, promauto, promhttp.Handler), YAML (rate(), histogram_quantile, for:, labels:, annotations:) ✅
- Logging patterns: Node.js Winston (winston import, JSON format, req.headers, x-request-id, crypto.randomUUID) ✅
- Language syntax: Go (package main, func, http.Handle), JavaScript (require/import, module.exports/export), Python (async def, def, asyncio) ✅
- HTTP clients: Python (FastAPI, httpx, aiohttp with timeout/retry), Node.js (Express middleware) ✅

---

### ✅ neon-postgres - VERIFIED (31 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 01: Added TypeScript syntax sources (interface/type declarations, async function, export keyword)
- Task 02: Added Python async def source, updated FastAPI source to GitHub raw README for decorator patterns
- Task 03: Added Node.js process.on('SIGTERM') source for graceful shutdown
- Task 04: Split Drizzle relational queries source, added Drizzle operators source for and() specifically
- Task 05: Added TypeScript class, generics, and JSON serialization sources

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ neon.com/docs/serverless/serverless-driver.md - Neon serverless driver (import @neondatabase/serverless, neon(), process.env.DATABASE_URL)
- ✅ neon.com/docs/guides/python.md - Python asyncpg patterns (await connect/execute/fetch)
- ✅ neon.com/docs/guides/node.md - Node.js pg/node-postgres patterns (Pool, query, connect)
- ✅ neon.com/docs/guides/drizzle.md - Drizzle ORM with Neon integration
- ✅ www.typescriptlang.org/docs/handbook/2/* - TypeScript syntax (interface, type, async function, export, class, generics)
- ✅ docs.python.org/3/library/asyncio.html - Python async def
- ✅ raw.githubusercontent.com/fastapi/fastapi/master/README.md - FastAPI decorators (@app.get, @router.get)
- ✅ node-postgres.com/apis/pool - Pool configuration (max, connectionTimeoutMillis, idleTimeoutMillis)
- ✅ nodejs.org/api/process.html#process_signal_events - process.on('SIGTERM') for graceful shutdown
- ✅ orm.drizzle.team/docs/* - Drizzle column types (pgTable, serial, varchar, timestamp), relational queries (relations, one, many, eq), operators (and), type helpers (InferSelectModel, InferInsertModel)
- ✅ github.com/redis/ioredis - ioredis client (import Redis, get/set/del commands)
- ✅ redis.io/docs/latest/commands/ - Redis commands reference (TTL, pattern scanning)
- ✅ developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON - JSON.parse() and JSON.stringify()

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- Neon serverless patterns: TypeScript (import @neondatabase/serverless, neon(), process.env.DATABASE_URL, sql template literals) ✅
- Database drivers: Python (asyncpg with await fetch/execute, create_pool), JavaScript (node-postgres Pool, pool.query, pool.connect) ✅
- ORMs: Drizzle (pgTable schema, serial/varchar/timestamp types, relations/one/many, eq/and operators, InferSelectModel/InferInsertModel types) ✅
- Language syntax: TypeScript (interface, type, async function, export, class, generics <T>), Python (async def), JavaScript (process.on SIGTERM) ✅
- Frameworks: FastAPI (from fastapi, @app.get, @router.get, async def endpoints), Redis (ioredis import, get/set, JSON.parse/stringify) ✅

---

### ✅ ossfuzz - VERIFIED (37 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 01: Added LibFuzzer documentation for LLVMFuzzerTestOneInput entry point function signature
- Task 03: Added PyYAML, Python import statement, and Python decorator syntax sources
- Task 04: Added POSIX shell syntax source for bash variable expansion ($VAR) patterns
- Task 05: Added Dockerfile reference for FROM, RUN, WORKDIR, COPY instruction syntax

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ raw.githubusercontent.com/google/oss-fuzz - OSS-Fuzz docs (new project guide, fuzzer environment, language-specific guides)
- ✅ llvm.org/docs/LibFuzzer.html - LibFuzzer LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) entry point
- ✅ raw.githubusercontent.com/google/oss-fuzz/refs/heads/master/projects/ujson/* - Example Python Atheris fuzzer (ujson_fuzzer.py, build.sh, Dockerfile, project.yaml)
- ✅ go.dev/doc/security/fuzz - Go native fuzzing (testing.F, f.Add, f.Fuzz)
- ✅ pkg.go.dev/testing#F - Go testing.F type documentation
- ✅ pyyaml.org/wiki/PyYAMLDocumentation - PyYAML yaml.safe_load() and yaml.load()
- ✅ docs.python.org/3/reference/simple_stmts.html#import - Python import statement
- ✅ docs.python.org/3/glossary.html#term-decorator - Python @ decorator syntax
- ✅ pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html - POSIX shell syntax ($VAR expansion)
- ✅ docs.docker.com/reference/dockerfile/ - Dockerfile instructions (FROM, RUN, WORKDIR, COPY)

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- OSS-Fuzz C++ patterns: LLVMFuzzerTestOneInput, $CXX, $CXXFLAGS, $LIB_FUZZING_ENGINE, $OUT directory, gcr.io/oss-fuzz-base/base-builder, libfuzzer, address sanitizer, project.yaml ✅
- Go native fuzzing: func Fuzz*(*testing.F), f.Add(), f.Fuzz(), testing package (NOT OSS-Fuzz infrastructure) ✅
- Python Atheris patterns: import atheris, @atheris.instrument_func, atheris.FuzzedDataProvider, atheris.Setup(), atheris.Fuzz(), compile_python_fuzzer ✅
- Bash build scripts: $CXX/$CXXFLAGS/$LIB_FUZZING_ENGINE variables, static linking (.a files, --disable-shared), seed_corpus.zip ✅
- Rust OSS-Fuzz: FROM gcr.io/oss-fuzz-base/base-builder, language: rust, RUN git clone, WORKDIR, COPY build.sh ✅
- YAML parsing: yaml.safe_load, yaml.load ✅

---

### ✅ pdf - VERIFIED (34 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 01: Added pandas, Python exception handling sources
- Task 02: Added Node.js fs.writeFileSync and Buffer sources
- Task 03: Added Ruby require and def syntax sources
- Task 04: Added Python exception handling source

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ github.com/jsvine/pdfplumber - pdfplumber library (import pdfplumber, extract_text(), extract_tables(), .pages)
- ✅ docs.python.org/3/library/* - Python built-in modules (len, csv, open, os.path)
- ✅ docs.python.org/3/tutorial/errors.html - Python try/except exception handling
- ✅ pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html - Pandas CSV export
- ✅ pdf-lib.js.org - JavaScript pdf-lib library (PDFDocument, addPage, drawText, StandardFonts, embedFont)
- ✅ nodejs.org/api/fs.html - Node.js fs.writeFileSync()
- ✅ nodejs.org/api/buffer.html - Node.js Buffer and Uint8Array
- ✅ github.com/prawnpdf/prawn - Ruby Prawn gem (Prawn::Document.generate)
- ✅ raw.githubusercontent.com/prawnpdf/prawn/master/manual/* - Prawn examples (table, text methods)
- ✅ ruby-doc.org/3.3.6/syntax/* - Ruby syntax (require, def methods)
- ✅ www.reportlab.com/docs/reportlab-userguide.pdf - Python ReportLab anti-patterns (canvas.Canvas, SimpleDocTemplate)
- ✅ pypdf.readthedocs.io/en/stable/* - pypdf library (PdfWriter, merging patterns)
- ✅ python-markdown.github.io/reference/ - Python-Markdown library
- ✅ developer.mozilla.org/en-US/docs/Web/HTML/* - MDN HTML/CSS docs

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- Python PDF libraries: pdfplumber (extract_text, extract_tables, .pages, len(pages)), pypdf (PdfWriter, PdfReader, add_page, merge) ✅
- JavaScript PDF: pdf-lib (PDFDocument, addPage, drawText, StandardFonts, embedFont, Uint8Array, Buffer) ✅
- Ruby PDF: Prawn (require 'prawn', Prawn::Document.generate, table, make_table, text, def) ✅
- Python standard library: csv, pandas, try/except, with open('wb'), os.path.exists, argparse ✅
- HTML/CSS: <!DOCTYPE html>, <html>, <style>, <link rel='stylesheet'> ✅
- Document conversion: markdown.markdown(), markdown.convert() ✅

---

### ✅ prompt-agent - VERIFIED (33 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 01: Added POSIX shell spec for #!/bin/bash shebang
- Task 02: Added Python function definition source for def keyword
- Task 04: Added curl HTTPS/SSL source, chmod restrictive permissions source
- Task 05: Added Python class syntax source, Python def source, OWASP SQL injection patterns, CWE path traversal patterns

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ man7.org/linux/man-pages/man1/* - Linux utilities (find, ls, grep, chmod, stat, set, trap, mktemp) - all user-verified
- ✅ jqlang.github.io/jq/manual/ - jq JSON validation
- ✅ pubs.opengroup.org/onlinepubs/9699919799/utilities/* - POSIX specifications (crontab, shell)
- ✅ docs.python.org/3/* - Python standard library (hashlib, json, argparse, re, classes, functions)
- ✅ man.openbsd.org/sha256 - sha256sum/shasum checksums
- ✅ curl.se/docs/sslcerts.html - HTTPS/SSL for secure downloads
- ✅ httpd.apache.org/docs/current/logs.html - Apache combined log format
- ✅ cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html - OWASP SQL injection patterns
- ✅ cwe.mitre.org/data/definitions/22.html - CWE-22 path traversal (..)

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- Bash scripting: #!/bin/bash, find, ls, grep, jq, chmod/stat permissions, CRITICAL/WARNING/INFO severity levels ✅
- POSIX sh: #!/bin/sh, crontab, cron expressions, $1/$2/${} variables, if [/test, trap signal handling ✅
- Python file integrity: hashlib.sha256, json.dump/dumps, def functions, argparse CLI modes ✅
- Security patterns: HTTPS (https://), mktemp secure temp dirs, shasum/sha256sum checksums, set error handling, trap cleanup, restrictive chmod (600/644/755 not 777) ✅
- Intrusion detection: Python class syntax, re.compile/search regex, SQL injection patterns (UNION SELECT, sqli), directory traversal (../ path), def parse/analyze/detect methods ✅

---

### ✅ provider-resources - VERIFIED (30 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 01: Added Go package/func syntax source
- Task 02: Added Python def syntax source
- Task 03: Added Go testing package source for test function signatures
- Task 05: Added HCL data source and provider block sources; **REMOVED** unverifiable patterns (variable, output, validation blocks) to maintain pattern data quality

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ raw.githubusercontent.com/hashicorp/terraform-provider-scaffolding-framework - Terraform Plugin Framework scaffolding (example_resource.go, example_resource_test.go, resource.tf, data-source.tf, provider.tf all verified)
- ✅ go.dev/doc/code - Go package and func syntax
- ✅ pkg.go.dev/testing - Go testing.T test function signatures (TestXxx pattern)
- ✅ pkg.go.dev/.../resource - Terraform plugin testing helpers (ParallelTest, TestCase, ImportState)
- ✅ www.pulumi.com/docs/concepts/resources/dynamic-providers/ - Pulumi ResourceProvider CRUD methods (create, read, update, delete all documented)
- ✅ docs.python.org/3/tutorial/controlflow.html - Python def keyword

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- Terraform Plugin Framework (Go): framework.ResourceWithConfigure, resource.MetadataRequest, schema.Schema{}, schema.StringAttribute, stringplanmodifier.RequiresReplace, resp.Diagnostics.AddError, resp.State.Set(ctx), req.State.Get(ctx), req.Plan.Get(ctx), resp.State.RemoveResource(ctx) ✅
- Terraform acceptance testing (Go): resource.ParallelTest, resource.TestCase{}, acctest.PreCheck, ProtoV5ProviderFactories, CheckDestroy, ImportState verification, testAccCheck patterns, ExpectNonEmptyPlan ✅
- Pulumi dynamic providers (Python): pulumi import, ResourceProvider/dynamic.Resource, def create/read/update/delete methods ✅
- HCL configuration: resource "..." "..." {}, data "..." "..." {}, provider "..." "..." {} block syntax ✅
- Go language: package, func, test functions (func TestXxx(t *testing.T)) ✅
- Python language: def keyword for function definitions ✅

**Note:** Removed variable, output, and validation patterns from Task 05 due to inability to verify sources (HashiCorp developer docs rate-limited, Terraform repo structure changes). This maintains pattern data quality by only including patterns with verified provenance.

---

### ✅ react-native-best-practices - VERIFIED (32 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 05: Updated react-window source description to accurately reflect verification limitations (TypeScript definitions reference)

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ github.com/Shopify/flash-list - FlashList import, renderItem (estimatedItemSize not in v2 as noted)
- ✅ reactnative.dev/docs/flatlist - FlatList keyExtractor, onRefresh, refreshing, renderItem patterns
- ✅ react.dev/reference/react/* - React memo, useDeferredValue, useCallback, useMemo, lazy, Suspense, useState, useEffect hooks
- ✅ reactnative.dev/docs/stylesheet - StyleSheet.create() pattern
- ✅ developer.apple.com/documentation/uikit/* - UIKit APIs (UICollectionView, compositional layouts, diffable data sources) - **SME-validated by Apple dev**
- ✅ docs.swift.org/swift-book/.../classesandstructures/ - Swift class/func syntax - **SME-validated by Apple dev**
- ✅ developer.android.com/guide/topics/ui/layout/recyclerview - Android RecyclerView with Kotlin examples (class Activity, RecyclerView.Adapter, ViewHolder)
- ✅ developer.android.com/reference/* - Android ListAdapter, DiffUtil.ItemCallback APIs
- ✅ developer.android.com/topic/libraries/view-binding - Android ViewBinding patterns
- ✅ github.com/bvaughn/react-window - react-window library (component names in TypeScript definitions)
- ✅ developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch - MDN Fetch API

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- React Native FlashList: import @shopify/flash-list, FlashList component, renderItem, estimatedItemSize (v1), React.memo, keyExtractor, onRefresh/refreshing ✅
- Swift/UIKit: import UIKit, UICollectionView, UICollectionViewCompositionalLayout, NSCollectionLayoutSection, UICollectionViewDiffableDataSource, NSDiffableDataSourceSnapshot, class inheritance, func declarations ✅
- Kotlin/Android: class Activity/AppCompatActivity, RecyclerView, ListAdapter, RecyclerView.Adapter, DiffUtil.ItemCallback, ViewBinding, fun declarations ✅
- React performance: React.memo, useCallback, useMemo, useDeferredValue/useTransition, StyleSheet.create ✅
- React web virtualization: react-window (FixedSizeList/VariableSizeList), React.lazy, Suspense, useState/useEffect/useCallback, fetch() ✅

---

### ✅ sharp-edges - VERIFIED (23 patterns, all sourced, URLs verified)

**No missing sources** - all patterns already had complete coverage

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ docs.python.org/3/library/* - Python hmac.compare_digest, hashlib algorithms
- ✅ cheatsheetseries.owasp.org/cheatsheets/* - OWASP cheat sheets (Authentication, Session Management, Secure Product Design) for dangerous defaults, pit of success, misuse-resistant design
- ✅ learn.microsoft.com/.../the-pit-of-success - Microsoft original "pit of success" article by Rico Mariani/Brad Abrams
- ✅ www.php.net/manual/en/function.* - PHP functions (sodium_crypto_box, password_hash, hash_equals, hash, setcookie)
- ✅ pkg.go.dev/crypto/* - Go crypto packages (hmac, subtle.ConstantTimeCompare)
- ✅ docs.rs/ring/latest/ring/signature/ - Rust ring signature API with distinct key/signature types
- ✅ docs.rs/ed25519-dalek/latest/ed25519_dalek/ - Rust ed25519 (SigningKey, VerifyingKey, Signature types)
- ✅ cwe.mitre.org/data/definitions/208.html - CWE-208 Observable Timing Discrepancy (timing attacks)
- ✅ www.typescriptlang.org/docs/handbook/2/objects.html - TypeScript interface definitions
- ✅ developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto - JavaScript crypto.subtle API

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- Security analysis patterns: dangerous defaults (max_attempts=0, timeout=0, secureCookies=false), empty key bypass, unvalidated parameters, algorithm validation, pit of success, secure-by-default ✅
- Timing-safe comparison: Python (hmac.compare_digest), Go (subtle.ConstantTimeCompare, hmac.Equal), PHP (hash_equals), timing attack detection ✅
- Rust misuse-resistant API: struct (Signature|SigningKey|VerifyingKey), impl, pub fn (sign|verify), Result<> error handling ✅
- Configuration validation: TypeScript interface Config, throw/Error(), SSL/TLS checks, timeout>0, secret.length validation ✅
- Language-specific crypto: PHP (hash, setcookie, password_hash), Go (crypto/subtle, crypto/hmac), Python (hashlib, hmac), Rust (ring, ed25519-dalek) ✅

---

### ✅ skill-creator - VERIFIED (30 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 01: Added Markdown Guide for ## heading and ``` code block syntax
- Task 02: Added Python def and re module sources for function definitions and regex validation
- Task 05: Added TypeScript async/await documentation

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ agentskills.io/specification.md - Agent Skills spec (YAML frontmatter ---,  name/description fields, validation rules, directory structure, references/)
- ✅ www.markdownguide.org/basic-syntax/ - Markdown ## headers and ``` code blocks
- ✅ docs.python.org/3/* - Python (argparse, PyYAML, def, re module)
- ✅ www.gnu.org/software/bash/manual/bash.html - Bash ($1, mkdir -p, cat <<EOF heredoc) - user verified
- ✅ github.com/archiverjs/node-archiver - archiver library (archive.directory, archive.glob, archive.finalize)
- ✅ www.typescriptlang.org/docs/handbook/* - TypeScript (Promise<T>, async/await)
- ✅ nodejs.org/api/fs.html - Node.js createWriteStream

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- SKILL.md format: YAML frontmatter (---), name: field ([a-z0-9-] pattern), description: field (1-1024 chars), references/ directory, ## headings, ``` code blocks ✅
- Python validation: import argparse/yaml, def functions, re.regex patterns ([a-z0-9] validation), frontmatter parsing ✅
- Bash initialization: #!/bin/bash, mkdir -p, $1/${1} positional params, cat <<EOF heredoc, SKILL.md/references/scripts/ directory creation ✅
- SKILL.md best practices: description includes "when to use", avoid changelog/installation sections, use references/ for long content ✅
- TypeScript archiving: import/require archiver, Promise<number>, createWriteStream, archive.directory/glob/finalize, async/await ✅

---

### ✅ upgrade-stripe - VERIFIED (26 patterns, all sourced, URLs verified)

**Added missing sources:**
- Task 01: Added Python import statement source
- Task 02: Added Go func keyword source
- Task 03: Added Node.js require/module.exports source
- Task 05: Added Ruby class and def method sources

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ docs.stripe.com/api/*.md?lang=* - Stripe API docs with language-specific examples (Python, Node.js, Ruby, Go) for customers, subscriptions, versioning, error handling, webhooks, events
- ✅ raw.githubusercontent.com/stripe/stripe-go/refs/heads/master/README.md - Go stripe-go library (import path, stripe.Key, customer.Get)
- ✅ raw.githubusercontent.com/stripe/stripe-go/refs/heads/master/customer/client.go - Go customer package source code
- ✅ raw.githubusercontent.com/stripe/stripe-node/refs/heads/master/README.md - Node.js Stripe initialization (require, apiVersion)
- ✅ docs.python.org/3/reference/simple_stmts.html#import - Python import statement
- ✅ go.dev/doc/code - Go func keyword
- ✅ nodejs.org/api/modules.html - Node.js require/module.exports
- ✅ ruby-doc.org/3.3.6/syntax/* - Ruby class and def keywords

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- Python Stripe: StripeClient, stripe.api_version=, client.v1.customers.create, client.v1.subscriptions.create, stripe.StripeError/CardError/InvalidRequestError, import stripe ✅
- Go Stripe: github.com/stripe/stripe-go import, stripe.Key=, customer.Get(), func declarations ✅
- JavaScript/Node.js Stripe: require('stripe'), apiVersion: constructor option, stripe.webhooks.constructEvent, req.body, module.exports/export ✅
- API version upgrade: 2024-12-18.acacia → 2026-01-28.clover, js.stripe.com/basil → js.stripe.com/clover ✅
- Ruby Stripe: Stripe::Webhook.construct_event, class definitions, def methods, customer.subscription.* events ✅

---

### ✅ wiki-agents-md - VERIFIED (25 patterns, all sourced, URLs verified + 2 sources corrected)

**Added missing sources:**
- None needed - all patterns had sources

**Fixed inaccurate sources:**
- Task 04: Updated llms.txt source description to accurately reflect that llms-full.txt is an implementation-specific variant, not part of the core specification
- Task 05: Removed solmaz.io migration guide (documented symlink approach, not redirect pattern); Added microsoft/skills deep-wiki command source documenting CLAUDE.md companion generation with directive to read AGENTS.md

**URL Verification:** ✅ All sources verified to exist and contain expected patterns
- ✅ python-poetry.org/docs/cli/ - Poetry CLI commands (poetry install)
- ✅ docs.pytest.org/en/stable/ - pytest test framework
- ✅ github.com/agentsmd/agents.md - AGENTS.md specification
- ✅ doc.rust-lang.org/cargo/commands/* - Cargo commands (build, test, clippy, fmt/rustfmt)
- ✅ pnpm.io/cli/* - pnpm CLI (install, run, test)
- ✅ vitest.dev/guide/ - Vitest test runner
- ✅ nextjs.org/docs/app/getting-started/project-structure - Next.js App Router app/ directory
- ✅ vitepress.dev/guide/getting-started - VitePress commands (dev, build, preview)
- ✅ emersonbottero.github.io/vitepress-plugin-mermaid/ - VitePress Mermaid plugin
- ✅ llmstxt.org/ - llms.txt specification (llms-full.txt is implementation-specific)
- ✅ code.claude.com/docs/en/memory - Claude Code CLAUDE.md documentation
- ✅ raw.githubusercontent.com/microsoft/skills/refs/heads/main/.github/plugins/deep-wiki/commands/generate.md - CLAUDE.md companion pattern (line 114: "a heading, a generated-file comment, and a directive to read AGENTS.md")

**Pattern Verification:** All patterns are required by prompts and have valid sources.
- Python FastAPI AGENTS.md: poetry install, pytest, src/api/ directory references ✅
- Rust AGENTS.md: cargo build/test/clippy/fmt, lib.rs entry point ✅
- TypeScript Next.js AGENTS.md: pnpm install/run/test, vitest, app/ and src/components/ directories ✅
- VitePress wiki AGENTS.md: vitepress dev/build, llms.txt and llms-full.txt files, Mermaid diagrams, onboarding/ directory ✅
- CLAUDE.md companion: CLAUDE.md filename, redirect patterns (read AGENTS.md / follow AGENTS) ✅

---

## Final Status: 20/20 skills complete (100%) ✅

All pattern sources have been verified. The eval framework dataset is now scientifically rigorous with all patterns traceable to verified sources.
