from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectPlan:
    idea: str
    title: str
    summary: str
    audience: list[str]
    goals: list[str]
    requirements: list[str]
    roadmap: list[str]
    risks: list[str]
    open_questions: list[str]
    tasks: list[str]


def make_title(idea: str) -> str:
    cleaned = " ".join(idea.strip().split())
    if not cleaned:
        return "New Project"
    words = cleaned.replace("-", " ").split()
    stop_words = {"a", "an", "the", "for", "to", "of", "and", "or"}
    title_words = [word.capitalize() if word.lower() not in stop_words else word.lower() for word in words[:8]]
    if title_words:
        title_words[0] = title_words[0].capitalize()
    return " ".join(title_words)


def planner_agent(idea: str) -> tuple[str, str]:
    title = make_title(idea)
    summary = (
        f"This project starts from the idea: {idea.strip()}. "
        "The first version should clarify the user, the problem, the first useful outcome, "
        "and the smallest set of work needed to validate the direction."
    )
    return title, summary


def pm_agent(idea: str) -> tuple[list[str], list[str], list[str], list[str]]:
    audience = [
        "Founder or product manager driving the project",
        "Early users who will validate whether the project solves a real problem",
        "Engineering or design partners who need a clear handoff",
    ]
    goals = [
        "Turn the rough idea into a clear project brief",
        "Identify the primary users and their most important needs",
        "Define a small first version that can be reviewed quickly",
        "Capture open questions before execution begins",
        "Create a workspace that keeps decisions, tasks, and research organized",
    ]
    requirements = [
        "Clear project purpose and target users",
        "Initial must-have features or deliverables",
        "Simple roadmap with practical phases",
        "Visible risks and unanswered questions",
        "Next tasks that a founder, PM, designer, or engineer can act on",
    ]
    open_questions = [
        "Who is the primary user for the first version?",
        "What problem must this solve better than the current workaround?",
        "What is the smallest useful demo or prototype?",
        "What data, tools, or people are needed before work starts?",
        "How will the team know the project is worth continuing?",
    ]
    return audience, goals, requirements, open_questions


def execution_agent() -> tuple[list[str], list[str]]:
    roadmap = [
        "Phase 1: Clarify users, problem, success criteria, and constraints",
        "Phase 2: Create a first concept, workflow, or prototype outline",
        "Phase 3: Gather feedback from the most important users or stakeholders",
        "Phase 4: Build the smallest useful version",
        "Phase 5: Review outcomes, risks, and the next investment decision",
    ]
    tasks = [
        "Write a one-paragraph project brief",
        "Choose the primary user for version 1",
        "List the top 5 must-have requirements",
        "Answer the open questions that block execution",
        "Create the first demo, wireframe, or technical handoff",
    ]
    return roadmap, tasks


def risk_agent() -> list[str]:
    return [
        "The project may be too broad unless version 1 is kept small",
        "The primary user may not be specific enough yet",
        "Required data, integrations, or approvals may be missing",
        "Stakeholders may disagree on what success means",
        "The team may start building before the riskiest assumptions are tested",
    ]


def create_project_plan(idea: str) -> ProjectPlan:
    title, summary = planner_agent(idea)
    audience, goals, requirements, open_questions = pm_agent(idea)
    roadmap, tasks = execution_agent()
    risks = risk_agent()
    return ProjectPlan(
        idea=idea.strip(),
        title=title,
        summary=summary,
        audience=audience,
        goals=goals,
        requirements=requirements,
        roadmap=roadmap,
        risks=risks,
        open_questions=open_questions,
        tasks=tasks,
    )
