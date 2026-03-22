---
name: security-practices
description: "Bảo mật ứng dụng và infrastructure. Sử dụng khi quản lý secrets (Doppler/Infisical), bảo mật Docker, dependency scanning, Cloudflare Access, Firebase Auth security."
---

# Security Practices Guide

## Khi Nào Dùng

- Quản lý secrets với Doppler (infra) hoặc Infisical (app)
- Bảo mật Docker containers và images
- Setup dependency scanning (Semgrep, Renovate)
- Cấu hình Cloudflare Access cho services
- Audit security cho ứng dụng và infrastructure

> **Test Coverage**: ≥ 95% cho tất cả security validations và auth logic.

### Bảng Bác Bỏ Lý Do Bỏ Qua Security

| Lý do | Thực tế |
|-------|---------|
| "Chỉ là internal service" | Internal services bị compromise → lateral movement toàn hệ thống. |
| "Biến môi trường an toàn mà" | `.env` commit lên git = leak vĩnh viễn (git history). |
| "Hardcode tạm, sửa sau" | "Tạm" biến thành permanent. Secret trong code = 1 git push là lộ. |
| "Service nhỏ, không ai hack đâu" | Automated scanners quét mọi IP. Nhỏ hay lớn đều bị scan. |
| "Docker image tin tưởng được" | Base image có thể chứa CVE. Luôn scan, luôn pin version. |
| "--no-verify nhanh hơn" | Pre-commit hooks tồn tại vì lý do. Bypass = đưa secret/vuln vào prod. |

## Secrets Management

### Hierarchy

| Layer | Tool | Scope | Khi nào dùng |
|-------|------|-------|-------------|
| Infrastructure | Doppler | VM-level env vars | Docker Compose, system services |
| Application | Infisical | App-level secrets (ALL projects) | API keys, DB credentials, deploy tokens |
| CI/CD | GitHub Secrets (auto-sync from Infisical) | Workflow secrets | Infisical prod -> GitHub Secrets (overwrite mode) |
| Runtime | Platform secrets (GCloud Secret Manager, Modal) | Container runtime | Bổ sung Infisical, không thay thế |
| Local Dev | `.env` files | Developer machine | **KHÔNG commit vào git** |

> **BẮT BUỘC**: Mọi project (public lẫn private) đều dùng Infisical làm source of truth cho secrets. Infisical prod auto-sync sang GitHub Secrets (overwrite mode). Platform secrets (GCloud Secret Manager, Modal) dùng cho runtime nếu platform yêu cầu.

### Rules BẮT BUỘC

```
# .gitignore — LUÔN CÓ các patterns này
.env
.env.*
!.env.example
*.pem
*.key
**/secrets/
```

- **KHÔNG BAO GIỜ** hardcode secrets trong code
- **KHÔNG BAO GIỜ** log secrets (kể cả masked)
- **KHÔNG BAO GIỜ** commit `.env` files
- Dùng `os.environ` / `process.env` — truyền qua environment variables
- Rotate secrets định kỳ (90 ngày cho production)

### Doppler (Infrastructure)

```bash
# Setup
doppler setup --project oci-vm-infra --config prd

# Inject vào Docker Compose
doppler run -- docker compose up -d

# Inject vào script
doppler run -- ./scripts/backup.sh
```

### Infisical (Application)

```python
# Python SDK
from infisical_sdk import InfisicalSDKClient

client = InfisicalSDKClient(host="https://infisical.n24q02m.com")
client.auth.universal_auth.login(
    client_id=os.environ["INFISICAL_CLIENT_ID"],
    client_secret=os.environ["INFISICAL_CLIENT_SECRET"],
)

secrets = client.secrets.list(
    project_id="project-id",
    environment="prod",
    secret_path="/",
)
```

```go
// Go SDK
import infisical "github.com/infisical/go-sdk"

client := infisical.NewInfisicalClient(context.Background(), infisical.Config{
    SiteURL: "https://infisical.n24q02m.com",
})

client.Auth().UniversalAuthLogin("client-id", "client-secret")

secrets, _ := client.Secrets().List(infisical.ListSecretsOptions{
    ProjectID:   "project-id",
    Environment: "prod",
    SecretPath:  "/",
})
```

---

## Docker Security

### Image Best Practices

```dockerfile
# syntax=docker/dockerfile:1

# 1. BuildKit syntax directive — BẮT BUỘC dòng đầu tiên
# Đảm bảo BuildKit features hoạt động nhất quán (mount cache, bind mounts)

# 2. Dùng specific version tags (KHÔNG dùng :latest)
FROM python:3.13-slim-bookworm AS base

# 3. Non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -m appuser

# 4. Multi-stage build (giảm attack surface)
FROM base AS builder
COPY . .
RUN uv sync --frozen --no-dev

FROM base AS runtime
COPY --from=builder /app/.venv /app/.venv
USER appuser

# 5. Read-only filesystem khi có thể
# docker run --read-only --tmpfs /tmp myapp

# 6. Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1
```

### .dockerignore (BẮT BUỘC)

Mỗi Dockerfile **PHẢI** có `.dockerignore` tương ứng để giảm build context size và tránh leak thông tin nhạy cảm:

```dockerignore
# Git
.git
.github

# IDE
.vscode
.idea

# Cache
.ruff_cache
.pytest_cache
__pycache__

# Development
tests/
temp/
docs/
*.md
!README.md

# Docker
Dockerfile
docker-compose.yml
.dockerignore

# Config (không cần trong runtime)
.pre-commit-config.yaml
.editorconfig
.mise.toml

# Environment
.env
.env.*
```

### BuildKit Cache Patterns

> **Nguyên tắc**: Tách dependency install và project install để tối ưu Docker layer cache.
> Dùng `--mount=type=cache` cho package manager cache và `--mount=type=bind` cho lock files.

#### Python (uv)

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Bước 1: Cài dependencies (cached khi deps không đổi)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Bước 2: Copy code và cài project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev
```

#### Node.js (bun)

```dockerfile
FROM oven/bun:alpine AS builder
WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .
RUN bun run build
```

#### Go

```dockerfile
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
```

### Docker Compose Security

```yaml
services:
  api:
    image: myapp:v1.2.3
    restart: unless-stopped
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    mem_limit: 512m
    cpus: 0.5
    networks:
      - oci-network
    # KHÔNG expose ports trực tiếp — dùng Caddy reverse proxy
```

### Container Scanning

```yaml
# CI: Scan Docker images
- name: Build image
  run: docker build -t myapp:${{ github.sha }} .

- name: Scan with Trivy
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: myapp:${{ github.sha }}
    format: table
    exit-code: 1
    severity: CRITICAL,HIGH
```

---

## Dependency Security

### Automated Scanning

```yaml
# .github/workflows/ci.yml — dependency-review job
dependency-review:
  name: Dependency Review
  if: github.event_name == 'pull_request'
  runs-on: ubuntu-latest
  continue-on-error: true  # cho private repos
  steps:
    - uses: actions/checkout@v6
    - uses: actions/dependency-review-action@v4
      with:
        fail-on-severity: moderate
        comment-summary-in-pr: always
```

### Language-Specific Audits

```bash
# Python
uv pip audit

# Node.js
bun pm audit

# Go
govulncheck ./...

# Rust
cargo audit
```

### Dependabot (GitHub native)

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      minor-and-patch:
        update-types: ["minor", "patch"]

  - package-ecosystem: "npm"
    directory: "/apps/web"
    schedule:
      interval: "weekly"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## Authentication & Authorization

### Firebase Auth Security Rules

```javascript
// Firestore Security Rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Authenticated users only
    match /users/{userId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if request.auth != null && request.auth.uid == userId;
    }

    // Admin-only
    match /admin/{document=**} {
      allow read, write: if request.auth != null
        && request.auth.token.admin == true;
    }

    // Default deny
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

### Backend Token Validation

```python
# FastAPI middleware pattern
from firebase_admin import auth

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    try:
        decoded = auth.verify_id_token(credentials.credentials)
        # Kiểm tra token expiration
        if decoded.get("exp", 0) < time.time():
            raise HTTPException(status_code=401, detail="Token expired")
        return decoded
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token expired")
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")
```

---

## Cloudflare Access

### Bảo vệ Selfhost Services

Dùng CF Access để bảo vệ **selfhost services** (Infisical UI). **KHÔNG** bảo vệ API endpoints (API dùng Firebase Auth). MLflow dùng built-in auth — KHÔNG cần CF Access.

| Service | Auth Method | Policy |
|---------|-------------|--------|
| Infisical UI | OTP (email) | Allowed emails |
| API (app) | Service Token | Machine-to-machine |

> **MLflow**: Built-in authentication (username/password). Apps trên VM access qua internal IP (`http://mlflow:5000`), không cần CF Access headers. External access (local dev) qua `https://mlflow.n24q02m.com` với basic auth (`MLFLOW_TRACKING_USERNAME` / `MLFLOW_TRACKING_PASSWORD`).

### Service Token (Machine-to-Machine)

```python
import os
import httpx

# Headers cho CF Access
headers = {
    "CF-Access-Client-Id": os.environ["CF_ACCESS_CLIENT_ID"],
    "CF-Access-Client-Secret": os.environ["CF_ACCESS_CLIENT_SECRET"],
}

# Request qua CF Access
response = httpx.get("https://mlflow.n24q02m.com/api/...", headers=headers)
```

---

## Network Security

### Docker Network Isolation

```yaml
# docker-compose.yml
networks:
  oci-network:
    driver: bridge
    ipam:
      config:
        - subnet: 10.0.0.0/24

# Services chỉ giao tiếp trong internal network
# Caddy là duy nhất expose port ra ngoài
```

### Caddy (TLS + Reverse Proxy)

```caddyfile
# Auto HTTPS via CF Tunnel — TLS terminated at Cloudflare
{$SERVICE_DOMAIN} {
    reverse_proxy oci-{service}:{port}

    # Security headers
    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        Referrer-Policy strict-origin-when-cross-origin
        -Server
    }
}
```

### Rate Limiting (API)

```python
# FastAPI với slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(request: Request):
    ...
```

```go
// Echo với rate limiter middleware
import "github.com/labstack/echo/v4/middleware"

e.Use(middleware.RateLimiter(middleware.NewRateLimiterMemoryStore(20)))
```

---

## Security Audit Checklist

### Secrets
- [ ] Không có hardcoded secrets trong code?
- [ ] `.env` files trong `.gitignore`?
- [ ] Secrets được quản lý bởi Doppler/Infisical?
- [ ] CI/CD secrets trong GitHub Secrets?
- [ ] Secret rotation policy (90 ngày)?

### Docker
- [ ] BuildKit syntax directive (`# syntax=docker/dockerfile:1`) ở dòng đầu?
- [ ] `.dockerignore` có mặt và đầy đủ?
- [ ] Dùng specific image tags (không `:latest`)?
- [ ] Non-root user trong Dockerfile?
- [ ] Multi-stage builds?
- [ ] BuildKit `--mount=type=cache` cho package managers?
- [ ] Tách dependency install và project install (cache optimization)?
- [ ] `mem_limit` và `cpus` set cho mọi service?
- [ ] `no-new-privileges:true`?
- [ ] Container scanning trong CI?

### Dependencies
- [ ] `dependency-review-action` trong CI?
- [ ] Language-specific audit commands chạy định kỳ?
- [ ] Dependabot configured?

### Authentication
- [ ] Firebase Auth security rules configured?
- [ ] Token validation ở backend (verify + expiration check)?
- [ ] Rate limiting ở auth endpoints?

### Network
- [ ] Services chỉ giao tiếp qua internal Docker network?
- [ ] Chỉ Caddy expose port ra ngoài?
- [ ] CF Access bảo vệ selfhost UIs?
- [ ] Security headers set trong Caddy?
