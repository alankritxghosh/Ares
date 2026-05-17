from __future__ import annotations

import re
import string
from dataclasses import dataclass
from pathlib import Path


PREFERRED_SOURCES = {
    "risk": ["risks.md"],
    "risks": ["risks.md"],
    "blocked": ["risks.md"],
    "danger": ["risks.md"],
    "missing": ["open_questions.md", "requirements.md", "tasks.md"],
    "kickoff": ["open_questions.md", "requirements.md", "tasks.md"],
    "unanswered": ["open_questions.md", "requirements.md", "tasks.md"],
    "question": ["open_questions.md", "requirements.md", "tasks.md"],
    "questions": ["open_questions.md", "requirements.md", "tasks.md"],
    "who": ["users.md"],
    "user": ["users.md"],
    "customer": ["users.md"],
    "roadmap": ["roadmap.md"],
    "phase": ["roadmap.md"],
    "timeline": ["roadmap.md"],
    "next": ["tasks.md"],
}

SUMMARY_FILES = [
    "brief.md",
    "goals.md",
    "requirements.md",
    "risks.md",
    "open_questions.md",
    "tasks.md",
    "roadmap.md",
]

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "before",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
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
class KnowledgeChunk:
    source: str
    heading: str
    text: str
    score: int


@dataclass(frozen=True)
class AskResult:
    answer: str
    sources: list[str]


@dataclass(frozen=True)
class SummaryResult:
    title: str
    focus: list[str]
    goals: list[str]
    requirements: list[str]
    risks: list[str]
    open_questions: list[str]
    next_actions: list[str]


def ask_project(folder: Path, question: str) -> AskResult:
    folder = _require_folder(folder)
    if not question.strip():
        raise ValueError("Please provide a question.")

    chunks = rank_chunks(load_markdown_chunks(folder), question)
    preferred_sources = set(_preferred_sources(question))
    if preferred_sources and any(chunk.source in preferred_sources for chunk in chunks):
        chunks = [chunk for chunk in chunks if chunk.source in preferred_sources]
    useful_chunks = [chunk for chunk in chunks if chunk.score > 0][:5]
    if not useful_chunks:
        return AskResult(
            answer=(
                "I could not find enough project context to answer that yet.\n\n"
                "Try adding notes to brief.md, requirements.md, risks.md, or open_questions.md."
            ),
            sources=[],
        )

    lines = _top_extracts(useful_chunks)
    answer = "\n".join(f"- {line}" for line in lines[:5])
    sources = sorted({chunk.source for chunk in useful_chunks})
    return AskResult(answer=answer, sources=sources)


def summarize_project(folder: Path) -> SummaryResult:
    folder = _require_folder(folder)
    return SummaryResult(
        title=_read_title(folder),
        focus=_read_section_items(folder / "brief.md", fallback_limit=2),
        goals=_read_section_items(folder / "goals.md", fallback_limit=3),
        requirements=_read_section_items(folder / "requirements.md", fallback_limit=3),
        risks=_read_section_items(folder / "risks.md", fallback_limit=3),
        open_questions=_read_section_items(folder / "open_questions.md", fallback_limit=3),
        next_actions=_read_section_items(folder / "tasks.md", fallback_limit=3),
    )


def load_markdown_chunks(folder: Path) -> list[KnowledgeChunk]:
    folder = _require_folder(folder)
    chunks: list[KnowledgeChunk] = []
    for path in sorted(folder.glob("*.md")):
        chunks.extend(_chunks_from_markdown(path))
    return chunks


def rank_chunks(chunks: list[KnowledgeChunk], question: str) -> list[KnowledgeChunk]:
    terms = set(_tokens(question))
    preferred = set(_preferred_sources(question))
    ranked: list[KnowledgeChunk] = []
    for chunk in chunks:
        chunk_terms = set(_tokens(f"{chunk.heading} {chunk.text}"))
        score = len(terms & chunk_terms)
        if chunk.source in preferred:
            score += 3
        if score > 0:
            ranked.append(KnowledgeChunk(chunk.source, chunk.heading, chunk.text, score))
    return sorted(ranked, key=lambda chunk: -chunk.score)


def _require_folder(folder: Path) -> Path:
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"{folder} is not a project folder.")
    return folder


def _chunks_from_markdown(path: Path) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    heading = path.stem.replace("_", " ").title()
    lines: list[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            if lines:
                chunks.extend(_line_chunks(path.name, heading, lines))
                lines = []
            heading = line.lstrip("#").strip() or heading
            continue
        lines.append(line)

    if lines:
        chunks.extend(_line_chunks(path.name, heading, lines))
    return list(reversed(chunks))


def _line_chunks(source: str, heading: str, lines: list[str]) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for line in lines:
        cleaned = _clean_markdown_item(line)
        if cleaned:
            chunks.append(KnowledgeChunk(source=source, heading=heading, text=cleaned, score=0))
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


def _preferred_sources(question: str) -> list[str]:
    tokens = set(_tokens(question))
    sources: list[str] = []
    for term, filenames in PREFERRED_SOURCES.items():
        if term in tokens:
            sources.extend(filenames)
    return sources


def _top_extracts(chunks: list[KnowledgeChunk]) -> list[str]:
    seen: set[str] = set()
    extracts: list[str] = []
    for chunk in chunks:
        if chunk.text not in seen:
            seen.add(chunk.text)
            extracts.append(chunk.text)
    return extracts


def _read_title(folder: Path) -> str:
    readme = folder / "README.md"
    if readme.is_file():
        for line in readme.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped.lstrip("#").strip()
    return folder.name


def _read_section_items(path: Path, fallback_limit: int) -> list[str]:
    if not path.is_file():
        return []

    items: list[str] = []
    fallback: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = _clean_markdown_item(raw_line.strip())
        if not line or line.startswith("#"):
            continue
        if raw_line.strip().startswith(("-", "*")) or re.match(r"^\d+\.", raw_line.strip()):
            items.append(line)
        elif len(fallback) < fallback_limit and not line.lower().startswith("project idea:"):
            fallback.append(line)

    return (items or fallback)[:fallback_limit]
