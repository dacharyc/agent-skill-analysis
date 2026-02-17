"""
Configuration and skill registry for behavioral eval system.

Tests whether structural cross-contamination risk scores predict
actual code generation degradation when skills are loaded.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "data" / "skills"
TASKS_DIR = Path(__file__).resolve().parent / "tasks"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
GENERATIONS_DIR = RESULTS_DIR / "generations"
SCORES_DIR = RESULTS_DIR / "scores"
CACHE_DIR = Path(__file__).resolve().parent / ".eval_cache"
FIGURES_DIR = REPO_ROOT / "paper" / "figures"
BEHAVIORAL_OUTPUT = REPO_ROOT / "data" / "processed" / "behavioral-eval.json"

# --- Model configuration ---

MODEL_GENERATION = "claude-sonnet-4-5-20250929"
MODEL_JUDGE = "claude-opus-4-6"
TEMPERATURE = 0.3
RUNS_PER_CONDITION = 3
MAX_GENERATION_TOKENS = 4096
MAX_JUDGE_TOKENS = 1500

# --- Skill registry ---
# Each skill has:
#   path: relative to REPO_ROOT
#   contamination_score: from structural analysis (SKILL.md only)
#   ref_contamination_score: from reference files (if applicable)
#   risk_level: high / medium
#   test_category: what contamination pattern we're testing
#   has_refs: whether the skill has reference files to load
#   hidden_contamination: if True, run 3 conditions (baseline, SKILL-only, SKILL+refs)

SKILLS: dict[str, dict] = {
    # === HIGH-RISK (contamination >= 0.5) ===
    "upgrade-stripe": {
        "path": "data/skills/stripe-skills/skills/upgrade-stripe",
        "contamination_score": 0.93,
        "risk_level": "high",
        "test_category": "multi_sdk",
        "has_refs": False,
        "hidden_contamination": False,
    },
    "sharp-edges": {
        "path": "data/skills/trailofbits-skills/plugins/sharp-edges/skills/sharp-edges",
        "contamination_score": 0.62,
        "risk_level": "high",
        "test_category": "multi_reference",
        "has_refs": True,
        "hidden_contamination": False,
    },
    "claude-settings-audit": {
        "path": "data/skills/sentry-skills/plugins/sentry-skills/skills/claude-settings-audit",
        "contamination_score": 0.63,
        "risk_level": "high",
        "test_category": "high_risk_high_novelty",
        "has_refs": True,
        "hidden_contamination": False,
    },
    "copilot-sdk": {
        "path": "data/skills/microsoft-skills/.github/skills/copilot-sdk",
        "contamination_score": 0.63,
        "risk_level": "high",
        "test_category": "multi_sdk",
        "has_refs": True,
        "hidden_contamination": False,
    },
    "wiki-agents-md": {
        "path": "data/skills/microsoft-skills/.github/plugins/deep-wiki/skills/wiki-agents-md",
        "contamination_score": 0.57,
        "risk_level": "high",
        "test_category": "high_risk_high_novelty",
        "has_refs": True,
        "hidden_contamination": False,
    },
    "gemini-api-dev": {
        "path": "data/skills/google-gemini-skills/skills/gemini-api-dev",
        "contamination_score": 0.55,
        "risk_level": "high",
        "test_category": "multi_lang_api",
        "has_refs": True,
        "hidden_contamination": False,
    },
    "provider-resources": {
        "path": "data/skills/hashicorp-skills/terraform/provider-development/skills/provider-resources",
        "contamination_score": 0.55,
        "risk_level": "high",
        "test_category": "app_to_aux",
        "has_refs": True,
        "hidden_contamination": False,
    },
    "ossfuzz": {
        "path": "data/skills/trailofbits-skills/plugins/testing-handbook-skills/skills/ossfuzz",
        "contamination_score": 0.53,
        "risk_level": "high",
        "test_category": "app_to_app_and_aux",
        "has_refs": True,
        "hidden_contamination": False,
    },
    "azure-identity-java": {
        "path": "data/skills/microsoft-skills/.github/skills/azure-identity-java",
        "contamination_score": 0.52,
        "risk_level": "high",
        "test_category": "sdk_cross_lang",
        "has_refs": True,
        "hidden_contamination": False,
    },
    "azure-security-keyvault-secrets-java": {
        "path": "data/skills/microsoft-skills/.github/skills/azure-security-keyvault-secrets-java",
        "contamination_score": 0.52,
        "risk_level": "high",
        "test_category": "sdk_cross_lang",
        "has_refs": True,
        "hidden_contamination": False,
    },

    # === MEDIUM-RISK (selected for pattern diversity) ===
    "monitoring-observability": {
        "path": "data/skills/devops-skills/monitoring-observability",
        "contamination_score": 0.50,
        "risk_level": "medium",
        "test_category": "app_to_aux",
        "has_refs": True,
        "hidden_contamination": False,
    },
    "skill-creator": {
        "path": "data/skills/anthropic-skills/skills/skill-creator",
        "contamination_score": 0.46,
        "risk_level": "medium",
        "test_category": "meta_skill_high_novelty",
        "has_refs": False,
        "hidden_contamination": False,
    },
    "pdf": {
        "path": "data/skills/anthropic-skills/skills/pdf",
        "contamination_score": 0.33,
        "risk_level": "medium",
        "test_category": "net_negative",
        "has_refs": False,
        "hidden_contamination": False,
    },
    "neon-postgres": {
        "path": "data/skills/neon-skills/skills/neon-postgres",
        "contamination_score": 0.00,
        "ref_contamination_score": 0.83,
        "risk_level": "medium",
        "test_category": "hidden_contamination",
        "has_refs": True,
        "hidden_contamination": True,
    },
    "react-native-best-practices": {
        "path": "data/skills/callstack-skills/skills/react-native-best-practices",
        "contamination_score": 0.075,
        "ref_contamination_score": 1.0,
        "risk_level": "medium",
        "test_category": "hidden_contamination",
        "has_refs": True,
        "hidden_contamination": True,
    },
    "azure-containerregistry-py": {
        "path": "data/skills/microsoft-skills/.github/skills/azure-containerregistry-py",
        "contamination_score": 0.33,
        "risk_level": "medium",
        "test_category": "net_negative",
        "has_refs": True,
        "hidden_contamination": False,
    },
    "azure-identity-dotnet": {
        "path": "data/skills/microsoft-skills/.github/skills/azure-identity-dotnet",
        "contamination_score": 0.33,
        "risk_level": "medium",
        "test_category": "net_negative",
        "has_refs": True,
        "hidden_contamination": False,
    },
    "prompt-agent": {
        "path": "data/skills/clawsec-skills/skills/prompt-agent",
        "contamination_score": 0.48,
        "risk_level": "medium",
        "test_category": "net_negative",
        "has_refs": False,
        "hidden_contamination": False,
    },

    # === NEGATIVE CONTROLS ===
    "fastapi-router-py": {
        "path": "data/skills/microsoft-skills/.github/skills/fastapi-router-py",
        "contamination_score": 0.00,
        "risk_level": "control",
        "test_category": "negative_control_code",
        "has_refs": True,
        "hidden_contamination": False,
    },
    "doc-coauthoring": {
        "path": "data/skills/anthropic-skills/skills/doc-coauthoring",
        "contamination_score": 0.00,
        "risk_level": "control",
        "test_category": "negative_control_noncode",
        "has_refs": False,
        "hidden_contamination": False,
    },

    # === EXPERIMENTAL (partial knowledge hypothesis) ===
    # Synthetic skill variants for testing whether targeted API reference
    # files reduce fabrication. Not included in default eval runs.
    # Level 1: Minimal ground truth — correct class names, signatures, versions.
    "upgrade-stripe-targeted": {
        "path": "eval/synthetic-skills/upgrade-stripe-targeted",
        "contamination_score": 0.93,  # same SKILL.md as upgrade-stripe
        "risk_level": "experimental",
        "test_category": "partial_knowledge",
        "has_refs": True,
        "hidden_contamination": False,
        "experimental": True,  # excluded from default --all runs
    },
    # Level 2: Full SDK docs — tests if extensive examples trigger over-engineering.
    "upgrade-stripe-comprehensive": {
        "path": "eval/synthetic-skills/upgrade-stripe-comprehensive",
        "contamination_score": 0.93,  # same SKILL.md as upgrade-stripe
        "risk_level": "experimental",
        "test_category": "partial_knowledge",
        "has_refs": True,
        "hidden_contamination": False,
        "experimental": True,  # excluded from default --all runs
    },
}


def get_skill_path(skill_name: str) -> Path:
    """Return the absolute path to a skill directory."""
    return REPO_ROOT / SKILLS[skill_name]["path"]


def get_skill_md(skill_name: str) -> str | None:
    """Read and return the SKILL.md content for a skill."""
    skill_dir = get_skill_path(skill_name)
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        return skill_md.read_text()
    return None


def get_skill_refs(skill_name: str) -> list[tuple[str, str]]:
    """Return list of (filename, content) for all reference .md files."""
    skill_dir = get_skill_path(skill_name)
    refs_dir = skill_dir / "references"
    if not refs_dir.exists():
        return []
    refs = []
    for f in sorted(refs_dir.iterdir()):
        if f.suffix == ".md" and f.name != "SKILL.md":
            refs.append((f.name, f.read_text()))
    return refs


def get_skill_content_with_refs(skill_name: str, ref_files: list[str]) -> str | None:
    """Return SKILL.md + only the named reference files concatenated.

    Falls back to full content if ref_files is empty.
    """
    if not ref_files:
        return get_full_skill_content(skill_name)

    skill_md = get_skill_md(skill_name)
    if skill_md is None:
        return None

    skill_dir = get_skill_path(skill_name)
    refs_dir = skill_dir / "references"

    parts = [skill_md]
    for fname in ref_files:
        ref_path = refs_dir / fname
        if ref_path.exists():
            parts.append(f"\n\n---\n\n# Reference: {fname}\n\n{ref_path.read_text()}")
        else:
            print(f"  WARNING: Reference file not found: {fname}", file=__import__('sys').stderr)
    return "\n".join(parts)


def get_full_skill_content(skill_name: str) -> str | None:
    """Return SKILL.md + all reference files concatenated (mimics skill loading)."""
    skill_md = get_skill_md(skill_name)
    if skill_md is None:
        return None

    refs = get_skill_refs(skill_name)
    if not refs:
        return skill_md

    parts = [skill_md]
    for filename, content in refs:
        parts.append(f"\n\n---\n\n# Reference: {filename}\n\n{content}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Condition D: Realistic context simulation
# ---------------------------------------------------------------------------
# In real Claude Code usage, the model sees:
#   1. A large system prompt (CC instructions + tool defs + loaded skills)
#   2. Conversation turns including tool results (file reads, explore agent summaries)
#
# We simulate this by:
#   - Prepending a condensed Claude Code system preamble to the skill system prompt
#   - Injecting a multi-turn conversation with simulated codebase context
#     (explore agent summary + file read) before the actual task prompt

CC_SYSTEM_PREAMBLE = """\
You are Claude Code, an interactive agent that helps users with software engineering tasks.

# Doing tasks
- Read code before modifying it. Understand existing patterns before suggesting changes.
- Prefer editing existing files to creating new ones.
- Be careful not to introduce security vulnerabilities.
- Keep solutions simple and focused. Don't over-engineer.

# Response format
- Respond with code directly. Do not simulate tool calls or emit XML tags.
- When asked to write code, output the code itself, not file-writing commands.

# Environment
- Working directory: /Users/dev/project
- Platform: linux
- Shell: bash
"""

# Language-specific codebase snippets that simulate what an explore agent
# would return + a representative file read. These are generic, idiomatic
# code in the target language — enough to anchor the model in the right
# language context without biasing toward any specific API.
_CODEBASE_SNIPPETS: dict[str, str] = {
    "python": '''# Explore agent summary:
The project is a Python web service using FastAPI with SQLAlchemy for database access.
Key files: src/main.py (app entrypoint), src/models.py (DB models), src/services/ (business logic).
Uses Poetry for dependency management, pytest for testing. Python 3.12.

# File read: src/services/base.py
```python
"""Base service with common patterns used across the application."""
import logging
from typing import TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Base

T = TypeVar("T", bound=Base)
logger = logging.getLogger(__name__)

class BaseService(Generic[T]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, model_class: type[T], id: int) -> T | None:
        result = await self.session.get(model_class, id)
        if result is None:
            logger.warning("Entity %s with id=%d not found", model_class.__name__, id)
        return result

    async def create(self, instance: T) -> T:
        self.session.add(instance)
        await self.session.flush()
        logger.info("Created %s id=%d", type(instance).__name__, instance.id)
        return instance
```''',

    "python_sync": '''# Explore agent summary:
The project is a Python web service using Flask with SQLAlchemy for database access.
Key files: src/app.py (app entrypoint), src/models.py (DB models), src/services/ (business logic).
Uses Poetry for dependency management, pytest for testing. Python 3.12.

# File read: src/services/base.py
```python
"""Base service with common patterns used across the application."""
import logging
from typing import TypeVar, Generic
from sqlalchemy.orm import Session
from src.models import Base

T = TypeVar("T", bound=Base)
logger = logging.getLogger(__name__)

class BaseService(Generic[T]):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, model_class: type[T], id: int) -> T | None:
        result = self.session.get(model_class, id)
        if result is None:
            logger.warning("Entity %s with id=%d not found", model_class.__name__, id)
        return result

    def create(self, instance: T) -> T:
        self.session.add(instance)
        self.session.flush()
        logger.info("Created %s id=%d", type(instance).__name__, instance.id)
        return instance
```''',

    "javascript": '''# Explore agent summary:
The project is a Node.js Express API with MongoDB via Mongoose. Key directories:
src/routes/, src/models/, src/middleware/. Uses ESM imports, Jest for testing. Node 20.

# File read: src/middleware/auth.js
```javascript
import jwt from "jsonwebtoken";
import { User } from "../models/user.js";

export function requireAuth(req, res, next) {
  const token = req.headers.authorization?.split(" ")[1];
  if (!token) {
    return res.status(401).json({ error: "Authentication required" });
  }
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.userId = decoded.sub;
    next();
  } catch (err) {
    return res.status(401).json({ error: "Invalid token" });
  }
}

export async function loadUser(req, res, next) {
  if (req.userId) {
    req.user = await User.findById(req.userId).lean();
  }
  next();
}
```''',

    "typescript": '''# Explore agent summary:
The project is a TypeScript application using React with Next.js. Key directories:
src/app/ (pages), src/components/, src/lib/ (utilities). Uses pnpm, Vitest for testing. TS 5.4.

# File read: src/lib/api-client.ts
```typescript
interface ApiResponse<T> {
  data: T;
  error?: string;
}

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3000/api";

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<ApiResponse<T>> {
  const url = `${BASE_URL}${endpoint}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    return { data: undefined as T, error: body.message ?? response.statusText };
  }
  const data: T = await response.json();
  return { data };
}
```''',

    "go": '''# Explore agent summary:
The project is a Go HTTP service using chi router with PostgreSQL via pgx. Key packages:
cmd/server/ (entrypoint), internal/handler/, internal/store/. Uses Go 1.22, go test for testing.

# File read: internal/store/store.go
```go
package store

import (
\t"context"
\t"fmt"
\t"log/slog"

\t"github.com/jackc/pgx/v5/pgxpool"
)

type Store struct {
\tpool *pgxpool.Pool
}

func New(ctx context.Context, dsn string) (*Store, error) {
\tpool, err := pgxpool.New(ctx, dsn)
\tif err != nil {
\t\treturn nil, fmt.Errorf("connect to database: %w", err)
\t}
\tif err := pool.Ping(ctx); err != nil {
\t\treturn nil, fmt.Errorf("ping database: %w", err)
\t}
\tslog.Info("connected to database")
\treturn &Store{pool: pool}, nil
}

func (s *Store) Close() {
\ts.pool.Close()
}
```''',

    "java": '''# Explore agent summary:
The project is a Java Spring Boot 3 application with JPA/Hibernate. Key packages:
com.example.app.controller, com.example.app.service, com.example.app.model. Uses Maven, JUnit 5. Java 21.

# File read: src/main/java/com/example/app/service/BaseService.java
```java
package com.example.app.service;

import jakarta.persistence.EntityNotFoundException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public abstract class BaseService<T, ID> {
    protected final Logger log = LoggerFactory.getLogger(getClass());
    protected final JpaRepository<T, ID> repository;

    protected BaseService(JpaRepository<T, ID> repository) {
        this.repository = repository;
    }

    public T findById(ID id) {
        return repository.findById(id)
            .orElseThrow(() -> new EntityNotFoundException(
                "Entity not found with id: " + id));
    }

    public T save(T entity) {
        T saved = repository.save(entity);
        log.info("Saved entity: {}", saved);
        return saved;
    }
}
```''',

    "ruby": '''# Explore agent summary:
The project is a Ruby on Rails 7 API application. Key directories:
app/controllers/, app/models/, app/services/. Uses Bundler, RSpec for testing. Ruby 3.3.

# File read: app/services/application_service.rb
```ruby
# frozen_string_literal: true

class ApplicationService
  def self.call(...)
    new(...).call
  end

  private

  def logger
    @logger ||= Rails.logger
  end

  def with_error_handling
    yield
  rescue ActiveRecord::RecordNotFound => e
    logger.warn("Record not found: #{e.message}")
    ServiceResult.failure(error: :not_found, message: e.message)
  rescue ActiveRecord::RecordInvalid => e
    logger.warn("Validation failed: #{e.message}")
    ServiceResult.failure(error: :validation, message: e.message)
  rescue StandardError => e
    logger.error("Unexpected error: #{e.class} - #{e.message}")
    raise
  end
end
```''',

    "csharp": '''# Explore agent summary:
The project is a C# ASP.NET Core 8 Web API. Key directories:
Controllers/, Services/, Models/. Uses .NET 8, xUnit for testing.

# File read: Services/BaseService.cs
```csharp
using Microsoft.Extensions.Logging;

namespace App.Services;

public abstract class BaseService<T> where T : class
{
    protected readonly ILogger Logger;
    protected readonly AppDbContext DbContext;

    protected BaseService(AppDbContext dbContext, ILogger logger)
    {
        DbContext = dbContext;
        Logger = logger;
    }

    public async Task<T?> GetByIdAsync(int id)
    {
        var entity = await DbContext.Set<T>().FindAsync(id);
        if (entity is null)
        {
            Logger.LogWarning("Entity {Type} with id {Id} not found", typeof(T).Name, id);
        }
        return entity;
    }

    public async Task<T> CreateAsync(T entity)
    {
        DbContext.Set<T>().Add(entity);
        await DbContext.SaveChangesAsync();
        Logger.LogInformation("Created {Type}", typeof(T).Name);
        return entity;
    }
}
```''',

    "rust": '''# Explore agent summary:
The project is a Rust web service using Axum with SQLx for PostgreSQL. Key modules:
src/main.rs, src/handlers/, src/models/, src/db/. Uses cargo, tokio runtime. Rust 1.77.

# File read: src/db/mod.rs
```rust
use sqlx::PgPool;
use tracing::{info, warn};

pub struct Database {
    pool: PgPool,
}

impl Database {
    pub async fn connect(database_url: &str) -> anyhow::Result<Self> {
        let pool = PgPool::connect(database_url).await?;
        info!("Connected to database");
        Ok(Self { pool })
    }

    pub async fn get_by_id<T>(&self, id: i64) -> anyhow::Result<Option<T>>
    where
        T: for<\'r> sqlx::FromRow<\'r, sqlx::postgres::PgRow> + Send + Unpin,
    {
        let result = sqlx::query_as::<_, T>("SELECT * FROM items WHERE id = $1")
            .bind(id)
            .fetch_optional(&self.pool)
            .await?;
        if result.is_none() {
            warn!(id, "Entity not found");
        }
        Ok(result)
    }
}
```''',

    "kotlin": '''# Explore agent summary:
The project is a Kotlin Android app using Jetpack Compose, Hilt for DI, and Room for local DB.
Key packages: ui/, data/, domain/. Uses Gradle with KTS, JUnit 5. Kotlin 2.0.

# File read: data/repository/BaseRepository.kt
```kotlin
package com.example.app.data.repository

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import timber.log.Timber

abstract class BaseRepository {
    protected fun <T> safeApiCall(call: suspend () -> T): Flow<Result<T>> = flow {
        try {
            val result = call()
            emit(Result.success(result))
        } catch (e: Exception) {
            Timber.e(e, "API call failed")
            emit(Result.failure(e))
        }
    }
}
```''',

    "swift": '''# Explore agent summary:
The project is a Swift iOS app using SwiftUI with Combine. Key groups:
Views/, ViewModels/, Services/, Models/. Uses SPM, XCTest. Swift 5.10.

# File read: Services/NetworkService.swift
```swift
import Foundation
import Combine

final class NetworkService {
    static let shared = NetworkService()
    private let session: URLSession

    private init(session: URLSession = .shared) {
        self.session = session
    }

    func request<T: Decodable>(_ endpoint: Endpoint) -> AnyPublisher<T, Error> {
        guard let url = endpoint.url else {
            return Fail(error: URLError(.badURL)).eraseToAnyPublisher()
        }
        return session.dataTaskPublisher(for: url)
            .map(\\.data)
            .decode(type: T.self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }
}
```''',

    "cpp": '''# Explore agent summary:
The project is a C++ application using CMake build system. Key directories:
src/, include/, tests/. Uses C++20, Google Test for testing.

# File read: src/utils/logger.h
```cpp
#pragma once

#include <iostream>
#include <string>
#include <format>

namespace utils {

enum class LogLevel { Debug, Info, Warning, Error };

class Logger {
public:
    static Logger& instance() {
        static Logger logger;
        return logger;
    }

    template<typename... Args>
    void log(LogLevel level, std::format_string<Args...> fmt, Args&&... args) {
        if (level >= min_level_) {
            std::cerr << level_prefix(level)
                      << std::format(fmt, std::forward<Args>(args)...)
                      << std::endl;
        }
    }

private:
    LogLevel min_level_ = LogLevel::Info;

    static std::string level_prefix(LogLevel level) {
        switch (level) {
            case LogLevel::Debug:   return "[DEBUG] ";
            case LogLevel::Info:    return "[INFO] ";
            case LogLevel::Warning: return "[WARN] ";
            case LogLevel::Error:   return "[ERROR] ";
        }
        return "";
    }
};

} // namespace utils
```''',

    "php": '''# Explore agent summary:
The project is a PHP Laravel 11 application. Key directories:
app/Http/Controllers/, app/Models/, app/Services/. Uses Composer, PHPUnit. PHP 8.3.

# File read: app/Services/BaseService.php
```php
<?php

namespace App\\Services;

use Illuminate\\Database\\Eloquent\\Model;
use Illuminate\\Support\\Facades\\Log;

abstract class BaseService
{
    public function findOrFail(string $modelClass, int $id): Model
    {
        $instance = $modelClass::find($id);
        if ($instance === null) {
            Log::warning("Entity {$modelClass} with id {$id} not found");
            throw new \\RuntimeException("Entity not found: {$id}");
        }
        return $instance;
    }

    public function create(string $modelClass, array $attributes): Model
    {
        $instance = $modelClass::create($attributes);
        Log::info("Created " . class_basename($modelClass) . " id={$instance->id}");
        return $instance;
    }
}
```''',
}

# Fallback for languages without a specific snippet (markdown, yaml, bash, etc.)
_GENERIC_CODEBASE_SNIPPET = '''# Explore agent summary:
The project is a multi-file codebase with configuration, scripts, and documentation.
Key directories: src/, config/, scripts/, docs/. Uses standard tooling for the ecosystem.

# File read: README.md
The project follows conventional structure with source code in src/, configuration in config/,
and automation scripts in scripts/. See docs/ for architecture decisions.'''


def get_codebase_context(target_language: str, variant: str | None = None) -> str:
    """Return a representative codebase snippet for the target language.

    Simulates what an explore agent would return plus a file read — enough to
    anchor the model in the correct language context without biasing toward
    any specific API under test.

    Args:
        target_language: The target language key (e.g. "python", "go").
        variant: Optional override key into _CODEBASE_SNIPPETS (e.g.
            "python_sync"). When set, used instead of target_language.
    """
    key = variant or target_language
    return _CODEBASE_SNIPPETS.get(key, _GENERIC_CODEBASE_SNIPPET)


def build_realistic_system(skill_content: str) -> str:
    """Build a system prompt that mimics real Claude Code: CC preamble + skill."""
    return f"{CC_SYSTEM_PREAMBLE}\n\n---\n\n{skill_content}"


def build_realistic_messages(
    task_prompt: str,
    target_language: str,
    codebase_variant: str | None = None,
) -> list[dict]:
    """Build a multi-turn message list simulating a real Claude Code session.

    The conversation simulates:
      1. User asks to work on the project
      2. Assistant acknowledges and reports explore agent / file read results
      3. User provides the actual task prompt

    This places codebase context in the conversation history (as it would appear
    from tool results) rather than in the system prompt.

    Args:
        task_prompt: The user's task prompt.
        target_language: The target language key.
        codebase_variant: Optional override for the codebase snippet key
            (e.g. "python_sync"). Passed through to get_codebase_context().
    """
    codebase_ctx = get_codebase_context(target_language, variant=codebase_variant)
    return [
        {
            "role": "user",
            "content": "I need help with a task in this project. Let me know when you've looked around.",
        },
        {
            "role": "assistant",
            "content": (
                f"I've explored the project structure and read some key files. "
                f"Here's what I found:\n\n{codebase_ctx}\n\n"
                f"I'm ready to help. What do you need?"
            ),
        },
        {
            "role": "user",
            "content": task_prompt,
        },
    ]
