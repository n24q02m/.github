---
name: observability
description: "Monitoring, logging, tracing cho infrastructure và applications. Sử dụng khi cấu hình Grafana Selfhost (Grafana + Loki + Alloy + Node Exporter + Vector), MLflow tracing, MLflow experiment tracking, hoặc debug production."
---

# Observability Guide

## Khi Nào Dùng

- Cấu hình Grafana Selfhost (Alloy, Loki, Vector) cho monitoring
- Thiết lập MLflow tracing cho AI/LLM applications
- Setup MLflow tracking cho ML experiments
- Cấu hình alerting rules và notification channels
- Debug production issues bằng logs/metrics/traces

> **Test Coverage**: ≥ 95% cho tất cả monitoring integrations và alert logic.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  APPLICATIONS (VM Prod)                                      │
│  FastAPI / Echo / Workers                                    │
│  → MLflow (AI/LLM tracing + experiment tracking)            │
│  → Structured Logs → Vector                                  │
├─────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE (VM Infra + VM Prod)                         │
│  → Alloy (Prometheus metrics)                                │
│  → Node Exporter (system metrics)                            │
│  → Vector (log collection + forwarding)                      │
├─────────────────────────────────────────────────────────────┤
│  GRAFANA SELFHOST (VM Infra)                                 │
│  → Metrics: Prometheus / Mimir                               │
│  → Logs: Loki                                                │
│  → Traces: Tempo (future)                                    │
│  → Dashboards + Alerting                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Metrics: Grafana Alloy + Node Exporter

### Alloy (Prometheus-compatible agent)

```yaml
# services/monitoring/alloy/config.alloy
prometheus.scrape "node_exporter" {
  targets = [{"__address__" = "node-exporter:9100"}]
  forward_to = [prometheus.remote_write.grafana_selfhost.receiver]
  scrape_interval = "60s"
}

prometheus.scrape "caddy" {
  targets = [{"__address__" = "caddy:2019"}]
  forward_to = [prometheus.remote_write.grafana_selfhost.receiver]
  scrape_interval = "60s"
}

// Thêm service metrics
prometheus.scrape "app_metrics" {
  targets = [{"__address__" = "oci-api:8000"}]
  metrics_path = "/metrics"
  forward_to = [prometheus.remote_write.grafana_selfhost.receiver]
  scrape_interval = "60s"
}

prometheus.remote_write "grafana_selfhost" {
  endpoint {
    url = env("GRAFANA_PROMETHEUS_URL")
    basic_auth {
      username = env("GRAFANA_PROMETHEUS_USERNAME")
      password = env("GRAFANA_API_KEY")
    }
  }
}
```

### Docker Compose

```yaml
services:
  alloy:
    image: grafana/alloy:latest
    container_name: oci-alloy
    restart: unless-stopped
    mem_limit: 256m
    volumes:
      - ./config/alloy:/etc/alloy
    command: ["run", "/etc/alloy/config.alloy"]
    networks:
      - oci-network

  node-exporter:
    image: prom/node-exporter:latest
    container_name: oci-node-exporter
    restart: unless-stopped
    mem_limit: 50m
    pid: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - "--path.procfs=/host/proc"
      - "--path.sysfs=/host/sys"
      - "--path.rootfs=/rootfs"
    networks:
      - oci-network
```

### App Metrics (Python)

```python
# FastAPI với prometheus_client
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)

    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## Logs: Vector → Grafana Loki

### Vector Config

```yaml
# services/monitoring/vector/vector.yaml
sources:
  docker_logs:
    type: docker_logs
    include_containers:
      - "oci-*"

transforms:
  parse_logs:
    type: remap
    inputs: ["docker_logs"]
    source: |
      .service = del(.container_name)
      .service = replace(.service, "oci-", "")
      # Parse JSON logs
      parsed, err = parse_json(.message)
      if err == null {
        . = merge(., parsed)
      }

sinks:
  loki:
    type: loki
    inputs: ["parse_logs"]
    endpoint: "${GRAFANA_LOKI_URL}"
    auth:
      strategy: basic
      user: "${GRAFANA_LOKI_USERNAME}"
      password: "${GRAFANA_API_KEY}"
    labels:
      service: "{{ service }}"
      host: "${HOSTNAME}"
    encoding:
      codec: json
```

### Structured Logging (Python)

```python
# Dùng loguru với JSON output
from loguru import logger
import sys

# Cấu hình JSON format cho production
logger.remove()
logger.add(
    sys.stderr,
    format="{message}",
    serialize=True,  # JSON output
    level="INFO",
)

# Usage
logger.info("User created", user_id=user.id, email=user.email)
logger.error("Payment failed", order_id=order.id, error=str(e))
```

### Structured Logging (Go)

```go
// Dùng slog (standard library)
import "log/slog"

logger := slog.New(slog.NewJSONHandler(os.Stderr, &slog.HandlerOptions{
    Level: slog.LevelInfo,
}))
slog.SetDefault(logger)

// Usage
slog.Info("User created", "user_id", user.ID, "email", user.Email)
slog.Error("Payment failed", "order_id", order.ID, "error", err)
```

---

## AI Tracing: MLflow

MLflow 3.x selfhost tại `mlflow.n24q02m.com`, **built-in authentication** (KHÔNG cần CF Access).
Apps trên VM access qua internal IP: `http://mlflow:5000`.

### Setup

```python
import mlflow

# VM internal (apps chạy trên cùng Docker network)
mlflow.set_tracking_uri("http://mlflow:5000")

# Local dev (qua public URL + basic auth)
mlflow.set_tracking_uri("https://mlflow.n24q02m.com")
os.environ["MLFLOW_TRACKING_USERNAME"] = os.environ["MLFLOW_USERNAME"]
os.environ["MLFLOW_TRACKING_PASSWORD"] = os.environ["MLFLOW_PASSWORD"]
```

### Trace RAG / LLM Pipeline

```python
@mlflow.trace(name="rag_pipeline")
async def rag_query(query: str) -> str:
    with mlflow.start_span(name="retrieval") as span:
        docs = await retrieve(query)
        span.set_attributes({
            "num_docs": len(docs),
            "sources": [d.source for d in docs],
        })

    with mlflow.start_span(name="reranking") as span:
        reranked = await rerank(query, docs)
        span.set_attributes({"top_score": reranked[0].score})

    with mlflow.start_span(name="llm_call") as span:
        response = await generate(query, reranked)
        span.set_inputs({"query": query, "context": [d.text for d in reranked]})
        span.set_outputs({"response": response})

    return response
```

> **LiteLLM Proxy integration**: Khi dùng LiteLLM Proxy, tracing tự động forward tới MLflow qua callback. Apps KHÔNG cần instrument LLM calls thủ công — LiteLLM callback handles it.

### Evaluation Scores

```python
# Log quality scores vào active run
with mlflow.start_run():
    mlflow.log_metrics({
        "relevance": 0.85,
        "faithfulness": 0.92,
        "answer_correctness": 0.78,
    })
```

---

## ML Tracking: MLflow

MLflow 3.x selfhost tại `mlflow.n24q02m.com`, **built-in authentication** (KHÔNG cần CF Access).

### Setup

```python
import mlflow

# Local dev (qua built-in auth)
mlflow.set_tracking_uri("https://mlflow.n24q02m.com")
os.environ["MLFLOW_TRACKING_USERNAME"] = os.environ["MLFLOW_USERNAME"]
os.environ["MLFLOW_TRACKING_PASSWORD"] = os.environ["MLFLOW_PASSWORD"]

# VM internal
mlflow.set_tracking_uri("http://mlflow:5000")
```

### Experiment Tracking

```python
mlflow.set_experiment("rag-pipeline-v2")

with mlflow.start_run(run_name="embedding-tuning"):
    mlflow.log_params({
        "model": "qwen3-embedding-0.6b",
        "chunk_size": 500,
        "overlap": 50,
    })

    for epoch in range(epochs):
        mlflow.log_metrics({
            "retrieval_precision": precision,
            "retrieval_recall": recall,
            "ndcg@10": ndcg,
        }, step=epoch)

    mlflow.log_artifact("evaluation_results.jsonl")
```

---

## LLM Gateway: LiteLLM Proxy

> **Nguyên tắc**: LiteLLM Proxy là **CÁCH DUY NHẤT** để gọi LLMs. Không fallback sang direct API keys. Apps chỉ giữ LiteLLM virtual key — không bao giờ giữ API key của Gemini/OpenAI/xAI.

### Tại sao bắt buộc

| Lợi ích | Mô tả |
|---------|-------|
| **Cost tracking** | Virtual keys per-app → theo dõi chi phí từng ứng dụng |
| **Credential isolation** | Apps không cần biết LLM API key thực — chỉ cần virtual key |
| **Model routing** | Credential-isolated routing: cùng model alias, khác project/key |
| **Tracing** | Tự động forward traces tới MLflow — không cần instrument thủ công |

### App Integration

```python
from openai import OpenAI

# Tất cả apps dùng LiteLLM Proxy — KHÔNG direct API
client = OpenAI(
    base_url="http://litellm:4000/v1",       # Internal Docker network (VM)
    api_key=os.environ["LITELLM_API_KEY"],    # Virtual key cho app này
)

response = client.chat.completions.create(
    model="gemini/gemini-3-flash",            # Model alias trong LiteLLM config
    messages=[{"role": "user", "content": "Hello"}],
)
```

### Virtual Keys

Mỗi app có virtual key riêng → track cost per app.

```bash
# Tạo virtual key cho app mới
curl -X POST http://litellm:4000/key/generate \
  -H "Authorization: Bearer ${LITELLM_MASTER_KEY}" \
  -d '{
    "key_alias": "my-app",
    "models": ["gemini/gemini-3-flash", "gemini/gemini-3-pro"]
  }'
```

### Checklist thêm LLM vào app mới

- [ ] Lấy virtual key từ LiteLLM (đừng tạo mới nếu đã có)
- [ ] Set `LITELLM_API_KEY` trong secrets (GitHub Secrets / Doppler)
- [ ] `base_url` = `http://litellm:4000/v1` (internal) hoặc `https://litellm.n24q02m.com/v1` (external)
- [ ] KHÔNG hardcode hoặc fallback sang direct LLM API key

---

## Per-Product Monitoring

Mỗi product cần dashboard riêng trong Grafana. KHÔNG gộp chung vào 1 dashboard "API".

### Dashboard per Product

| Product | API Container | Worker | Dashboard Panels |
|---------|---------------|--------|------------------|
| **KnowledgePrism** | `oci-klprism-api` | `oci-klprism-worker` | Request rate, Latency P95/P99, Error rate, Worker queue depth, RAG pipeline duration |
| **QuikShipping** | `oci-qship-api` | — | Request rate, Latency P95, Error rate, Shipping API response time |
| **Aiora** | `oci-aiora-api` | — | Request rate, Latency P95, Error rate |
| **Better Notion MCP** | `oci-better-notion-mcp` | — | Tool call rate, Latency P95, Notion API errors, Rate limit hits |

### Health Check Endpoint (bắt buộc mỗi service)

```python
# FastAPI health probe — kiểm tra từng dependency
@app.get("/health")
async def health():
    checks = {"status": "healthy", "uptime": time.time() - START_TIME}
    try:
        await db.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception:
        checks["database"] = "unhealthy"
        checks["status"] = "unhealthy"
    try:
        await redis.ping()
        checks["cache"] = "healthy"
    except Exception:
        checks["cache"] = "unhealthy"
        checks["status"] = "unhealthy"
    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(checks, status_code=status_code)
```

Alloy scrape health endpoints mỗi 30s → alert khi HTTP status != 200.

### Domain Health Checks

Cấu hình Grafana Synthetic Monitoring hoặc blackbox exporter cho:

| Domain | Expected | Alert Condition |
|--------|----------|-----------------|
| `klprism.com` | 200 | Down > 2 phút |
| `qship.app` | 200 | Down > 2 phút |
| `aiora.app` | 200 | Down > 2 phút |
| `*.n24q02m.com` (infra services) | 200/401 | Down > 5 phút |

### Correlation IDs (Python contextvars)

```python
import contextvars
from uuid import uuid4

correlation_id_var = contextvars.ContextVar("correlation_id", default="")

@app.middleware("http")
async def correlation_middleware(request, call_next):
    cid = request.headers.get("x-correlation-id", str(uuid4()))
    correlation_id_var.set(cid)
    response = await call_next(request)
    response.headers["x-correlation-id"] = cid
    return response

# Trong logger: tự động gắn correlation_id vào mọi log entry
logger.configure(extra={"correlation_id": lambda: correlation_id_var.get("")})
```

> **Cross-service**: Khi service A gọi service B, forward `X-Correlation-ID` header → trace request xuyên suốt.

---

## Alerting (Grafana Selfhost)

### Nguyên tắc Alerting

**Alert tốt** = rate-based, có thời gian đủ lâu, yêu cầu hành động cụ thể:
- Error rate > 1% trong 5 phút → actionable
- P99 latency > 2s trong 10 phút → meaningful
- Disk usage > 80% → preventive

**Alert xấu** = event-based, quá nhạy, không có hành động rõ ràng:
- CPU spike 30 giây → quá noisy
- Bất kỳ 1 lỗi 500 → quá sensitive
- "Có gì đó sai" → không actionable

> **Alert fatigue là thật**. Mỗi alert phải yêu cầu human action cụ thể. Nếu không → xoá alert đó.

### Key Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| High CPU | > 80% for 5min | Warning |
| High Memory | > 90% for 5min | Critical |
| Disk Space Low | < 10% free | Critical |
| Service Down | container restart > 3 in 10min | Critical |
| API Error Rate | 5xx > 1% for 5min | Warning |
| API Latency | P95 > 2s for 5min | Warning |
| Health Check Failed | HTTP != 200 for 2min | Critical |
| Domain Unreachable | Probe failed for 2min | Critical |

### Alert Channel
- **Primary**: Notification qua Grafana selfhost alerting
- **Escalation**: Email cho critical alerts

---

## Debug Production Issues

### Workflow

```
1. Kiểm tra Grafana dashboards (metrics overview)
2. Lọc Loki logs theo service + time range
3. Kiểm tra MLflow traces (cho AI/LLM-related issues)
4. SSH vào VM nếu cần: ssh user@vm-ip
5. Docker logs: docker logs oci-<service> --tail 100 -f
6. Container stats: docker stats --no-stream
```

### Common Queries (Loki)

```logql
# Error logs cho service cụ thể
{service="api"} |= "error" | json

# Slow requests (> 2s)
{service="api"} | json | duration > 2s

# Tất cả errors trong giờ qua
{host="oci-prod"} |= "ERROR" | json
```

---

## Checklist

- [ ] Alloy + Node Exporter deployed và scraping metrics?
- [ ] Vector collecting Docker logs và forwarding tới Loki?
- [ ] Structured logging (JSON) trong tất cả services?
- [ ] MLflow tracing cho AI/LLM pipelines?
- [ ] MLflow tracking cho ML experiments?
- [ ] LiteLLM Proxy: apps dùng proxy thay vì direct API keys?
- [ ] LiteLLM: virtual key per app cho cost tracking?
- [ ] App metrics exposed (/metrics endpoint)?
- [ ] Health check endpoint (`/health`) cho mỗi service?
- [ ] Correlation ID middleware trong tất cả FastAPI services?
- [ ] Grafana dashboard riêng cho mỗi product?
- [ ] Domain health checks configured?
- [ ] Alerting rules set cho critical metrics (rate-based, không event-based)?
- [ ] Test coverage ≥ 95% cho monitoring integrations?
