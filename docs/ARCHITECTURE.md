# Architecture

Ares is intentionally small, modular, and dependency-light. The newest layer makes it a local project control plane: users declare intent in `ares.yaml`, Ares builds shared project state from the workspace, then validation, drift detection, workflows, and agents operate over that state.

## System Map

```text
CLI
  -> MCP Integration Layer
  -> Project Control Plane
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

### MCP Integration Layer

`mcp_server.py` exposes selected Ares internals as a local stdio MCP server for Claude Code. The entry point is `ares-mcp`, and the optional dependency is installed with `pipx inject ares-pm mcp`. The layer keeps the normal CLI unchanged, labels mutating tools clearly, and returns plain text reports so Claude can show the same outputs a terminal user would see.

### Project Control Plane

`config.py`, `state.py`, `validate.py`, `drift.py`, `jobs.py`, and `catalog.py` provide the platform layer. `ares.yaml` captures desired project state, `state` summarizes what exists, `validate` checks readiness, `drift` finds project-management mismatch, and `.project_launcher/jobs.json` records long-running command history.

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
- Control-plane state: commands can share the same view of project config, evidence, health, and job history.
- Tool-server friendly: Claude Code can use Ares through local MCP without changing the underlying command behavior.
- Codex-friendly structure: modules are small enough for an agent or reviewer to navigate quickly.
