import os
from pathlib import Path

import anthropic
import chromadb
from openai import OpenAI

from .ingestion import CHROMA_PATH, COLLECTION_NAME, ingest_file
from .retrieval import search
from .generation import generate_answer, generate_answer_compat, GITHUB_CHAT_MODEL

GITHUB_ENDPOINT = "https://models.inference.ai.azure.com"


class RAGPipeline:
    def __init__(
        self,
        chroma_path: str = CHROMA_PATH,
        collection_name: str = COLLECTION_NAME,
        provider: str = "default",
    ):
        if provider == "github":
            token = os.environ["GITHUB_TOKEN"]
            github_client = OpenAI(base_url=GITHUB_ENDPOINT, api_key=token)
            self.openai_client = github_client
            self._generate = lambda q, h: generate_answer_compat(q, h, github_client, GITHUB_CHAT_MODEL)
        else:
            self.openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
            self._generate = lambda q, h: generate_answer(q, h, anthropic_client)

        chroma = chromadb.PersistentClient(path=chroma_path)
        self.collection = chroma.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def ingest(self, path: str) -> int:
        p = Path(path)
        total = 0
        if p.is_dir():
            supported = {".pdf", ".md", ".txt", ".markdown"}
            files = [f for f in p.rglob("*") if f.suffix.lower() in supported]
            if not files:
                print(f"No supported files found under {path}")
                return 0
            for f in files:
                print(f"Ingesting {f}...")
                count = ingest_file(str(f), self.collection, self.openai_client)
                print(f"  -> {count} chunks indexed")
                total += count
        elif p.is_file():
            print(f"Ingesting {p}...")
            total = ingest_file(str(p), self.collection, self.openai_client)
            print(f"  -> {total} chunks indexed")
        else:
            raise FileNotFoundError(f"Path not found: {path}")
        return total

    def query(self, question: str, top_k: int = 5) -> dict:
        hits = search(question, self.openai_client, self.collection, top_k=top_k)
        answer = self._generate(question, hits)
        return {"answer": answer, "sources": hits}

    def stats(self) -> dict:
        return {"total_chunks": self.collection.count(), "collection": self.collection.name}
