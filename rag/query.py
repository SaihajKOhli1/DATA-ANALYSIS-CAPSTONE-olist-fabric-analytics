"""
RAG query CLI for the Olist analytics data dictionary + business summary.

Usage:
    python rag/query.py "What was our total revenue?"
    python rag/query.py "What does the recency_days column mean?" --top-k 5

Retrieves the most relevant chunks from the local TF-IDF vector store
(rag/vector_store.pkl, built from data_dictionary.md and business_summary.md)
and sends them as context to Claude along with the question.
"""

import argparse
import os
import sys

from anthropic import Anthropic
from sklearn.metrics.pairwise import cosine_similarity

from build_index import load_or_build_index

MODEL = "claude-sonnet-5"
DEFAULT_TOP_K = 4

SYSTEM_PROMPT = """You are a data assistant for an Olist e-commerce analytics \
project. Answer questions using ONLY the provided context, which is drawn \
from the project's data dictionary and a business metrics summary. If the \
context doesn't contain the answer, say so plainly rather than guessing. \
Cite specific numbers from the context when answering business-metrics \
questions. Be concise."""


def retrieve(index: dict, question: str, top_k: int) -> list[dict]:
    query_vec = index["vectorizer"].transform([question])
    scores = cosine_similarity(query_vec, index["matrix"])[0]
    ranked = sorted(zip(scores, index["chunks"]), key=lambda x: x[0], reverse=True)
    return [chunk for score, chunk in ranked[:top_k] if score > 0]


def build_context(chunks: list[dict]) -> str:
    parts = []
    for chunk in chunks:
        parts.append(f"[Source: {chunk['source']} - {chunk['heading']}]\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)


def answer_question(question: str, top_k: int = DEFAULT_TOP_K) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")

    index = load_or_build_index()
    chunks = retrieve(index, question, top_k)

    if not chunks:
        return "No relevant context found for this question."

    context = build_context(chunks)
    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Context:\n\n{context}\n\nQuestion: {question}",
            }
        ],
    )
    return response.content[0].text


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the Olist RAG assistant")
    parser.add_argument("question", help="The question to ask")
    parser.add_argument(
        "--top-k", type=int, default=DEFAULT_TOP_K, help="Number of chunks to retrieve"
    )
    parser.add_argument(
        "--show-context", action="store_true", help="Print retrieved chunks before the answer"
    )
    args = parser.parse_args()

    if args.show_context:
        index = load_or_build_index()
        chunks = retrieve(index, args.question, args.top_k)
        print("--- Retrieved context ---", file=sys.stderr)
        for chunk in chunks:
            print(f"[{chunk['source']} - {chunk['heading']}]", file=sys.stderr)
        print("--------------------------\n", file=sys.stderr)

    print(answer_question(args.question, args.top_k))


if __name__ == "__main__":
    main()
