from openai import OpenAI

from .ingestion import EMBED_MODEL


def search(query: str, openai_client: OpenAI, collection, top_k: int = 5) -> list[dict]:
    response = openai_client.embeddings.create(model=EMBED_MODEL, input=[query])
    query_embedding = response.data[0].embedding

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        hits.append({"text": doc, "metadata": meta, "score": 1 - (dist / 2)})

    return hits
