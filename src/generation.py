import anthropic

CLAUDE_MODEL = "claude-sonnet-4-6"
GITHUB_CHAT_MODEL = "gpt-4o"
MAX_TOKENS = 1024

_SYSTEM = (
    "You are a helpful assistant that answers questions based strictly on the provided context. "
    "Use ONLY information from the context. If the context does not contain enough information "
    "to answer the question, say so clearly. Cite source document names when relevant."
)


def _build_context(hits: list[dict]) -> str:
    parts = []
    for i, hit in enumerate(hits, 1):
        source = hit["metadata"].get("source", "unknown")
        page = hit["metadata"].get("page", "")
        label = f"{source}" + (f" (page {page})" if page else "")
        parts.append(f"[{i}] {label}\n{hit['text']}")
    return "\n\n---\n\n".join(parts)


def generate_answer(query: str, hits: list[dict], client: anthropic.Anthropic) -> str:
    if not hits:
        return "No relevant documents found to answer your question."

    user_message = f"Context:\n{_build_context(hits)}\n\nQuestion: {query}"

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def generate_answer_compat(query: str, hits: list[dict], client, model: str = GITHUB_CHAT_MODEL) -> str:
    """OpenAI-compatible generation — used by the GitHub Copilot provider."""
    if not hits:
        return "No relevant documents found to answer your question."

    user_message = f"Context:\n{_build_context(hits)}\n\nQuestion: {query}"

    response = client.chat.completions.create(
        model=model,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content
