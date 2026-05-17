from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from project_launcher.agents import create_project_plan
from project_launcher.templates import all_templates


REQUIRED_FILES = [
    "README.md",
    "brief.md",
    "goals.md",
    "users.md",
    "requirements.md",
    "roadmap.md",
    "risks.md",
    "open_questions.md",
    "tasks.md",
    "decisions.md",
]

REQUIRED_DIRS = ["research", "designs", "data", "docs", "reports"]


@dataclass(frozen=True)
class InitResult:
    path: Path
    files: list[Path]
    directories: list[Path]


@dataclass(frozen=True)
class ReviewResult:
    path: Path
    missing_files: list[str]
    missing_directories: list[str]
    empty_files: list[str]
    readiness_score: int


def is_empty_directory(path: Path) -> bool:
    return path.is_dir() and not any(path.iterdir())


def init_workspace(folder: Path, idea: str) -> InitResult:
    folder = folder.expanduser().resolve()
    if not idea.strip():
        raise ValueError("Please provide a project idea.")

    if folder.exists() and not folder.is_dir():
        raise ValueError(f"{folder} exists but is not a folder.")

    if folder.exists() and not is_empty_directory(folder):
        raise ValueError(f"{folder} already has files. Choose an empty folder or a new path.")

    folder.mkdir(parents=True, exist_ok=True)

    plan = create_project_plan(idea)
    created_dirs: list[Path] = []
    for directory in REQUIRED_DIRS:
        target = folder / directory
        target.mkdir()
        created_dirs.append(target)

    created_files: list[Path] = []
    for filename, content in all_templates(plan).items():
        target = folder / filename
        target.write_text(content, encoding="utf-8")
        created_files.append(target)

    return InitResult(path=folder, files=created_files, directories=created_dirs)


def review_workspace(folder: Path) -> ReviewResult:
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"{folder} is not a project folder.")

    missing_files = [name for name in REQUIRED_FILES if not (folder / name).is_file()]
    missing_directories = [name for name in REQUIRED_DIRS if not (folder / name).is_dir()]
    empty_files = [
        name
        for name in REQUIRED_FILES
        if (folder / name).is_file() and (folder / name).read_text(encoding="utf-8").strip() == ""
    ]
    total_items = len(REQUIRED_FILES) + len(REQUIRED_DIRS)
    missing_or_empty = len(set(missing_files + empty_files)) + len(missing_directories)
    readiness_score = round(((total_items - missing_or_empty) / total_items) * 100)
    return ReviewResult(
        path=folder,
        missing_files=missing_files,
        missing_directories=missing_directories,
        empty_files=empty_files,
        readiness_score=readiness_score,
    )


def next_actions(folder: Path) -> list[str]:
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"{folder} is not a project folder.")

    candidates = _read_numbered_items(folder / "tasks.md")
    if len(candidates) < 3:
        candidates.extend(_read_numbered_items(folder / "open_questions.md"))
    if len(candidates) < 3:
        candidates.extend(_read_numbered_items(folder / "roadmap.md"))

    if not candidates:
        return [
            "Write a short project brief",
            "Choose the primary user",
            "List the top 5 requirements",
        ]
    return candidates[:3]


def _read_numbered_items(path: Path) -> list[str]:
    if not path.is_file():
        return []

    items: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or "." not in stripped:
            continue
        number, text = stripped.split(".", 1)
        if number.isdigit() and text.strip():
            items.append(text.strip())
    return items
