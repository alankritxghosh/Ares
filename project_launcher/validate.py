from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from project_launcher.state import ProjectState, build_project_state
from project_launcher.workflows import suggest_commands
from project_launcher.workspace import review_workspace


@dataclass(frozen=True)
class ValidationCheck:
    passed: bool
    message: str
    fix: str


@dataclass(frozen=True)
class ValidationReport:
    checks: list[ValidationCheck]
    suggested_commands: list[str]


def validate_project(folder: Path) -> ValidationReport:
    state = build_project_state(folder)
    review = review_workspace(folder)
    checks = [
        ValidationCheck(state.has_config, "ares.yaml is present", "Run init for new projects or add ares.yaml."),
        ValidationCheck(not review.missing_files and not review.empty_files, "Required workspace files are present", "Restore missing or empty workspace files."),
        ValidationCheck(state.health.score >= 80, f"Project health is {state.health.score}%", "Run ares health and apply recommended fixes."),
        ValidationCheck(state.config.primary_user != "To confirm", "Primary user is declared in config", "Set primary_user in ares.yaml."),
        ValidationCheck(bool(state.decisions), "At least one decision is recorded", f'ares add-decision {state.folder} "Version 1 will target ..."'),
        ValidationCheck(not state.unanswered_questions, "Open questions have answers", f'ares answer-question {state.folder} 1 "The primary user is ..."'),
        ValidationCheck(bool(state.evidence_sources), "Evidence sources are available", "Add Markdown notes to docs/, research/, or reports/."),
        ValidationCheck(not state.index_stale, "Semantic index is current or absent", f"ares index {state.folder}"),
        ValidationCheck(len(state.next_actions) >= 3, "Next actions are available", f'ares add-task {state.folder} "Interview the first target user"'),
    ]
    commands = suggest_commands(state.folder, state.health)
    commands.extend(check.fix for check in checks if not check.passed and check.fix.startswith("ares "))
    return ValidationReport(checks=checks, suggested_commands=_unique(commands))


def format_validation(report: ValidationReport) -> str:
    lines = ["Validation Report", "", "Checks:"]
    for check in report.checks:
        marker = "PASS" if check.passed else "FAIL"
        lines.append(f"- [{marker}] {check.message}")
        if not check.passed:
            lines.append(f"  Fix: {check.fix}")
    lines.extend(["", "Suggested Commands:", *_commands(report.suggested_commands)])
    return "\n".join(lines).rstrip() + "\n"


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

