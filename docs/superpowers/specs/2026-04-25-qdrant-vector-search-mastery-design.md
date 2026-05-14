# Qdrant Vector Search Mastery — Design Spec
**Date:** 2026-04-25  
**Goal:** Master vector search fundamentals through concept-first Jupyter notebooks, covering both Qdrant Essentials and Multi-Vector Search courses.  
**Audience:** Venkat — strong in agent systems, building up vector search fundamentals for production use and interviews.

---

## 1. Objective

Build a self-contained Jupyter notebook series that takes vector search from zero to production-grade. Each notebook is both a learning artifact and an interview reference card. By the end, Venkat can reason about *why* search systems behave a certain way, not just *how* to call the API.

---

## 2. Structure: Concept Clusters

4 clusters, 12 notebooks. Grouped by concept family so each cluster is a self-contained reference unit.

### Cluster 1 — Vectors & Search Fundamentals
**Directory:** `notebooks/01-fundamentals/`

| File | Concepts | Example Used |
|---|---|---|
| `1.1-what-is-a-vector.ipynb` | Embeddings, vector space, semantic proximity | Embed 10 movie descriptions, visualize in 2D with PCA |
| `1.2-distance-metrics.ipynb` | Cosine, Dot Product, Euclidean, Manhattan — when each applies | Same query, different metrics — rank ordering shifts explained |
| `1.3-qdrant-anatomy.ipynb` | Collections, Points, Vectors, Payloads — full CRUD | Build a mini product catalog, insert/update/delete/filter |

### Cluster 2 — Indexing & Performance
**Directory:** `notebooks/02-indexing/`

| File | Concepts | Example Used |
|---|---|---|
| `2.1-hnsw-deep-dive.ipynb` | HNSW graph structure, `m`, `ef_construct`, `ef_search` | Visualize the navigable small world graph layer by layer |
| `2.2-filtering-with-hnsw.ipynb` | Pre-filter vs post-filter, payload indexes, threshold tradeoffs | News articles filtered by category + semantic query |
| `2.3-benchmarking.ipynb` | Recall@k, latency, throughput experiments | Sweep `ef_search` 16→512, plot recall/latency curve |

### Cluster 3 — Search Types & Hybrid Search
**Directory:** `notebooks/03-hybrid-search/`

| File | Concepts | Example Used |
|---|---|---|
| `3.1-sparse-vectors.ipynb` | BM25/SPLADE, inverted indexes, keyword recall | Query "Python async" — dense misses, sparse catches it |
| `3.2-hybrid-search.ipynb` | Dense + sparse fusion, RRF vs linear combo, Universal Query API | Stack Overflow Q&A hybrid retrieval, show RRF score math |
| `3.3-recommendations.ipynb` | Positive/negative examples, `recommend` API, use cases | "More like this" product recommendation from cart items |

### Cluster 4 — Optimization & Multi-Vector
**Directory:** `notebooks/04-advanced/`

| File | Concepts | Example Used |
|---|---|---|
| `4.1-quantization.ipynb` | Scalar (SQ8), Product (PQ), Binary quantization — memory/accuracy tradeoffs | Quantize 100k vectors, measure index size and recall@10 |
| `4.2-multi-vector-late-interaction.ipynb` | ColBERT, MaxSim metric, token-level matching | Query "bank" disambiguation — single vec fails, ColBERT succeeds |
| `4.3-colpali-multimodal.ipynb` | ColPali for PDF/image search, multi-stage retrieval, MUVERA | Search across PDF slides without OCR |

---

## 3. Notebook Template (Applied to Every Notebook)

Each notebook follows this exact structure:

```
## Section 1: Concept Diagram
   ASCII or matplotlib visual of the core idea

## Section 2: The Why (Theory)
   Plain English explanation — 150-200 words
   No jargon without definition
   "This matters because..." connection to real systems

## Section 3: Concrete Example
   Runnable experiment using real or realistic data
   Minimum 3, maximum 5 code cells
   Each cell has a comment explaining what to observe

## Section 4: Experiment — Vary the Parameters
   Change one variable, observe the effect
   Builds intuition for production tuning decisions

## Section 5: Gotchas
   2-3 bullet points: common mistakes, edge cases, surprises
   Written as "If you see X, it's because Y"

## Section 6: Interview Cheat Sheet
   5 Q&A pairs in the format:
   Q: [question a senior engineer would ask]
   A: [crisp 1-2 sentence answer]
```

---

## 4. Stack

| Component | Choice | Reason |
|---|---|---|
| Qdrant | Local Docker (`localhost:6333`) | Zero cost, full control, mirrors prod setup |
| Dense embeddings | `fastembed` + `BAAI/bge-small-en-v1.5` | ONNX-quantized, CPU-fast, no GPU required |
| Sparse embeddings | `fastembed` sparse (`Qdrant/bm25`) | Native Qdrant integration, fewer dependencies |
| Multi-vector | `colpali-engine` | Required for ColBERT/ColPali notebooks only |
| Dataset | `ms_marco` passages (small split) + synthetic for specific demos | Real retrieval benchmark data |
| Visualization | `matplotlib`, `umap-learn` (for vector space plots) | Show what vectors actually look like in space |
| Python env | `uv` + `pyproject.toml` | Workspace convention |

---

## 5. Directory Layout

```
projects/qdrant-mastery/
├── notebooks/
│   ├── 01-fundamentals/
│   │   ├── 1.1-what-is-a-vector.ipynb
│   │   ├── 1.2-distance-metrics.ipynb
│   │   └── 1.3-qdrant-anatomy.ipynb
│   ├── 02-indexing/
│   │   ├── 2.1-hnsw-deep-dive.ipynb
│   │   ├── 2.2-filtering-with-hnsw.ipynb
│   │   └── 2.3-benchmarking.ipynb
│   ├── 03-hybrid-search/
│   │   ├── 3.1-sparse-vectors.ipynb
│   │   ├── 3.2-hybrid-search.ipynb
│   │   └── 3.3-recommendations.ipynb
│   └── 04-advanced/
│       ├── 4.1-quantization.ipynb
│       ├── 4.2-multi-vector-late-interaction.ipynb
│       └── 4.3-colpali-multimodal.ipynb
├── data/
│   └── ms_marco_sample.jsonl
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 6. Learning Progression

```
Cluster 1 (Week 1-2)     →  Cluster 2 (Week 3-4)
What are vectors?             How does search scale?
How does similarity work?     What makes HNSW fast?
How does Qdrant store data?   How do filters interact?

Cluster 3 (Week 5-6)     →  Cluster 4 (Week 7-8)
Why does keyword matter?      When is one vector not enough?
How do you combine signals?   What does ColBERT see that MiniLM misses?
How do you recommend?         How do you search PDFs without OCR?
```

---

## 7. Success Criteria

- Can explain HNSW graph traversal without looking at notes
- Can reason about when to use cosine vs dot product
- Can design a hybrid search pipeline for a new use case
- Can explain MaxSim and why late interaction outperforms single-vector on ambiguous queries
- Each notebook's Interview Cheat Sheet passes a mock senior engineer review
