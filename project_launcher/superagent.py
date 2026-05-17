from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from project_launcher.data_inspector import DataInspectionUnavailableError, format_data_inspection, inspect_data_folder
from project_launcher.health import assess_health
from project_launcher.knowledge import ask_project, summarize_project
from project_launcher.multiagent import run_pm_review
from project_launcher.semantic_rag import answer_rag_question
from project_launcher.workflows import suggest_commands
from project_launcher.workspace import next_actions


@dataclass(frozen=True)
class SuperagentResult:
    report: str


def run_superagent(folder: Path, request: str, mode: str = "fast") -> SuperagentResult:
    folder = _require_folder(folder)
    if not request.strip():
        raise ValueError("Please provide a superagent request.")

    lowered = request.lower()
    evidence: list[str] = []
    if any(term in lowered for term in ["data", "csv", "metric", "revenue", "score"]):
        answer = _data_answer(folder)
        evidence.append("data/")
    elif any(term in lowered for term in ["review", "investor", "kickoff", "prepare", "ready"]):
        answer = run_pm_review(folder, mode=mode).report
        evidence.append(f"PM review agents ({mode})")
    elif any(term in lowered for term in ["customer", "complain", "research", "evidence"]):
        rag = answer_rag_question(folder, request)
        answer = rag.answer
        evidence.extend(rag.sources)
    elif any(term in lowered for term in ["summary", "summarize", "status"]):
        summary = summarize_project(folder)
        answer = "\n".join(
            [
                f"Project: {summary.title}",
                "Top goals:",
                *_bullets(summary.goals),
                "Next actions:",
                *_numbered(summary.next_actions),
            ]
        )
        evidence.append("root Markdown workspace")
    else:
        ask = ask_project(folder, request)
        answer = ask.answer
        evidence.extend(ask.sources)

    health = assess_health(folder)
    commands = suggest_commands(folder, health)
    lines = [
        "Superagent Response",
        "",
        "Answer:",
        answer,
        "",
        "Evidence:",
        *_bullets(evidence),
        "",
        "Recommended Next Actions:",
        *_numbered(next_actions(folder)),
        "",
        "Suggested Commands:",
        *_commands(commands),
    ]
    return SuperagentResult(report="\n".join(lines).rstrip() + "\n")


def _data_answer(folder: Path) -> str:
    try:
        return format_data_inspection(inspect_data_folder(folder))
    except DataInspectionUnavailableError as exc:
        return f"Data inspection needs local optional dependencies.\n{exc}"


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


def _commands(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return items
