from __future__ import annotations

import io
import shutil
from dataclasses import dataclass
from pathlib import Path

from project_launcher import local_models
from project_launcher.editor import add_decision, add_risk, add_task, answer_question
from project_launcher.graph import run_kickoff_graph
from project_launcher.ingest import ingest_file
from project_launcher.drift import detect_drift, format_drift
from project_launcher.multiagent import run_pm_review
from project_launcher.quality import format_quality_gate, run_quality_gate
from project_launcher.semantic_rag import answer_rag_question, index_project
from project_launcher.state import build_project_state, format_state
from project_launcher.superagent import run_superagent
from project_launcher.validate import format_validation, validate_project
from project_launcher.workspace import init_workspace


@dataclass(frozen=True)
class E2EResult:
    passed: bool
    blocked: bool
    report: str


def run_e2e_check() -> E2EResult:
    status = local_models.check_model_status()
    if not status.server_reachable or status.missing_models:
        next_command = status.setup_commands[0] if status.setup_commands else "ollama pull llama3.2"
        report = "\n".join(
            [
                "E2E UX Result: BLOCKED",
                "Reason: Local model setup incomplete.",
                f"Next command: {next_command}",
                "",
                local_models.format_model_status(status).rstrip(),
            ]
        ) + "\n"
        return E2EResult(passed=False, blocked=True, report=report)

    temp_root = Path("/private/tmp/offline-project-launch-assistant-e2e")
    if temp_root.exists():
        shutil.rmtree(temp_root)
    temp_root.mkdir(parents=True)
    try:
        project = temp_root / "support-dashboard"
        init_workspace(project, "Build a customer support dashboard for support managers")
        add_decision(project, "Version 1 will target support managers")
        add_risk(project, "Zendesk API access may be delayed")
        add_task(project, "Interview 3 support managers")
        answer_question(project, 1, "The primary user is the support operations manager")
        note = project / "research" / "customer-interviews.md"
        note.write_text("# Interviews\n\n- Customers complain about slow response time.\n", encoding="utf-8")
        sample = project / "docs" / "sample.txt"
        sample.write_text("Support managers need faster queue visibility.", encoding="utf-8")
        ingest_file(project, sample)
        index_project(project)
        rag = answer_rag_question(project, "What are customers complaining about?")
        state = format_state(build_project_state(project))
        validation = format_validation(validate_project(project))
        drift = format_drift(detect_drift(project))
        pm = run_pm_review(project, mode="fast")
        super_result = run_superagent(project, "Prepare this project for kickoff", mode="fast")
        graph = run_kickoff_graph(project)
        quality = run_quality_gate(project)

        combined = "\n".join([rag.answer, state, validation, drift, pm.report, super_result.report, graph.report, format_quality_gate(quality)])
        required = ["Sources:", "Project State", "Validation Report", "Drift Report", "Agent Findings", "Suggested Commands", "Trace:", "Quality Gate Rating"]
        missing = [marker for marker in required if marker not in combined]
        passed = not missing and quality.rating >= 9.5
        output = io.StringIO()
        print("E2E UX Result: PASS" if passed else "E2E UX Result: FAIL", file=output)
        print(f"Workspace path: {project}", file=output)
        print(f"Final Rating: {quality.rating:.1f}/10", file=output)
        if missing:
            print("Missing markers:", ", ".join(missing), file=output)
        return E2EResult(passed=passed, blocked=False, report=output.getvalue())
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
