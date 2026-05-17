# LinkedIn Launch Post

I built a fully offline PM superagent CLI.

It is called Ares, and the idea is simple:

Give it a blank folder and a rough founder/PM idea. It turns that into a structured project workspace with briefs, goals, users, requirements, risks, tasks, decisions, kickoff reports, local RAG, multiagent review, and business data inspection.

The part I care about most: it runs locally.

No OpenAI API.
No hosted inference.
No enterprise model dependency.
No hidden cloud calls.

The project includes:

- workspace generation from a rough idea
- source-backed local Q&A over project docs
- deeper RAG-style search across docs, research, and reports
- optional semantic RAG with local Ollama embeddings
- local PM review agents with a fast default mode and full review mode
- graph-style workflow orchestration
- optional LangGraph workflow support
- pandas/NumPy CSV inspection for business data
- local multimodal ingestion paths for files, images, and audio metadata
- a quality gate and E2E user test

The default multiagent review now runs in a faster 3-agent mode, with `--full` available when I want the complete 7-agent review. That was an important product decision because local AI products win or lose on latency.

This started as a terminal-first learning project around Python, RAG, LangGraph-shaped workflows, local models, and multiagent systems. It has become a real portfolio artifact: a product management workflow tool that can help a founder go from “I have an idea” to “we have a kickoff-ready project.”

What I learned:

Building agentic software is not only about calling a model.

The useful parts are the system around the model:

- clear commands
- good fallback behavior
- source citations
- deterministic checks
- fast paths for daily use
- explicit review gates
- workflows that can run even when the model is unavailable

This project is still a v0.1, but it already feels like the shape of something I would use: a local PM copilot for serious project thinking.

Next up:

- packaging polish
- richer local model UX
- better report exports
- embedding-based retrieval improvements
- more real-world project demos

If you are building local-first AI tools, agent workflows, or founder/product systems, I would love to compare notes.

