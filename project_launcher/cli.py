from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TextIO

from project_launcher.data_inspector import format_data_inspection, inspect_data_folder
from project_launcher.e2e import run_e2e_check
from project_launcher.editor import add_decision, add_risk, add_task, answer_question
from project_launcher.graph import run_kickoff_graph
from project_launcher.health import assess_health
from project_launcher.ingest import ingest_audio, ingest_file, ingest_folder, ingest_image
from project_launcher.knowledge import ask_project, summarize_project
from project_launcher.langgraph_workflow import run_kickoff_langgraph
from project_launcher.local_models import LocalModelUnavailableError, check_model_status, format_model_status, generate_text, setup_message
from project_launcher.multiagent import run_pm_review
from project_launcher.quality import format_quality_gate, run_quality_gate
from project_launcher.rag import answer_deep_question
from project_launcher.semantic_rag import answer_rag_question, index_project
from project_launcher.superagent import run_superagent
from project_launcher.workflows import run_kickoff_workflow
from project_launcher.workspace import init_workspace, next_actions, review_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="offline-project-launcher",
        description="Turn a blank folder and rough idea into a founder/PM project workspace.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a new project workspace.")
    init_parser.add_argument("folder", help="New or empty folder to initialize.")
    init_parser.add_argument("idea", help="Rough founder/PM project idea.")

    review_parser = subparsers.add_parser("review", help="Review workspace completeness.")
    review_parser.add_argument("folder", help="Project workspace folder.")

    next_parser = subparsers.add_parser("next", help="Suggest the next project actions.")
    next_parser.add_argument("folder", help="Project workspace folder.")

    ask_parser = subparsers.add_parser("ask", help="Ask a question about the project workspace.")
    ask_parser.add_argument("folder", help="Project workspace folder.")
    ask_parser.add_argument("question", help="Question to answer from local project files.")

    ask_deep_parser = subparsers.add_parser("ask-deep", help="Ask a question across root docs and project folders.")
    ask_deep_parser.add_argument("folder", help="Project workspace folder.")
    ask_deep_parser.add_argument("question", help="Question to answer from deeper local project files.")

    summarize_parser = subparsers.add_parser("summarize", help="Summarize project status.")
    summarize_parser.add_argument("folder", help="Project workspace folder.")

    decision_parser = subparsers.add_parser("add-decision", help="Add a decision to the project.")
    decision_parser.add_argument("folder", help="Project workspace folder.")
    decision_parser.add_argument("decision", help="Decision to record.")

    risk_parser = subparsers.add_parser("add-risk", help="Add a risk to the project.")
    risk_parser.add_argument("folder", help="Project workspace folder.")
    risk_parser.add_argument("risk", help="Risk to record.")

    task_parser = subparsers.add_parser("add-task", help="Add a task to the project.")
    task_parser.add_argument("folder", help="Project workspace folder.")
    task_parser.add_argument("task", help="Task to record.")

    answer_parser = subparsers.add_parser("answer-question", help="Answer a numbered open question.")
    answer_parser.add_argument("folder", help="Project workspace folder.")
    answer_parser.add_argument("number", type=int, help="Question number to answer.")
    answer_parser.add_argument("answer", help="Answer text to record.")

    health_parser = subparsers.add_parser("health", help="Assess project readiness.")
    health_parser.add_argument("folder", help="Project workspace folder.")

    kickoff_parser = subparsers.add_parser("kickoff", help="Run the project kickoff workflow.")
    kickoff_parser.add_argument("folder", help="Project workspace folder.")

    kickoff_graph_parser = subparsers.add_parser("kickoff-graph", help="Run the graph-style kickoff workflow.")
    kickoff_graph_parser.add_argument("folder", help="Project workspace folder.")

    kickoff_langgraph_parser = subparsers.add_parser("kickoff-langgraph", help="Run the optional LangGraph kickoff workflow.")
    kickoff_langgraph_parser.add_argument("folder", help="Project workspace folder.")

    inspect_data_parser = subparsers.add_parser("inspect-data", help="Inspect CSV files in the project data folder.")
    inspect_data_parser.add_argument("folder", help="Project workspace folder.")

    subparsers.add_parser("model-status", help="Check local Ollama and recommended model availability.")

    chat_parser = subparsers.add_parser("chat", help="Ask the local model about a project.")
    chat_parser.add_argument("folder", help="Project workspace folder.")
    chat_parser.add_argument("question", help="Question for the local PM assistant.")

    index_parser = subparsers.add_parser("index", help="Build a local semantic project index.")
    index_parser.add_argument("folder", help="Project workspace folder.")

    ask_rag_parser = subparsers.add_parser("ask-rag", help="Ask a question using the local semantic index.")
    ask_rag_parser.add_argument("folder", help="Project workspace folder.")
    ask_rag_parser.add_argument("question", help="Question to answer from indexed local context.")

    pm_review_parser = subparsers.add_parser("pm-review", help="Run the local multiagent PM review.")
    pm_review_parser.add_argument("folder", help="Project workspace folder.")
    _add_review_mode_flags(pm_review_parser)

    super_parser = subparsers.add_parser("super", help="Ask the offline PM superagent to route a request.")
    super_parser.add_argument("folder", help="Project workspace folder.")
    super_parser.add_argument("request", help="Natural-language PM/founder request.")
    _add_review_mode_flags(super_parser)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a local PDF/text/image/audio file into the project.")
    ingest_parser.add_argument("folder", help="Project workspace folder.")
    ingest_parser.add_argument("source", help="Local file to ingest.")

    ingest_image_parser = subparsers.add_parser("ingest-image", help="Ingest a local image or screenshot.")
    ingest_image_parser.add_argument("folder", help="Project workspace folder.")
    ingest_image_parser.add_argument("source", help="Local image file to ingest.")

    ingest_audio_parser = subparsers.add_parser("ingest-audio", help="Ingest a local audio file.")
    ingest_audio_parser.add_argument("folder", help="Project workspace folder.")
    ingest_audio_parser.add_argument("source", help="Local audio file to ingest.")

    ingest_folder_parser = subparsers.add_parser("ingest-folder", help="Ingest supported files from a local folder.")
    ingest_folder_parser.add_argument("folder", help="Project workspace folder.")
    ingest_folder_parser.add_argument("source_folder", help="Local folder to ingest.")

    quality_parser = subparsers.add_parser("quality-gate", help="Run the 9.5/10 readiness quality gate.")
    quality_parser.add_argument("folder", help="Project workspace folder.")

    subparsers.add_parser("e2e-check", help="Run the new-user end-to-end UX check.")

    return parser


def main(argv: list[str] | None = None, stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            result = init_workspace(Path(args.folder), args.idea)
            print(f"Created project workspace: {result.path}", file=stdout)
            print("\nFolders:", file=stdout)
            for directory in result.directories:
                print(f"- {directory.name}/", file=stdout)
            print("\nFiles:", file=stdout)
            for path in result.files:
                print(f"- {path.name}", file=stdout)
            print("\nNext step:", file=stdout)
            print(f"python main.py next {result.path}", file=stdout)
            return 0

        if args.command == "review":
            result = review_workspace(Path(args.folder))
            print(f"Workspace: {result.path}", file=stdout)
            print(f"Readiness score: {result.readiness_score}%", file=stdout)
            _print_list("Missing files", result.missing_files, stdout)
            _print_list("Missing folders", result.missing_directories, stdout)
            _print_list("Empty files", result.empty_files, stdout)
            if result.readiness_score == 100:
                print("\nReady for kickoff.", file=stdout)
            return 0

        if args.command == "next":
            print("Recommended next actions:", file=stdout)
            for index, action in enumerate(next_actions(Path(args.folder)), start=1):
                print(f"{index}. {action}", file=stdout)
            return 0

        if args.command == "ask":
            result = ask_project(Path(args.folder), args.question)
            print("Answer:", file=stdout)
            print(result.answer, file=stdout)
            if result.sources:
                print("\nSources:", file=stdout)
                for source in result.sources:
                    print(f"- {source}", file=stdout)
            return 0

        if args.command == "ask-deep":
            result = answer_deep_question(Path(args.folder), args.question)
            print("Answer:", file=stdout)
            print(result.answer, file=stdout)
            if result.sources:
                print("\nSources:", file=stdout)
                for source in result.sources:
                    print(f"- {source}", file=stdout)
            return 0

        if args.command == "summarize":
            result = summarize_project(Path(args.folder))
            print(f"Project: {result.title}", file=stdout)
            _print_list("Current focus", result.focus, stdout)
            _print_list("Top goals", result.goals, stdout)
            _print_list("Top requirements", result.requirements, stdout)
            _print_list("Top risks", result.risks, stdout)
            _print_list("Open questions", result.open_questions, stdout)
            _print_list("Next actions", result.next_actions, stdout)
            return 0

        if args.command == "add-decision":
            result = add_decision(Path(args.folder), args.decision)
            print(result.message, file=stdout)
            return 0

        if args.command == "add-risk":
            result = add_risk(Path(args.folder), args.risk)
            print(result.message, file=stdout)
            return 0

        if args.command == "add-task":
            result = add_task(Path(args.folder), args.task)
            print(result.message, file=stdout)
            return 0

        if args.command == "answer-question":
            result = answer_question(Path(args.folder), args.number, args.answer)
            print(result.message, file=stdout)
            return 0

        if args.command == "health":
            result = assess_health(Path(args.folder))
            print(f"Project Health: {result.score}%", file=stdout)
            _print_list("Strengths", result.strengths, stdout)
            _print_list("Weak Spots", result.weak_spots, stdout)
            _print_numbered_list("Recommended Fixes", result.recommended_fixes, stdout)
            return 0

        if args.command == "kickoff":
            result = run_kickoff_workflow(Path(args.folder))
            print("Kickoff Workflow", file=stdout)
            print("\nStep 1: Project Summary", file=stdout)
            print(f"Project: {result.summary.title}", file=stdout)
            _print_list("Top goals", result.summary.goals, stdout)
            _print_list("Top requirements", result.summary.requirements, stdout)

            print("\nStep 2: Health Check", file=stdout)
            print(f"Project Health: {result.health.score}%", file=stdout)
            _print_list("Weak Spots", result.health.weak_spots, stdout)

            print("\nStep 3: Recommended Next Actions", file=stdout)
            _print_numbered_items(result.next_actions, stdout)

            print("\nStep 4: Suggested Commands", file=stdout)
            _print_command_list(result.suggested_commands, stdout)
            return 0

        if args.command == "kickoff-graph":
            result = run_kickoff_graph(Path(args.folder))
            print(result.report, end="", file=stdout)
            return 0

        if args.command == "kickoff-langgraph":
            report = run_kickoff_langgraph(Path(args.folder))
            print(report, end="", file=stdout)
            return 0

        if args.command == "inspect-data":
            report = inspect_data_folder(Path(args.folder))
            print(format_data_inspection(report), end="", file=stdout)
            return 0

        if args.command == "model-status":
            print(format_model_status(check_model_status()), end="", file=stdout)
            return 0

        if args.command == "chat":
            summary = summarize_project(Path(args.folder))
            prompt = (
                "You are a concise offline product management assistant. "
                "Answer as a practical PM/founder collaborator and avoid inventing facts.\n\n"
                f"Project: {summary.title}\n"
                f"Goals: {', '.join(summary.goals)}\n"
                f"Requirements: {', '.join(summary.requirements)}\n"
                f"Risks: {', '.join(summary.risks)}\n\n"
                f"Question: {args.question}\n\nAnswer:"
            )
            try:
                answer = generate_text(prompt)
                print("Answer:", file=stdout)
                print(answer, file=stdout)
            except LocalModelUnavailableError:
                print("Answer:", file=stdout)
                print(setup_message(), file=stdout)
            return 0

        if args.command == "index":
            result = index_project(Path(args.folder))
            print(f"Indexed project: {result.index_path}", file=stdout)
            print(f"Chunks: {result.chunk_count}", file=stdout)
            _print_list("Sources", result.sources, stdout)
            return 0

        if args.command == "ask-rag":
            result = answer_rag_question(Path(args.folder), args.question)
            print("Answer:", file=stdout)
            print(result.answer, file=stdout)
            if result.sources:
                print("\nSources:", file=stdout)
                for source in result.sources:
                    print(f"- {source}", file=stdout)
            return 0

        if args.command == "pm-review":
            result = run_pm_review(Path(args.folder), mode=args.review_mode)
            print(result.report, end="", file=stdout)
            return 0

        if args.command == "super":
            result = run_superagent(Path(args.folder), args.request, mode=args.review_mode)
            print(result.report, end="", file=stdout)
            return 0

        if args.command == "ingest":
            result = ingest_file(Path(args.folder), Path(args.source))
            print(result.message, file=stdout)
            return 0

        if args.command == "ingest-image":
            result = ingest_image(Path(args.folder), Path(args.source))
            print(result.message, file=stdout)
            return 0

        if args.command == "ingest-audio":
            result = ingest_audio(Path(args.folder), Path(args.source))
            print(result.message, file=stdout)
            return 0

        if args.command == "ingest-folder":
            results = ingest_folder(Path(args.folder), Path(args.source_folder))
            for result in results:
                print(result.message, file=stdout)
            return 0

        if args.command == "quality-gate":
            print(format_quality_gate(run_quality_gate(Path(args.folder))), end="", file=stdout)
            return 0

        if args.command == "e2e-check":
            result = run_e2e_check()
            print(result.report, end="", file=stdout)
            return 0 if result.passed else 1

    except ValueError as exc:
        print(f"Error: {exc}", file=stderr)
        return 1

    parser.error(f"Unknown command: {args.command}")
    return 2


def _add_review_mode_flags(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--fast", dest="review_mode", action="store_const", const="fast", default="fast", help="Run the faster 3-agent review mode.")
    group.add_argument("--full", dest="review_mode", action="store_const", const="full", help="Run the complete 7-agent review mode.")


def _print_list(title: str, items: list[str], stdout: TextIO) -> None:
    print(f"\n{title}:", file=stdout)
    if not items:
        print("- None", file=stdout)
        return
    for item in items:
        print(f"- {item}", file=stdout)


def _print_numbered_list(title: str, items: list[str], stdout: TextIO) -> None:
    print(f"\n{title}:", file=stdout)
    _print_numbered_items(items, stdout)


def _print_numbered_items(items: list[str], stdout: TextIO) -> None:
    if not items:
        print("- None", file=stdout)
        return
    for index, item in enumerate(items, start=1):
        print(f"{index}. {item}", file=stdout)


def _print_command_list(items: list[str], stdout: TextIO) -> None:
    if not items:
        print("- None", file=stdout)
        return
    for item in items:
        print(item, file=stdout)
