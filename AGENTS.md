# Agent Collaboration

## Quick reference

- Repo: `n24q02m/.github`
- Description: Community-health defaults for [@n24q02m](https://github.com/n24q02m)'s repositories.
- License: Apache-2.0

## Build & Test

See [README.md](README.md) for end-user install. For development:

```sh
mise run setup     # First-time dev environment
mise run lint      # Read-only lint + format check + type check
mise run test      # Run tests
mise run fix       # Auto-fix lint + format
```

## Release

Releases triggered manually via `workflow_dispatch` on `cd.yml`. Choose `beta` or `stable`. better-semantic-release handles version bump, CHANGELOG, tag, and GitHub Release. It is a drop-in fork of python-semantic-release, so configuration keys are unchanged (`[semantic_release]` / `[tool.semantic_release]`).

## Conventions

- Commits: only `feat:` and `fix:` prefixes (enforced by pre-commit `commit-msg` hook)
- Test coverage: ≥ 95% on internal modules
- No secrets in code, commits, or memory — use [skret](https://skret.n24q02m.com) for secret retrieval
