from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from project_launcher.health import HealthReport, assess_health
from project_launcher.knowledge import SummaryResult, summarize_project
from project_launcher.workspace import next_actions


@dataclass(frozen=True)
class KickoffWorkflowResult:
    summary: SummaryResult
    health: HealthReport
    next_actions: list[str]
    suggested_commands: list[str]


def run_kickoff_workflow(folder: Path) -> KickoffWorkflowResult:
    folder = folder.expanduser().resolve()
    summary = summarize_project(folder)
    health = assess_health(folder)
    actions = next_actions(folder)
    commands = suggest_commands(folder, health)
    return KickoffWorkflowResult(
        summary=summary,
        health=health,
        next_actions=actions,
        suggested_commands=commands,
    )


def suggest_commands(folder: Path, health: HealthReport) -> list[str]:
    if health.score == 100:
        return []

    folder_text = str(folder)
    commands: list[str] = []
    for weak_spot in health.weak_spots:
        lowered = weak_spot.lower()
        if "decision" in lowered:
            commands.append(f'python main.py add-decision {folder_text} "Version 1 will target ..."')
        elif "open questions" in lowered or "answer" in lowered:
            commands.append(f'python main.py answer-question {folder_text} 1 "The primary user is ..."')
        elif "risk" in lowered:
            commands.append(f'python main.py add-risk {folder_text} "Name the biggest project risk"')
        elif "task" in lowered:
            commands.append(f'python main.py add-task {folder_text} "Interview the first target user"')

    return _unique(commands)


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items
