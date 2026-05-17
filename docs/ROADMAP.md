# Roadmap

The current version is a complete offline CLI demo with optional local model, semantic RAG, multiagent, superagent, ingestion, quality gate, and E2E UX-check paths. Future phases can deepen the intelligence while preserving the same terminal-first workflow.

## Near-Term Improvements

- Add task completion and status tracking.
- Export health and kickoff reports as Markdown or HTML.
- Add richer example project packs for sales, hiring, finance, and operations use cases.
- Improve command suggestions with more project-specific wording.

## AI And Retrieval

- Improve embedding-based RAG with incremental indexing, better chunk merging, and richer retrieval diagnostics.
- Add configurable local model profiles for fast, balanced, and quality modes.
- Support reranking and better chunk merging while keeping source citations.
- Add safeguards that separate retrieved evidence from generated recommendations.

## Workflow Orchestration

- Expand LangGraph state beyond the current kickoff mirror and current multiagent report.
- Add conditional workflow branches for weak project health, missing data, or unanswered questions.
- Persist workflow traces as report artifacts.
- Add more reviewer-agent nodes, such as market validation, requirements clarity, and execution risk.

## Data Inspection

- Support more data formats, including `.xlsx`, `.json`, and `.parquet`.
- Add column profiling, outlier detection, and lightweight data quality checks.
- Generate data-backed recommendations for PM and founder decisions.
- Connect CSV insights to project risks, open questions, and next actions.

## Portfolio Polish

- Add a short demo video script.
- Add sample screenshots or terminal captures.
- Add a comparison page explaining how the dependency-free graph differs from real LangGraph.
- Add a recruiter-facing one-page summary.
