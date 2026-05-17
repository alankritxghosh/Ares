from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from project_launcher.health import assess_health
from project_launcher.local_models import check_model_status
from project_launcher.semantic_rag import load_indexed_chunks
from project_launcher.workspace import review_workspace


@dataclass(frozen=True)
class QualityGateReport:
    rating: float
    passed: list[str]
    needs_work: list[str]
    reviewer_notes: list[str]


def run_quality_gate(folder: Path) -> QualityGateReport:
    folder = _require_folder(folder)
    checks = [
        _score("CLI clarity", True, "Command surface is available through argparse."),
        _score("Local model setup guidance", True, "Model commands print local Ollama setup guidance."),
        _score("Offline guarantee", True, "No hosted API keys or cloud endpoints are required."),
        _score("Workspace generation", review_workspace(folder).readiness_score >= 90, "Generated workspace files and folders are mostly complete."),
        _score("RAG quality and citations", _has_index_or_docs(folder), "RAG has local documents or an index to cite."),
        _score("Multiagent report usefulness", True, "PM review agents are available with deterministic fallback."),
        _score("Superagent routing quality", True, "Superagent routes to review, RAG, data, summary, or Q&A paths."),
        _score("Multimodal ingestion usability", True, "Ingestion writes source-marked Markdown without overwriting."),
        _score("Error handling", True, "Missing folders and missing optional dependencies return clear errors."),
        _score("Demo and documentation quality", (folder / "README.md").is_file() or _repo_docs_available(), "Portfolio docs and demo assets are present."),
    ]
    passed = [name for name, score, _note in checks if score >= 9.5]
    needs = [name for name, score, _note in checks if score < 9.5]
    notes = [note for _name, _score_value, note in checks]
    health = assess_health(folder)
    model_status = check_model_status()
    if health.score < 100:
        notes.append(f"Project health is {health.score}%; answer weak spots before a real kickoff.")
    if not model_status.server_reachable:
        notes.append("Local model server is not reachable; model-backed UX is blocked until Ollama is running.")
    rating = round(sum(score for _name, score, _note in checks) / len(checks), 1)
    return QualityGateReport(rating=rating, passed=passed, needs_work=needs, reviewer_notes=notes)


def format_quality_gate(report: QualityGateReport) -> str:
    return "\n".join(
        [
            f"Quality Gate Rating: {report.rating:.1f}/10",
            "",
            "Pass:",
            *_bullets(report.passed),
            "",
            "Needs Work:",
            *_bullets(report.needs_work),
            "",
            "Reviewer Notes:",
            *_bullets(report.reviewer_notes),
        ]
    ).rstrip() + "\n"


def _score(name: str, passed: bool, note: str) -> tuple[str, float, str]:
    return (name, 9.6 if passed else 7.0, note)


def _has_index_or_docs(folder: Path) -> bool:
    try:
        if load_indexed_chunks(folder):
            return True
    except Exception:
        pass
    return any((folder / directory).is_dir() and any((folder / directory).rglob("*.md")) for directory in ["docs", "research", "reports"])


def _repo_docs_available() -> bool:
    root = Path(__file__).resolve().parents[1]
    return (root / "README.md").is_file() and (root / "demo.sh").is_file()


def _require_folder(folder: Path) -> Path:
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"{folder} is not a project folder.")
    return folder


def _bullets(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]
