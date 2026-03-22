---
name: fullstack-dev
description: "Full-stack development: Next.js 16, Expo, Tauri, FastAPI, Echo, MCP servers, testing, frontend design, Godot game dev. Dung khi build web/mobile/desktop apps, APIs, MCP servers, tests, UI components, hoac game."
---

# Full-stack Development

## Khi nao dung

- Web app (Next.js 16 static export, Cloudflare Pages)
- Mobile app (React Native Expo, EAS builds)
- Desktop app (Tauri 2, Rust + React)
- Go API (Echo + sqlc + pgx/v5)
- Python API (FastAPI + SQLModel + Alembic)
- MCP server (Python FastMCP / TypeScript SDK, 7-phase workflow including plugin packaging)
- Testing (TDD, Playwright E2E, MCP live test)
- Frontend design (Anti-AI aesthetics, shadcn/ui, a11y)
- Game development (Godot 4.x + Rust gdext)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Languages | Python, TypeScript, Rust, Go |
| AI/Low-perf API | FastAPI + Modal.com |
| High-perf API | Echo (Go) |
| Frontend | Static Next.js 16 -> Cloudflare Pages |
| Desktop / Mobile | Tauri 2 (Rust) / React Native (Expo) |
| Game Dev | Godot Engine 4.x + Rust (gdext) |
| DB <-> Python | SQLModel + Alembic |
| DB <-> Go | sqlc + golang-migrate |
| API Spec | FastAPI auto-gen (Python) / swag (Go) |
| FE Client Gen | Orval -> TanStack Query + Zod |
| Auth | Firebase Auth (WIF, no service account) |
| Package Manager | bun (all JS/TS) |
| Runtime | Node 24 (LTS) |

## End-to-End Type Safety

```
DATABASE (PostgreSQL)
  -> DB <-> BE: SQLModel (Python) / sqlc (Go)
    -> API Contract: OpenAPI Spec
      -> Orval Code Generation -> TanStack Query hooks + Zod
        -> CLIENTS: Next.js (Web) + Expo (Mobile)
```

## Monorepo Structure

```
project/
  apps/
    api/              # Backend (FastAPI or Echo)
    web/              # Next.js (Static Export)
    desktop/          # Tauri 2 (Rust + React)
    mobile/           # Expo (React Native)
  packages/shared/    # Shared types, utils
  scripts/gen-api.sh  # Orval generation
```

## References (doc on demand)

- `references/web-nextjs.md` -- Next.js 16 static export, Cloudflare Pages deploy
- `references/mobile-expo.md` -- React Native Expo, EAS builds, Zustand, MMKV
- `references/desktop-tauri.md` -- Tauri 2 IPC, auto-update, capabilities, CI/CD matrix
- `references/api-go-echo.md` -- Echo handlers, sqlc, golang-migrate, Firebase Auth Go
- `references/api-python.md` -- FastAPI lifespan, LiteLLM proxy, health probe, OpenAPI gen
- `references/mcp-server.md` -- 5-phase MCP workflow, mega-tool pattern, registries, live test protocol
- `references/testing.md` -- TDD, Playwright E2E, factory functions, Page Objects, Go/Rust/Python testing
- `references/frontend-design.md` -- Anti-AI aesthetics, shadcn/ui, a11y, touch targets, animations
- `references/game-godot.md` -- Godot 4.x + Rust gdext, better-godot-mcp, scene design

Doc reference file tuong ung TRUOC KHI bat dau lam viec tren topic do.

## Quy tac chung

- Test Coverage >= 95% cho tat ca code.
- BUN only cho JS/TS (KHONG npm/yarn/pnpm).
- Firebase Auth: WIF (no service account). Chi can `APP_FIREBASE_PROJECT_ID`.
- Dodo Payments: Web checkout (KHONG Apple IAP). Expo/RN SDK available.
- 3-Environment: dev (localhost) / staging (api-staging) / production (api).
- Secrets: Infisical (app), Doppler (infra). KHONG commit .env files.
