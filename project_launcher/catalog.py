from __future__ import annotations

from dataclasses import dataclass


PROJECT_TYPES = ["saas-dashboard", "ai-agent", "internal-tool", "data-product", "marketplace-app", "founder-mvp"]
DEFAULT_PROJECT_TYPE = "founder-mvp"
DEFAULT_STAGE = "discovery"


@dataclass(frozen=True)
class CatalogEntry:
    name: str
    description: str
    extra_requirements: list[str]
    extra_risks: list[str]
    extra_tasks: list[str]
    extra_questions: list[str]


CATALOG: dict[str, CatalogEntry] = {
    "saas-dashboard": CatalogEntry(
        name="saas-dashboard",
        description="B2B dashboard, reporting, or operations product.",
        extra_requirements=["Identify the core metrics the first dashboard must show"],
        extra_risks=["Dashboard users may not trust the data if source systems are unclear"],
        extra_tasks=["Collect one sample dataset for the dashboard"],
        extra_questions=["Which metric would make this dashboard worth opening every day?"],
    ),
    "ai-agent": CatalogEntry(
        name="ai-agent",
        description="AI assistant, agent workflow, or local model product.",
        extra_requirements=["Define the agent's allowed actions and fallback behavior"],
        extra_risks=["The agent may sound confident without enough project evidence"],
        extra_tasks=["Write three realistic user prompts for the agent"],
        extra_questions=["What should the agent never do without explicit approval?"],
    ),
    "internal-tool": CatalogEntry(
        name="internal-tool",
        description="Workflow tool for an internal team.",
        extra_requirements=["Name the internal workflow this tool should shorten"],
        extra_risks=["Internal users may keep using the old process if switching costs are high"],
        extra_tasks=["Interview one internal user about the current workflow"],
        extra_questions=["Which manual step should disappear in version 1?"],
    ),
    "data-product": CatalogEntry(
        name="data-product",
        description="Data workflow, metric layer, or analysis product.",
        extra_requirements=["List required datasets, owners, and freshness expectations"],
        extra_risks=["Data quality may hide the real product risk"],
        extra_tasks=["Inspect one representative CSV or export"],
        extra_questions=["Which decision will this data product improve?"],
    ),
    "marketplace-app": CatalogEntry(
        name="marketplace-app",
        description="App or extension for an ecosystem marketplace.",
        extra_requirements=["Define marketplace install, onboarding, and permissions requirements"],
        extra_risks=["Marketplace approval or integration rules may delay launch"],
        extra_tasks=["Review marketplace submission requirements"],
        extra_questions=["What is the smallest installable marketplace experience?"],
    ),
    "founder-mvp": CatalogEntry(
        name="founder-mvp",
        description="Early founder-led product or prototype.",
        extra_requirements=["Define the smallest demo that proves the idea is worth continuing"],
        extra_risks=["The MVP may validate building effort instead of customer demand"],
        extra_tasks=["Talk to one target user before expanding scope"],
        extra_questions=["What signal would make this MVP worth another week of work?"],
    ),
}


def get_catalog_entry(project_type: str) -> CatalogEntry:
    normalized = project_type.strip() or DEFAULT_PROJECT_TYPE
    if normalized not in CATALOG:
        raise ValueError(f"Unknown project type: {project_type}. Run `ares catalog` to see available types.")
    return CATALOG[normalized]


def format_catalog() -> str:
    lines = ["Ares Project Catalog", ""]
    for name in PROJECT_TYPES:
        entry = CATALOG[name]
        lines.append(f"- {entry.name}: {entry.description}")
    return "\n".join(lines).rstrip() + "\n"

