
# Repository Structure Standards

## Khi Nào Dùng

- Tạo repository mới cần chuẩn hóa từ đầu
- Setup CI/CD với GitHub Actions (lint, test, release)
- Cấu hình pre-commit hooks cho project
- Setup python-semantic-release cho automated versioning
- Chuẩn hóa repo hiện có (mise, linting, CODEOWNERS)

> **Test Coverage**: ≥ 95% cho tất cả CI/CD workflows và automation scripts.

## Base Structure (All Languages)

```
project/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md               # Bug report template
│   │   └── feature_request.md          # Feature request template
│   ├── PULL_REQUEST_TEMPLATE.md        # PR template (Conventional Commits checklist)
│   ├── workflows/
│   │   ├── ci.yml                      # Lint + Test + PR Title Check + AI PR Review + Email Notify
│   │   └── cd.yml                      # Release + Build + Deploy (workflow_dispatch)
│   ├── rulesets/                        # Exported rulesets (for reference)
│   │   └── main.json
│   ├── best_practices.md                # Custom prompt/coding standards cho Qodo Merge
│   └── CODEOWNERS
├── .infisical.json                      # Infisical project link (KHONG gitignore)
├── .pr_agent.toml                       # Qodo Merge config (model, fallback)
├── .mise.toml                           # Tool versions (thay thế asdf)
├── .pre-commit-config.yaml              # Pre-commit hooks
├── AGENTS.md                            # AI assistant instructions (public repos)
├── CHANGELOG.md                         # Auto-generated bởi python-semantic-release
├── CODE_OF_CONDUCT.md                   # Contributor Covenant (public repos)
├── CONTRIBUTING.md                      # Contribution guidelines (public repos)
├── LICENSE
├── README.md
└── SECURITY.md                          # Security policy (public repos)
```

> **Public repos**: AGENTS.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md là **BẮT BUỘC**. Private repos: không cần.
> **PSR config**: Python repos dùng `[tool.semantic_release]` trong `pyproject.toml`. Non-Python repos dùng `semantic-release.toml` (standalone).
> **Templates**: Issue/PR templates là **BẮT BUỘC** cho tất cả repos. PR template generic (không chứa repo-specific test commands).
> **Infisical**: `.infisical.json` **PHẢI** được commit (KHÔNG gitignore). Chỉ chứa `workspaceId` (không nhạy cảm). Tất cả secrets qua Infisical (auto-sync → GitHub), KHÔNG dùng `gh secret set` trực tiếp.

---

## README Format

**Cấu trúc bắt buộc**: Title → Bold one-liner → 2-row badges → Content.

```markdown
# Project Name

**Bold one-liner mô tả project.**

[![CI](...)][ci] [![codecov](...)][codecov] [![PyPI](...)][pypi] [![License](...)][license]

[![Python](...)](#) [![Framework](...)](#) [![semantic-release](...)][psr] [![Renovate](...)][renovate]
```

| Row | Badges | Ghi chú |
|-----|--------|---------|
| **Row 1** | CI status + Codecov + PyPI/Docker (nếu có) + License | Status badges |
| **Row 2** | Tech stack shields + semantic-release + Renovate | Tech info badges |

> **Codecov badge token**: `?token=XXX` trong URL badge là **graph token** (read-only, public-safe). KHÔNG cần set GitHub Secret cho badge. `CODECOV_TOKEN` trong CI action là upload token — đó mới cần secret.
> **License badge**: Dùng `img.shields.io/github/license/org/repo` (dynamic từ repo) thay vì hardcode màu.
> **No PyPI/Docker badge**: Nếu project không publish PyPI hoặc Docker Hub thì bỏ qua — không force badge không liên quan.

---

## GitHub Repo Settings (via API)

> **Nguyên tắc**: Description, topics, và rulesets phải được set qua `gh api` / `gh repo edit`. File trong repo (`.github/rulesets/main.json`) chỉ là reference — không tự apply lên GitHub.

```bash
# Set description + homepage
gh repo edit --description "Bold one-liner description" --homepage "https://pypi.org/project/xxx"

# Set topics (replace all)
gh api -X PUT repos/{owner}/{repo}/topics \
  -f names[]="python" -f names[]="mcp" -f names[]="ai"

# Apply ruleset (sau khi repo tạo xong)
gh api repos/{owner}/{repo}/rulesets --method POST \
  --input .github/rulesets/main.json
```

> Ruleset trong `.github/rulesets/main.json` là **exported reference** — để version control. Ruleset thực tế trên GitHub cần apply riêng.

---

## Git Branching Strategy

```
main                  ◄── Squash merge từ feature branches (1 approval + code owner)
    │                     Release thủ công qua workflow_dispatch (beta hoặc stable)
    │  PR (squash only)
    │
feature/*             ◄── Development work → PR to main
```

| Branch | Purpose | PR Approvals | Merge Method | Release |
|--------|---------|--------------|--------------|-------|
| `main` | Trunk (duy nhất) | 1 + Code Owner | Squash only | workflow_dispatch: beta hoặc stable |
| `feature/*` | Development | - | PR to `main` | - |

> **Không dùng `dev` branch**. Release được trigger **thủ công** qua `workflow_dispatch` với lựa chọn `beta` hoặc `stable`. python-semantic-release (PSR) v10 xử lý version bump, changelog, tag, và GitHub Release.

### Commit Message Guidelines

> **Nguyên tắc**: Commit message là nguồn duy nhất cho CHANGELOG (python-semantic-release). Sai commit = sai changelog = sai release notes.

| Quy tắc | Sai | Đúng |
|---------|-----|------|
| **Atomic commits** — 1 logic change / commit | `feat: overhaul search + add GitHub fallback + clean content` (3 changes) | Tách thành 3 commits riêng biệt |
| **Đúng type** — `feat/fix` nếu ảnh hưởng user | `refactor: remove stop words` (thay đổi search behavior) | `fix: remove language-specific stop words for better multilingual support` |
| **Mô tả đầy đủ** — message phải phản ánh ALL changes | `feat: add GitHub raw markdown` (bỏ sót BM25, RRF, quality scoring) | `feat: add GitHub raw markdown fallback for docs indexing` (chỉ 1 change) |
| **Không mâu thuẫn** — commit B undo commit A | `feat: add stop words` → `refactor: remove stop words` | Squash thành 1 commit, hoặc dùng `fix:` cho commit B |

**Hidden types** (`refactor`, `chore`, `style`, `test`, `build`, `ci`) **KHÔNG xuất hiện** trong CHANGELOG. Nếu thay đổi ảnh hưởng tới user-facing behavior, **BẮT BUỘC** dùng `feat:`, `fix:`, hoặc `perf:`.

### Commit Enforcement (feat/fix only)

> **Nguyên tắc**: Enforce commit message prefix bằng `commit-msg` hook (pre-commit). Chỉ cho phép `feat:`, `fix:`, và `chore(release):` (auto-generated bởi PSR).

**Script**: `scripts/enforce-commit.sh`

```bash
#!/usr/bin/env bash
MSG=$(head -1 "$1")
if [[ "$MSG" =~ ^(feat|fix)(\(.+\))?:.+ ]] || [[ "$MSG" =~ ^chore\(release\):.+ ]]; then
  exit 0
fi
echo "ERROR: Commit blocked. Only 'feat:' and 'fix:' prefixes allowed."
echo "Got: $MSG"
exit 1
```

**Pre-commit config** (thêm vào `.pre-commit-config.yaml`):

```yaml
  # Commit message stage — chạy với --hook-type commit-msg
  - repo: local
    hooks:
      - id: enforce-commit
        name: Enforce feat and fix commit prefixes
        entry: bash scripts/enforce-commit.sh
        language: system
        stages: [commit-msg]
```

**Setup task** cần cài cả `commit-msg` hook:

```toml
# Trong .mise.toml setup task, thêm dòng này sau "uv run pre-commit install":
"uv run pre-commit install --hook-type commit-msg",
```

> **Lưu ý**: `chore(release):` được exempt vì PSR tự tạo commit này khi bump version.

### Branch Rules (Main Ruleset)
- **Linear History**: Bắt buộc
- **No Force Push**: Non-fast-forward bị block
- **No Deletion**: Protected branches không thể xóa
- **Pull Request**: 1 approval, dismiss stale reviews, code owner review
- **Merge Methods**: Squash only
- **Code Scanning**: CodeQL (high_or_higher)

### Repository Ruleset Bypass

> [!NOTE]
> PSR cần push commit (version bump + CHANGELOG) và tag trực tiếp lên `main`.
> `GH_PAT` (admin) bypass được ruleset. `GITHUB_TOKEN` **KHÔNG** bypass được.

**Bypass list**: Repository admin
**Mode**: Always allow
**Mục đích**: Cho phép PSR (chạy với `GH_PAT`) push version commit + tag lên `main`.

---

## Dev Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  TRƯỚC DEV (one-time)                                       │
│  $ mise run setup                                           │
│  → Install tools → Install deps → Install pre-commit hooks │
├─────────────────────────────────────────────────────────────┤
│  TRONG DEV                                                  │
│  $ mise run dev          # Run dev server                   │
│  $ mise run fix          # Auto-fix lint + format           │
│  $ git commit            # Pre-commit hooks tự động chạy   │
├─────────────────────────────────────────────────────────────┤
│  SAU DEV - Bước 1: CI                                       │
│  PR → main → CI workflow (lint + test) → Code Review → Merge│
│  Pre-commit hooks = subset của CI checks (local gate)       │
├─────────────────────────────────────────────────────────────┤
│  SAU DEV - Bước 2: CD (thủ công)                            │
│  workflow_dispatch → chọn beta/stable → PSR version bump    │
│  → tag → GitHub Release → publish/deploy                    │
└─────────────────────────────────────────────────────────────┘
```

### Quan hệ giữa mise tasks, pre-commit, và CI

| Check | `mise run fix` | Pre-commit | `mise run lint` | CI |
|-------|:-:|:-:|:-:|:-:|
| Lint (auto-fix) | x | x | | |
| Format (auto-fix) | x | x | | |
| Lint (read-only) | | | x | x |
| Format (read-only) | | | x | x |
| Type check | | x | x | x |
| Tests | | x | x | x |
| Build | | | | x |
| Dependency review | | | | x |

---

## mise.toml (Tool Version Manager)

> **Nguyên tắc**: mise quản lý **language runtimes** và **package managers**. Linter/formatter versions do package manager quản lý (uv, bun, go modules).

```toml
[tools]
# Language runtimes
python = "3.13"    # Pin minor (breaking changes between minors)
node = "24"        # Pin major (ESM/CJS, API changes)
go = "latest"      # Go 1 compat promise, go.mod is minimum
rust = "latest"    # Edition system handles breaking changes

# Package managers (latest)
uv = "latest"
bun = "latest"

# CLI tools (latest, chỉ thêm khi cần)
# github-cli = "latest"
# infisical = "latest"
# doppler = "latest"
# wrangler = "latest"
# golangci-lint = "latest"   # Go: external tool, không có trong go modules
```

> **Version Policy**: Python/Node pin minor (3.13, 24) — breaking changes giữa các version. Go/Rust dùng `latest` — backward-compatible (go.mod `go` directive / rust-toolchain.toml `edition` là đủ). Các tool khác: latest.
> **Linter tools**: `ruff`, `ty` qua `uv run` (dev deps). `biome` qua `bunx` (devDeps). `golangci-lint` qua mise (external). `cargo fmt`/`clippy` built-in Rust toolchain.

### Standardized Tasks

Mỗi repo **BẮT BUỘC** có 4 tasks: `setup`, `lint`, `test`, `fix`. Task `dev` tùy chọn.

| Task | Mục đích | Khi nào chạy |
|------|----------|-------------|
| `setup` | First-time dev environment | `git clone` xong |
| `lint` | Read-only checks (lint + format check + type check) | Trước commit, CI |
| `test` | Run tests | Trước PR, CI |
| `fix` | Auto-fix (lint fix + format) | Trong dev |
| `dev` | Run dev server | Trong dev |

#### Setup Task Pattern

> **Description**: Luôn là `"Setup development environment"` (tiếng Anh).
> **Pattern chung**: `mise install` → Clean venv → Install deps → Project-specific → Pre-commit → Done.
> **Thứ tự quan trọng**: `clean-venv.mjs` chạy **TRƯỚC** `uv sync` (tránh xóa deps vừa cài).
> **Pre-commit**: Luôn là bước **CUỐI CÙNG** trước `echo`.
> **Monorepo `cd` pattern**: Mỗi element trong `run` array chạy từ **project root** → **KHÔNG cần** `cd ../..` cuối dòng.
> **Monorepo pre-commit**: `.venv` nằm trong `apps/api/` → phải `cd apps/api` khi cài pre-commit.

```toml
[tasks.setup]
description = "Setup development environment"
run = [
  # Phase 1: Install tool versions
  "mise install",
  # Phase 2: Clean venv (nếu có) — TRƯỚC install deps
  "node scripts/clean-venv.mjs",
  # Phase 3: Install language dependencies
  "<uv sync / bun install / go mod download>",
  # Phase 4: Project-specific (download binaries, etc.)
  # ...
  # Phase 5: Pre-commit (LUÔN CUỐI CÙNG)
  "uv pip install pre-commit",
  "uv run pre-commit install",
  "uv run pre-commit install --hook-type commit-msg",
  # Done
  "echo 'Setup complete!'"
]
```

**Python single repo:**
```toml
[tasks.setup]
description = "Setup development environment"
run = [
  "mise install",
  "node scripts/clean-venv.mjs",     # nếu có, TRƯỚC uv sync
  "uv sync --group dev",
  "uv pip install pre-commit",
  "uv run pre-commit install",
  "uv run pre-commit install --hook-type commit-msg",
  "echo 'Setup complete!'"
]
```

**TypeScript single repo:**
```toml
[tasks.setup]
description = "Setup development environment"
run = [
  "mise install",
  "bun install",
  "node scripts/clean-venv.mjs",     # clean venv cho pre-commit
  "uv pip install pre-commit",
  "uv run pre-commit install",
  "uv run pre-commit install --hook-type commit-msg",
  "echo 'Setup complete!'"
]
```

**Monorepo (Python/Go + TypeScript):**
```toml
[tasks.setup]
description = "Setup development environment"
run = [
  "mise install",
  # Clean venv TRƯỚC install deps
  "node scripts/clean-venv.mjs apps/api",
  # Backend deps
  "cd apps/api && <backend-install-deps>",
  # Frontend deps
  "cd apps/web && bun install",
  # Pre-commit — cd vào dir có .venv
  "cd apps/api && uv pip install pre-commit",
  "cd apps/api && uv run pre-commit install",
  "cd apps/api && uv run pre-commit install --hook-type commit-msg",
  "echo 'Setup complete!'"
]
```

> **Lưu ý monorepo**: `cd apps/api && go mod download` — KHÔNG thêm `&& cd ../..` vì element tiếp theo tự động chạy từ project root.

#### Python repos

```toml
[tasks.lint]
description = "Run all quality checks (ruff + ty)"
run = [
  "uv run ruff check .",
  "uv run ruff format --check .",
  "uv run ty check",
]

[tasks.test]
description = "Run tests"
run = "uv run pytest"

[tasks.fix]
description = "Auto-fix formatting and linting issues"
run = [
  "uv run ruff check --fix .",
  "uv run ruff format .",
]
```

#### TypeScript repos

```toml
[tasks.lint]
description = "Run all quality checks (biome + tsc)"
run = "bun run check"
# package.json: "check": "biome check . && bun run type-check"

[tasks.test]
description = "Run tests"
run = "bun test"

[tasks.fix]
description = "Auto-fix formatting and linting issues"
run = "bun run check:fix"
# package.json: "check:fix": "biome check --write . && bun run type-check"
```

#### Go repos

```toml
[tasks.lint]
description = "Run all quality checks (golangci-lint + gofumpt)"
run = [
  "cd apps/api && golangci-lint run",
  "cd apps/api && test -z \"$(gofumpt -l cmd internal)\" || { gofumpt -l cmd internal; exit 1; }",
]

[tasks.test]
description = "Run tests"
run = "cd apps/api && go test ./..."

[tasks.fix]
description = "Auto-fix formatting issues"
run = "cd apps/api && gofumpt -w cmd internal"
```

#### Rust + TypeScript (Tauri) repos

```toml
[tasks.lint]
description = "Run all quality checks"
run = [
  "cargo fmt --all -- --check",
  "cargo clippy -p <core-crate> -- -D warnings",
  "cd apps/web && bun run typecheck && bun run lint",
]

[tasks.test]
description = "Run tests"
run = "cargo test -p <core-crate>"

[tasks.fix]
description = "Auto-fix formatting issues"
run = [
  "cargo fmt --all",
  "cd apps/web && bunx biome check --write .",
]
```

#### Monorepo (Python + TypeScript / Go + TypeScript)

```toml
[tasks.lint]
description = "Run all quality checks"
run = [
  # Backend
  "cd apps/api && <backend-lint-commands>",
  # Frontend
  "cd apps/web && bun run lint && bun run type-check",
]

[tasks.test]
description = "Run tests"
run = [
  "cd apps/api && <backend-test-command>",
]

[tasks.fix]
description = "Auto-fix formatting issues"
run = [
  "cd apps/api && <backend-fix-commands>",
  "cd apps/web && bun run format",
]
```

---

## python-semantic-release (PSR) v10

> **Nguyên tắc**: Automated release với [python-semantic-release/python-semantic-release@v10](https://github.com/python-semantic-release/python-semantic-release).
> Trigger thủ công qua `workflow_dispatch` → PSR phân tích commits → bump version → update CHANGELOG + version files → commit + tag → GitHub Release.
> Beta release: `--as-prerelease --prerelease-token beta` → version `X.Y.Z-beta.N`.
> Stable release: không có flag → version `X.Y.Z`.

**Chi tiết config, monorepo, per-language setup** → xem [references/semantic-release-guide.md](references/semantic-release-guide.md)

---

## Pre-commit Config

> **Nguyên tắc**: Pre-commit = **local gate** trước commit. Chạy **auto-fix** (lint fix + format), **type check**, và **tests**.
> Pre-commit hooks là **subset** của CI checks — không chạy build hay dependency review.

### Common Hooks (BẮT BUỘC cho tất cả repos)

```yaml
  # ============================================================================
  # Common Checks
  # ============================================================================
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
        name: trim trailing whitespace
        exclude_types: [image]
      - id: check-merge-conflict
        name: check for merge conflicts
      - id: check-json
        name: check JSON files
        types: [json]
      - id: check-yaml
        name: check YAML files
        types: [yaml]
      - id: check-toml
        name: check TOML files
        types: [toml]
      - id: end-of-file-fixer
        name: fix end of files
        exclude_types: [image]
```

> **Lưu ý**: Gộp TẤT CẢ common hooks vào **MỘT block** duy nhất. KHÔNG tách thành nhiều `repo:` entries.
> Monorepo: thêm `files: ^apps/` để scope hooks vào thư mục apps.

### Python

```yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.6
    hooks:
      - id: ruff
        name: ruff lint
        args: [--fix, --target-version=py313]
      - id: ruff-format
        name: ruff format

  - repo: local
    hooks:
      - id: ty
        name: ty type check
        entry: uv run ty check
        language: system
        types: [python]
        pass_filenames: false

      - id: pytest
        name: pytest
        entry: uv run pytest --tb=short -q
        language: system
        types: [python]
        pass_filenames: false
```

### TypeScript

```yaml
  - repo: local
    hooks:
      - id: biome
        name: biome check
        entry: bunx biome check --write
        language: system
        types_or: [javascript, ts, tsx, jsx, json]

      - id: typescript-check
        name: typescript type check
        entry: bunx tsc --noEmit
        language: system
        types: [ts, tsx]
        pass_filenames: false

      - id: test
        name: test
        entry: bun test
        language: system
        types: [ts, tsx]
        pass_filenames: false
```

### Go

```yaml
  - repo: local
    hooks:
      - id: golangci-lint
        name: golangci-lint
        entry: sh -c "cd apps/api && golangci-lint run"
        language: system
        files: \.go$
        pass_filenames: false

      - id: gofumpt
        name: gofumpt
        entry: sh -c "cd apps/api && gofumpt -w cmd internal"
        language: system
        files: \.go$
        pass_filenames: false

      - id: go-test
        name: go test
        entry: sh -c "cd apps/api && go test ./..."
        language: system
        files: \.go$
        pass_filenames: false
```

### Rust

```yaml
  - repo: local
    hooks:
      - id: cargo-fmt
        name: cargo fmt
        entry: cargo fmt --all --
        language: system
        types: [rust]
        pass_filenames: false

      - id: cargo-clippy
        name: cargo clippy
        entry: cargo clippy -p <core-crate> -- -D warnings
        language: system
        types: [rust]
        pass_filenames: false

      - id: cargo-test
        name: cargo test
        entry: cargo test -p <core-crate>
        language: system
        types: [rust]
        pass_filenames: false
```

---

## GitHub Workflows (CI/CD)

> **Nguyên tắc**: CI dùng **specialized GitHub Actions** (setup-uv, setup-bun, setup-go, rust-toolchain). KHÔNG dùng mise-action — mise-action install TẤT CẢ tools trong `.mise.toml` (Python + Node + Go + Rust) dù CI job chỉ cần 1 language, gây chậm pipeline và cache miss. Specialized actions chỉ install đúng tool cần cho job đó.
> CI checks = **superset** của pre-commit: lint + format + type check + tests + build + dependency review.

| Workflow | File | Trigger | Content |
|----------|------|---------|---------|
| CI | `ci.yml` | PR, push to main, issue_comment, workflow_dispatch, issues | PR title check, commit message check, lint, test, build, dependency-review, Qodo Merge AI PR Review, email notify |
| CD | `cd.yml` | workflow_dispatch (manual) | PSR version bump, publish, deploy |

> `dependency-review-action` chỉ hoạt động trên **public repos**. Với private repos, thêm `continue-on-error: true`.
> **`uv sync`** trong CI (không `--locked`). **`uv sync --frozen`** trong Dockerfile.

### AI PR Review (Qodo Merge)

- AI PR Review is handled by **Qodo Merge (qodo-ai/pr-agent)** using Bring Your Own Key (BYOK) architecture via GitHub Actions in `ci.yml`.
- We use a `.pr_agent.toml` file at the root to configure models and bot filtering:
  ```toml
  [config]
  model = "gemini/gemini-3-flash-preview"
  fallback_models = ["gemini/gemini-2.5-flash"]
  ignore_pr_authors = ["^(?!n24q02m$)"]
  ```
- `ignore_pr_authors` uses negative lookahead regex to ONLY allow PRs from `n24q02m`. All bot PRs (Jules, Renovate, Dependabot, etc.) are automatically ignored by Qodo.
- Custom prompt/coding standards are placed in `.github/best_practices.md` and loaded dynamically into Qodo's env vars during the Action step.
- The Action triggers on `pull_request` and `issue_comment`, with 3-layer filtering:
  - `issue_comment`: only for non-Bot senders
  - `pull_request`: only for non-Bot senders AND PRs NOT authored by `n24q02m` (skip AI review on own PRs to save runner minutes)
  - Qodo-level: `ignore_pr_authors` regex as final filter

**Templates CI/CD, Rulesets, CODEOWNERS** → xem [references/ci-cd-workflows.md](references/ci-cd-workflows.md)

---

## MCP Server Env Vars

> **Nguyên tắc**: MCP server env vars cấu hình trong **MCP client config** (`"env": {...}` trong jsonc), KHÔNG dùng `.env` files. Pydantic Settings trong `config.py` đọc từ env vars do client inject.

```jsonc
// claude_desktop_config.json / opencode config
{
  "mcpServers": {
    "my-mcp": {
      "command": "uvx",
      "args": ["my-mcp"],
      "env": {
        "DATABASE_PATH": "~/.my-mcp/data.db",
        "LITELLM_API_KEY": "sk-xxx",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

> MCP server không cần `.env` file, không cần `.env.example`. Secrets đi trong client config, không trong repo.

---

## Docker Build

> **Nguyên tắc**: Dockerfile phải dùng multi-stage build, BuildKit cache, non-root user, và `.dockerignore`.
> Chi tiết bảo mật Docker → xem skill `security-practices`.

### Cấu trúc file Docker

```
project/
├── Dockerfile
├── .dockerignore           # BẮT BUỘC — giảm build context
└── docker-compose.yml      # Tùy chọn — cho local dev
```

### Dockerfile Templates

#### Python (uv)

```dockerfile
# syntax=docker/dockerfile:1

# ========================
# Stage 1: Builder
# ========================
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Cài dependencies trước (cached khi deps không đổi)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy code và cài project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ========================
# Stage 2: Runtime
# ========================
FROM python:3.13-slim-bookworm

WORKDIR /app

# Copy virtual environment từ builder
COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -m appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["python", "-m", "package_name"]
```

#### Node.js (bun)

```dockerfile
# syntax=docker/dockerfile:1

FROM oven/bun:alpine AS builder
WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .
RUN bun run build

# Runtime
FROM oven/bun:alpine
WORKDIR /app

COPY --from=builder /app/build ./build
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

ENV NODE_ENV=production
USER bun

CMD ["bun", "run", "build/index.js"]
```

#### Go

```dockerfile
# syntax=docker/dockerfile:1

FROM golang:1-alpine AS builder
WORKDIR /build

COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

COPY . .
ARG TARGETARCH
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux GOARCH=$TARGETARCH go build -o /out/app ./cmd/server

# Runtime — alpine version cố định, KHÔNG dùng :latest
FROM alpine:3.21
WORKDIR /app

RUN apk add --no-cache ca-certificates curl
COPY --from=builder /out/app ./app

RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["./app"]
```

### Multi-arch Build trong CD Workflow

> **Nguyên tắc**: Dùng **native ARM64 runner** (`ubuntu-24.04-arm`) thay vì QEMU cross-compilation.
> QEMU chậm 3-5x so với native — lãng phí GitHub Actions minutes.

#### Khi nào dùng multi-arch (amd64 + arm64)

| Loại project | Multi-arch | Lý do |
|--------------|------------|-------|
| MCP Server (public) | CÓ | Users dùng cả Mac ARM + Linux x86 |
| npm package (public) | CÓ | Tương tự |
| Internal API (deploy lên OCI VM) | KHÔNG | OCI VM chỉ ARM64 → build single arch |

#### Pattern 1: Multi-arch (MCP servers, public packages)

```yaml
build-docker:
  name: Build Docker (${{ matrix.platform }})
  strategy:
    fail-fast: false
    matrix:
      include:
        - platform: linux/amd64
          runner: ubuntu-latest
          artifact: linux-amd64
        - platform: linux/arm64
          runner: ubuntu-24.04-arm      # Native — KHÔNG dùng QEMU
          artifact: linux-arm64
  runs-on: ${{ matrix.runner }}
  steps:
    - uses: actions/checkout@v6
    - uses: docker/setup-buildx-action@v4
    - uses: docker/login-action@v4
      with:
        # ... registry login
    - uses: docker/build-push-action@v7
      with:
        context: .
        platforms: ${{ matrix.platform }}
        outputs: type=image,"name=...",push-by-digest=true,name-canonical=true,push=true
        cache-from: type=gha,scope=${{ github.ref_name }}-${{ matrix.artifact }}
        cache-to: type=gha,mode=max,scope=${{ github.ref_name }}-${{ matrix.artifact }}
```

#### Pattern 2: Single arch (Internal APIs — OCI VM ARM64)

```yaml
deploy-api:
  name: Deploy API to GHCR
  runs-on: ubuntu-24.04-arm            # Native ARM64 — KHÔNG dùng QEMU
  steps:
    - uses: actions/checkout@v6
    - uses: docker/setup-buildx-action@v4
    - uses: docker/login-action@v4
      with:
        registry: ghcr.io
        # ...
    - uses: docker/build-push-action@v7
      with:
        context: .
        platforms: linux/arm64
        push: true
        tags: |
          ${{ env.IMAGE_NAME }}:${{ github.sha }}
          ${{ env.IMAGE_NAME }}:${{ github.ref == 'refs/heads/main' && 'latest' || 'staging' }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

### Cache Strategy

| Layer | Công cụ | Mục đích |
|-------|---------|----------|
| Dockerfile | `--mount=type=cache` | Cache package manager (uv, bun, go modules) |
| CI/CD | `cache-from: type=gha` | Cache Docker layers giữa các builds |
| Scope | `scope=${{ github.ref_name }}-${{ matrix.artifact }}` | Tách cache theo branch + platform |

> **Quan trọng**: `--mount=type=cache` trong Dockerfile và `type=gha` trong CI **bổ sung** cho nhau.
> BuildKit mount cache giảm thời gian install dependencies. GHA cache giảm thời gian rebuild layers.

---

## Language-Specific Structures

### Python
```
project/
├── src/<package>/
│   ├── __init__.py       # Dynamic version (importlib.metadata)
│   └── ...
├── tests/
│   ├── conftest.py
│   └── test_*.py
├── pyproject.toml
├── uv.lock
└── py.typed              # PEP 561 marker
```

> **BẮT BUỘC**: `__init__.py` phải dùng dynamic version từ `importlib.metadata`:
> ```python
> from importlib.metadata import version
> __version__ = version("package-name")
> ```
> Release-please chỉ cập nhật `pyproject.toml`, KHÔNG cập nhật `__init__.py` cho src-layout.
> Dynamic version đảm bảo `__version__` luôn đồng bộ với `pyproject.toml`.

### TypeScript
```
project/
├── src/
│   └── index.ts
├── tests/
│   └── *.test.ts
├── package.json
├── bun.lock
├── tsconfig.json
└── biome.json
```

### Go
```
project/
├── cmd/
│   └── app/
│       └── main.go
├── internal/
│   └── ...
├── pkg/
│   └── ...
├── go.mod
├── go.sum
└── .golangci.yml
```

### Tauri (Rust + React)
```
project/
├── src-tauri/
│   ├── src/
│   │   ├── main.rs
│   │   └── lib.rs
│   ├── Cargo.toml
│   └── tauri.conf.json
├── src/                   # React frontend
│   └── ...
├── package.json
└── bun.lock
```

---

## Renovate Config

> **Nguyên tắc**: `renovate.json` ở root repo. Renovate tự detect dependencies và tạo PR update. Dùng `rangeStrategy: "bump"` + `allowedVersions` ranges để pin version an toàn.

### Full Config (BẮT BUỘC cho tất cả repos)

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended", ":semanticCommits"],
  "schedule": ["before 5am"],
  "timezone": "Asia/Ho_Chi_Minh",
  "prConcurrentLimit": 5,
  "prHourlyLimit": 3,
  "labels": ["dependencies"],
  "rangeStrategy": "bump",
  "lockFileMaintenance": {
    "enabled": true,
    "schedule": ["before 5am"]
  },
  "packageRules": [
    {
      "description": "Auto-merge non-major devDependencies",
      "matchDepTypes": ["devDependencies"],
      "matchUpdateTypes": ["minor", "patch"],
      "automerge": true,
      "automergeType": "pr"
    },
    {
      "description": "Auto-merge patch production dependencies",
      "matchDepTypes": ["dependencies"],
      "matchUpdateTypes": ["patch"],
      "automerge": true,
      "automergeType": "pr"
    },
    {
      "description": "Group all non-major updates",
      "matchUpdateTypes": ["minor", "patch"],
      "groupName": "non-major dependencies",
      "groupSlug": "non-major"
    },
    {
      "description": "Pin GitHub Actions to SHA for security",
      "matchManagers": ["github-actions"],
      "pinDigests": true
    },
    {
      "description": "Pin PSR to v10 — block Renovate downgrades",
      "matchPackagePatterns": ["^python-semantic-release/"],
      "matchManagers": ["github-actions"],
      "allowedVersions": ">=10.0.0"
    },
    {
      "description": "Pin Python runtime to 3.13.x",
      "matchPackageNames": ["python"],
      "allowedVersions": ">=3.13.0 <3.14.0"
    },
    {
      "description": "Pin Node.js runtime to 24.x",
      "matchPackageNames": ["node"],
      "allowedVersions": ">=24.0.0 <25.0.0"
    },
    {
      "description": "Pin Java runtime to 21.x LTS",
      "matchPackageNames": ["java"],
      "allowedVersions": ">=21.0.0 <22.0.0"
    },
    {
      "description": "Disable runtime version updates from mise (pinned in CLAUDE.md)",
      "matchManagers": ["mise"],
      "matchDepNames": ["python", "node", "java"],
      "enabled": false
    }
  ]
}
```

> **`rangeStrategy: "bump"`**: Bump ranges thay vì pin exact — lock file giữ version cụ thể, range trong package.json/pyproject.toml vẫn linh hoạt.
> **`allowedVersions`**: Runtime vẫn nhận patch/minor updates trong phạm vi pin (3.13.x, 24.x) qua package managers.
> **`mise` disable**: Renovate cũng detect runtime versions trong `.mise.toml` — phải disable riêng để tránh Renovate tạo PR bump runtime ngoài phạm vi `allowedVersions` (mise manager bypass `allowedVersions` rules của package manager).
> **`pinDigests: true`**: GitHub Actions pin SHA — chống supply-chain attacks (tag bị hijack).
> **Auto-merge**: devDependencies (minor+patch) + prod dependencies (patch only) — giảm PR noise.
> **Harmless nếu package không tồn tại**: Rules chỉ apply khi Renovate detect package đó trong repo — thêm vào mọi repo là an toàn.

---

## Checklist

- [ ] Git branching: single `main` branch (không có `dev`)?
- [ ] GitHub Ruleset: Main ruleset exported vào `.github/rulesets/main.json`?
- [ ] GitHub Ruleset: Đã apply lên GitHub qua `gh api repos/.../rulesets --method POST`?
- [ ] GitHub repo: description + topics set qua `gh repo edit` / `gh api`?
- [ ] PSR config: `[tool.semantic_release]` trong `pyproject.toml` (Python) hoặc `semantic-release.toml` (non-Python)?
- [ ] `.mise.toml` với tool versions + standardized tasks (`setup`, `lint`, `test`, `fix`)?
- [ ] `.pre-commit-config.yaml` với language-specific hooks + common hooks (single block)?
- [ ] Commit enforcement: `scripts/enforce-commit.sh` + `commit-msg` hook (feat/fix only)?
- [ ] `.github/ISSUE_TEMPLATE/bug_report.md` + `feature_request.md` có mặt?
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` có mặt (generic, không repo-specific)?
- [ ] `.github/workflows/ci.yml` cho PR title check + commit message check + lint + test + Qodo Merge AI PR Review + email notify?
- [ ] `.github/workflows/cd.yml` với `workflow_dispatch` (beta/stable) + PSR?
- [ ] Infisical project: `infisical init` đã link repo? `.infisical.json` KHÔNG bị gitignore?
- [ ] Infisical secrets (prod): `SMTP_USERNAME`, `SMTP_PASSWORD`, `NOTIFY_EMAIL`, `CODECOV_TOKEN`, `GEMINI_API_KEY`, `GH_PAT` (auto-sync → GitHub)?
- [ ] `.github/CODEOWNERS` cho code review assignment?
- [ ] `.pr_agent.toml` configure model + `.github/best_practices.md` cho Qodo Merge?
- [ ] `README.md`: Bold one-liner giữa title và badges?
- [ ] `README.md`: Row 1 status badges (CI + Codecov + PyPI/Docker + License)?
- [ ] `README.md`: Row 2 tech stack badges (Python/framework + semantic-release + Renovate)?
- [ ] `LICENSE` file present?
- [ ] **Public repo**: AGENTS.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md?
- [ ] Docker: `Dockerfile` dùng multi-stage build + BuildKit cache?
- [ ] Docker: `.dockerignore` có mặt?
- [ ] Docker: Non-root user trong runtime stage?
- [ ] Docker: Native ARM runner (KHÔNG QEMU) trong CD workflow?
- [ ] Renovate: `renovate.json` có pinning rules cho PSR v10, Python 3.13, Node 24, Java 21?
- [ ] Verify: `mise run lint` passes locally?
- [ ] Verify: `pre-commit run --all-files` passes?
- [ ] Verify: CI workflow passes on push?
- [ ] Python: `__version__` dùng dynamic version (`importlib.metadata`)?

