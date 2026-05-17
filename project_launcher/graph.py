from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from project_launcher.health import HealthReport, assess_health
from project_launcher.knowledge import SummaryResult, summarize_project
from project_launcher.workflows import suggest_commands
from project_launcher.workspace import next_actions


@dataclass
class GraphState:
    folder: Path
    summary: SummaryResult | None = None
    health: HealthReport | None = None
    next_actions: list[str] | None = None
    suggested_commands: list[str] | None = None
    report: str = ""


@dataclass(frozen=True)
class GraphKickoffResult:
    trace: list[str]
    report: str


Node = Callable[[GraphState], GraphState]


def run_kickoff_graph(folder: Path) -> GraphKickoffResult:
    state = GraphState(folder=folder.expanduser().resolve())
    trace: list[str] = []
    for name, node in _graph_nodes():
        state = node(state)
        trace.append(name)
    return GraphKickoffResult(trace=trace, report=state.report)


def summary_node(state: GraphState) -> GraphState:
    state.summary = summarize_project(state.folder)
    return state


def health_node(state: GraphState) -> GraphState:
    state.health = assess_health(state.folder)
    return state


def next_actions_node(state: GraphState) -> GraphState:
    state.next_actions = next_actions(state.folder)
    return state


def suggested_commands_node(state: GraphState) -> GraphState:
    if state.health is None:
        raise ValueError("health_node must run before suggested_commands_node.")
    state.suggested_commands = suggest_commands(state.folder, state.health)
    return state


def final_report_node(state: GraphState) -> GraphState:
    if state.summary is None:
        raise ValueError("summary_node must run before final_report_node.")
    if state.health is None:
        raise ValueError("health_node must run before final_report_node.")
    actions = state.next_actions or []
    commands = state.suggested_commands or []
    trace = [name for name, _node in _graph_nodes()]

    lines = [
        "Graph Kickoff Workflow",
        "",
        "Trace:",
        *_numbered(trace),
        "",
        "Step 1: Project Summary",
        f"Project: {state.summary.title}",
        "",
        "Top goals:",
        *_bullets(state.summary.goals),
        "",
        "Top requirements:",
        *_bullets(state.summary.requirements),
        "",
        "Step 2: Health Check",
        f"Project Health: {state.health.score}%",
        "",
        "Weak Spots:",
        *_bullets(state.health.weak_spots),
        "",
        "Step 3: Recommended Next Actions",
        *_numbered(actions),
        "",
        "Step 4: Suggested Commands",
        *_commands(commands),
    ]
    state.report = "\n".join(lines).rstrip() + "\n"
    return state


def _graph_nodes() -> list[tuple[str, Node]]:
    return [
        ("summary_node", summary_node),
        ("health_node", health_node),
        ("next_actions_node", next_actions_node),
        ("suggested_commands_node", suggested_commands_node),
        ("final_report_node", final_report_node),
    ]


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
