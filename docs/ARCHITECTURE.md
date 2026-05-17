# Architecture

Ares is intentionally small, modular, and dependency-light. Each layer maps to a project capability that can be understood, tested, and later replaced with a richer AI implementation.

## System Map

```text
CLI
  -> Workspace Generator
  -> Knowledge/Q&A Layer
  -> Editor Layer
  -> Health Reviewer
  -> Workflow Orchestrator
  -> Graph / Optional LangGraph Layer
  -> Local RAG Layer
  -> Local Model Runtime
  -> Semantic RAG Layer
  -> Multiagent / Superagent Layer
  -> Multimodal Ingestion
  -> Data Inspector
```

## Layers

### CLI

`main.py` delegates to `project_launcher/cli.py`. The CLI handles argument parsing, command routing, friendly output, and consistent exit codes.

### Workspace Generator

`workspace.py`, `agents.py`, and `templates.py` turn a plain project idea into a complete Markdown workspace. The generator is conservative: it creates a new folder or uses an empty one, but refuses to overwrite existing files.

### Knowledge/Q&A Layer

`knowledge.py` reads root-level Markdown files, splits useful project notes into chunks, ranks them with deterministic keyword overlap, and returns concise answers with source filenames.

### Editor Layer

`editor.py` provides append-oriented commands for decisions, risks, tasks, and answers to open questions. It avoids destructive rewrites and keeps Markdown readable for humans.

### Health Reviewer

`health.py` scores readiness with simple checks: brief quality, users, requirements, risks, tasks, roadmap, decisions, answered questions, and expected folders. Weak spots become recommended command-style fixes.

### Workflow Orchestrator

`workflows.py` combines summary, health, next actions, and suggested commands into one kickoff report. This makes the assistant feel like a project reviewer rather than separate utilities.

### Graph / Optional LangGraph Layer

`graph.py` runs the kickoff workflow through named nodes over shared state and prints an execution trace. `langgraph_workflow.py` mirrors that structure with optional LangGraph imports, so the app still works without extra dependencies.

### Local RAG Layer

`rag.py` extends retrieval beyond root Markdown into `docs/`, `research/`, and `reports/`. It is RAG-shaped but still transparent: no embeddings, no hidden model calls, and no network dependency.

### Local Model Runtime

`local_models.py` talks to a local Ollama server at `127.0.0.1:11434` using only the Python standard library. It checks model readiness, prints setup commands, and never calls hosted inference APIs.

### Semantic RAG Layer

`semantic_rag.py` adds optional embedding search with `nomic-embed-text`. It stores local vectors in `.project_launcher/index.json` inside each project workspace.

### Multiagent / Superagent Layer

`agents_llm.py` and `multiagent.py` define PM-focused roles such as Founder Clarifier, PM Strategist, Risk Reviewer, and Final Reviewer. The default review path runs a faster 3-agent set for local latency, while `--full` runs all 7 roles. `superagent.py` routes a natural user request to the right local tool path and suggests commands instead of silently editing files.

### Multimodal Ingestion

`ingest.py` turns local PDFs, text files, images, and audio metadata into source-marked Markdown notes. Vision and transcription remain local-only and degrade to setup guidance when models or tools are missing.

### Data Inspector

`data_inspector.py` lazily imports pandas and NumPy to inspect `data/**/*.csv`. It reports shape, missing values, column types, numeric summaries, and possible business metrics based on column names.

## Design Principles

- Offline first: no cloud calls are required.
- Explainable before clever: deterministic scoring and retrieval make behavior easy to inspect.
- Optional dependencies: LangGraph, pandas, and NumPy are additive rather than required.
- Append-oriented edits: project files remain readable and recoverable.
- Codex-friendly structure: modules are small enough for an agent or reviewer to navigate quickly.
