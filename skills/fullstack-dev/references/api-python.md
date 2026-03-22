# API Python FastAPI (AI Services)

Dùng cho AI/ML endpoints: RAG pipeline, embeddings, reranking, LLM generation.

## Cấu Trúc

```
apps/api/           # hoặc apps/ai/
├── pyproject.toml  # uv project
├── Dockerfile
├── src/
│   ├── main.py         # FastAPI app + lifespan
│   ├── config.py       # Pydantic Settings
│   ├── deps.py         # Dependencies injection
│   ├── routers/
│   │   ├── health.py   # /health endpoint (bắt buộc)
│   │   └── rag.py      # Domain routers
│   ├── services/       # Business logic
│   ├── schemas/        # Pydantic models (request/response)
│   └── db/
│       ├── models.py   # SQLModel models
│       └── session.py  # AsyncSession factory
└── tests/
```

## Patterns

### Lifespan (startup/shutdown)

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB pool, connect services
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    # Shutdown: cleanup
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

### LLM Calls — LiteLLM Proxy ONLY

```python
from openai import AsyncOpenAI

llm = AsyncOpenAI(
    base_url="http://litellm:4000/v1",
    api_key=settings.LITELLM_API_KEY,
)
# KHÔNG BAO GIỜ import trực tiếp google.generativeai, openai key, etc.
```

### Health Probe + Metrics

```python
@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    checks = {"status": "healthy"}
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception:
        checks["database"] = "unhealthy"
        checks["status"] = "unhealthy"
    return JSONResponse(checks, status_code=200 if checks["status"] == "healthy" else 503)

@router.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### OpenAPI Schema Generation (cho Orval)

```python
app = FastAPI(
    title="KnowledgePrism API",
    version="1.0.0",
    servers=[
        {"url": "/api/v1", "description": "Production"},
    ],
)(
# Export: python -m src.main --export-openapi > openapi.json
```

## Testing

```bash
# Chạy tests
uv run pytest tests/ -v --cov=src --cov-report=term-missing
# Coverage target: ≥ 95%
```

Dùng `httpx.AsyncClient` + `pytest-asyncio` cho async test.

## Deploy

```yaml
# docker-compose.yml
services:
  api:
    build: .
    container_name: oci-<product>-api
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 0.25G  # Tuỳ product
    env_file: .env
    networks:
      - oci-network
```
