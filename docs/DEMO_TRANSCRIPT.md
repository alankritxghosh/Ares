# Demo Transcript

This transcript shows the intended shape of a short portfolio demo. It omits some repeated lines so the important behavior is easy to scan.

## Run The Demo

```bash
bash demo.sh
```

Expected opening:

```text
Offline Project Launch Assistant Demo
Generated workspace path: /private/tmp/offline-project-launch-assistant-demo

Created project workspace: /private/tmp/offline-project-launch-assistant-demo
```

The demo then records a decision, risk, task, and answer:

```text
Added decision to decisions.md
Added risk to risks.md
Added task 6 to tasks.md
Answered question 1 in open_questions.md
```

## Ask Root Project Docs

```bash
python main.py ask /private/tmp/offline-project-launch-assistant-demo "What is missing before kickoff?"
```

Representative output:

```text
Answer:
- Who is the primary user?
- What is the smallest useful first version?
- Interview 3 support managers

Sources:
- open_questions.md
- tasks.md
```

## Ask Deep Project Knowledge

```bash
python main.py ask-deep /private/tmp/offline-project-launch-assistant-demo "What are customers complaining about?"
```

Representative output:

```text
Answer:
- Customers repeatedly complain about slow response time during high-priority incidents.
- Customers say repeated handoffs make them feel like they are explaining the same issue again.
- Support managers want visibility into overloaded agents before service levels slip.

Sources:
- research/customer-interviews.md
```

## Health Report

```bash
python main.py health /private/tmp/offline-project-launch-assistant-demo
```

Representative output:

```text
Project Health: 100%

Strengths:
- Project brief is present
- Requirements are documented
- Risks are documented
- At least one product decision is recorded
```

Exact score can change as the generated workspace changes, but the report should always show strengths, weak spots, and recommended fixes.

## Graph Workflow

```bash
python main.py kickoff-graph /private/tmp/offline-project-launch-assistant-demo
```

Representative output:

```text
Graph Kickoff Workflow

Trace:
1. summary_node
2. health_node
3. next_actions_node
4. suggested_commands_node
5. final_report_node

Step 1: Project Summary
Project: Build A Customer Support Dashboard For Support Managers
```

## Data Inspection

```bash
python main.py inspect-data /private/tmp/offline-project-launch-assistant-demo
```

If pandas and NumPy are installed, representative output includes:

```text
Data Inspection

Files:
- data/support_tickets.csv

support_tickets.csv:
- Rows: 6
- Missing values: customer_region has 1 missing values
- Possible metrics:
  1. Counts by priority
  2. Counts by status
  3. Average response time minutes
```

If pandas and NumPy are not installed, the command prints:

```text
Error: pandas and NumPy are required for data inspection.
Install them with: pip install pandas numpy
```

## Local Models, PM Review, And Superagent

```bash
python main.py model-status
python main.py pm-review /private/tmp/offline-project-launch-assistant-demo --fast
python main.py pm-review /private/tmp/offline-project-launch-assistant-demo --full
python main.py super /private/tmp/offline-project-launch-assistant-demo "Prepare this project for kickoff" --fast
```

If Ollama is running with the recommended models, the PM review uses local model responses. If not, it still prints deterministic PM-agent fallback findings:

```text
PM Review

Project: Build a Customer Support Dashboard for Support Managers
Overall Readiness: 100%

Agent Findings:

PM Strategist (deterministic fallback, 0.0s):
- Tighten goals, requirements, and roadmap around the first useful version.

Timing:
- Mode: fast
- Agents run: 3
- Total: 0.0s
```

The superagent wraps the workflow in a single natural-language response:

```text
Superagent Response

Answer:
PM Review
...

Recommended Next Actions:
1. Write a one-paragraph project brief
```

## E2E UX Check

```bash
bash e2e_user_test.sh
```

If local models are not ready, the check stops honestly:

```text
E2E UX Result: BLOCKED
Reason: Local model setup incomplete.
Next command: ollama pull llama3.2
```
