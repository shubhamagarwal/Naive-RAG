# RAG (Retrieval-Augmented Generation) — MCQ Quiz

> 10 progressively harder questions · Answers & explanations at the bottom
> Try answering all 10 before scrolling down!

---

## 🟢 Easy (Q1–Q3)

### Q1. What fundamental LLM limitation does RAG primarily solve?

- A) LLMs are too slow at inference
- B) LLMs lack access to up-to-date or private knowledge
- C) LLMs cannot generate text longer than 512 tokens
- D) LLMs cannot process images

---

### Q2. In a standard RAG pipeline, what is the correct order of the INGESTION phase?

- A) Embed → Chunk → Load → Store
- B) Load → Chunk → Embed → Store in Vector DB
- C) Load → Embed → Chunk → Store in SQL DB
- D) Chunk → Load → Store → Embed

---

### Q3. What is an "embedding" in the context of RAG?

- A) A compressed version of the original document
- B) A dense numerical vector that captures the semantic meaning of text
- C) A hash of the document used for de-duplication
- D) The tokenized form of text before it enters the LLM

---

## 🟡 Medium (Q4–Q6)

### Q4. Which chunking strategy preserves parent-child document hierarchy and allows retrieving a small chunk but passing the larger parent to the LLM?

- A) Fixed-size chunking with overlap
- B) Recursive character text splitting
- C) Parent Document Retrieval
- D) Semantic chunking

---

### Q5. What is "hybrid search" in RAG, and why is it used?

- A) Combining keyword search (BM25/sparse) with vector search (dense) for better recall
- B) Searching across two different vector databases simultaneously
- C) Using both GPT-4 and Claude to generate answers from the same context
- D) Running the same query against both SQL and NoSQL databases

---

### Q6. What does a **reranker** do in a RAG pipeline, and where does it sit?

- A) It re-embeds the query with a different model before vector search
- B) It re-orders the retrieved chunks by relevance using a cross-encoder, sitting between retrieval and generation
- C) It ranks the LLM's multiple output candidates and picks the best one
- D) It sorts documents by recency before chunking during ingestion

---

## 🟠 Hard (Q7–Q8)

### Q7. In HyDE (Hypothetical Document Embeddings), what happens before the vector search?

- A) The user query is translated into SQL and run against a relational database
- B) The LLM generates a hypothetical answer to the query, which is then embedded and used for vector search instead of the original query
- C) The vector database generates a hypothetical document and compares it to the query
- D) The query is broken into sub-queries and each is searched independently

---

### Q8. You have a RAG system with high **context recall** (relevant chunks are retrieved) but low **faithfulness** (the LLM's answer contains claims not in the retrieved context). What is the most likely root cause?

- A) The embedding model is too small
- B) The chunks are too large, causing the LLM to ignore parts of the context
- C) The LLM is hallucinating — it's generating information from its parametric memory instead of grounding in the provided context
- D) The vector database index needs rebuilding

---

## 🔴 Very Hard (Q9–Q10)

### Q9. When would you choose **GraphRAG** over standard vector-based RAG, and what is its key advantage?

- A) When documents are very short (< 100 tokens) — GraphRAG handles small texts better
- B) When queries require multi-hop reasoning across connected entities — GraphRAG builds a knowledge graph that captures relationships standard embeddings miss
- C) When you need faster retrieval — graph traversal is always faster than vector search
- D) When you want to avoid using an LLM entirely — GraphRAG replaces the generation step

---

### Q10. You are designing a production RAG system for a regulated financial institution. The system must handle 10K queries/day across 500K documents, ensure no hallucinated financial figures, meet audit requirements, and keep costs under $2K/month. Describe the architecture by selecting the BEST combination:

- A) Single large LLM (GPT-4o) for everything, fixed-size chunking, Chroma (in-memory), no caching
- B) Hybrid search (pgvector + BM25), recursive chunking with metadata, reranker, model cascading (small model for simple queries → large model fallback), semantic cache, output guardrails with numerical fact-checking against source, full tracing via LangFuse, PII redaction
- C) Fine-tuned Llama 70B self-hosted on single GPU, semantic chunking, Pinecone, no guardrails (fine-tuning handles safety)
- D) RAG with GraphRAG for all queries, GPT-4o only, no caching, manual human review of every response

---
---

# ✅ Answer Key & Explanations

## Q1: **B** — LLMs lack access to up-to-date or private knowledge

LLMs have a knowledge cutoff date and cannot access private/enterprise data. RAG solves this by retrieving relevant external documents at query time and injecting them into the LLM's context. This avoids expensive retraining while giving the model access to fresh, domain-specific information.

---

## Q2: **B** — Load → Chunk → Embed → Store in Vector DB

The ingestion pipeline follows this order:
1. **Load** documents from sources (PDFs, APIs, databases)
2. **Chunk** them into smaller pieces (using recursive, semantic, or fixed-size strategies)
3. **Embed** each chunk into a dense vector using an embedding model
4. **Store** vectors + metadata in a vector database

---

## Q3: **B** — A dense numerical vector that captures the semantic meaning of text

Embeddings are high-dimensional vectors (e.g., 1536-d for OpenAI's `text-embedding-3-small`) where semantically similar texts are close together in vector space. This enables semantic search — finding relevant content even when exact keywords don't match.

**Why not A?** Compression loses information; embeddings capture meaning.
**Why not C?** Hashes are exact-match; embeddings capture similarity.
**Why not D?** Tokens are discrete IDs; embeddings are continuous vectors.

---

## Q4: **C** — Parent Document Retrieval

Parent Document Retrieval splits documents into small child chunks (for precise retrieval) but stores references to the larger parent document. At query time, you search by child chunks but return the parent context to the LLM. This gives you the best of both worlds: precise matching + rich context.

**Why not B?** Recursive splitting creates chunks of varying detail but doesn't maintain parent-child linking.
**Why not D?** Semantic chunking groups by topic but doesn't have a parent retrieval mechanism.

---

## Q5: **A** — Combining keyword search (BM25/sparse) with vector search (dense) for better recall

- **Dense search** (vectors) excels at semantic similarity — "car" matches "automobile"
- **Sparse search** (BM25) excels at exact keyword matching — "ISO-27001" matches "ISO-27001"
- **Hybrid** combines both with a weighted fusion (e.g., Reciprocal Rank Fusion) to catch what either alone would miss

This is critical in production because pure vector search often misses exact terms, acronyms, and codes.

---

## Q6: **B** — Re-orders retrieved chunks by relevance using a cross-encoder, between retrieval and generation

The pipeline flow: `Query → Vector Search (fast, broad recall) → Top-K chunks → Reranker (slow, precise) → Top-N chunks → LLM`

- **Bi-encoders** (embedding models) are fast but approximate — they encode query and docs independently
- **Cross-encoders** (rerankers like Cohere Rerank, `bge-reranker`) process query+doc pairs jointly — much more accurate but slower
- Reranking is the single biggest quality boost you can add to a naive RAG pipeline

---

## Q7: **B** — The LLM generates a hypothetical answer, which is embedded for search

HyDE (Hypothetical Document Embeddings) works as follows:
1. User asks: *"What are the tax implications of stock options?"*
2. The LLM generates a **hypothetical answer** (may be imperfect, that's OK)
3. This hypothetical answer is **embedded** and used for vector search
4. The intuition: a hypothetical answer is closer in embedding space to real answers than the original short query is

**When to use:** Short, vague queries where the user's intent is clear but the query embedding is too sparse to find good matches.

---

## Q8: **C** — The LLM is hallucinating from parametric memory

This is a classic diagnosis scenario:
- **High context recall** = the retrieval pipeline is working — relevant chunks ARE being fetched
- **Low faithfulness** = the LLM is NOT sticking to the retrieved context — it's adding information from its training data

**Fixes:**
- Strengthen the system prompt: *"Answer ONLY based on the provided context. If the answer is not in the context, say 'I don't know.'"*
- Use a smaller/weaker model (less parametric knowledge to hallucinate from)
- Add output guardrails that check claims against source chunks
- Use Self-RAG (model assesses whether its own output is grounded)

**Why not B?** Large chunks might cause the LLM to miss details, but that would show as low context precision, not low faithfulness with high recall.

---

## Q9: **B** — Multi-hop reasoning across connected entities

Standard vector RAG embeds chunks independently — it has no concept of *relationships between entities*. GraphRAG builds a knowledge graph from documents:
- Entities become nodes (people, companies, concepts)
- Relationships become edges (works-at, acquired-by, depends-on)
- Queries like *"What companies are connected to Person X through Board memberships?"* require traversing relationships that flat vector search cannot capture

**When to use GraphRAG:**
- Queries requiring 2+ hops of reasoning
- Highly interconnected data (org charts, legal entity structures, supply chains)
- Global summarization questions ("What are the main themes across all documents?")

**Why not C?** Graph traversal is NOT always faster; it's about *capability*, not speed.

---

## Q10: **B** — The full production architecture

Let's break down why each component matters for this scenario:

| Requirement | Solution in B | Why |
|-------------|--------------|-----|
| 500K docs | pgvector + BM25 hybrid | Scales well, hybrid catches exact financial terms |
| No hallucinated figures | Output guardrails + numerical fact-checking against source | Cross-references generated numbers with retrieved chunks |
| Audit compliance | Full tracing via LangFuse + PII redaction | Every query/response logged, PII scrubbed |
| $2K/month budget | Model cascading + semantic cache | 70%+ queries handled by small model; cache cuts repeat costs |
| 10K queries/day | Semantic cache + model cascading | Cache hit rate of 30-50% reduces LLM calls dramatically |

**Why not A?** GPT-4o for everything at 10K queries/day would blow the budget (~$5-15K/month). No guardrails = compliance failure.
**Why not C?** 70B model on single GPU requires INT4 quantization and won't handle 10K/day throughput. No guardrails in regulated finance is a non-starter.
**Why not D?** GraphRAG for ALL queries is overkill and slow. Manual review of every response doesn't scale to 10K/day.

---

## Scoring Guide

| Score | Level | Recommendation |
|-------|-------|---------------|
| 9–10 | 🏆 Expert | You're ready to architect production RAG systems |
| 7–8 | 🟢 Strong | Review advanced patterns (HyDE, GraphRAG, Self-RAG) |
| 5–6 | 🟡 Solid foundations | Deep dive into reranking, evaluation metrics, and production guardrails |
| 3–4 | 🟠 Getting there | Re-study the RAG pipeline end-to-end, focus on chunking and hybrid search |
| 0–2 | 🔴 Keep going | Start with Session 3 of the 20-hour plan and rebuild fundamentals |
