import hashlib
from pathlib import Path

import chromadb
from openai import OpenAI

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "documents"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBED_MODEL = "text-embedding-3-small"


def load_pdf(path: str) -> list[tuple[str, dict]]:
    from pypdf import PdfReader
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append((text, {"source": path, "page": i + 1}))
    return pages


def load_text_file(path: str) -> list[tuple[str, dict]]:
    with open(path, "r", encoding="utf-8") as f:
        return [(f.read(), {"source": path, "page": 1})]


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    text = text.strip()
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            # prefer breaking at paragraph or sentence boundary
            boundary = text.rfind("\n", start, end)
            if boundary <= start:
                boundary = text.rfind(". ", start, end)
            if boundary > start:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        next_start = end - overlap
        if next_start <= start:
            next_start = start + 1
        start = next_start
    return chunks


def embed_texts(texts: list[str], client: OpenAI, batch_size: int = 100) -> list[list[float]]:
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(model=EMBED_MODEL, input=batch)
        embeddings.extend([e.embedding for e in response.data])
    return embeddings


def _doc_id(source: str, page: int, chunk_idx: int) -> str:
    key = f"{source}:p{page}:c{chunk_idx}"
    return hashlib.md5(key.encode()).hexdigest()


def ingest_file(path: str, collection, openai_client: OpenAI) -> int:
    path = str(Path(path).resolve())
    ext = Path(path).suffix.lower()

    if ext == ".pdf":
        pages = load_pdf(path)
    elif ext in (".md", ".txt", ".markdown"):
        pages = load_text_file(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    all_chunks: list[str] = []
    all_ids: list[str] = []
    all_metadata: list[dict] = []

    for text, meta in pages:
        for i, chunk in enumerate(chunk_text(text)):
            all_chunks.append(chunk)
            all_ids.append(_doc_id(meta["source"], meta["page"], i))
            all_metadata.append({**meta, "chunk_index": i})

    if not all_chunks:
        return 0

    print(f"  Embedding {len(all_chunks)} chunks...")
    embeddings = embed_texts(all_chunks, openai_client)

    for i in range(0, len(all_chunks), 500):
        collection.upsert(
            ids=all_ids[i : i + 500],
            embeddings=embeddings[i : i + 500],
            documents=all_chunks[i : i + 500],
            metadatas=all_metadata[i : i + 500],
        )

    return len(all_chunks)
