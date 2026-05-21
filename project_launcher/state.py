from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from project_launcher.config import AresConfig, config_path, load_config
from project_launcher.health import HealthReport, assess_health
from project_launcher.knowledge import summarize_project
from project_launcher.semantic_rag import INDEX_DIR, INDEX_FILE
from project_launcher.workspace import next_actions


@dataclass(frozen=True)
class ProjectState:
    folder: Path
    config: AresConfig
    has_config: bool
    health: HealthReport
    next_actions: list[str]
    decisions: list[str]
    open_questions: list[str]
    unanswered_questions: list[str]
    evidence_sources: list[str]
    index_exists: bool
    index_stale: bool


def build_project_state(folder: Path) -> ProjectState:
    folder = _require_folder(folder)
    summary = summarize_project(folder)
    config = load_config(folder, fallback_name=summary.title, fallback_idea=summary.focus[0] if summary.focus else "")
    questions = _numbered_items(folder / "open_questions.md")
    unanswered = [question for question in questions if "answer:" not in question.lower()]
    sources = _evidence_sources(folder)
    index_path = folder / INDEX_DIR / INDEX_FILE
    return ProjectState(
        folder=folder,
        config=config,
        has_config=config_path(folder).is_file(),
        health=assess_health(folder),
        next_actions=next_actions(folder),
        decisions=_bullet_items(folder / "decisions.md"),
        open_questions=questions,
        unanswered_questions=unanswered,
        evidence_sources=sources,
        index_exists=index_path.is_file(),
        index_stale=_index_stale(folder, index_path),
    )


def format_state(state: ProjectState) -> str:
    lines = [
        "Project State",
        "",
        f"Name: {state.config.name}",
        f"Type: {state.config.project_type}",
        f"Stage: {state.config.stage}",
        f"Primary user: {state.config.primary_user}",
        f"Config: {'ares.yaml' if state.has_config else 'not found, inferred defaults'}",
        f"Health: {state.health.score}%",
        f"Open decisions: {len(state.decisions)} recorded",
        f"Open questions: {len(state.open_questions)} total, {len(state.unanswered_questions)} unanswered",
        f"Semantic index: {_index_label(state)}",
        "",
        "Next actions:",
        *_numbered(state.next_actions),
        "",
        "Evidence sources:",
        *_bullets(state.evidence_sources[:10]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def _index_label(state: ProjectState) -> str:
    if not state.index_exists:
        return "missing"
    if state.index_stale:
        return "stale"
    return "current"


def _evidence_sources(folder: Path) -> list[str]:
    sources: list[str] = []
    for pattern in ["*.md", "docs/**/*.md", "research/**/*.md", "reports/**/*.md"]:
        sources.extend(path.relative_to(folder).as_posix() for path in sorted(folder.glob(pattern)))
    return sources


def _index_stale(folder: Path, index_path: Path) -> bool:
    if not index_path.is_file():
        return False
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
        modified_times = [float(chunk.get("modified_time", 0.0)) for chunk in data.get("chunks", [])]
    except (ValueError, OSError):
        return True
    indexed_time = max(modified_times or [0.0])
    for source in _evidence_sources(folder):
        path = folder / source
        if path.is_file() and path.stat().st_mtime > indexed_time + 0.001:
            return True
    return False


def _bullet_items(path: Path) -> list[str]:
    if not path.is_file():
        return []
    decision_pattern = re.compile(r"^-\s+\d{4}-\d{2}-\d{2}:")
    items: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and ("decisions.md" not in path.name or decision_pattern.match(stripped)):
            items.append(stripped[2:].strip())
    return items


def _numbered_items(path: Path) -> list[str]:
    if not path.is_file():
        return []
    items: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if "." in stripped:
            number, text = stripped.split(".", 1)
            if number.isdigit() and text.strip():
                items.append(text.strip())
    return items


def _require_folder(folder: Path) -> Path:
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"{folder} is not a project folder.")
    return folder


def _bullets(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


def _numbered(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"{index}. {item}" for index, item in enumerate(items, start=1)]
