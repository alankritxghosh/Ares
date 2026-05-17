from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from project_launcher.workspace import REQUIRED_DIRS


@dataclass(frozen=True)
class HealthReport:
    score: int
    strengths: list[str]
    weak_spots: list[str]
    recommended_fixes: list[str]


@dataclass(frozen=True)
class HealthCheck:
    passed: bool
    strength: str
    weak_spot: str
    fix: str


def assess_health(folder: Path) -> HealthReport:
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"{folder} is not a project folder.")

    checks = [
        _content_check(folder / "brief.md", "Project brief is present", "Project brief is missing or too thin", "Add a clear brief in brief.md."),
        _contains_check(
            folder / "users.md",
            ["user", "stakeholder"],
            "Users or stakeholders are documented",
            "Primary users are not clear yet",
            "Clarify the primary user in users.md.",
        ),
        _bullet_check(
            folder / "requirements.md",
            "Requirements are documented",
            "Requirements are missing",
            "Add requirements to requirements.md.",
        ),
        _bullet_check(folder / "risks.md", "Risks are documented", "Risks are missing", "Add a risk with add-risk."),
        _numbered_check(folder / "tasks.md", "Tasks are documented", "Tasks are missing", "Add a task with add-task."),
        _numbered_check(folder / "roadmap.md", "Roadmap is documented", "Roadmap is missing", "Add roadmap phases to roadmap.md."),
        _decision_check(folder / "decisions.md"),
        _numbered_check(
            folder / "open_questions.md",
            "Open questions are documented",
            "Open questions are missing",
            "Add kickoff questions to open_questions.md.",
        ),
        _answered_question_check(folder / "open_questions.md"),
        _folders_check(folder),
    ]

    strengths = [check.strength for check in checks if check.passed]
    weak_spots = [check.weak_spot for check in checks if not check.passed]
    recommended_fixes = [check.fix for check in checks if not check.passed]
    score = round((len(strengths) / len(checks)) * 100)
    return HealthReport(score=score, strengths=strengths, weak_spots=weak_spots, recommended_fixes=recommended_fixes[:5])


def _content_check(path: Path, strength: str, weak_spot: str, fix: str) -> HealthCheck:
    passed = path.is_file() and len(_meaningful_lines(path)) >= 3
    return HealthCheck(passed, strength, weak_spot, fix)


def _contains_check(path: Path, terms: list[str], strength: str, weak_spot: str, fix: str) -> HealthCheck:
    text = _read_text(path).lower()
    passed = path.is_file() and any(term in text for term in terms)
    return HealthCheck(passed, strength, weak_spot, fix)


def _bullet_check(path: Path, strength: str, weak_spot: str, fix: str) -> HealthCheck:
    passed = path.is_file() and any(line.strip().startswith(("-", "*")) for line in _read_lines(path))
    return HealthCheck(passed, strength, weak_spot, fix)


def _numbered_check(path: Path, strength: str, weak_spot: str, fix: str) -> HealthCheck:
    passed = path.is_file() and any(re.match(r"^\s*\d+\.\s+", line) for line in _read_lines(path))
    return HealthCheck(passed, strength, weak_spot, fix)


def _decision_check(path: Path) -> HealthCheck:
    decision_pattern = re.compile(r"^\s*-\s+\d{4}-\d{2}-\d{2}:")
    passed = path.is_file() and any(decision_pattern.match(line) for line in _read_lines(path))
    return HealthCheck(
        passed,
        "At least one decision has been recorded",
        "No decision has been recorded yet",
        "Add at least one decision with add-decision.",
    )


def _answered_question_check(path: Path) -> HealthCheck:
    passed = path.is_file() and any(line.strip().startswith("Answer:") for line in _read_lines(path))
    return HealthCheck(
        passed,
        "At least one open question has an answer",
        "Some open questions have no answers",
        "Answer question 1 with answer-question.",
    )


def _folders_check(folder: Path) -> HealthCheck:
    missing = [name for name in REQUIRED_DIRS if not (folder / name).is_dir()]
    return HealthCheck(
        not missing,
        "Required project folders are present",
        "One or more required project folders are missing",
        "Restore the required project folders with init in a clean workspace.",
    )


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _read_lines(path: Path) -> list[str]:
    return _read_text(path).splitlines()


def _meaningful_lines(path: Path) -> list[str]:
    lines = []
    for line in _read_lines(path):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            lines.append(stripped)
    return lines
