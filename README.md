# .github

[![CI](https://github.com/n24q02m/.github/actions/workflows/ci.yml/badge.svg)](https://github.com/n24q02m/.github/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Renovate](https://img.shields.io/badge/renovate-enabled-brightgreen.svg)](renovate.json)
[![Security](https://img.shields.io/badge/security-policy-brightgreen.svg)](SECURITY.md)

**Community health files and shared workflows for [@n24q02m](https://github.com/n24q02m)'s repositories.**

- `FUNDING.yml` — default sponsor button applied across all repositories that do not define their own.
- `CODEOWNERS` — default code review ownership.
- `SECURITY.md` — vulnerability reporting policy and response SLOs.
- `CODE_OF_CONDUCT.md` — Contributor Covenant v2.1 community standard.
- `CONTRIBUTING.md` — contribution guide.

## Conventions

- Every product repo carries exactly two workflows: `.github/workflows/ci.yml` (PR/push checks) and `.github/workflows/cd.yml` (release/deploy/scheduled jobs). No additional workflow files.
- Unified documentation hub: [mcp.n24q02m.com](https://mcp.n24q02m.com) — MCP servers under `/servers/`, tools under `/tools/`, skret under `/skret/`.
