# Document AI — Enterprise RAG Platform

> **An enterprise-grade, zero-disk Retrieval-Augmented Generation (RAG) platform** engineered for rapid, grounded question-answering across complex documents with sub-second retrieval, persistent semantic caching, and automated governance evaluation.

---

## Executive Summary

Standard RAG architectures often suffer from cold-start latency, unbounded LLM token costs, and silent hallucinations. **Document AI** addresses these challenges through an end-to-end decoupled architecture designed for low-latency retrieval, controlled inference costs, strict document isolation, and continuous quality governance.

### Key Highlights

- **Zero-Disk In-Memory Ingestion**: Files are processed directly in memory; chunk vectors and contextual metadata are persisted securely in a managed vector database (Qdrant Cloud), with zero persistent local disk footprint.
- **Sub-20ms Semantic Caching**: Upstash Serverless Redis caches query embeddings, allowing recurring answers to be returned instantly at **$0.00 marginal inference cost**.
- **Strict Document Isolation**: Metadata payload filtering enforces multi-tenant data boundaries and prevents cross-document vector leakage.
- **Continuous Quality Governance**: Built-in automated **RAGAS** evaluation scores responses across Faithfulness, Context Relevancy, and Answer Correctness.

---

## System Architecture & Workflow

```text
[ User Query / Document ]
           │
           ▼
┌────────────────────────────────────────────────────────┐
│             Next.js 14 Web Interface                  │
│       (Streaming SSE, Markdown Tables, Citations)      │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTPS / SSE
                           ▼
┌────────────────────────────────────────────────────────┐
│                 FastAPI Gateway Layer                  │
│        (Routing, Telemetry, Async Task Workers)        │
└──────────┬───────────────────┬─────────────────────────┘
           │                   │
           │ 1. Semantic Check │ 2. Vector Retrieval
           ▼                   ▼
┌─────────────────────┐ ┌────────────────────────────────┐
│ Upstash Redis Cache │ │         Qdrant Cloud           │
│  (Cosine Sim ≥ 88%) │ │   (Vector + Metadata Payloads) │
└──────────┬──────────┘ └──────────────┬─────────────────┘
           │ [Cache Hit]               │ [Cache Miss]
           │ (14ms response)           │ Top-K Chunks + Metadata
           │                           ▼
           │            ┌────────────────────────────────┐
           │            │    Cross-Encoder Guardrail     │
           │            │ (Relevance Cutoff Score Check) │
           │            └──────────────┬─────────────────┘
           │                           │ Relevant Context
           │                           ▼
           │            ┌────────────────────────────────┐
           │            │       Groq Inference LPU       │
           │            │      (Llama 3.3 70B Stream)    │
           │            └──────────────┬─────────────────┘
           │                           │
           └───────────────────────────┴────────► [ Client UI ]
                                                        │
                                     Background Async   ▼
                                        ┌────────────────┐
                                        │  RAGAS Triad   │
                                        │ (Faithfulness, │
                                        │   Relevancy)   │
                                        └────────────────┘
```

### End-to-End Processing Stages

#### 1. Ingestion & Metadata Layering

- PDFs are parsed in memory using character-recursive chunking with context overlap.
- Chunks, SHA-256 document signatures, token estimates, and page references are upserted into Qdrant Cloud vector payloads.

#### 2. Intent Routing & Semantic Cache Lookup

- Conversational queries are contextualized through query reformulation.
- Inbound query embeddings are compared against cached semantic representations in Upstash Redis.
- When cosine similarity meets the configured threshold (**≥ 88%**), cached answers can stream back immediately.

#### 3. Targeted Retrieval & Guardrail Filtering

- On cache misses, Qdrant executes vector search filtered strictly by the active `doc_hash`.
- Retrieved chunks pass through a confidence threshold cutoff to eliminate irrelevant context and reduce hallucination risk.

#### 4. Token Streaming & Telemetry

- High-throughput inference streams directly to the frontend via Server-Sent Events (SSE).
- Exact page citations and context metadata accompany every completion.

#### 5. Quality Triad Evaluation

An asynchronous evaluation worker benchmarks generated responses against the retrieved contexts using RAGAS metrics:

- **Faithfulness**: Verifies that generated claims are grounded in the retrieved context.
- **Context Relevancy**: Measures the signal-to-noise ratio of the retrieved context.
- **Answer Correctness**: Assesses alignment between the generated response and the intended answer.

---

## Core Enterprise Capabilities

| Capability | Technical Mechanism | Business Impact |
| --- | --- | --- |
| **Cost Optimization** | Upstash Redis semantic caching | Up to **60–80% cost reduction** on redundant organizational queries |
| **Hallucination Control** | Cross-Encoder reranking + Guardrail cutoff | Keeps responses grounded in verified source chunks |
| **Stateless Scalability** | Zero local disk dependencies, managed cloud layers | Supports auto-scaling, cold reboots, and multi-region deployment |
| **Auditability** | Interactive page-level citations & payload inspection | Improves compliance visibility for Legal, Security, and Finance teams |

---

## Tech Stack Overview

| Layer | Technology |
| --- | --- |
| **Frontend** | Next.js 14 (App Router), Tailwind CSS, React-Markdown, Remark-GFM |
| **Backend API** | FastAPI, Pydantic v2, Python 3.11, Uvicorn |
| **LLM Engine** | Groq Cloud (`llama-3.3-70b-versatile`) |
| **Vector Store** | Qdrant Cloud (Managed Vector DB with Payload Layering) |
| **Semantic Cache** | Upstash Serverless Redis (REST API) |
| **Evaluation Framework** | RAGAS (Retrieval Augmented Generation Assessment) |
| **Deployment Target** | Vercel (Frontend Edge) & Render / Docker (Stateless Backend) |

---

## Project Structure

A recommended repository layout is:

```text
document-ai/
├── backend/
│   ├── src/
│   │   └── main.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── app/
│   ├── public/
│   ├── package.json
│   └── ...
├── README.md
└── ...
```

> Adjust the structure above to match the actual repository implementation.

---

## Quickstart & Verification

### 1. Environment Configuration

Create a `.env` file in `backend/`:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key

UPSTASH_REDIS_REST_URL=https://your-db.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_upstash_token
```

### 2. Run Backend (Local or Container)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### 3. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to interact with the platform.

---

## Verification Checklist

Use the following checks to verify the local deployment:

- [ ] Backend starts successfully on port `8000`.
- [ ] Frontend starts successfully on port `3000`.
- [ ] Groq API credentials are loaded correctly.
- [ ] Qdrant Cloud is reachable and accepts vector upserts/searches.
- [ ] Upstash Redis is reachable and semantic cache lookups succeed.
- [ ] Document ingestion stores `doc_hash`, page references, and chunk metadata.
- [ ] Retrieval is restricted to the active document through metadata filtering.
- [ ] Cache hits return without invoking the LLM unnecessarily.
- [ ] Cache misses perform vector retrieval and guardrail filtering.
- [ ] Responses include page-level citations.
- [ ] RAGAS evaluation runs asynchronously after response generation.

---

## Production Design Principles

### Stateless Application Tier

The FastAPI layer is designed to remain stateless so application instances can be replicated horizontally without relying on local persistent storage.

### Managed Persistence

Vector data and semantic cache state are delegated to managed cloud services, reducing operational overhead associated with local databases and persistent application volumes.

### Grounded Generation

The retrieval pipeline combines document-level filtering, relevance checks, and source citations to keep generated responses tied to retrieved evidence.

### Observable Quality

RAGAS evaluation provides an automated feedback layer for measuring response quality and detecting degradation in retrieval or generation behavior over time.

---

## Deployment Architecture

### Frontend

Deploy the Next.js application to **Vercel** or another edge-compatible hosting platform.

### Backend

Deploy the FastAPI service to **Render**, Docker-based infrastructure, or an equivalent stateless container platform.

### Data Services

Use managed **Qdrant Cloud** for vector storage and **Upstash Redis** for semantic caching.

### Enterprise Variants

The same architecture can be adapted for:

- Private VPC deployments on AWS, GCP, or Azure
- Self-hosted or on-premise Qdrant / Milvus clusters
- Air-gapped environments using open-source LLMs
- Organization- and tenant-scoped document access controls
- Custom data connectors and enterprise authentication layers

---

## Security & Governance Considerations

For enterprise deployments, extend the baseline architecture with the following controls as required by the target environment:

- Authentication and role-based access control (RBAC)
- Tenant-aware authorization at the API and retrieval layers
- Encryption in transit and at rest
- Secret management through a managed secret store
- Audit logging for document ingestion, retrieval, and response events
- Document retention and deletion policies
- PII / sensitive-data detection and redaction
- Rate limiting and abuse protection
- Model and prompt version tracking
- Evaluation thresholds and release gates for production changes

> The controls above are deployment considerations and should be mapped to the organization's security, privacy, and compliance requirements.

---

## Performance & Cost Strategy

The platform is designed around three primary optimization levers:

1. **Semantic caching** reduces repeated LLM inference for semantically similar queries.
2. **Targeted retrieval and reranking** reduce the amount of low-value context passed to the model.
3. **Streaming inference** improves perceived response latency by returning generated tokens as they become available.

The stated latency and cost figures are architecture targets or observed implementation characteristics and should be validated under the workload, model, region, and service configuration used in production.

---

## Commercial Licensing & Enterprise Deployment

This architecture can be customized and deployed into private VPCs (AWS, GCP, Azure), with on-premise vector clusters such as Milvus or Qdrant and air-gapped open models.

For technical audits, custom connectors, or enterprise pilots, engage through your client engagement channel.

---

## License

Add the applicable project license here, for example:

```text
Proprietary / Commercial License
```

> Replace this section with the actual legal license terms before publishing the repository publicly.
