from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from project_launcher.agents_llm import AgentFinding, agents_for_mode, run_agent
from project_launcher.data_inspector import DataInspectionUnavailableError, format_data_inspection, inspect_data_folder
from project_launcher.health import assess_health
from project_launcher.knowledge import summarize_project
from project_launcher.rag import answer_deep_question
from project_launcher.workspace import next_actions


@dataclass(frozen=True)
class PMReviewResult:
    report: str
    findings: list[AgentFinding]
    mode: str
    elapsed_seconds: float


def run_pm_review(folder: Path, mode: str = "fast") -> PMReviewResult:
    folder = _require_folder(folder)
    agents = agents_for_mode(mode)
    context = _build_context(folder)
    started = time.perf_counter()
    findings = [run_agent(agent, context) for agent in agents]
    elapsed_seconds = time.perf_counter() - started
    health = assess_health(folder)
    summary = summarize_project(folder)
    actions = next_actions(folder)
    sources = _sources(folder)
    lines = [
        "PM Review",
        "",
        f"Project: {summary.title}",
        f"Overall Readiness: {health.score}%",
        "",
        "Agent Findings:",
    ]
    for finding in findings:
        execution_mode = "local model" if finding.used_model else "deterministic fallback"
        lines.extend([f"", f"{finding.name} ({execution_mode}, {finding.elapsed_seconds:.1f}s):", finding.output])
    lines.extend(
        [
            "",
            "Recommended Decisions:",
            "- Choose the primary version 1 user and success metric.",
            "- Record the riskiest product assumption before kickoff.",
            "",
            "Recommended Tasks:",
            *_numbered(actions),
            "",
            "Risks:",
            *_bullets(health.weak_spots),
            "",
            "Sources:",
            *_bullets(sources),
            "",
            "Timing:",
            f"- Mode: {mode}",
            f"- Agents run: {len(findings)}",
            f"- Total: {elapsed_seconds:.1f}s",
        ]
    )
    return PMReviewResult(report="\n".join(lines).rstrip() + "\n", findings=findings, mode=mode, elapsed_seconds=elapsed_seconds)


def _build_context(folder: Path) -> str:
    summary = summarize_project(folder)
    health = assess_health(folder)
    deep = answer_deep_question(folder, "What customer evidence, risks, requirements, and next actions matter?")
    try:
        data_report = format_data_inspection(inspect_data_folder(folder))
    except (ValueError, DataInspectionUnavailableError):
        data_report = "Data inspection unavailable or no data files inspected."
    return "\n\n".join(
        [
            f"Project: {summary.title}",
            "Goals:\n" + "\n".join(summary.goals),
            "Requirements:\n" + "\n".join(summary.requirements),
            "Health weak spots:\n" + "\n".join(health.weak_spots),
            "Deep project notes:\n" + deep.answer,
            "Data:\n" + data_report,
        ]
    )


def _sources(folder: Path) -> list[str]:
    sources = [path.relative_to(folder).as_posix() for path in sorted(folder.glob("*.md"))]
    for directory in ["docs", "research", "reports"]:
        root = folder / directory
        if root.is_dir():
            sources.extend(path.relative_to(folder).as_posix() for path in sorted(root.rglob("*.md")))
    return sources[:10]


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
