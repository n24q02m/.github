
# Thêm Service vào OCI VM

## Khi Nào Dùng

- Deploy service mới lên OCI VM (Infrastructure hoặc Production)
- Cấu hình Docker Compose cho service
- Setup Caddy reverse proxy cho domain mới
- Cấu hình Cloudflare Access cho service bảo mật
- Allocate resources (Dragonfly, Qdrant, FalkorDB)

> **Test Coverage**: ≥ 95% cho tất cả infrastructure scripts và configs.

## VM Architecture

| VM | Path | Repo | Purpose | Specs |
|----|------|------|---------|-------|
| **VM 1: Infrastructure** | `/opt/oci-infra` | [oci-vm-infra](https://github.com/n24q02m/oci-vm-infra) | Databases, Observability, Secrets | 3 OCPU, 16 GB RAM, 150 GB Disk |
| **VM 2: Production** | `/opt/oci-prod` | [oci-vm-prod](https://github.com/n24q02m/oci-vm-prod) | Application APIs, Workers, CLIProxyAPIPlus | 3 OCPU, 16 GB RAM, 50 GB Disk |

## Cấu trúc Service

```
services/<tên-service>/
├── docker-compose.yml    # Service definition
└── <config-files>        # Cấu hình riêng (nếu cần)
```

---

## Workflow: Thêm Service Mới

### Bước 1: Tạo thư mục service

```bash
mkdir -p services/<tên-service>
```

### Bước 2: Tạo docker-compose.yml

```yaml
services:
  <tên-service>:
    image: <image>:<tag>
    container_name: oci-<tên-service>
    restart: unless-stopped
    mem_limit: <limit>
    environment:
      - VAR1=${VAR1}
    volumes:
      - <tên-service>-data:/data
    networks:
      - oci-network

volumes:
  <tên-service>-data:

networks:
  oci-network:
    external: true
```

### Bước 3: Include vào root docker-compose.yml

```yaml
include:
  - services/<tên-service>/docker-compose.yml
```

### Bước 4: Cấu hình Doppler secrets

| Environment | Doppler Project |
|-------------|-----------------|
| Infrastructure | `oci-vm-infra` |
| Production | `oci-vm-prod` |

### Bước 5: Cấu hình Caddy (nếu expose)

Thêm reverse proxy vào Caddyfile:

```caddyfile
{$TEN_SERVICE_DOMAIN} {
    reverse_proxy oci-<ten-service>:<port>
}
```

### Bước 6: Cấu hình Cloudflare Access (nếu cần auth)

Tạo CF Access Application trong Dashboard:
- **Auth Method**: OTP (UI) hoặc Service Token (API)
- **Policy**: Email domain hoặc Service Token

### Bước 7: Deploy

```bash
make up
make logs-<tên-service>
```

---

## Memory Limits Reference (VM Infra - 16 GB RAM, 150 GB Disk)

| Service | Limit | Category |
|---------|-------|----------|
| PostgreSQL | 2 GB | Database |
| Qdrant | 1.5 GB | Vector DB |
| FalkorDB | 2 GB | Graph DB |
| Dragonfly | 1.5 GB | Cache |
| MLflow | 2 GB | Observability (Tracing + Experiment Tracking) |
| Infisical | 1 GB | Secrets |
| Alloy | 0.25 GB | Monitoring Agent |
| Node Exporter | 0.05 GB | Monitoring Agent |
| Vector | 0.25 GB | Log Collector |
| Caddy | 0.125 GB | Proxy |

> **Monitoring**: Grafana Selfhost (metrics, logs, traces). Agents: Alloy, Node Exporter, Vector.

## Memory Limits Reference (VM Prod - 16 GB RAM, 50 GB Disk)

| Service | Limit | Category |
|---------|-------|----------|
| KnowledgePrism API | 2.5 GB | Python FastAPI (AI) |
| KnowledgePrism Worker | 0.5 GB | Celery Worker |
| KnowledgePrism Go API | 0.25 GB | Go Echo (CRUD) |
| QuikShipping API | 0.5 GB | Python FastAPI |
| Aiora API | 0.25 GB | Python FastAPI |
| Better Notion MCP | 0.125 GB | TypeScript MCP |
| Cloudflared | 0.125 GB | Tunnel |
| Watchtower | 0.125 GB | Auto-update |
| Caddy | 0.125 GB | Proxy |
| Alloy | 0.25 GB | Monitoring Agent |
| Node Exporter | 0.05 GB | Monitoring Agent |
| cAdvisor | 0.125 GB | Container Metrics |

> **Staging**: Mỗi product có staging instance riêng với memory giảm (~50% so với prod). Chỉ deploy staging khi cần test.

---

## Resource Allocation Scripts

### Dragonfly Database
```bash
# Tạo user với quyền truy cập DB index
./scripts/auth/dragonfly_mgr.sh -u <user> -p <password> -d <db_index>
```

| DB | Service | Purpose |
|----|---------|---------|
| 0 | Infisical | Session/cache |
| 1 | LiteLLM | Proxy cache |
| 2 | KnowledgePrism (prod) | App cache |
| 3 | KnowledgePrism (staging) | App cache |
| 4 | Aiora (prod) | App cache |
| 5 | Aiora (staging) | App cache |

### Qdrant Collection
```bash
# Mint JWT token cho app (prefix-based access)
doppler run -- uv run ./scripts/auth/qdrant_mint.py <app_name>
```

Collection naming: `<app_name>_*` (prefix pattern)

### FalkorDB Database
```bash
# FalkorDB sử dụng Redis protocol, tạo user với ACL
./scripts/auth/falkordb_manager.sh -u <user> -p <password> -g <graph_name>
```

---

## Checklist Thêm Service

- [ ] Chọn đúng VM (infra vs prod)
- [ ] Tạo `services/<tên-service>/docker-compose.yml`
- [ ] Set `mem_limit` phù hợp
- [ ] Include vào root docker-compose
- [ ] Thêm secrets vào Doppler
- [ ] Cấu hình Caddy reverse proxy (nếu expose)
- [ ] Cấu hình CF Access (nếu cần auth)
- [ ] Allocate resources (Dragonfly DB, Qdrant collection, etc.)
- [ ] Test: `make up && make logs-<service>`
- [ ] Cập nhật README.md

---

## Backup (Infra VM)

| Service | Backup | Retention |
|---------|--------|-----------|
| PostgreSQL | 2x/ngày | Local: 7d, R2/GDrive: 30d |
| Qdrant | 2x/ngày | Local: 7d, R2/GDrive: 30d |
| FalkorDB | 2x/ngày | Local: 7d, R2/GDrive: 30d |
| Dragonfly | 2x/ngày | Local: 7d, R2/GDrive: 30d |

```bash
# Manual backup
make backup

# Restore
./scripts/restore.sh <service> <backup-file>
```
