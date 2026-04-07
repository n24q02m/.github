# CI/CD Workflow Templates

> Reference file cho `repo-structure` skill. Xem [SKILL.md](../SKILL.md) để hiểu pipeline tổng quan.

> **Template repo**: https://github.com/n24q02m/.github — chứa đầy đủ CI/CD templates cho private (self-hosted ARM64) và public repos.
> Copy template phù hợp, customize các phần đánh dấu `# CUSTOMIZE:`.
> Templates: `private-monorepo`, `public-python`, `public-typescript`, `public-python-lib`, `public-modal`.

---

## CI Workflow (.github/workflows/ci.yml)

> **Nguyên tắc**: CI dùng **specialized GitHub Actions** cho từng ngôn ngữ (setup-uv, setup-bun, setup-go, rust-toolchain). KHÔNG dùng mise-action.
> CI checks = **superset** của pre-commit: lint + format + type check + **tests** + **build** + **dependency review**.
> **Tất cả jobs PHẢI inline** trong ci.yml/cd.yml — KHÔNG dùng reusable workflows (workflow_call).

### SAST Strategy

> **Public repos**: CodeQL (miễn phí, bật trong repo Settings → Code security → Code scanning). KHÔNG cần Semgrep.
> **Private repos**: Semgrep trong CI (CodeQL yêu cầu GitHub Advanced Security — trả phí cho private repos).
> **Commit Message Check**: ĐÃ XÓA — commit đã push không sửa được, fail CI vô ích. PR Title Check vẫn giữ vì có thể auto-fix.

### Private Repo (Self-hosted ARM64)

> **Áp dụng cho**: Aiora, KnowledgePrism, QuikShipping (private monorepos trên OCI VM2).

| Job | Runner | harden-runner | Ghi chú |
|-----|--------|---------------|---------|
| PR title check | `ubuntu-latest` | YES | Auto-fix bot titles. Trigger: `pull_request` |
| Semgrep SAST | `ubuntu-latest` (container) | **NO** (container job không tương thích) | Thay thế CodeQL cho private repos. `--exclude-rule` cho false positives |
| Qodo AI review | `ubuntu-latest` | NO | Trigger: `pull_request` + `issue_comment`. Skip owner + bots. Auth: WIF → Vertex AI |
| Dependency review | `ubuntu-latest` | YES | `continue-on-error: true` ở **step level** (private repos cần vì không có GitHub Advanced Security) |
| Email notify | `ubuntu-latest` | YES | Trigger: `pull_request`. Skip owner + bots |
| Lint/Test/Build | `[self-hosted, linux, arm64]` | **NO** | **KHÔNG** dùng harden-runner trên self-hosted |
| Codecov upload | (cùng lint job) | — | **PHẢI** có `os: linux-arm64` |

### Python

```yaml
name: CI

on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened, ready_for_review]
  push:
    branches: [main]
  issue_comment:
    types: [created, edited]
  workflow_dispatch: {}
  issues:
    types: [opened, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  lint-and-test:
    name: Lint & Test
    if: github.event_name != 'issues'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v7
        with:
          version: "latest"
      - uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - run: uv sync --group dev
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run ty check
      - name: Run tests
        run: |
          if [ -d "tests" ] && [ "$(ls -A tests/*.py 2>/dev/null)" ]; then
            uv run pytest --tb=short
          else
            echo "No tests found, skipping..."
          fi

  dependency-review:
    name: Dependency Review
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: moderate
          comment-summary-in-pr: always
```

> **CHÚ Ý**: `dependency-review-action` **chỉ hoạt động trên public repos** (hoặc repos có GitHub Advanced Security enabled — tính năng trả phí cho private repos). Với **private repos**, thêm `continue-on-error: true` để job không block CI pipeline.

### TypeScript

```yaml
jobs:
  lint-and-test:
    name: Lint, Test & Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: oven-sh/setup-bun@v2
      - run: bun install --frozen-lockfile
      - run: bun run check         # biome check + type-check
      - run: bun test              # vitest
      - run: bun run build
```

### Go

```yaml
jobs:
  lint-and-test:
    name: Lint & Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-go@v6
        with:
          go-version: stable
      - run: go install mvdan.cc/gofumpt@latest
      - name: Gofumpt check
        working-directory: apps/api
        run: test -z "$(gofumpt -l cmd internal)" || { gofumpt -l cmd internal; exit 1; }
      - uses: golangci/golangci-lint-action@v9
        with:
          version: latest
          working-directory: apps/api
      - name: Go test
        working-directory: apps/api
        run: go test ./...
```

### Rust + TypeScript (Tauri)

```yaml
jobs:
  lint-rust:
    name: Rust Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      # ... install system deps, build frontend
      - run: cargo fmt --all -- --check
      - run: cargo clippy --workspace --all-targets -- -D warnings
      - run: cargo audit

  lint-frontend:
    name: Frontend Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: oven-sh/setup-bun@v2
      - run: bun install --frozen-lockfile
      - run: bun run typecheck
      - run: bun run lint

  test:
    name: Test
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v6
      # ... setup toolchain + frontend build
      - run: cargo test --workspace
```

### Monorepo (path-filtered)

```yaml
on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened, ready_for_review]
    paths:
      - "apps/**"
      - ".github/workflows/ci.yml"
  push:
    branches: [main]
    paths:
      - "apps/**"
      - ".github/workflows/ci.yml"
  issue_comment:
    types: [created, edited]
  workflow_dispatch: {}
  issues:
    types: [opened, reopened]

jobs:
  lint-api:
    name: Backend - Lint & Test
    if: github.event_name != 'issues'
    # ... backend-specific steps

  build-api:
    name: Backend - Build
    needs: lint-api

  lint-web:
    name: Frontend - Lint & Type Check
    if: github.event_name != 'issues'
    # ... frontend-specific steps

  build-web:
    name: Frontend - Build
    needs: lint-web

  dependency-review:
    name: Dependency Review
    if: github.event_name == 'pull_request'
```

> **KHÔNG** thêm PR comment steps (actions/github-script). GitHub UI đã hiển thị CI status — comment chỉ tạo noise.
> **`uv sync` vs `uv sync --locked` vs `uv sync --frozen`**:
> - **CI**: Dùng `uv sync` (không `--locked`) vì PSR bump version trong `pyproject.toml` nhưng không update `uv.lock` — `--locked` sẽ fail trên version bump commits.
> - **Dockerfile**: Dùng `uv sync --frozen` (không `--locked`, không bare `uv sync`) vì Docker layers là read-only.

---

## Issue & PR Templates (BẮT BUỘC cho tất cả repos)

### PR Template (.github/PULL_REQUEST_TEMPLATE.md)

```markdown
## Description

Brief description of the changes in this PR.

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Test addition/update

## Related Issues

Closes #(issue number)

## Changes Made

- Change 1
- Change 2

## Testing

- [ ] Existing tests pass
- [ ] Added new tests for new functionality
- [ ] Tested manually

## Checklist

- [ ] My code follows the project's code style
- [ ] I have performed a self-review of my code
- [ ] My changes generate no new warnings or errors
- [ ] I have added tests that prove my fix/feature works
- [ ] My commits follow the [Conventional Commits](https://www.conventionalcommits.org/) specification

## Screenshots (if applicable)

Add screenshots to help explain your changes.

## Additional Notes

Any additional information that reviewers should know.
```

> **Generic template**: KHÔNG chứa repo-specific test commands (như `bun test`, `go test`). Mỗi contributor tự biết cách chạy test từ README/CONTRIBUTING.

### Issue Templates (.github/ISSUE_TEMPLATE/)

**bug_report.md:**

```markdown
---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:

1. ...
2. ...
3. ...

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment (please complete the following information):**

- OS: [e.g. macOS, Linux, Windows]

**Additional context**
Add any other context about the problem here.
```

**feature_request.md:**

```markdown
---
name: Feature request
about: Suggest an idea for this project
title: ''
labels: ''
assignees: ''
---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.
```

> **Environment section**: Giữ generic (chỉ OS). Mỗi repo có thể thêm fields riêng (Python version, Node version, etc.) nếu cần.

---

## Common CI Jobs (cross-language)

### PR Title Check (Conventional Commits)

> **Nguyên tắc**: Squash merge dùng PR title làm commit message. PR title PHẢI tuân thủ Conventional Commits — tương đương `enforce-commit.sh` ở CI level.
> **Auto-fix**: Thay vì chỉ reject, script tự sửa title không hợp lệ (strip Bolt/Sentinel/Guard/Shield prefix từ bot PRs, auto-categorize feat/fix dựa trên keywords).

```yaml
  pr-title-check:
    name: PR Title Check
    if: >-
      github.event_name == 'pull_request'
      && github.event.sender.type != 'Bot'
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - name: Harden Runner
        uses: step-security/harden-runner@v2
        with:
          egress-policy: audit

      - name: Validate and auto-fix PR title
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          title=$(gh pr view ${{ github.event.pull_request.number }} --repo ${{ github.repository }} --json title -q .title)
          if [[ "$title" =~ ^(feat|fix)(\(.+\))?:.+ ]] || [[ "$title" =~ ^chore\(release\):.+ ]]; then
            echo "Title is valid: $title"
            exit 0
          fi
          clean=$(echo "$title" | sed -E 's/^[^a-zA-Z]*//; s/^(Bolt|Sentinel|Guard|Shield): *(\[.*\] *)?//')
          if echo "$clean" | grep -qiE 'fix|bug|vulnerability|security|patch|resolve|crash|error'; then
            new_title="fix: $(echo "$clean" | sed 's/^./\L&/')"
          else
            new_title="feat: $(echo "$clean" | sed 's/^./\L&/')"
          fi
          gh pr edit ${{ github.event.pull_request.number }} --repo ${{ github.repository }} --title "$new_title"
          echo "Auto-fixed: $title -> $new_title"
```

> **Auto-fix thay vì reject**: Renovate/bot PRs thường có title như `Bolt: [deps] update X` — script strip prefix và auto-categorize dựa trên keywords (fix/bug/vulnerability → `fix:`, còn lại → `feat:`).
> **`pull-requests: write`**: Cần write permission để `gh pr edit` sửa title.
> **`chore(release):` exempt**: PSR tự tạo PR với title `chore(release):` — được pass qua.
> **Skip bot PRs**: `github.event.sender.type != 'Bot'` — Renovate/Dependabot PRs có `sender.type == 'Bot'`, skip hoàn toàn.
> **Vị trí**: Đặt **TRƯỚC** `lint-and-test` job trong ci.yml, chạy song song (independent, không blocking).


### Semgrep SAST Scan

```yaml
  semgrep:
    name: Semgrep SAST Scan
    runs-on: ubuntu-latest
    if: github.actor != 'dependabot[bot]' && github.actor != 'renovate[bot]'
    permissions:
      contents: read
    container:
      image: semgrep/semgrep
    steps:
      - uses: actions/checkout@v6
      - name: Run Semgrep scan
        run: semgrep scan --config auto --error --verbose
```

### AI PR Review

**Public repos**: Dùng **CodeRabbit GitHub App** — không cần job trong CI. Cấu hình qua `.coderabbit.yaml` ở root repo.

```yaml
# .coderabbit.yaml
language: "en-US"
reviews:
  auto_review:
    enabled: true
    drafts: false
    ignore_usernames:
      - "n24q02m"
      - "dependabot[bot]"
      - "renovate[bot]"
      - "github-actions[bot]"
      - "devin-ai-integration[bot]"
      - "google-labs-jules[bot]"
  profile: "chill"
  request_changes_workflow: false
  high_level_summary: true
  auto_incremental_review: true
issue_enrichment:
  auto_enrich:
    enabled: true
  planning:
    enabled: true
chat:
  auto_reply: false
```

**Private repos**: Dùng **Qodo Merge (qodo-ai/pr-agent)** qua GitHub Actions + Vertex AI WIF.

```yaml
  ai_pr_review:
    name: Qodo AI Code Review
    if: >-
      (
        github.event_name == 'issue_comment'
        && github.event.sender.type != 'Bot'
        && github.event.sender.login != 'n24q02m'
      ) || (
        github.event_name == 'pull_request'
        && github.event.sender.type != 'Bot'
        && github.event.pull_request.user.login != 'n24q02m'
      )
    runs-on: ubuntu-latest
    permissions:
      issues: write
      pull-requests: write
      contents: read
      id-token: write

    steps:
      - name: Checkout repo
        uses: actions/checkout@v6

      - name: Load custom instructions
        run: |
          if [ -f ".github/best_practices.md" ]; then
            INSTRUCTIONS=$(cat .github/best_practices.md)
            RANDOM_EOF=$(dd if=/dev/urandom bs=15 count=1 status=none | base64)
            echo "CUSTOM_INSTRUCTIONS<<$RANDOM_EOF" >> "$GITHUB_ENV"
            echo "$INSTRUCTIONS" >> "$GITHUB_ENV"
            echo "$RANDOM_EOF" >> "$GITHUB_ENV"
          fi

      - name: Authenticate to GCP (Vertex AI)
        uses: google-github-actions/auth@v3
        with:
          workload_identity_provider: ${{ vars.VERTEX_WIF_PROVIDER }}
          service_account: ${{ vars.VERTEX_SERVICE_ACCOUNT }}

      - name: PR Agent action step
        uses: qodo-ai/pr-agent@main
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          VERTEXAI_PROJECT: ${{ vars.VERTEX_PROJECT }}
          VERTEXAI_LOCATION: global
          PR_REVIEWER__EXTRA_INSTRUCTIONS: ${{ env.CUSTOM_INSTRUCTIONS }}
          PR_CODE_SUGGESTIONS__EXTRA_INSTRUCTIONS: ${{ env.CUSTOM_INSTRUCTIONS }}
          PR_DESCRIPTION__EXTRA_INSTRUCTIONS: ${{ env.CUSTOM_INSTRUCTIONS }}
          GITHUB_ACTION_CONFIG__AUTO_REVIEW: "true"
          GITHUB_ACTION_CONFIG__AUTO_DESCRIBE: "true"
          GITHUB_ACTION_CONFIG__AUTO_IMPROVE: "true"
          GITHUB_ACTION_CONFIG__HANDLE_PR_ACTIONS: '["opened", "reopened", "ready_for_review", "synchronize"]'
```

> **if: condition**: Cả 2 nhánh (`issue_comment` và `pull_request`) đều phải filter bot VÀ owner. `issue_comment` dùng `sender.login`, `pull_request` dùng `pull_request.user.login`.
> **Auth**: Vertex AI qua WIF — không cần `GEMINI_API_KEY`. Vars `VERTEX_WIF_PROVIDER`, `VERTEX_SERVICE_ACCOUNT`, `VERTEX_PROJECT` là repo vars (không phải secrets).

---

## CD Workflow (.github/workflows/cd.yml)

Pattern chung cho tất cả repos, dùng python-semantic-release v10 + workflow_dispatch:

> **QUAN TRỌNG**: Dùng `GH_PAT` (admin token) để PSR push commit + tag bypass branch ruleset.
> `GITHUB_TOKEN` KHÔNG bypass rulesets → PSR push sẽ bị reject.

### Single-package (Python)

```yaml
name: CD

on:
  workflow_dispatch:
    inputs:
      release_type:
        description: "Release type"
        required: true
        type: choice
        options:
          - beta
          - stable

permissions:
  contents: write
  id-token: write

concurrency:
  group: release
  cancel-in-progress: false

jobs:
  # =================== Release ===================
  release:
    name: Semantic Release
    runs-on: ubuntu-latest
    outputs:
      released: ${{ steps.release.outputs.released }}
      tag: ${{ steps.release.outputs.tag }}
      version: ${{ steps.release.outputs.version }}
      is_prerelease: ${{ steps.release.outputs.is_prerelease }}
    steps:
      - uses: actions/checkout@v6
        with:
          token: ${{ secrets.GH_PAT }}
          fetch-depth: 0

      - uses: python-semantic-release/python-semantic-release@v10
        id: release
        with:
          github_token: ${{ secrets.GH_PAT }}
          prerelease: ${{ inputs.release_type == 'beta' }}
          prerelease_token: beta

      - uses: python-semantic-release/publish-action@v10
        if: steps.release.outputs.released == 'true'
        with:
          github_token: ${{ secrets.GH_PAT }}
          tag: ${{ steps.release.outputs.tag }}

  # =================== Publish to PyPI ===================
  publish-pypi:
    name: Publish to PyPI
    needs: release
    if: needs.release.outputs.released == 'true'
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ needs.release.outputs.tag }}
      - uses: astral-sh/setup-uv@v7
      - run: uv build
      - uses: pypa/gh-action-pypi-publish@release/v1

  # =================== Build Docker ===================
  build-docker:
    name: Build Docker (${{ matrix.platform }})
    needs: release
    if: needs.release.outputs.released == 'true'
    strategy:
      fail-fast: false
      matrix:
        include:
          - platform: linux/amd64
            runner: ubuntu-latest
            artifact: linux-amd64
          - platform: linux/arm64
            runner: ubuntu-24.04-arm
            artifact: linux-arm64
    runs-on: ${{ matrix.runner }}
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ needs.release.outputs.tag }}
      - uses: docker/setup-buildx-action@v4
      - uses: docker/login-action@v4
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - uses: docker/login-action@v4
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v7
        id: build
        with:
          context: .
          platforms: ${{ matrix.platform }}
          outputs: type=image,"name=${{ env.DOCKERHUB_IMAGE }},${{ env.GHCR_IMAGE }}",push-by-digest=true,name-canonical=true,push=true
          cache-from: type=gha,scope=${{ github.ref_name }}-${{ matrix.artifact }}
          cache-to: type=gha,mode=max,scope=${{ github.ref_name }}-${{ matrix.artifact }}
      - run: |
          mkdir -p ${{ runner.temp }}/digests
          echo "${{ steps.build.outputs.digest }}" > "${{ runner.temp }}/digests/${{ matrix.artifact }}"
      - uses: actions/upload-artifact@v4
        with:
          name: digest-${{ matrix.artifact }}
          path: ${{ runner.temp }}/digests/*

  # =================== Merge Docker Manifests ===================
  merge-docker:
    name: Merge Docker Manifests
    needs: [release, build-docker]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          pattern: digest-*
          path: ${{ runner.temp }}/digests
          merge-multiple: true
      - uses: docker/login-action@v4
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - uses: docker/login-action@v4
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Create and push manifests
        env:
          VERSION: ${{ needs.release.outputs.version }}
          IS_PRERELEASE: ${{ needs.release.outputs.is_prerelease }}
        run: |
          # Build tag lists based on release type
          if [ "$IS_PRERELEASE" = "true" ]; then
            TAGS="beta ${VERSION}"
          else
            MAJOR=$(echo "$VERSION" | cut -d. -f1)
            MINOR=$(echo "$VERSION" | cut -d. -f1-2)
            TAGS="latest ${VERSION} ${MINOR} ${MAJOR}"
          fi

          DIGESTS=$(cat ${{ runner.temp }}/digests/*)

          for IMAGE in "$DOCKERHUB_IMAGE" "$GHCR_IMAGE"; do
            TAG_ARGS=""
            for TAG in $TAGS; do
              TAG_ARGS="$TAG_ARGS -t ${IMAGE}:${TAG}"
            done
            docker buildx imagetools create $TAG_ARGS \
              $(echo "$DIGESTS" | xargs -I{} echo "${IMAGE}@{}")
          done
```

### Single-package (Node/TypeScript)

Giống Python template, thay publish job:

```yaml
  publish-npm:
    name: Publish to npm
    needs: release
    if: needs.release.outputs.released == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ needs.release.outputs.tag }}
      - uses: oven-sh/setup-bun@v2
      - run: bun install --frozen-lockfile
      - run: bun run build
      - run: bun publish --no-git-checks --tag ${{ needs.release.outputs.is_prerelease == 'true' && 'beta' || 'latest' }}
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Monorepo (Multi-package)

```yaml
name: CD

on:
  workflow_dispatch:
    inputs:
      release_type:
        description: "Release type"
        required: true
        type: choice
        options:
          - beta
          - stable

permissions:
  contents: write
  id-token: write

concurrency:
  group: release
  cancel-in-progress: false

jobs:
  # =================== Release per component ===================
  release:
    name: Semantic Release
    runs-on: ubuntu-latest
    outputs:
      api-released: ${{ steps.release-api.outputs.released }}
      api-tag: ${{ steps.release-api.outputs.tag }}
      api-version: ${{ steps.release-api.outputs.version }}
      api-is-prerelease: ${{ steps.release-api.outputs.is_prerelease }}
      web-released: ${{ steps.release-web.outputs.released }}
      web-tag: ${{ steps.release-web.outputs.tag }}
      web-version: ${{ steps.release-web.outputs.version }}
      web-is-prerelease: ${{ steps.release-web.outputs.is_prerelease }}
    steps:
      - uses: actions/checkout@v6
        with:
          token: ${{ secrets.GH_PAT }}
          fetch-depth: 0

      - name: Release API
        id: release-api
        uses: python-semantic-release/python-semantic-release@v10
        with:
          directory: apps/api
          github_token: ${{ secrets.GH_PAT }}
          prerelease: ${{ inputs.release_type == 'beta' }}
          prerelease_token: beta

      - name: Publish API to GitHub Release
        uses: python-semantic-release/publish-action@v10
        if: steps.release-api.outputs.released == 'true'
        with:
          directory: apps/api
          github_token: ${{ secrets.GH_PAT }}
          tag: ${{ steps.release-api.outputs.tag }}

      - name: Release Web
        id: release-web
        uses: python-semantic-release/python-semantic-release@v10
        with:
          directory: apps/web
          github_token: ${{ secrets.GH_PAT }}
          prerelease: ${{ inputs.release_type == 'beta' }}
          prerelease_token: beta

      - name: Publish Web to GitHub Release
        uses: python-semantic-release/publish-action@v10
        if: steps.release-web.outputs.released == 'true'
        with:
          directory: apps/web
          github_token: ${{ secrets.GH_PAT }}
          tag: ${{ steps.release-web.outputs.tag }}

  # =================== Deploy per component ===================
  deploy-api:
    name: Deploy API
    needs: release
    if: needs.release.outputs.api-released == 'true'
    # ... Docker build + push steps (single-arch ARM64 cho OCI VM)

  deploy-web:
    name: Deploy Web
    needs: release
    if: needs.release.outputs.web-released == 'true'
    # ... CF Pages deploy steps
```

> **Token**: Dùng `secrets.GH_PAT` (Personal Access Token) để PSR push bypass branch ruleset + trigger downstream workflows.
> **Concurrency**: `cancel-in-progress: false` để không cancel release đang chạy.
> **Tag checkout**: Post-release jobs checkout theo tag (`ref: ${{ needs.release.outputs.tag }}`) để build đúng version.

### Publish to MCP Registry (cho MCP Server repos)

Thêm job này vào CD workflow sau publish-npm/publish-pypi + merge-docker. Yêu cầu `id-token: write` ở top-level permissions.

```yaml
  # =================== Publish to MCP Registry ===================
  publish-mcp-registry:
    name: Publish to MCP Registry
    needs: [release, publish-npm, merge-docker]  # hoặc publish-pypi cho Python repos
    if: needs.release.outputs.released == 'true' && needs.release.outputs.is_prerelease != 'true'
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: step-security/harden-runner@v2
        with:
          egress-policy: audit
      - uses: actions/checkout@v6
        with:
          ref: ${{ needs.release.outputs.tag }}
      - name: Update server.json version
        run: |
          VERSION="${{ needs.release.outputs.version }}"
          jq --arg v "$VERSION" '
            .version = $v |
            .packages = [.packages[] |
              if .registryType == "oci" then del(.version)
              else .version = $v
              end
            ]
          ' server.json > server.json.tmp && mv server.json.tmp server.json
      - name: Install MCP Publisher
        run: |
          curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher
      - name: Login to MCP Registry
        run: ./mcp-publisher login github-oidc
      - name: Publish to MCP Registry
        run: ./mcp-publisher publish
```

> **needs merge-docker**: OCI image phải sẵn sàng trước khi MCP Registry validate. Nếu không có Docker, bỏ `merge-docker` khỏi needs.
> **Dynamic version update**: `server.json` có version cứng, jq step update version runtime. OCI packages KHÔNG có `version` field (dùng `del(.version)`).
> **Chỉ publish stable releases**: `is_prerelease != 'true'` — beta releases không lên MCP Registry.
> **OIDC auth**: GitHub Actions tự cấp token, không cần secrets. Chỉ cần `id-token: write`.
> **server.json**: Phải có ở root repo. Description max 100 ký tự. Xem `mcp-server` skill Phase 6 cho validation rules đầy đủ.

---

### Email Notification (External Contributors)

> **Nguyên tắc**: Notification nằm trong ci.yml (KHÔNG tạo file notify.yml riêng). Thêm `issues` trigger vào ci.yml, các job hiện tại thêm `if:` condition để skip issue events.

**Triggers đã có sẵn trong ci.yml `on:` block** (xem template Python/Monorepo ở trên):

```yaml
on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened, ready_for_review]
  push:
    branches: [main]
  issue_comment:
    types: [created, edited]
  workflow_dispatch: {}
  issues:
    types: [opened, reopened]
```

**Thêm `if:` condition cho các job không nên chạy trên issue events:**

```yaml
  lint-and-test:
    name: Lint & Test
    if: github.event_name != 'issues'    # THÊM DÒNG NÀY
    # ... existing steps
```

> **Tại sao cần `if:`**: Khi thêm `issues` trigger, TẤT CẢ jobs sẽ chạy khi có issue event. Lint/test/build vô nghĩa cho issues → phải filter. Các job đã có `if:` riêng (dependency-review, qodo, pr-title-check) tự động skip — không cần sửa.

**Email notify job (thêm vào cuối `jobs:`):**

```yaml
  email-notify:
    name: Email Notification
    if: >-
      (github.event_name == 'issues' || github.event_name == 'pull_request')
      && github.actor != 'n24q02m'
      && github.event.sender.type != 'Bot'
    runs-on: ubuntu-latest
    steps:
      - name: Harden Runner
        uses: step-security/harden-runner@v2
        with:
          egress-policy: audit

      - name: Send email notification
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.gmail.com
          server_port: 587
          username: ${{ secrets.SMTP_USERNAME }}
          password: ${{ secrets.SMTP_PASSWORD }}
          subject: >-
            [${{ github.event.repository.name }}]
            ${{ github.event_name == 'issues' && 'Issue' || 'PR' }}
            #${{ github.event.issue.number || github.event.pull_request.number }}:
            ${{ github.event.issue.title || github.event.pull_request.title }}
          to: ${{ secrets.NOTIFY_EMAIL }}
          from: GitHub Notify <${{ secrets.SMTP_USERNAME }}>
          body: |
            ${{ github.event_name == 'issues' && 'New issue' || 'New pull request' }} in ${{ github.repository }}

            Title: ${{ github.event.issue.title || github.event.pull_request.title }}
            Author: ${{ github.actor }}
            URL: ${{ github.event.issue.html_url || github.event.pull_request.html_url }}
            Action: ${{ github.event.action }}

            ---
            ${{ github.event.issue.body || github.event.pull_request.body || 'No description provided.' }}
```

> **Filter logic**: `github.actor != 'n24q02m'` — bỏ qua PR/issue của chính mình. `sender.type != 'Bot'` — bỏ qua Renovate, Dependabot, etc.
> **Dùng `pull_request` (không `pull_request_target`)**: Đã có trong ci.yml. Fork PRs không có secrets → notification sẽ skip (chấp nhận — solo dev, fork PRs hiếm).
> **Gmail SMTP**: Cần App Password (không phải password thường). Tạo tại myaccount.google.com → Security → 2-Step Verification → App passwords.
> **Secrets cần thêm vào GitHub** (mỗi repo): `SMTP_USERNAME` (Gmail address), `SMTP_PASSWORD` (App Password), `NOTIFY_EMAIL` (email nhận thông báo).
> **Tách riêng khỏi Infisical**: Secrets email là cross-cutting concern, thêm trực tiếp vào GitHub Secrets (không cần Infisical auto-sync vì không dùng ở runtime).

---

## GitHub Rulesets

Tạo **1 ruleset** trong repo Settings → Rules → Rulesets:

### Main Ruleset
| Rule | Setting |
|------|----------|
| Target | `refs/heads/main` |
| Bypass | Repository admin (Always) |
| Deletion | Block |
| Non-fast-forward | Block |
| Linear History | Required |
| Pull Request | 1 approval, dismiss stale, code owner review |
| Merge Methods | Squash only |
| Code Scanning | CodeQL (high_or_higher) |

> **Không có Development Ruleset** — chỉ có 1 branch `main`, 1 ruleset.
> **Bypass list**: Admin → cho phép PSR (chạy với GH_PAT) push version commit + tag.
> **Export**: Settings → Rules → Rulesets → ... → Export → Lưu vào `.github/rulesets/main.json`

---

## CODEOWNERS (.github/CODEOWNERS)
```
# Default owners cho toàn bộ
* @username

# Backend
/api/ @backend-team
/src/ @backend-team

# Frontend
/web/ @frontend-team
/app/ @frontend-team

# Infrastructure
/.github/ @devops-team
/infra/ @devops-team
/terraform/ @devops-team

# Documentation
/docs/ @docs-team
*.md @docs-team
```
