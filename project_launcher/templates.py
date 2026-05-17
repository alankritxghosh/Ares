from __future__ import annotations

from project_launcher.agents import ProjectPlan


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def numbered(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def readme(plan: ProjectPlan) -> str:
    return f"""# {plan.title}

## Project Idea
{plan.idea}

## What This Workspace Is For
{plan.summary}

## Start Here
1. Read `brief.md`.
2. Answer the questions in `open_questions.md`.
3. Review `requirements.md`.
4. Use `tasks.md` to plan the next working session.

## Folders
- `research/`: notes, market research, user interviews, and references.
- `designs/`: sketches, wireframes, screenshots, and design notes.
- `data/`: sample data, CSV files, exports, and analysis inputs.
- `docs/`: supporting documents, policies, specs, and handoff material.
- `reports/`: summaries, updates, and decision-ready outputs.
"""


def brief(plan: ProjectPlan) -> str:
    return f"""# Project Brief

## Working Title
{plan.title}

## Rough Idea
{plan.idea}

## Purpose
{plan.summary}

## First-Version Focus
The first version should make the project concrete enough for a founder, PM, designer, or engineer to discuss, challenge, and start executing.

## Success Signal
The project is ready to move forward when the team can name the primary user, the key problem, the first useful version, and the biggest risks.
"""


def goals(plan: ProjectPlan) -> str:
    return f"""# Goals

Project idea: {plan.idea}

{bullets(plan.goals)}
"""


def users(plan: ProjectPlan) -> str:
    return f"""# Users

Project idea: {plan.idea}

## Likely Stakeholders
{bullets(plan.audience)}

## Primary User To Confirm
Choose one primary user before building version 1. A project with one clear first user is easier to validate than a project trying to serve everyone.
"""


def requirements(plan: ProjectPlan) -> str:
    return f"""# Requirements

Project idea: {plan.idea}

## Initial Requirements
{bullets(plan.requirements)}

## Must Stay True
- Keep version 1 small enough to demo quickly.
- Write decisions down as the project becomes clearer.
- Update this file when new requirements are confirmed.
"""


def roadmap(plan: ProjectPlan) -> str:
    return f"""# Roadmap

Project idea: {plan.idea}

{numbered(plan.roadmap)}
"""


def risks(plan: ProjectPlan) -> str:
    return f"""# Risks

Project idea: {plan.idea}

{bullets(plan.risks)}
"""


def open_questions(plan: ProjectPlan) -> str:
    return f"""# Open Questions

Project idea: {plan.idea}

{numbered(plan.open_questions)}
"""


def tasks(plan: ProjectPlan) -> str:
    return f"""# Tasks

Project idea: {plan.idea}

{numbered(plan.tasks)}
"""


def decisions(plan: ProjectPlan) -> str:
    return f"""# Decisions

Project idea: {plan.idea}

Use this file to record important project choices.

## Decision Log
- No major decisions recorded yet.
"""


def all_templates(plan: ProjectPlan) -> dict[str, str]:
    return {
        "README.md": readme(plan),
        "brief.md": brief(plan),
        "goals.md": goals(plan),
        "users.md": users(plan),
        "requirements.md": requirements(plan),
        "roadmap.md": roadmap(plan),
        "risks.md": risks(plan),
        "open_questions.md": open_questions(plan),
        "tasks.md": tasks(plan),
        "decisions.md": decisions(plan),
    }
