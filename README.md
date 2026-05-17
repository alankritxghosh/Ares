# Ares

Ares is a terminal-first, fully offline PM superagent that turns a blank folder and a rough founder or PM idea into a structured, reviewable project workspace. It creates kickoff docs, answers questions from local project notes, tracks decisions and risks, runs readiness reviews, executes workflow-style reports, searches deeper project folders, and optionally inspects CSV business data without requiring cloud APIs or an external AI service.

## Why This Project Matters

This project is built as a portfolio-ready example of offline agentic product tooling. It shows how a small Python app can model practical PM/founder workflows with deterministic agents, local retrieval, graph-shaped orchestration, optional LangGraph support, and pandas/NumPy data inspection while staying explainable enough to run entirely in a terminal.

## Quick Demo

Run the full repeatable demo pack:

```bash
bash demo.sh
```

The script creates a disposable workspace at:

```text
/private/tmp/offline-project-launch-assistant-demo
```

It then initializes a support dashboard project, adds decisions/risks/tasks, copies sample research/docs/reports/data into the workspace, and runs the main assistant commands.

You can also try the core flow manually:

```bash
ares init ./customer-support-dashboard "Build a customer support dashboard for support managers"
ares ask ./customer-support-dashboard "What is missing before kickoff?"
ares add-decision ./customer-support-dashboard "Version 1 will target support managers"
ares add-risk ./customer-support-dashboard "Zendesk API access may be delayed"
ares health ./customer-support-dashboard
ares kickoff-graph ./customer-support-dashboard
ares model-status
ares chat ./customer-support-dashboard "What should we do before kickoff?"
ares index ./customer-support-dashboard
ares ask-rag ./customer-support-dashboard "What are customers complaining about?"
ares pm-review ./customer-support-dashboard --fast
ares pm-review ./customer-support-dashboard --full
ares super ./customer-support-dashboard "Prepare this project for kickoff" --fast
ares quality-gate ./customer-support-dashboard
```

## Install Locally

With pipx:

```bash
pipx install .
```

For development or portfolio review:

```bash
python3 -m pip install -e .
```

Then run the main CLI command:

```bash
ares model-status
```

The package is named `ares-pm` for pip and pipx installs. The main CLI command is `ares`; `opla` and `offline-project-launcher` remain available as compatibility aliases. The project has no required runtime dependencies beyond the Python standard library. Optional local features can use Ollama models, LangGraph, pandas, and NumPy when installed.

## Features

### Workspace Generation

- Creates a structured project folder from a plain-English idea.
- Generates starter Markdown for brief, goals, users, requirements, roadmap, risks, open questions, tasks, and decisions.
- Refuses to overwrite a non-empty folder.

### Local Knowledge and Q&A

- `ask` answers project questions from root-level Markdown files.
- `summarize` produces a compact PM/founder status snapshot.
- Answers include source filenames so the reasoning trail stays visible.

### Workspace Editing

- `add-decision` appends dated decisions.
- `add-risk` appends new project risks.
- `add-task` adds the next numbered task.
- `answer-question` records answers under numbered open questions.

### Review and Workflow Orchestration

- `health` scores project readiness and suggests fixes.
- `kickoff` runs summary, health, next actions, and suggested commands as one report.
- `kickoff-graph` runs the same logic through named graph-style workflow nodes.
- `kickoff-langgraph` optionally mirrors the graph workflow with real LangGraph when installed.
- `pm-review` runs multiple PM/research/risk/execution agents with local-model support and deterministic fallback. It defaults to fast 3-agent mode for local latency; use `--full` for the complete 7-agent review.
- `super` routes a natural PM/founder request across the assistant's local tools. Review-style requests also default to fast mode and accept `--full`.

### Local RAG-Style Retrieval

- `ask-deep` searches root Markdown plus nested Markdown in `docs/`, `research/`, and `reports/`.
- Retrieval is deterministic: chunking, keyword overlap, ranking, and source-backed output.
- No embeddings or cloud calls are required.
- `index` and `ask-rag` add optional semantic retrieval with local Ollama embeddings.

### Local Models and Multimodal Ingestion

- `model-status` checks local Ollama readiness and recommended models.
- `chat` talks to a local PM assistant model when `llama3.2:3b` is available.
- `ingest`, `ingest-image`, `ingest-audio`, and `ingest-folder` turn local files into source-marked Markdown notes.
- Model-backed features never call hosted APIs and print setup guidance when local models are missing.

### Business Data Inspection

- `inspect-data` optionally scans `data/**/*.csv` with pandas and NumPy.
- Reports rows, columns, missing values, numeric summaries, text/category columns, and possible business metrics.
- The command fails gracefully if optional data dependencies are not installed.

## Command Reference

```bash
ares init <folder> <idea>
ares review <folder>
ares next <folder>
ares ask <folder> <question>
ares ask-deep <folder> <question>
ares summarize <folder>
ares add-decision <folder> <decision>
ares add-risk <folder> <risk>
ares add-task <folder> <task>
ares answer-question <folder> <number> <answer>
ares health <folder>
ares kickoff <folder>
ares kickoff-graph <folder>
ares kickoff-langgraph <folder>
ares inspect-data <folder>
ares model-status
ares chat <folder> <question>
ares index <folder>
ares ask-rag <folder> <question>
ares pm-review <folder> [--fast|--full]
ares super <folder> <request> [--fast|--full]
ares ingest <folder> <file>
ares ingest-image <folder> <image>
ares ingest-audio <folder> <audio>
ares ingest-folder <folder> <source-folder>
ares quality-gate <folder>
ares e2e-check
```

## Generated Workspace

```text
project/
  README.md
  brief.md
  goals.md
  users.md
  requirements.md
  roadmap.md
  risks.md
  open_questions.md
  tasks.md
  decisions.md
  research/
  designs/
  data/
  docs/
  reports/
```

## Architecture Overview

```text
CLI
  -> Workspace Generator
  -> Knowledge/Q&A Layer
  -> Editor Layer
  -> Health Reviewer
  -> Workflow Orchestrator
  -> Graph / Optional LangGraph Layer
  -> Local RAG Layer
  -> Data Inspector
```

- **CLI:** `main.py` and `project_launcher/cli.py` parse terminal commands and route work.
- **Workspace Generator:** `workspace.py`, `agents.py`, and `templates.py` create the first project workspace.
- **Knowledge/Q&A Layer:** `knowledge.py` reads root Markdown and returns source-aware answers.
- **Editor Layer:** `editor.py` performs conservative append-oriented Markdown updates.
- **Health Reviewer:** `health.py` scores project readiness and recommends practical fixes.
- **Workflow Orchestrator:** `workflows.py` combines summary, review, and next-action logic.
- **Graph / Optional LangGraph Layer:** `graph.py` provides dependency-free graph execution; `langgraph_workflow.py` adds optional real LangGraph support.
- **Local RAG Layer:** `rag.py` searches deeper Markdown in `docs/`, `research/`, and `reports/`.
- **Semantic RAG Layer:** `semantic_rag.py` stores local embeddings in `.project_launcher/index.json`.
- **Local Model Runtime:** `local_models.py` talks only to local Ollama endpoints.
- **Multiagent/Superagent Layer:** `multiagent.py`, `agents_llm.py`, and `superagent.py` coordinate PM roles and natural requests.
- **Multimodal Ingestion:** `ingest.py` creates source-marked Markdown notes from local files.
- **Data Inspector:** `data_inspector.py` optionally uses pandas and NumPy to inspect CSV business data.

More detail is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Optional Dependencies

The core CLI uses only the Python standard library.

Install LangGraph only if you want to run the real LangGraph workflow:

```bash
pip install langgraph
```

Install pandas and NumPy only if you want CSV data inspection:

```bash
pip install pandas numpy
```

Install local Ollama models only if you want local chat, semantic RAG, and image review:

```bash
ollama pull llama3.2
ollama pull qwen2.5:3b-instruct
ollama pull nomic-embed-text
ollama pull moondream
```

Without these optional packages or models, the related commands print clear local setup instructions and the rest of the app keeps working.

## OpenAI and Codex Positioning

This is an offline-first agentic workflow tool designed to be easy for Codex to inspect, extend, and test. It demonstrates LangGraph-shaped orchestration, RAG-style project knowledge retrieval, pandas/NumPy business data inspection, and a clean Python CLI structure that can evolve into richer AI workflows while staying understandable to a technical reviewer.

## Demo Assets

The demo pack lives in [examples/support-dashboard](examples/support-dashboard). It includes:

- Customer interview notes in `research/customer-interviews.md`
- Support workflow notes in `docs/support-process.md`
- A weekly status report in `reports/weekly-summary.md`
- A small CSV dataset in `data/support_tickets.csv`

See [docs/DEMO_TRANSCRIPT.md](docs/DEMO_TRANSCRIPT.md) for a realistic walkthrough.

## Tests

Run the full test suite:

```bash
python3 -B -m unittest discover -s tests
```

The tests cover project generation, local Q&A, editing commands, health scoring, workflow orchestration, graph execution, optional LangGraph behavior, local RAG, optional data inspection, and the demo script contract.

Run the full new-user E2E check:

```bash
bash e2e_user_test.sh
```

If local models are not installed or Ollama is not running, the E2E check returns `BLOCKED` with the next setup command rather than pretending the model-backed UX passed.

## Roadmap

Future work includes embedding-based RAG, a local LLM adapter, richer LangGraph state, task completion tracking, report export, and more data formats. See [docs/ROADMAP.md](docs/ROADMAP.md).
