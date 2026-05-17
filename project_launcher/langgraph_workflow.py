from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

from project_launcher.health import HealthReport, assess_health
from project_launcher.knowledge import SummaryResult, summarize_project
from project_launcher.workflows import suggest_commands
from project_launcher.workspace import next_actions


class LangGraphUnavailableError(ValueError):
    pass


class KickoffLangGraphState(TypedDict, total=False):
    folder: Path
    summary: SummaryResult
    health: HealthReport
    next_actions: list[str]
    suggested_commands: list[str]
    trace: list[str]
    report: str


def build_kickoff_langgraph() -> Any:
    try:
        from langgraph.graph import END, StateGraph
    except ImportError as exc:
        raise LangGraphUnavailableError(
            "LangGraph is not installed.\nInstall it with: pip install langgraph"
        ) from exc

    graph = StateGraph(KickoffLangGraphState)
    graph.add_node("summary_node", summary_node)
    graph.add_node("health_node", health_node)
    graph.add_node("next_actions_node", next_actions_node)
    graph.add_node("suggested_commands_node", suggested_commands_node)
    graph.add_node("final_report_node", final_report_node)
    graph.set_entry_point("summary_node")
    graph.add_edge("summary_node", "health_node")
    graph.add_edge("health_node", "next_actions_node")
    graph.add_edge("next_actions_node", "suggested_commands_node")
    graph.add_edge("suggested_commands_node", "final_report_node")
    graph.add_edge("final_report_node", END)
    return graph.compile()


def run_kickoff_langgraph(folder: Path) -> str:
    app = build_kickoff_langgraph()
    state = app.invoke({"folder": folder.expanduser().resolve(), "trace": []})
    return state["report"]


def summary_node(state: KickoffLangGraphState) -> KickoffLangGraphState:
    folder = _folder(state)
    return {**state, "summary": summarize_project(folder), "trace": _trace(state, "summary_node")}


def health_node(state: KickoffLangGraphState) -> KickoffLangGraphState:
    folder = _folder(state)
    return {**state, "health": assess_health(folder), "trace": _trace(state, "health_node")}


def next_actions_node(state: KickoffLangGraphState) -> KickoffLangGraphState:
    folder = _folder(state)
    return {**state, "next_actions": next_actions(folder), "trace": _trace(state, "next_actions_node")}


def suggested_commands_node(state: KickoffLangGraphState) -> KickoffLangGraphState:
    folder = _folder(state)
    health = state.get("health")
    if health is None:
        raise ValueError("health_node must run before suggested_commands_node.")
    return {
        **state,
        "suggested_commands": suggest_commands(folder, health),
        "trace": _trace(state, "suggested_commands_node"),
    }


def final_report_node(state: KickoffLangGraphState) -> KickoffLangGraphState:
    summary = state.get("summary")
    health = state.get("health")
    if summary is None:
        raise ValueError("summary_node must run before final_report_node.")
    if health is None:
        raise ValueError("health_node must run before final_report_node.")

    trace = _trace(state, "final_report_node")
    actions = state.get("next_actions", [])
    commands = state.get("suggested_commands", [])
    lines = [
        "LangGraph Kickoff Workflow",
        "",
        "Trace:",
        *_numbered(trace),
        "",
        "Step 1: Project Summary",
        f"Project: {summary.title}",
        "",
        "Top goals:",
        *_bullets(summary.goals),
        "",
        "Top requirements:",
        *_bullets(summary.requirements),
        "",
        "Step 2: Health Check",
        f"Project Health: {health.score}%",
        "",
        "Weak Spots:",
        *_bullets(health.weak_spots),
        "",
        "Step 3: Recommended Next Actions",
        *_numbered(actions),
        "",
        "Step 4: Suggested Commands",
        *_commands(commands),
    ]
    return {**state, "trace": trace, "report": "\n".join(lines).rstrip() + "\n"}


def _folder(state: KickoffLangGraphState) -> Path:
    return state["folder"]


def _trace(state: KickoffLangGraphState, node_name: str) -> list[str]:
    return [*state.get("trace", []), node_name]


def _bullets(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


def _numbered(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"{index}. {item}" for index, item in enumerate(items, start=1)]


def _commands(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return items
