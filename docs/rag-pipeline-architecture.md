# RAG Pipeline — Architecture & Flow Diagram

> How this RAG pipeline works end-to-end, which methods get called, and where.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         RAG PIPELINE ARCHITECTURE                              │
│                                                                                 │
│  Entry Point: main.py                                                           │
│  ─────────────────────                                                          │
│  CLI parses args (--provider github|default, command: ingest|query|chat|stats)  │
│       │                                                                         │
│       ├── _check_env(provider)    → validates GITHUB_TOKEN or OPENAI/ANTHROPIC  │
│       ├── _pipeline(provider)     → creates RAGPipeline instance                │
│       │                                                                         │
│       ↓                                                                         │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │              RAGPipeline.__init__()  [src/pipeline.py]                   │   │
│  │                                                                          │   │
│  │  Provider = "github"              │  Provider = "default"                │   │
│  │  ─────────────────                │  ────────────────────                │   │
│  │  OpenAI(                          │  OpenAI(OPENAI_API_KEY)              │   │
│  │    base_url=models.inference.     │  Anthropic(ANTHROPIC_API_KEY)        │   │
│  │    ai.azure.com,                  │  _generate → generate_answer()      │   │
│  │    api_key=GITHUB_TOKEN)          │    (uses Claude claude-sonnet-4-6)   │   │
│  │  _generate → generate_answer_    │                                      │   │
│  │    compat() (uses GPT-4o)         │                                      │   │
│  │                                                                          │   │
│  │  ChromaDB PersistentClient(path="./chroma_db")                           │   │
│  │  Collection: "documents" (cosine similarity)                             │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Flow 1: Ingest

```bash
python main.py --provider github ingest docs/
```

```
  docs/ (directory)
       │
       ↓
  RAGPipeline.ingest(path)                          [src/pipeline.py]
       │  Scans for .pdf, .md, .txt, .markdown files
       │
       ↓  (for each file)
  ingest_file(path, collection, openai_client)      [src/ingestion.py]
       │
       ├──→ load_pdf(path)          → extracts text per page using pypdf
       │    OR
       ├──→ load_text_file(path)    → reads entire file as single page
       │
       ↓
  chunk_text(text, size=1000, overlap=200)           [src/ingestion.py]
       │  Splits text into ~1000-char chunks with 200-char overlap
       │  Prefers breaking at paragraph (\n) or sentence (". ") boundaries
       │
       ↓
  embed_texts(chunks, openai_client)                 [src/ingestion.py]
       │  Calls OpenAI API: text-embedding-3-small
       │  Batches of 100 chunks at a time
       │
       ↓
  collection.upsert(ids, embeddings, documents, metadatas)
       │  Stores in ChromaDB (batches of 500)
       │  ID = MD5 hash of "source:page:chunk_index"
       │  Metadata = {source, page, chunk_index}
       │
       ↓
  "Done. 109 total chunks indexed."
```

---

## Flow 2: Query

```bash
python main.py --provider github query "What is harness engineering?"
```

```
  "What is harness engineering?"
       │
       ↓
  RAGPipeline.query(question, top_k=5)               [src/pipeline.py]
       │
       ↓
  ┌─── RETRIEVAL ──────────────────────────────────────────────────────┐
  │  search(query, openai_client, collection, top_k)  [src/retrieval.py]
  │       │                                                            │
  │       ├──→ openai_client.embeddings.create()                       │
  │       │    Model: text-embedding-3-small                           │
  │       │    Converts question → embedding vector                    │
  │       │                                                            │
  │       ├──→ collection.query(query_embeddings, n_results=top_k)     │
  │       │    ChromaDB cosine similarity search                       │
  │       │                                                            │
  │       ↓                                                            │
  │    Returns top-K hits: [{text, metadata, score}, ...]              │
  └────────────────────────────────────────────────────────────────────┘
       │
       ↓
  ┌─── GENERATION ─────────────────────────────────────────────────────┐
  │  _generate(question, hits)                         [src/generation.py]
  │       │                                                            │
  │       ├──→ _build_context(hits)                                    │
  │       │    Formats retrieved chunks as numbered context:           │
  │       │    "[1] source (page N)\n text...\n---\n[2] ..."           │
  │       │                                                            │
  │       ├──→ Builds prompt:                                          │
  │       │    System: "Answer based strictly on provided context..."  │
  │       │    User:   "Context:\n{chunks}\n\nQuestion: {query}"       │
  │       │                                                            │
  │       ├──→ GitHub provider: client.chat.completions.create()       │
  │       │    Model: gpt-4o (via GitHub Models API)                   │
  │       │    OR                                                      │
  │       ├──→ Default provider: client.messages.create()              │
  │       │    Model: claude-sonnet-4-6 (Anthropic API)                │
  │       │                                                            │
  │       ↓                                                            │
  │    Returns answer string                                           │
  └────────────────────────────────────────────────────────────────────┘
       │
       ↓
  {"answer": "...", "sources": [hits]}
```

---

## Flow 3: Chat (Interactive)

```bash
python main.py --provider github chat
```

Same as **Flow 2** but runs in a `while True` loop, reading user input from stdin and calling `pipeline.query()` repeatedly until the user types `quit`.

---

## File Map & Key Methods

| File | Method | Purpose |
|------|--------|---------|
| **main.py** | `_check_env(provider)` | Validates required env vars per provider |
| | `_pipeline(provider)` | Creates `RAGPipeline` instance |
| | `cmd_ingest(args)` | Calls `pipeline.ingest()` |
| | `cmd_query(args)` | Calls `pipeline.query()`, prints answer |
| | `cmd_chat(args)` | Interactive loop calling `pipeline.query()` |
| | `cmd_stats(args)` | Calls `pipeline.stats()` |
| **src/pipeline.py** | `RAGPipeline.__init__()` | Sets up OpenAI/Anthropic/GitHub clients + ChromaDB |
| | `ingest(path)` | File discovery → calls `ingest_file()` per file |
| | `query(question)` | Calls `search()` → `_generate()` → returns answer |
| | `stats()` | Returns chunk count from ChromaDB |
| **src/ingestion.py** | `load_pdf(path)` | Extracts text per page using pypdf |
| | `load_text_file(path)` | Reads entire file as plain text |
| | `chunk_text(text)` | Sliding window chunker (1000 chars, 200 overlap) |
| | `embed_texts(texts)` | OpenAI `text-embedding-3-small` (batched) |
| | `ingest_file(path)` | Orchestrates: load → chunk → embed → upsert |
| | `_doc_id(source, page, idx)` | Generates MD5 hash ID for deduplication |
| **src/retrieval.py** | `search(query)` | Embeds query → ChromaDB cosine search → ranked hits |
| **src/generation.py** | `_build_context(hits)` | Formats retrieved chunks into numbered context |
| | `generate_answer()` | Anthropic Claude API generation |
| | `generate_answer_compat()` | OpenAI-compatible API generation (GitHub Models) |

---

## Key Configuration

| Setting | Value | Defined In |
|---------|-------|------------|
| Chunk size | 1000 characters | `src/ingestion.py` |
| Chunk overlap | 200 characters | `src/ingestion.py` |
| Embedding model | `text-embedding-3-small` | `src/ingestion.py` |
| Chat model (GitHub) | `gpt-4o` | `src/generation.py` |
| Chat model (default) | `claude-sonnet-4-6` | `src/generation.py` |
| Max tokens (generation) | 1024 | `src/generation.py` |
| Vector DB path | `./chroma_db` | `src/ingestion.py` |
| Collection name | `documents` | `src/ingestion.py` |
| Similarity metric | Cosine | `src/pipeline.py` |
| Default top-K results | 5 | `main.py` |
