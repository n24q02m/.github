# Shared Job Patterns

Reference cho cac job chung giua tat ca repos. Moi job duoc inline trong ci.yml/cd.yml — KHONG dung reusable workflows.

## CI Jobs

### PR Title Check

- **Trigger**: `pull_request_target` (public repos dung `pull_request` cua no) + `sender.type != 'Bot'`
- **Runner**: `ubuntu-latest` (with harden-runner)
- **Permissions**: `pull-requests: write`
- **Logic**: Validate Conventional Commits (feat/fix only). Auto-fix bot PR titles (strip Bolt/Sentinel/Guard/Shield/Palette prefix). `chore(release):` exempt cho PSR.

### Semgrep SAST Scan

- **Trigger**: `pull_request` hoac `push`, skip Dependabot/Renovate
- **Runner**: `ubuntu-latest` (container: `semgrep/semgrep`)
- **Permissions**: `contents: read`
- **Config**: `semgrep ci --config auto --error --verbose`
- **Customization**: `--exclude-rule <rule-id>` cho false positives (vd: Go signedness cast)

### Qodo AI Code Review

- **Trigger**: `issue_comment` (non-bot) OR `pull_request_target` (non-bot, non-owner)
- **Runner**: `ubuntu-latest`
- **Permissions**: `issues: write`, `pull-requests: write`, `contents: read`
- **Config**: Auto review + describe + improve. Custom instructions tu `.github/best_practices.md`.
- **Secrets**: `GEMINI_API_KEY`

### Dependency Review

- **Trigger**: `pull_request` only
- **Runner**: `ubuntu-latest` (with harden-runner)
- **Private repos**: PHAI co `continue-on-error: true` (GitHub Advanced Security required)
- **Config**: `fail-on-severity: moderate`, `comment-summary-in-pr: always`
- **Customization**: `allow-ghsas` cho known false positives

### Email Notification

- **Trigger**: `issues` hoac `pull_request_target`, skip owner + bots
- **Runner**: `ubuntu-latest` (with harden-runner)
- **Secrets**: `SMTP_USERNAME`, `SMTP_PASSWORD`, `NOTIFY_EMAIL`
- **Config**: Gmail SMTP (App Password, khong phai password thuong)

### Codecov Coverage Upload

- **Trigger**: `push` to main only (khong upload tren PRs)
- **Self-hosted ARM64**: PHAI co `os: linux-arm64` parameter
- **GitHub-hosted**: Khong can `os` parameter

## CD Jobs

### Semantic Release (PSR v10)

- **Runner**: Luon `ubuntu-latest`
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
- **Tag**: `latest` (stable) hoac `staging` (beta)
- **NO GHCR push, NO Watchtower**

### MCP Registry Publish

- **Trigger**: Stable releases only (`is_prerelease != 'true'`)
- **Auth**: GitHub OIDC (`id-token: write`), khong can secrets
- **Prerequisite**: PyPI/npm + Docker phai xong truoc

## Key Differences: Private vs Public

| Aspect | Private (Aiora, KP, QShip) | Public (MCP servers, libs) |
|--------|---------------------------|---------------------------|
| Lint/Test runner | `[self-hosted, linux, arm64]` | `ubuntu-latest` |
| harden-runner | NO (self-hosted) | YES (all jobs) |
| Codecov os | `linux-arm64` | (default) |
| Docker build | Local, single-arch ARM64 | Multi-arch amd64+arm64 |
| Deploy | `docker compose up` on VM2 | GHCR + DockerHub + Watchtower |
| dependency-review | `continue-on-error: true` | No flag needed |

## Secrets Required

| Secret | Purpose | Source |
|--------|---------|-------|
| `GH_PAT` | PSR bypass branch rulesets | GitHub PAT (admin) |
| `GEMINI_API_KEY` | Qodo AI review | Infisical |
| `CODECOV_TOKEN` | Coverage upload | Infisical |
| `SMTP_USERNAME` | Email notification | Infisical |
| `SMTP_PASSWORD` | Email notification | Infisical |
| `NOTIFY_EMAIL` | Email recipient | Infisical |
| `DOCKERHUB_USERNAME` | Docker push | Infisical |
| `DOCKERHUB_TOKEN` | Docker push | Infisical |
| `NPM_TOKEN` | npm publish | Infisical |
| `PYPI_TOKEN` | PyPI publish | Infisical |
