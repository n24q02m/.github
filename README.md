# .github - CI/CD Template Reference

This repository contains CI/CD workflow **templates** for n24q02m repos. Templates are meant to be **copied** into each repo's `.github/workflows/` directory and customized — they are NOT reusable workflows.

## Architecture

- **Private repos** (Aiora, KnowledgePrism, QuikShipping): Self-hosted ARM64 runners on OCI VM2 for lint/test/build. GitHub-hosted runners for PR checks, Semgrep, Qodo, email.
- **Public repos** (MCP servers, libraries): GitHub-hosted `ubuntu-latest` runners for everything, `harden-runner` on all jobs.

## Templates

### CI (`templates/ci/`)

| Template | Repos | Key traits |
|----------|-------|------------|
| `private-monorepo.yml` | Aiora, KnowledgePrism, QuikShipping | Self-hosted ARM64 lint/test, path-filtered triggers, `os: linux-arm64` for Codecov |
| `public-python.yml` | wet-mcp, mnemo-mcp | ubuntu-latest, harden-runner, Python 3.13, uv + ruff + ty |
| `public-typescript.yml` | better-notion-mcp, better-email-mcp, better-godot-mcp, better-telegram-mcp | ubuntu-latest, harden-runner, bun + biome + vitest |
| `public-python-lib.yml` | qwen3-embed | Multi-version matrix (3.10-3.14), lint on primary version only |
| `public-modal.yml` | modalcom-ai-workers | Same as public-python, Python 3.13 pinned |

### CD (`templates/cd/`)

| Template | Pipeline |
|----------|----------|
| `private-monorepo.yml` | PSR v10 -> local docker build -> compose up (self-hosted VM2) + CF Pages |
| `public-python.yml` | PSR v10 -> PyPI -> Docker multi-arch -> MCP Registry |
| `public-typescript.yml` | PSR v10 -> npm -> Docker multi-arch -> MCP Registry |
| `public-python-lib.yml` | PSR v10 -> PyPI only |
| `public-modal.yml` | PSR v10 -> Modal.com deploy |

### Shared patterns (`templates/shared-jobs.md`)

Documents common job patterns (PR title check, Semgrep, Qodo, email notification, dependency review) and the differences between private and public repos.

## How to use

1. Pick the appropriate CI and CD template for your repo type.
2. Copy to `.github/workflows/ci.yml` and `.github/workflows/cd.yml`.
3. Search for `# CUSTOMIZE:` comments and adjust:
   - Package names, working directories, Docker image names
   - Path filters (monorepo)
   - Semgrep exclude-rules (if false positives)
   - Build-time environment variables
4. Pin action versions with full SHA hashes (Renovate will update them).
