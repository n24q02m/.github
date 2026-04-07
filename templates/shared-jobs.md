# Shared Job Patterns

Reference for common jobs shared across all repos. Every job is inlined in ci.yml/cd.yml -- NO reusable workflows.

## CI Jobs

### PR Title Check

- **Trigger**: `pull_request` for private repos, `pull_request_target` for public repos (fork PRs need secrets access) + `sender.type != 'Bot'`
- **Runner**: `ubuntu-latest` (with harden-runner)
- **Permissions**: `pull-requests: write`
- **Logic**: Validate Conventional Commits (feat/fix only). Auto-fix bot PR titles (strip Bolt/Sentinel/Guard/Shield/Palette prefix). `chore(release):` exempt for PSR.

### Semgrep SAST Scan

- **Trigger**: `pull_request` or `push`, skip Dependabot/Renovate
- **Runner**: `ubuntu-latest` (container: `semgrep/semgrep`) -- NO harden-runner (container job)
- **Permissions**: `contents: read`
- **Config**: `semgrep scan --config auto --error --verbose`
- **Customization**: `--exclude-rule <rule-id>` for false positives (e.g., Go signedness cast)

### CodeRabbit AI Code Review (public repos)

- **Integration**: GitHub App (not GitHub Actions) — install at https://coderabbit.ai
- **Config**: `.coderabbit.yaml` at repo root (see template below)
- **Trigger**: Automatic on PR open/update and issue open (via CodeRabbit webhook)
- **Secrets**: None required — OSS tier free for public repos
- **Reviews**: External contributors only (owner + bots excluded via `ignore_usernames`)
- **Issue enrichment**: Enabled — auto-generates coding plans from issues
- **Chat**: Disabled (`auto_reply: false`) — no `@coderabbitai` mentions

`.coderabbit.yaml` template:
```yaml
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

### Qodo AI Code Review (private repos only)

- **Trigger**: `issue_comment` (non-bot, non-owner) OR `pull_request` (non-bot, non-owner)
- **Runner**: `ubuntu-latest`
- **Permissions**: `issues: write`, `pull-requests: write`, `contents: read`, `id-token: write`
- **Auth**: Vertex AI via WIF (`google-github-actions/auth@v3` + `VERTEX_WIF_PROVIDER`, `VERTEX_SERVICE_ACCOUNT`)
- **Config**: Auto review + describe + improve. Custom instructions from `.github/best_practices.md`.
- **Vars**: `VERTEX_WIF_PROVIDER`, `VERTEX_SERVICE_ACCOUNT`, `VERTEX_PROJECT` (repo vars, not secrets)
- **`if:` condition** (both branches must filter bot AND owner):
  ```yaml
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
  ```

### Dependency Review

- **Trigger**: `pull_request` only
- **Runner**: `ubuntu-latest` (with harden-runner)
- **Private repos**: `continue-on-error: true` at **step level** on the `dependency-review-action` step (GitHub Advanced Security required for full functionality)
- **Public repos**: No `continue-on-error` needed
- **Config**: `fail-on-severity: moderate`, `comment-summary-in-pr: always`
- **Customization**: `allow-ghsas` for known false positives

### Email Notification

- **Trigger**: `issues` or `pull_request` (private repos) / `pull_request_target` (public repos), skip owner + bots
- **Runner**: `ubuntu-latest` (with harden-runner)
- **Secrets**: `SMTP_USERNAME`, `SMTP_PASSWORD`, `NOTIFY_EMAIL`
- **Action**: `dawidd6/action-send-mail@v3` (private repos), `@v15` (public repos)
- **Config**: Gmail SMTP (App Password, not regular password)

### Codecov Coverage Upload

- **Trigger**: `push` to main only (no uploads on PRs)
- **Self-hosted ARM64**: MUST include `os: linux-arm64` parameter
- **GitHub-hosted**: No `os` parameter needed

## CD Jobs

### Semantic Release (PSR v10)

- **Runner**: Always `ubuntu-latest`
- **Token**: `secrets.GH_PAT` (admin token, bypass branch rulesets)
- **Concurrency**: `cancel-in-progress: false`
- **Outputs**: `released`, `tag`, `version`, `is_prerelease`

### Docker Multi-arch (public repos)

- **Strategy**: amd64 (`ubuntu-latest`) + arm64 (`ubuntu-24.04-arm`)
- **Pattern**: Build per-platform -> upload digest artifact -> merge manifests
- **Tags**: Stable = `latest`, `X.Y.Z`, `X.Y`, `X`. Beta = `beta`, `X.Y.Z-beta.N`.
- **Registries**: DockerHub + GHCR

### Docker Local Build (private repos)

- **Runner**: `[self-hosted, linux, arm64]`
- **Pattern**: `docker build` locally -> `docker compose up` -> health check
- **Tag**: `latest` (stable) or `staging` (beta)
- **NO GHCR push, NO Watchtower**

### MCP Registry Publish

- **Trigger**: Stable releases only (`is_prerelease != 'true'`)
- **Auth**: GitHub OIDC (`id-token: write`), no secrets needed
- **Prerequisite**: PyPI/npm + Docker must complete first

## Key Differences: Private vs Public

| Aspect | Private (Aiora, KP, QShip) | Public (MCP servers, libs) |
|--------|---------------------------|---------------------------|
| Lint/Test runner | `[self-hosted, linux, arm64]` | `ubuntu-latest` |
| harden-runner | NO (self-hosted) | YES (all jobs except Semgrep container) |
| Codecov os | `linux-arm64` | (default) |
| Docker build | Local, single-arch ARM64 | Multi-arch amd64+arm64 |
| Deploy | `docker compose up` on VM2 | GHCR + DockerHub + Watchtower |
| dependency-review | `continue-on-error: true` (step level) | No flag needed |
| PR event trigger | `pull_request` | `pull_request_target` (fork PR secrets) |
| Semgrep | Container job, no harden-runner | Container job, no harden-runner |
| Email action | `action-send-mail@v3` | `action-send-mail@v15` |
| Code review | Qodo (GitHub Actions + WIF) | CodeRabbit (GitHub App, OSS free) |
| `issue_comment` trigger | Yes (for Qodo) | No (CodeRabbit uses webhook) |

## Secrets Required

| Secret/Var | Purpose | Source | Scope |
|------------|---------|--------|-------|
| `GH_PAT` | PSR bypass branch rulesets | GitHub PAT (admin) | All |
| `CODECOV_TOKEN` | Coverage upload | Infisical | All |
| `SMTP_USERNAME` | Email notification | Infisical | All |
| `SMTP_PASSWORD` | Email notification | Infisical | All |
| `NOTIFY_EMAIL` | Email recipient | Infisical | All |
| `DOCKERHUB_USERNAME` | Docker push | Infisical | Public |
| `DOCKERHUB_TOKEN` | Docker push | Infisical | Public |
| `NPM_TOKEN` | npm publish | Infisical | Public |
| `PYPI_TOKEN` | PyPI publish | Infisical | Public |
| `VERTEX_WIF_PROVIDER` | Qodo WIF auth | Repo var | Private only |
| `VERTEX_SERVICE_ACCOUNT` | Qodo WIF auth | Repo var | Private only |
| `VERTEX_PROJECT` | Qodo Vertex AI project | Repo var | Private only |
