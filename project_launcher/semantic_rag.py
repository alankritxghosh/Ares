from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from project_launcher import local_models
from project_launcher.rag import RagChunk, chunk_documents, load_project_documents


INDEX_DIR = ".project_launcher"
INDEX_FILE = "index.json"


@dataclass(frozen=True)
class IndexedChunk:
    source: str
    chunk_id: str
    heading: str
    text: str
    embedding: list[float]
    modified_time: float


@dataclass(frozen=True)
class IndexResult:
    index_path: Path
    chunk_count: int
    sources: list[str]


@dataclass(frozen=True)
class RagAnswer:
    answer: str
    sources: list[str]


def index_project(folder: Path) -> IndexResult:
    folder = _require_folder(folder)
    documents = load_project_documents(folder)
    chunks = chunk_documents(documents)
    indexed: list[IndexedChunk] = []
    for index, chunk in enumerate(chunks, start=1):
        path = folder / chunk.source
        embedding = local_models.embed_text(f"{chunk.heading}\n{chunk.text}")
        indexed.append(
            IndexedChunk(
                source=chunk.source,
                chunk_id=f"{chunk.source}:{index}",
                heading=chunk.heading,
                text=chunk.text,
                embedding=embedding,
                modified_time=path.stat().st_mtime if path.exists() else 0.0,
            )
        )

    index_path = _index_path(folder)
    index_path.parent.mkdir(exist_ok=True)
    index_path.write_text(json.dumps({"chunks": [asdict(chunk) for chunk in indexed]}, indent=2), encoding="utf-8")
    return IndexResult(index_path=index_path, chunk_count=len(indexed), sources=sorted({chunk.source for chunk in indexed}))


def answer_rag_question(folder: Path, question: str) -> RagAnswer:
    folder = _require_folder(folder)
    if not question.strip():
        raise ValueError("Please provide a question.")
    if not _index_path(folder).is_file():
        return RagAnswer(
            answer="No local semantic index found yet.\n\nRun: python main.py index <project>",
            sources=[],
        )

    chunks = _load_index(folder)
    try:
        query_embedding = local_models.embed_text(question)
    except local_models.LocalModelUnavailableError:
        ranked = _keyword_fallback(chunks, question)[:5]
        return RagAnswer(
            answer=(
                "Local embedding model is not ready, so I used stored index text as a fallback.\n\n"
                + "\n".join(f"- {chunk.text}" for chunk in ranked)
                + "\n\nTo enable semantic RAG, run: ollama pull nomic-embed-text"
            ),
            sources=sorted({chunk.source for chunk in ranked}),
        )

    ranked = sorted(chunks, key=lambda chunk: _cosine(query_embedding, chunk.embedding), reverse=True)[:5]
    if not ranked:
        return RagAnswer(answer="I could not find enough indexed project context to answer that yet.", sources=[])

    context = "\n".join(f"[{chunk.source}] {chunk.text}" for chunk in ranked)
    prompt = (
        "You are an offline product management assistant. Answer only from the provided context. "
        "Be concise and include practical PM language.\n\n"
        f"Question: {question}\n\nContext:\n{context}\n\nAnswer:"
    )
    try:
        answer = local_models.generate_text(prompt)
    except local_models.LocalModelUnavailableError:
        answer = (
            "Local chat model is not ready, so here are the most relevant retrieved notes:\n\n"
            + "\n".join(f"- {chunk.text}" for chunk in ranked)
            + "\n\nTo enable generated answers, run: ollama pull llama3.2"
        )
    return RagAnswer(answer=answer, sources=sorted({chunk.source for chunk in ranked}))


def load_indexed_chunks(folder: Path) -> list[IndexedChunk]:
    return _load_index(_require_folder(folder))


def _load_index(folder: Path) -> list[IndexedChunk]:
    data = json.loads(_index_path(folder).read_text(encoding="utf-8"))
    return [IndexedChunk(**item) for item in data.get("chunks", [])]


def _keyword_fallback(chunks: list[IndexedChunk], question: str) -> list[IndexedChunk]:
    terms = {term for term in question.lower().replace("?", " ").split() if len(term) > 2}
    return sorted(
        chunks,
        key=lambda chunk: len(terms & set(f"{chunk.source} {chunk.heading} {chunk.text}".lower().split())),
        reverse=True,
    )


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _index_path(folder: Path) -> Path:
    return folder / INDEX_DIR / INDEX_FILE


def _require_folder(folder: Path) -> Path:
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"{folder} is not a project folder.")
    return folder
