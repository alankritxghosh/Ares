from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

from project_launcher.catalog import format_catalog
from project_launcher.drift import detect_drift, format_drift
from project_launcher.jobs import format_job, format_jobs, get_job, list_jobs, run_with_job
from project_launcher.knowledge import ask_project
from project_launcher.multiagent import run_pm_review
from project_launcher.quality import format_quality_gate, run_quality_gate
from project_launcher.rag import answer_deep_question
from project_launcher.runbook import generate_runbook
from project_launcher.semantic_rag import answer_rag_question, index_project
from project_launcher.state import build_project_state, format_state
from project_launcher.superagent import run_superagent
from project_launcher.validate import format_validation, validate_project
from project_launcher.workspace import init_workspace


MCP_SETUP_MESSAGE = (
    "Error: MCP support is not installed.\n"
    "Install it with: pipx inject ares-pm mcp\n"
)


def ares_catalog() -> str:
    return _safe(lambda: format_catalog())


def ares_init(folder: str, idea: str, project_type: str = "", stage: str = "discovery") -> str:
    def operation() -> str:
        selected_type = project_type.strip() or "founder-mvp"
        result = init_workspace(
            Path(folder),
            idea,
            project_type=selected_type,
            stage=stage,
            apply_catalog=bool(project_type.strip()),
        )
        return "\n".join(
            [
                f"Created project workspace: {result.path}",
                "",
                "Files:",
                *[f"- {path.name}" for path in result.files],
                "",
                "Next step:",
                f"Use Ares to inspect project state for {result.path}",
            ]
        ).rstrip() + "\n"

    return _safe(operation)


def ares_state(folder: str) -> str:
    return _safe(lambda: format_state(build_project_state(Path(folder))))


def ares_validate(folder: str) -> str:
    return _safe(lambda: format_validation(validate_project(Path(folder))))


def ares_drift(folder: str) -> str:
    return _safe(lambda: format_drift(detect_drift(Path(folder))))


def ares_runbook(folder: str) -> str:
    return _safe(lambda: generate_runbook(Path(folder)))


def ares_ask(folder: str, question: str) -> str:
    return _safe(lambda: _answer_with_sources_from_result(ask_project(Path(folder), question)))


def ares_ask_deep(folder: str, question: str) -> str:
    return _safe(lambda: _answer_with_sources_from_result(answer_deep_question(Path(folder), question)))


def ares_index(folder: str) -> str:
    def operation() -> str:
        path = Path(folder)
        result = run_with_job(
            path,
            "index",
            lambda: index_project(path),
            lambda item: f"Indexed {item.chunk_count} chunks",
        )
        return "\n".join(
            [
                f"Indexed project: {result.index_path}",
                f"Chunks: {result.chunk_count}",
                "",
                "Sources:",
                *_bullets(result.sources),
            ]
        ).rstrip() + "\n"

    return _safe(operation)


def ares_ask_rag(folder: str, question: str) -> str:
    return _safe(lambda: _answer_with_sources_from_result(answer_rag_question(Path(folder), question)))


def ares_pm_review(folder: str, mode: str = "fast") -> str:
    def operation() -> str:
        path = Path(folder)
        result = run_with_job(
            path,
            f"pm-review --{mode}",
            lambda: run_pm_review(path, mode=mode),
            lambda item: f"PM review {item.mode}, {len(item.findings)} agents",
        )
        return result.report

    return _safe(operation)


def ares_super(folder: str, request: str, mode: str = "fast") -> str:
    def operation() -> str:
        path = Path(folder)
        result = run_with_job(
            path,
            f"super --{mode}",
            lambda: run_superagent(path, request, mode=mode),
            lambda _item: "Superagent response generated",
        )
        return result.report

    return _safe(operation)


def ares_quality_gate(folder: str) -> str:
    def operation() -> str:
        path = Path(folder)
        result = run_with_job(
            path,
            "quality-gate",
            lambda: run_quality_gate(path),
            lambda item: f"Quality gate {item.rating:.1f}/10",
        )
        return format_quality_gate(result)

    return _safe(operation)


def ares_jobs(folder: str) -> str:
    return _safe(lambda: format_jobs(list_jobs(Path(folder))))


def ares_job_status(folder: str, job_id: str) -> str:
    return _safe(lambda: format_job(get_job(Path(folder), job_id)))


def build_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(MCP_SETUP_MESSAGE.strip()) from exc

    server = FastMCP("Ares")
    server.tool(description="Read-only. List built-in Ares project catalog types.")(ares_catalog)
    server.tool(description="Mutating. Create a new Ares project workspace in a new or empty folder.")(ares_init)
    server.tool(description="Read-only. Inspect Ares project control-plane state.")(ares_state)
    server.tool(description="Read-only. Validate Ares project readiness.")(ares_validate)
    server.tool(description="Read-only. Detect project-management drift.")(ares_drift)
    server.tool(description="Read-only. Generate an operational project runbook.")(ares_runbook)
    server.tool(description="Read-only. Ask root project Markdown files.")(ares_ask)
    server.tool(description="Read-only. Ask root and nested docs/research/reports Markdown files.")(ares_ask_deep)
    server.tool(description="Mutating. Build or refresh the local semantic index.")(ares_index)
    server.tool(description="Read-only. Ask the local semantic RAG index.")(ares_ask_rag)
    server.tool(description="Read-only. Run Ares PM review in fast or full mode.")(ares_pm_review)
    server.tool(description="Read-only. Route a natural PM/founder request through Ares.")(ares_super)
    server.tool(description="Read-only. Run the Ares quality gate.")(ares_quality_gate)
    server.tool(description="Read-only. List recorded Ares jobs.")(ares_jobs)
    server.tool(description="Read-only. Show one recorded Ares job.")(ares_job_status)
    return server


def main() -> int:
    try:
        server = build_server()
    except RuntimeError:
        print(MCP_SETUP_MESSAGE, file=sys.stderr, end="")
        return 1
    server.run()
    return 0


def _answer_with_sources(answer: str, sources: list[str]) -> str:
    lines = ["Answer:", answer]
    if sources:
        lines.extend(["", "Sources:", *_bullets(sources)])
    return "\n".join(lines).rstrip() + "\n"


def _answer_with_sources_from_result(result) -> str:
    return _answer_with_sources(result.answer, result.sources)


def _safe(operation: Callable[[], str]) -> str:
    try:
        return operation()
    except ValueError as exc:
        return f"Error: {exc}\n"


def _bullets(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


if __name__ == "__main__":
    raise SystemExit(main())
