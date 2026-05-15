#!/usr/bin/env python3
import argparse
import os
import sys


def _check_env(provider: str):
    keys = ("GITHUB_TOKEN",) if provider == "github" else ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        print(f"Error: missing environment variables: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in the required keys.")
        sys.exit(1)


def _pipeline(provider: str):
    from src.pipeline import RAGPipeline
    return RAGPipeline(provider=provider)


def cmd_ingest(args):
    _check_env(args.provider)
    pipeline = _pipeline(args.provider)
    total = pipeline.ingest(args.path)
    print(f"\nDone. {total} total chunks indexed.")


def cmd_query(args):
    _check_env(args.provider)
    pipeline = _pipeline(args.provider)
    if pipeline.stats()["total_chunks"] == 0:
        print("Nothing indexed yet. Run: python main.py ingest <path>")
        sys.exit(1)

    result = pipeline.query(args.question, top_k=args.top_k)

    print("\n" + "=" * 60)
    print("ANSWER")
    print("=" * 60)
    print(result["answer"])

    if args.show_sources:
        print("\n" + "=" * 60)
        print("SOURCES")
        print("=" * 60)
        for i, hit in enumerate(result["sources"], 1):
            src = hit["metadata"].get("source", "unknown")
            page = hit["metadata"].get("page", "")
            score = hit["score"]
            label = f"{src}" + (f" p.{page}" if page else "") + f"  (score: {score:.3f})"
            print(f"\n[{i}] {label}")
            preview = hit["text"][:300]
            print(preview + ("..." if len(hit["text"]) > 300 else ""))


def cmd_chat(args):
    _check_env(args.provider)
    pipeline = _pipeline(args.provider)
    stats = pipeline.stats()
    if stats["total_chunks"] == 0:
        print("Nothing indexed yet. Run: python main.py ingest <path>")
        sys.exit(1)

    print(f"RAG ready — {stats['total_chunks']} chunks indexed. Type 'quit' to exit.\n")
    while True:
        try:
            question = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break
        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break
        result = pipeline.query(question, top_k=args.top_k)
        print(f"\nAssistant: {result['answer']}\n")


def cmd_stats(args):
    _check_env(args.provider)
    stats = _pipeline(args.provider).stats()
    print(f"Collection : {stats['collection']}")
    print(f"Chunks     : {stats['total_chunks']}")


def main():
    from dotenv import load_dotenv
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="RAG pipeline — ingest documents and ask questions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  # default (OpenAI embeddings + Claude generation)
  python main.py ingest docs/
  python main.py query "What are the main findings?"
  python main.py chat

  # GitHub Copilot (single GITHUB_TOKEN, gpt-4o generation)
  python main.py --provider github ingest docs/
  python main.py --provider github query "What are the main findings?"
  python main.py --provider github chat
        """,
    )
    parser.add_argument(
        "--provider",
        choices=["default", "github"],
        default="default",
        help="'default' uses OPENAI_API_KEY + ANTHROPIC_API_KEY; 'github' uses a single GITHUB_TOKEN",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="Index a file or directory")
    p.add_argument("path", help="File or directory to ingest")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("query", help="Ask a single question")
    p.add_argument("question")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--show-sources", action="store_true")
    p.set_defaults(func=cmd_query)

    p = sub.add_parser("chat", help="Interactive Q&A session")
    p.add_argument("--top-k", type=int, default=5)
    p.set_defaults(func=cmd_chat)

    p = sub.add_parser("stats", help="Show index statistics")
    p.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
