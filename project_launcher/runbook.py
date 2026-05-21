from __future__ import annotations

from pathlib import Path

from project_launcher.state import build_project_state


def generate_runbook(folder: Path) -> str:
    state = build_project_state(folder)
    lines = [
        "Ares Project Runbook",
        "",
        "Project:",
        f"- Name: {state.config.name}",
        f"- Type: {state.config.project_type}",
        f"- Stage: {state.config.stage}",
        f"- Primary user: {state.config.primary_user}",
        "",
        "Where To Look:",
        "- brief.md for project purpose",
        "- requirements.md for must-have scope",
        "- decisions.md for product decisions",
        "- risks.md for known risks",
        "- tasks.md for execution",
        "- docs/, research/, reports/ for evidence",
        "- data/ for CSV inputs",
        "",
        "Before Kickoff:",
        "1. Run `ares validate <project>`",
        "2. Run `ares drift <project>`",
        "3. Run `ares health <project>`",
        "4. Run `ares pm-review <project> --fast`",
        "5. Run `ares quality-gate <project>`",
        "",
        "Known Weak Spots:",
        *_bullets(state.health.weak_spots),
        "",
        "Debugging Notes:",
        f"- Semantic index: {'stale' if state.index_stale else 'present' if state.index_exists else 'missing'}",
        f"- Evidence sources: {len(state.evidence_sources)}",
        f"- Unanswered questions: {len(state.unanswered_questions)}",
        "- Long-running command history is stored in .project_launcher/jobs.json",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _bullets(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]

