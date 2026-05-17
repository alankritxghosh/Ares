from __future__ import annotations

import time
from dataclasses import dataclass

from project_launcher import local_models


@dataclass(frozen=True)
class AgentSpec:
    name: str
    responsibility: str
    fallback: str


@dataclass(frozen=True)
class AgentFinding:
    name: str
    output: str
    used_model: bool
    elapsed_seconds: float


AGENTS = [
    AgentSpec("Founder Clarifier", "Check whether the idea, target user, and business goal are clear.", "Clarify the primary user, business goal, and smallest useful first version."),
    AgentSpec("PM Strategist", "Review goals, users, requirements, and roadmap.", "Tighten goals, requirements, and roadmap around the first useful version."),
    AgentSpec("Research Analyst", "Use project notes to identify customer evidence and missing research.", "Add customer evidence from research notes and identify the riskiest assumptions."),
    AgentSpec("Data Analyst", "Review CSV/data inspection findings when present.", "Use available CSV summaries to identify metrics worth tracking."),
    AgentSpec("Risk Reviewer", "Review risks, weak spots, and unanswered questions.", "Resolve unanswered kickoff questions and record project decisions."),
    AgentSpec("Execution Planner", "Turn findings into practical next actions.", "Prioritize interviews, validation tasks, and one concrete product decision."),
    AgentSpec("Final Reviewer", "Grade project readiness and summarize the handoff.", "Use the health score and next actions to prepare the project for kickoff."),
]


FAST_AGENT_NAMES = {"PM Strategist", "Risk Reviewer", "Execution Planner"}
REVIEW_MODES = {"fast", "full"}


def agents_for_mode(mode: str) -> list[AgentSpec]:
    if mode not in REVIEW_MODES:
        raise ValueError("Review mode must be 'fast' or 'full'.")
    if mode == "full":
        return list(AGENTS)
    return [agent for agent in AGENTS if agent.name in FAST_AGENT_NAMES]


def run_agent(spec: AgentSpec, context: str, timeout: float = 60.0) -> AgentFinding:
    started = time.perf_counter()
    prompt = (
        f"You are the {spec.name} for an offline product management assistant.\n"
        f"Responsibility: {spec.responsibility}\n\n"
        "Return 2-4 concise bullets. Be practical, founder/PM focused, and do not invent facts.\n\n"
        f"Project context:\n{context}\n\n"
        "Findings:"
    )
    try:
        output = local_models.generate_text(prompt, timeout=timeout)
        return AgentFinding(name=spec.name, output=output, used_model=True, elapsed_seconds=time.perf_counter() - started)
    except local_models.LocalModelUnavailableError:
        return AgentFinding(
            name=spec.name,
            output=f"- {spec.fallback}",
            used_model=False,
            elapsed_seconds=time.perf_counter() - started,
        )
