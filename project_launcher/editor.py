from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class EditResult:
    message: str


def add_decision(folder: Path, decision: str, today: date | None = None) -> EditResult:
    folder = _require_folder(folder)
    decision = _require_text(decision, "decision")
    today = today or date.today()
    path = folder / "decisions.md"
    lines = _read_lines(path)
    lines = _ensure_heading(lines, "# Decisions")
    lines = _ensure_heading(lines, "## Decision Log")
    lines = _append_line(lines, f"- {today.isoformat()}: {decision}")
    _write_lines(path, lines)
    return EditResult("Added decision to decisions.md")


def add_risk(folder: Path, risk: str) -> EditResult:
    folder = _require_folder(folder)
    risk = _require_text(risk, "risk")
    path = folder / "risks.md"
    lines = _read_lines(path)
    lines = _ensure_heading(lines, "# Risks")
    lines = _append_line(lines, f"- {risk}")
    _write_lines(path, lines)
    return EditResult("Added risk to risks.md")


def add_task(folder: Path, task: str) -> EditResult:
    folder = _require_folder(folder)
    task = _require_text(task, "task")
    path = folder / "tasks.md"
    lines = _read_lines(path)
    lines = _ensure_heading(lines, "# Tasks")
    next_number = _next_numbered_item(lines)
    lines = _append_line(lines, f"{next_number}. {task}")
    _write_lines(path, lines)
    return EditResult(f"Added task {next_number} to tasks.md")


def answer_question(folder: Path, number: int, answer: str) -> EditResult:
    folder = _require_folder(folder)
    answer = _require_text(answer, "answer")
    if number < 1:
        raise ValueError("Question number must be 1 or higher.")

    path = folder / "open_questions.md"
    if not path.is_file():
        raise ValueError("open_questions.md does not exist.")

    lines = path.read_text(encoding="utf-8").splitlines()
    target_pattern = re.compile(rf"^\s*{number}\.\s+")
    for index, line in enumerate(lines):
        if target_pattern.match(line):
            insert_at = index + 1
            while insert_at < len(lines) and lines[insert_at].strip().startswith("Answer:"):
                insert_at += 1
            lines.insert(insert_at, f"   Answer: {answer}")
            _write_lines(path, lines)
            return EditResult(f"Answered question {number} in open_questions.md")

    raise ValueError(f"Question {number} was not found in open_questions.md.")


def _require_folder(folder: Path) -> Path:
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"{folder} is not a project folder.")
    return folder


def _require_text(value: str, label: str) -> str:
    cleaned = " ".join(value.strip().split())
    if not cleaned:
        raise ValueError(f"Please provide a {label}.")
    return cleaned


def _read_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _ensure_heading(lines: list[str], heading: str) -> list[str]:
    if any(line.strip() == heading for line in lines):
        return lines
    if not lines:
        return [heading, ""]
    if lines[-1].strip():
        return [*lines, "", heading, ""]
    return [*lines, heading, ""]


def _append_line(lines: list[str], line: str) -> list[str]:
    if lines and lines[-1].strip():
        lines.append("")
    lines.append(line)
    return lines


def _next_numbered_item(lines: list[str]) -> int:
    highest = 0
    for line in lines:
        match = re.match(r"^\s*(\d+)\.\s+", line)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1
