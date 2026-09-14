"""
Chunks rag/data_dictionary.md and rag/business_summary.md into retrievable
sections and builds a local TF-IDF vector store (rag/vector_store.pkl).

Rebuilds automatically whenever query.py is run and a source file is newer
than the stored index, so this script is rarely run by hand — but can be
run directly to force a rebuild:

    python rag/build_index.py
"""

import pickle
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

RAG_DIR = Path(__file__).parent
SOURCE_FILES = ["data_dictionary.md", "business_summary.md"]
INDEX_PATH = RAG_DIR / "vector_store.pkl"


def chunk_markdown(text: str, source: str) -> list[dict]:
    """Split on level-2 (##) headers; keep the header as chunk context."""
    sections = re.split(r"\n(?=## )", text)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        heading_match = re.match(r"^#+\s*(.+)", section)
        heading = heading_match.group(1) if heading_match else "Intro"
        chunks.append({"source": source, "heading": heading, "text": section})
    return chunks


def build_index() -> dict:
    all_chunks = []
    for filename in SOURCE_FILES:
        path = RAG_DIR / filename
        text = path.read_text()
        all_chunks.extend(chunk_markdown(text, filename))

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform([c["text"] for c in all_chunks])

    return {"chunks": all_chunks, "vectorizer": vectorizer, "matrix": matrix}


def save_index(index: dict) -> None:
    with open(INDEX_PATH, "wb") as f:
        pickle.dump(index, f)


def load_or_build_index() -> dict:
    source_paths = [RAG_DIR / f for f in SOURCE_FILES]
    newest_source_mtime = max(p.stat().st_mtime for p in source_paths)

    if INDEX_PATH.exists() and INDEX_PATH.stat().st_mtime >= newest_source_mtime:
        with open(INDEX_PATH, "rb") as f:
            return pickle.load(f)

    index = build_index()
    save_index(index)
    return index


if __name__ == "__main__":
    index = build_index()
    save_index(index)
    print(f"Indexed {len(index['chunks'])} chunks from {SOURCE_FILES} -> {INDEX_PATH}")
