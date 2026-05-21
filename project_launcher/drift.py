from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from project_launcher.catalog import DEFAULT_STAGE
from project_launcher.state import ProjectState, build_project_state


@dataclass(frozen=True)
class DriftReport:
    drift: list[str]
    suggested_commands: list[str]


def detect_drift(folder: Path) -> DriftReport:
    state = build_project_state(folder)
    drift: list[str] = []
    commands: list[str] = []
    if len(state.decisions) == 0 and _count_items(state.folder / "requirements.md") + _count_items(state.folder / "tasks.md") >= 5:
        drift.append("Requirements and tasks exist, but no product decision has been recorded")
        commands.append(f'ares add-decision {state.folder} "Version 1 will target ..."')
    if state.unanswered_questions:
        drift.append("Open questions are still unanswered")
        commands.append(f'ares answer-question {state.folder} 1 "The primary user is ..."')
    if _count_items(state.folder / "risks.md") and not _contains_terms(state.folder / "tasks.md", ["risk", "mitigate", "validate"]):
        drift.append("Risks exist but no mitigation or validation task is recorded")
        commands.append(f'ares add-task {state.folder} "Validate the biggest project risk"')
    if state.index_exists and state.index_stale:
        drift.append("Research or docs changed after the semantic index was built")
        commands.append(f"ares index {state.folder}")
    if state.has_config and state.config.primary_user != "To confirm" and not _contains_text(state.folder / "users.md", state.config.primary_user):
        drift.append("ares.yaml primary user does not appear in users.md")
        commands.append(f"Update users.md to match primary_user in ares.yaml")
    if state.has_config and state.config.stage != DEFAULT_STAGE and state.config.stage.lower() not in _read_text(state.folder / "README.md").lower():
        drift.append("ares.yaml stage is not reflected in the workspace README")
    return DriftReport(drift=drift, suggested_commands=_unique(commands))


def format_drift(report: DriftReport) -> str:
    status = "Attention needed" if report.drift else "No drift detected"
    lines = ["Drift Report", f"Status: {status}", "", "Drift:", *_bullets(report.drift), "", "Suggested Commands:", *_commands(report.suggested_commands)]
    return "\n".join(lines).rstrip() + "\n"


def _count_items(path: Path) -> int:
    return sum(1 for line in _read_text(path).splitlines() if line.strip().startswith(("- ", "* ")) or _numbered(line.strip()))


def _numbered(line: str) -> bool:
    if "." not in line:
        return False
    number, text = line.split(".", 1)
    return number.isdigit() and bool(text.strip())


def _contains_terms(path: Path, terms: list[str]) -> bool:
    text = _read_text(path).lower()
    return any(term in text for term in terms)


def _contains_text(path: Path, expected: str) -> bool:
    return expected.lower() in _read_text(path).lower()


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _bullets(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


def _commands(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return items


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique
