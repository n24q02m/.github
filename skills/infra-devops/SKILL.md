---
name: infra-devops
description: "Infrastructure, DevOps, CI/CD, security. OCI VM, Docker, Caddy, monitoring (Grafana, Alloy, Loki, Vector), MLflow, Doppler, Infisical, GitHub Actions, pre-commit, mise, PSR, Renovate, security audit."
---

# Infrastructure & DevOps

## Khi nao dung

- Deploy service len OCI VM (Infrastructure hoac Production)
- Cau hinh Docker Compose, Caddy reverse proxy, Cloudflare Access
- Allocate resources (Dragonfly DB, Qdrant collection, FalkorDB)
- Monitoring: Grafana Selfhost, Alloy, Loki, Vector, Node Exporter
- MLflow tracing (AI/LLM) va experiment tracking
- LiteLLM Proxy: virtual keys, model routing, cost tracking
- Secrets management: Doppler (infra), Infisical (app)
- Docker security: multi-stage build, BuildKit cache, non-root user
- Dependency scanning: Semgrep, Renovate, Trivy
- CI/CD: GitHub Actions, PSR v10, pre-commit hooks
- Repository structure: mise, linting, CODEOWNERS
- Cloudflare Access, Firebase Auth security, rate limiting

## Infrastructure

```
EDGE: Cloudflare Pages (Static Next.js)
         | CF Tunnel
VM 2 (Prod): FastAPI + Echo, Docker Compose (3 OCPU, 16GB, 50GB)
         |   Repo: https://github.com/n24q02m/oci-vm-prod
VM 1 (Infra): PostgreSQL, Qdrant, FalkorDB, Dragonfly, Infisical, MLflow (3 OCPU, 16GB, 150GB)
              Repo: https://github.com/n24q02m/oci-vm-infra

MONITORING: Grafana + Loki selfhost (Alloy, Node Exporter, Vector) tren VM Infra
```

- **Ingress**: CF Tunnel + Caddy. **CF Access**: Chi bao ve selfhost services (KHONG bao ve API).
- **Secrets**: Doppler (Infra), Infisical (App). **Auth**: Firebase Auth.

## Storage (Polyglot Persistence)

| Loai | Service | Muc dich |
|------|---------|----------|
| Relational | PostgreSQL | User Data, Auth, Transactions, Logging |
| Vector | Qdrant | Embeddings, Semantic Search |
| Graph | FalkorDB | Knowledge Graph, GraphRAG |
| Cache | Dragonfly | Caching, Semantic Cache |
| Object | R2 (primary), GDrive (backup) | Files, Media |

## Dev Tools (Mise)

Terraform, uv, ruff, ty, pnpm, biome, golangci-lint, gofumpt, Infisical, Doppler, GitHub, Wrangler.

**Fixed Versions**: Python 3.13, Node 24, Java 21. Cac tool khac: latest.

## References (doc on demand)

- `references/oci-vm.md` -- VM architecture, deploy workflow, memory limits, resource allocation scripts, backup
- `references/observability.md` -- Grafana Selfhost, Alloy, Vector, Loki, MLflow tracing/tracking, LiteLLM Proxy, alerting
- `references/security.md` -- Secrets management (Doppler/Infisical), Docker security, dependency scanning, auth, rate limiting
- `references/repo-structure.md` -- Repository standards, mise tasks, pre-commit, Git branching, README format, Renovate, Docker build
- `references/ci-cd.md` -- CI/CD workflow templates (Python/TS/Go/Rust), PR title check, Semgrep, Qodo Merge, email notify
- `references/semantic-release.md` -- PSR v10 config (Python/TS/Rust/Go), monorepo, beta/stable, troubleshooting

Doc reference file tuong ung TRUOC KHI bat dau lam viec tren topic do.
