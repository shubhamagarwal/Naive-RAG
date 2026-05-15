# RAG Pipeline

A simple Retrieval-Augmented Generation (RAG) pipeline that lets you ingest documents (PDF, Markdown, TXT), store them as vector embeddings in ChromaDB, and query them using an LLM.

## Features

- **Document ingestion** — PDF, Markdown, and plain text files
- **Chunking** — Sliding window with smart boundary detection (paragraph/sentence)
- **Embeddings** — OpenAI `text-embedding-3-small`
- **Vector store** — ChromaDB with cosine similarity (persistent, local)
- **Generation** — Claude Sonnet (default) or GPT-4o (GitHub Models)
- **Two provider modes** — use your own OpenAI + Anthropic keys, or a single GitHub token
- **CLI interface** — `ingest`, `query`, `chat`, and `stats` commands

## Architecture

See [docs/rag-pipeline-architecture.md](docs/rag-pipeline-architecture.md) for the full flow diagram.

```
User Question
     │
     ↓
  Embed query (text-embedding-3-small)
     │
     ↓
  ChromaDB cosine search → top-K chunks
     │
     ↓
  LLM generates answer from retrieved context
     │
     ↓
  Answer + Sources
```

---

## Setup (Step by Step)

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/rag-pipeline.git
cd rag-pipeline
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in **one** of the two options:

**Option A — Default provider** (requires both keys):
```dotenv
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**Option B — GitHub Models provider** (single token):
1. Go to https://github.com/settings/tokens
2. Create a Personal Access Token with the `models:read` scope
3. Add it to `.env`:
```dotenv
GITHUB_TOKEN=github_pat_...
```

---

## Usage

> If using the GitHub provider, add `--provider github` to every command.

### Ingest documents

```bash
# Ingest a directory
python main.py --provider github ingest docs/

# Ingest a single file
python main.py --provider github ingest docs/my-file.pdf
```

Supported formats: `.pdf`, `.md`, `.txt`, `.markdown`

### Ask a single question

```bash
python main.py --provider github query "What is harness engineering?"

# Show source chunks
python main.py --provider github query "What is harness engineering?" --show-sources
```

### Interactive chat

```bash
python main.py --provider github chat
```

Type your questions and get answers. Type `quit` to exit.

### Check index stats

```bash
python main.py --provider github stats
```

---

## Project Structure

```
rag-pipeline/
├── main.py              # CLI entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Template for environment variables
├── docs/                # Documents to ingest
│   ├── rag-pipeline-architecture.md
│   └── ...
└── src/
    ├── __init__.py
    ├── ingestion.py     # Load, chunk, embed, and store documents
    ├── retrieval.py     # Vector similarity search
    ├── generation.py    # LLM answer generation
    └── pipeline.py      # RAGPipeline orchestrator class
```

---

## Configuration

| Setting | Value | File |
|---------|-------|------|
| Chunk size | 1000 chars | `src/ingestion.py` |
| Chunk overlap | 200 chars | `src/ingestion.py` |
| Embedding model | `text-embedding-3-small` | `src/ingestion.py` |
| Chat model (GitHub) | `gpt-4o` | `src/generation.py` |
| Chat model (default) | `claude-sonnet-4-6` | `src/generation.py` |
| Max generation tokens | 1024 | `src/generation.py` |
| Vector DB path | `./chroma_db` | `src/ingestion.py` |
| Top-K results | 5 | `main.py` |
