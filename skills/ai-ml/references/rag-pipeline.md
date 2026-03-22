
# RAG Pipeline Engineering Guide

## Khi Nào Dùng

- Xây dựng search/retrieval pipeline cho ứng dụng AI
- Data ingestion pipeline (3-Fusion: PDF/Image, Text, Video/Audio)
- Implement semantic chunking cho documents
- Cấu hình vector search với Qdrant
- Thiết kế graph traversal với FalkorDB
- Implement dynamic reranking (Text vs VL routing)
- Setup semantic cache với Dragonfly
- OCR extraction cho PDF/documents (DeepSeek OCR 2)
- Audio/video transcription (Qwen3 ASR)

Xem thêm: `dl-training`, `observability` (MLflow tracing).

## Models

| Task | Model | Dim / Note | Hosting |
|------|-------|-----------|---------|
| Multimodal Embedding | Gemini Embedding 2 | 3072D + MRL, text/image/video/audio/PDF | API (LiteLLM) |
| Text Embedding (light) | Qwen3-Embedding-0.6B | 1024D, text-only, real-time | Modal selfhost |
| Text Embedding (heavy) | Qwen3-Embedding-8B | 1024D, text-only, batch | Modal selfhost |
| Text Reranker (light) | Qwen3-Reranker-0.6B | Cross-encoder | Modal selfhost |
| Text Reranker (heavy) | Qwen3-Reranker-8B | Cross-encoder | Modal selfhost |
| VL Reranker (light) | Qwen3-VL-Reranker-2B | Text + Image + Video + Doc | Modal selfhost |
| VL Reranker (heavy) | Qwen3-VL-Reranker-8B | Text + Image + Video + Doc | Modal selfhost |
| OCR | DeepSeek-OCR-2 | 3.34B MoE, BM25 text + table extraction | Modal selfhost |
| ASR | Qwen3-ASR-0.6B / 1.7B | Audio → text transcription | Modal selfhost |
| Generation | Gemini 3 Flash / Pro | LLM | API (LiteLLM) |

> **Gemini Embedding 2**: Primary embedding cho mọi modality. MRL cho phép cắt 3072D → 1024/512/256.
> **Qwen3 Embedding**: Dùng khi cần text-only embedding nhanh, chi phí thấp (Modal selfhost).
> **Dynamic Reranking**: Text query → Text Reranker. Image/Video/Doc query → VL Reranker. Audio → ASR → Text Reranker.

> **Test Coverage**: ≥ 95% cho tất cả RAG pipeline code.

---

## 3-Fusion Data Ingestion (Dynamic Routing by MIME Type)

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT DOCUMENT                             │
│              (Detect MIME type at upload)                     │
└──────────┬──────────────┬──────────────┬────────────────────┘
           │              │              │
    PDF/Image         Text           Video/Audio
           │              │              │
           ▼              │              ▼
   DeepSeek OCR 2         │        Qwen3 ASR
   (extract text,         │        (transcribe)
    tables, layout)       │              │
           │              │              │
           ▼              ▼              ▼
   ┌───────────────────────────────────────────┐
   │          3 Parallel Storage Paths          │
   ├───────────────────────────────────────────┤
   │  1. Raw Text → PostgreSQL (BM25 source)   │
   │  2. Gemini Embedding 2 → Qdrant (vectors)  │
   │  3. Text → LLM NER → FalkorDB (graph)     │
   └───────────────────────────────────────────┘
```

### Ingestion Code Pattern
```python
async def ingest_document(file: UploadFile) -> str:
    mime = file.content_type

    if mime in ("application/pdf", "image/png", "image/jpeg"):
        # OCR → extract structured text
        ocr_result = await ocr_extract(file)  # DeepSeek OCR 2 via Modal
        raw_text = ocr_result.text
        # Also embed raw file with Gemini Embedding 2 (multimodal)
        embedding = await embed_multimodal(file)
    elif mime.startswith("video/") or mime.startswith("audio/"):
        # ASR → transcript
        transcript = await asr_transcribe(file)  # Qwen3 ASR via Modal
        raw_text = transcript.text
        embedding = await embed_multimodal(file)  # Gemini Embedding 2
    else:
        # Plain text
        raw_text = await file.read()
        embedding = await embed_text(raw_text)  # Gemini Embedding 2 or Qwen3

    # 3 parallel storage paths
    await asyncio.gather(
        store_postgresql(raw_text, metadata),    # BM25 source
        store_qdrant(embedding, metadata),       # Vector search
        extract_and_store_graph(raw_text),       # LLM NER → FalkorDB
    )

async def incremental_kg_update(new_text: str, doc_id: str):
    """Incremental KG update (LightRAG pattern) — chỉ cập nhật subgraph liên quan."""
    new_entities = await extract_entities(new_text)
    existing = await graph_client.query(
        "MATCH (n:Entity) WHERE n.doc_id = $doc_id RETURN n", {"doc_id": doc_id}
    )
    # Diff: chỉ thêm/xoá entities thay đổi, giữ nguyên phần còn lại
    to_add = new_entities - existing
    to_remove = existing - new_entities
    await graph_client.merge_entities(to_add)
    await graph_client.remove_entities(to_remove)
```

---

## Triple Fusion Retrieval Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    QUERY PROCESSING                          │
├─────────────────────────────────────────────────────────────┤
│  Query Rewriting → HyDE Expansion → Multi-Query Generation  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              TRIPLE FUSION RETRIEVAL (Parallel)              │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Vector Search │   Sparse Search │   Graph Traversal       │
│   (Qdrant)      │   (BM25)        │   (FalkorDB)            │
│ Gemini          │   PostgreSQL    │   Cypher queries        │
│ Embedding 2     │   full-text     │                         │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                FUSION & DYNAMIC RERANKING                    │
├─────────────────────────────────────────────────────────────┤
│  RRF Fusion → Dynamic Router → Reranker → MMR               │
│               ├─ Text → Qwen3-Reranker-0.6B / 8B            │
│               ├─ Image/Doc → Qwen3-VL-Reranker-2B / 8B      │
│               └─ Audio → ASR → Qwen3-Reranker               │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  GENERATION + GUARDRAILS                     │
├─────────────────────────────────────────────────────────────┤
│  Context Compression → LLM Generation → NeMo Guardrails     │
│                        (Gemini 3 Flash)   (Output Filtering) │
└─────────────────────────────────────────────────────────────┘
```

---

## Chunking Strategies

### Semantic Chunking (chonkie — Recommended)
```python
from chonkie import SemanticChunker

# chonkie: fast chunking library with Qdrant integration
chunker = SemanticChunker(
    embedding_model="gemini-embedding-2",
    threshold=0.7,
    min_chunk_size=100,
    max_chunk_size=1000,
)
chunks = chunker.chunk(document)
```

### Layout-Aware Chunking (Structured Documents)
```python
# For books/PDFs with clear structure (headings, paragraphs, tables)
# Preserves document hierarchy — better accuracy than fixed-size
from chonkie import RecursiveChunker

chunker = RecursiveChunker(
    chunk_size=1000,
    chunk_overlap=100,
    separators=["\n## ", "\n### ", "\n\n", "\n", ". "],  # heading-first
)
chunks = chunker.chunk(document)
```

### Parent-Child Relationships
```python
# Retrieve children (precise), return parents (context-rich)
parent_chunks = chunk_document(doc, size=2000, overlap=200)
for parent in parent_chunks:
    children = chunk_text(parent.text, size=400, overlap=50)
    for child in children:
        child.metadata["parent_id"] = parent.id
```

---

## Retrieval Implementation

### Vector Search (Qdrant)
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(url="http://qdrant:6333")

# Search with filters
results = client.search(
    collection_name="documents",
    query_vector=query_embedding,
    limit=20,
    query_filter=Filter(
        must=[FieldCondition(key="source", match=MatchValue(value="knowledge_base"))]
    ),
)
```

### Sparse Search (BM25)
```python
from rank_bm25 import BM25Okapi

# Build index
tokenized_corpus = [doc.split() for doc in documents]
bm25 = BM25Okapi(tokenized_corpus)

# Search
tokenized_query = query.split()
scores = bm25.get_scores(tokenized_query)
top_k = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:20]
```

### Graph Traversal (FalkorDB) — Dual-Level Queries

LightRAG pattern: chọn query mode dựa trên loại câu hỏi.

```cypher
// LOCAL mode: entity + neighbors (cho câu hỏi cụ thể)
MATCH (n:Entity)-[r*1..2]-(related)
WHERE n.name = $entity_name
RETURN n, r, related
LIMIT 50

// GLOBAL mode: community summaries (cho câu hỏi tổng quát)
MATCH (c:Community)-[:CONTAINS]->(e:Entity)
WHERE c.summary CONTAINS $keyword
RETURN c.summary, collect(e.name) AS entities
LIMIT 10
```

```python
async def graph_retrieve(query: str, mode: str = "auto") -> list[Document]:
    """Dual-level graph retrieval (LightRAG pattern)."""
    if mode == "auto":
        mode = await classify_query_scope(query)  # LLM judge: local vs global
    if mode == "local":
        return await entity_neighbor_search(query)
    return await community_summary_search(query)
```

---

## Fusion & Reranking

### Reciprocal Rank Fusion (RRF)
```python
def rrf_fusion(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Fuse multiple rankings using RRF."""
    scores = defaultdict(float)
    
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] += 1 / (k + rank + 1)
    
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

### Dynamic Reranking (Router Pattern)
```python
async def dynamic_rerank(query: str, candidates: list[Document], media_type: str) -> list[Document]:
    """Route to appropriate reranker based on content type."""
    if media_type in ("image", "video", "pdf"):
        # VL Reranker for visual content
        reranker = CrossEncoder("Qwen/Qwen3-VL-Reranker-2B")  # or 8B
        pairs = [(query, doc.text, doc.image) for doc in candidates]
    elif media_type == "audio":
        # ASR → Text Reranker cascade
        transcripts = [await asr_transcribe(doc.audio) for doc in candidates]
        reranker = CrossEncoder("Qwen/Qwen3-Reranker-0.6B")
        pairs = [(query, t.text) for t in transcripts]
    else:
        # Text Reranker (default)
        reranker = CrossEncoder("Qwen/Qwen3-Reranker-0.6B")
        pairs = [(query, doc.text) for doc in candidates]

    scores = reranker.predict(pairs)
    return sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
```

### Cross-Encoder Reranking (Text-only shortcut)
```python
from sentence_transformers import CrossEncoder

# Light model for real-time
reranker_light = CrossEncoder("Qwen/Qwen3-Reranker-0.6B")

# Heavy model for batch processing
reranker_heavy = CrossEncoder("Qwen/Qwen3-Reranker-8B")

pairs = [(query, doc.text) for doc in candidates]
scores = reranker_light.predict(pairs)  # or reranker_heavy
reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
```

---

## CRAG (Corrective RAG)

```python
async def crag_retrieve(query: str, docs: list[Document]) -> list[Document]:
    """Implement Corrective RAG pattern."""
    # Score document relevance
    relevance_scores = await score_relevance(query, docs)
    
    confident_docs = [d for d, s in zip(docs, relevance_scores) if s > 0.7]
    uncertain_docs = [d for d, s in zip(docs, relevance_scores) if 0.3 <= s <= 0.7]
    
    if len(confident_docs) < 3:
        # Web search fallback
        web_results = await web_search(query)
        confident_docs.extend(web_results[:5])
    
    if uncertain_docs:
        # Decompose and re-retrieve
        sub_queries = await decompose_query(query)
        for sub_q in sub_queries:
            additional = await retrieve(sub_q)
            confident_docs.extend(additional[:2])
    
    return confident_docs
```

---

## Evaluation (DeepEval + Ragas)

### DeepEval — Primary (CI-ready, custom metrics)
```python
from deepeval import evaluate
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, HallucinationMetric
from deepeval.test_case import LLMTestCase

# CI pipeline: `deepeval test run tests/test_rag_eval.py`
test_case = LLMTestCase(
    input=query,
    actual_output=response,
    expected_output=ground_truth,
    retrieval_context=[doc.text for doc in retrieved_docs],
)

metrics = [
    FaithfulnessMetric(threshold=0.9),      # Response grounded in context?
    AnswerRelevancyMetric(threshold=0.8),    # Response answers the question?
    HallucinationMetric(threshold=0.1),      # Hallucination rate < 10%?
]
evaluate(test_cases=[test_case], metrics=metrics)
```

### Ragas — RAG-Specific Metrics (bổ sung)
```python
from ragas import evaluate
from ragas.metrics import context_precision, context_recall

# Context precision/recall chuyên sâu hơn DeepEval
results = evaluate(dataset, metrics=[context_precision, context_recall])
```

### Custom Metrics (per-app)
```python
from deepeval.metrics import BaseMetric

class TranslationAccuracyMetric(BaseMetric):
    """KP: BLEU/COMET score cho translation quality."""
    ...

class HealthSafetyMetric(BaseMetric):
    """Aiora: Detect medical misinformation in output."""
    ...
```

### Operational Metrics
| Metric | Target | Monitoring |
|--------|--------|------------|
| Retrieval Latency (P95) | < 200ms | MLflow |
| Reranking Latency (P95) | < 100ms | MLflow |
| Generation Latency (P95) | < 2s | MLflow |
| Cache Hit Rate | > 40% | Dragonfly |
| Faithfulness | > 0.9 | DeepEval |
| Context Precision | > 0.8 | Ragas |
| Hallucination Rate | < 10% | DeepEval |

---

## Guardrails (NeMo)

```python
from nemoguardrails import RailsConfig, LLMRails

config = RailsConfig.from_path("./config")
rails = LLMRails(config)

# Define rails in config/
# - Input validation
# - Topic filtering
# - Hallucination detection
# - PII masking
# - Output safety

result = await rails.generate(
    messages=[{"role": "user", "content": query}],
    context={"documents": retrieved_docs},
)
```

---

## Observability (MLflow)

```python
import mlflow

mlflow.set_tracking_uri("http://mlflow:5000")  # VM internal

@mlflow.trace(name="rag_pipeline")
async def rag_query(query: str) -> str:
    with mlflow.start_span(name="retrieval") as span:
        docs = await retrieve(query)
        span.set_attributes({"num_docs": len(docs)})

    with mlflow.start_span(name="llm_call") as span:
        response = await generate(query, docs)
        span.set_inputs({"query": query})
        span.set_outputs({"response": response})

    return response
```

---

## Semantic Cache (Dragonfly)

```python
import hashlib
from redis import Redis

cache = Redis(host="dragonfly", port=6379)

async def cached_retrieve(query: str, threshold: float = 0.95) -> list[Document] | None:
    # Compute query embedding
    query_embedding = await embed(query)
    
    # Check semantic cache
    cached = await cache.ft().search(
        Query(f"*=>[KNN 1 @embedding $vec AS score]")
        .return_fields("response", "score")
        .dialect(2),
        query_params={"vec": query_embedding.tobytes()},
    )
    
    if cached.docs and float(cached.docs[0].score) > threshold:
        return json.loads(cached.docs[0].response)
    
    return None
```

---

## Checklist

- [ ] 3-Fusion Data Ingestion (PDF/Image → OCR, Text → direct, Video/Audio → ASR)?
- [ ] Incremental KG update (LightRAG pattern — partial subgraph diff)?
- [ ] Triple Fusion Retrieval (Vector + Sparse + Graph)?
- [ ] Dual-level graph queries (local: entity neighbors, global: community summaries)?
- [ ] Gemini Embedding 2 cho multimodal embedding (primary)?
- [ ] Dynamic Reranking router (Text vs VL vs Audio→ASR cascade)?
- [ ] Semantic chunking (chonkie) + layout-aware chunking cho structured docs?
- [ ] RRF fusion + cross-encoder reranking?
- [ ] CRAG pattern for low-confidence results?
- [ ] NeMo Guardrails configured?
- [ ] MLflow tracing enabled (per-step spans)?
- [ ] Semantic cache với Dragonfly?
- [ ] DeepEval + Ragas evaluation pipeline (CI-ready)?
- [ ] Custom eval metrics per-app (TranslationAccuracy, HealthSafety)?
- [ ] Latency targets met (< 200ms retrieval, < 2s total)?
