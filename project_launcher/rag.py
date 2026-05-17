from __future__ import annotations

import re
import string
from dataclasses import dataclass
from pathlib import Path


SEARCH_DIRECTORIES = ["docs", "research", "reports"]

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "for",
    "from",
    "how",
    "in",
    "is",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "with",
}


@dataclass(frozen=True)
class RagDocument:
    source: str
    text: str


@dataclass(frozen=True)
class RagChunk:
    source: str
    heading: str
    text: str
    score: int


@dataclass(frozen=True)
class DeepAskResult:
    answer: str
    sources: list[str]


def answer_deep_question(folder: Path, question: str) -> DeepAskResult:
    folder = _require_folder(folder)
    if not question.strip():
        raise ValueError("Please provide a question.")

    documents = load_project_documents(folder)
    chunks = chunk_documents(documents)
    ranked = [chunk for chunk in rank_chunks(chunks, question) if chunk.score > 0][:6]
    if not ranked:
        return DeepAskResult(
            answer=(
                "I could not find enough project context to answer that yet.\n\n"
                "Try adding Markdown notes to docs/, research/, or reports/."
            ),
            sources=[],
        )

    extracts = _top_extracts(ranked)
    answer = "\n".join(f"- {extract}" for extract in extracts[:5])
    sources = sorted({chunk.source for chunk in ranked})
    return DeepAskResult(answer=answer, sources=sources)


def load_project_documents(folder: Path) -> list[RagDocument]:
    folder = _require_folder(folder)
    paths: list[Path] = list(sorted(folder.glob("*.md")))
    for directory in SEARCH_DIRECTORIES:
        search_root = folder / directory
        if search_root.is_dir():
            paths.extend(sorted(search_root.rglob("*.md")))

    documents: list[RagDocument] = []
    for path in paths:
        documents.append(RagDocument(source=path.relative_to(folder).as_posix(), text=path.read_text(encoding="utf-8")))
    return documents


def chunk_documents(documents: list[RagDocument]) -> list[RagChunk]:
    chunks: list[RagChunk] = []
    for document in documents:
        chunks.extend(_chunks_from_document(document))
    return chunks


def rank_chunks(chunks: list[RagChunk], question: str) -> list[RagChunk]:
    terms = set(_tokens(question))
    ranked: list[RagChunk] = []
    for chunk in chunks:
        chunk_terms = set(_tokens(f"{chunk.source} {chunk.heading} {chunk.text}"))
        score = len(terms & chunk_terms)
        if score > 0:
            ranked.append(RagChunk(chunk.source, chunk.heading, chunk.text, score))
    return sorted(ranked, key=lambda chunk: (-chunk.score, chunk.source, chunk.heading))


def _require_folder(folder: Path) -> Path:
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"{folder} is not a project folder.")
    return folder


def _chunks_from_document(document: RagDocument) -> list[RagChunk]:
    heading = Path(document.source).stem.replace("_", " ").replace("-", " ").title()
    lines: list[str] = []
    chunks: list[RagChunk] = []

    for raw_line in document.text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            if lines:
                chunks.extend(_line_chunks(document.source, heading, lines))
                lines = []
            heading = line.lstrip("#").strip() or heading
            continue
        lines.append(line)

    if lines:
        chunks.extend(_line_chunks(document.source, heading, lines))
    return list(reversed(chunks))


def _line_chunks(source: str, heading: str, lines: list[str]) -> list[RagChunk]:
    chunks: list[RagChunk] = []
    for line in lines:
        cleaned = _clean_markdown_item(line)
        if cleaned:
            chunks.append(RagChunk(source=source, heading=heading, text=cleaned, score=0))
    return chunks


def _clean_markdown_item(line: str) -> str:
    cleaned = re.sub(r"^\s*[-*]\s+", "", line)
    cleaned = re.sub(r"^\s*\d+\.\s+", "", cleaned)
    cleaned = cleaned.replace("`", "").strip()
    if cleaned.lower().startswith("project idea:"):
        return ""
    return cleaned


def _tokens(text: str) -> list[str]:
    table = str.maketrans({char: " " for char in string.punctuation})
    words = text.lower().translate(table).split()
    return [word for word in words if len(word) > 2 and word not in STOP_WORDS]


def _top_extracts(chunks: list[RagChunk]) -> list[str]:
    seen: set[str] = set()
    extracts: list[str] = []
    for chunk in chunks:
        if chunk.text not in seen:
            seen.add(chunk.text)
            extracts.append(chunk.text)
    return extracts
