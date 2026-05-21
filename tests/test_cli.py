from __future__ import annotations

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import project_launcher.cli as cli
import project_launcher.data_inspector as data_inspector
import project_launcher.local_models as local_models
from project_launcher.cli import main
from project_launcher.workspace import REQUIRED_DIRS, REQUIRED_FILES


HAS_PANDAS_NUMPY = importlib.util.find_spec("pandas") is not None and importlib.util.find_spec("numpy") is not None


class CliTests(unittest.TestCase):
    def test_init_creates_workspace_in_new_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "support-dashboard"
            stdout = io.StringIO()

            code = main(["init", str(target), "Build a customer support dashboard"], stdout=stdout)

            self.assertEqual(code, 0)
            self.assertTrue(target.is_dir())
            for filename in REQUIRED_FILES:
                self.assertTrue((target / filename).is_file(), filename)
                self.assertIn("support dashboard", (target / filename).read_text(encoding="utf-8").lower())
            for directory in REQUIRED_DIRS:
                self.assertTrue((target / directory).is_dir(), directory)
            self.assertIn("Created project workspace", stdout.getvalue())
            self.assertTrue((target / "ares.yaml").is_file())
            self.assertIn("type: founder-mvp", (target / "ares.yaml").read_text(encoding="utf-8"))

    def test_catalog_lists_project_types(self) -> None:
        stdout = io.StringIO()

        code = main(["catalog"], stdout=stdout)

        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("Ares Project Catalog", output)
        self.assertIn("saas-dashboard", output)
        self.assertIn("ai-agent", output)

    def test_init_with_type_and_stage_updates_config_and_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"

            code = main(
                ["init", str(target), "Build a support dashboard", "--type", "saas-dashboard", "--stage", "validation"],
                stdout=io.StringIO(),
            )

            self.assertEqual(code, 0)
            config = (target / "ares.yaml").read_text(encoding="utf-8")
            self.assertIn("type: saas-dashboard", config)
            self.assertIn("stage: validation", config)
            self.assertIn("core metrics", (target / "requirements.md").read_text(encoding="utf-8"))

    def test_existing_workspace_without_config_still_supports_core_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            (target / "ares.yaml").unlink()

            health = main(["health", str(target)], stdout=io.StringIO())
            ask = main(["ask", str(target), "What are the risks?"], stdout=io.StringIO())
            graph = main(["kickoff-graph", str(target)], stdout=io.StringIO())
            with patch.object(local_models, "generate_text", side_effect=local_models.LocalModelUnavailableError("missing")):
                review = main(["pm-review", str(target), "--fast"], stdout=io.StringIO())

            self.assertEqual(health, 0)
            self.assertEqual(ask, 0)
            self.assertEqual(graph, 0)
            self.assertEqual(review, 0)

    def test_state_prints_control_plane_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["state", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Project State", output)
            self.assertIn("Stage: discovery", output)
            self.assertIn("Health:", output)
            self.assertIn("Evidence sources:", output)

    def test_validate_reports_config_and_suggested_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["validate", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Validation Report", output)
            self.assertIn("[PASS] ares.yaml is present", output)
            self.assertIn("[FAIL] Primary user is declared in config", output)
            self.assertIn("ares add-decision", output)

    def test_runbook_prints_operational_guide(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["runbook", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Ares Project Runbook", output)
            self.assertIn("Before Kickoff", output)
            self.assertIn("Debugging Notes", output)

    def test_drift_detects_project_management_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            (target / ".project_launcher").mkdir()
            (target / ".project_launcher" / "index.json").write_text('{"chunks": [{"modified_time": 1}]}', encoding="utf-8")
            stdout = io.StringIO()

            code = main(["drift", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Drift Report", output)
            self.assertIn("Attention needed", output)
            self.assertIn("no product decision", output)
            self.assertIn("semantic index", output.lower())

    def test_jobs_and_job_status_record_long_running_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            with patch.object(local_models, "generate_text", side_effect=local_models.LocalModelUnavailableError("missing")):
                code = main(["pm-review", str(target), "--fast"], stdout=io.StringIO())
            jobs_stdout = io.StringIO()

            jobs_code = main(["jobs", str(target)], stdout=jobs_stdout)
            job_line = next(line for line in jobs_stdout.getvalue().splitlines() if line.startswith("- job-"))
            job_id = job_line.split()[1]
            status_stdout = io.StringIO()
            status_code = main(["job-status", str(target), job_id], stdout=status_stdout)

            self.assertEqual(code, 0)
            self.assertEqual(jobs_code, 0)
            self.assertEqual(status_code, 0)
            self.assertIn("pm-review --fast", jobs_stdout.getvalue())
            self.assertIn("Job Status", status_stdout.getvalue())

    def test_init_uses_existing_empty_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "empty"
            target.mkdir()

            code = main(["init", str(target), "Build an onboarding tracker"], stdout=io.StringIO())

            self.assertEqual(code, 0)
            self.assertTrue((target / "README.md").is_file())

    def test_init_does_not_overwrite_non_empty_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "existing"
            target.mkdir()
            original = target / "notes.md"
            original.write_text("keep me", encoding="utf-8")
            stderr = io.StringIO()

            code = main(["init", str(target), "Build anything"], stdout=io.StringIO(), stderr=stderr)

            self.assertEqual(code, 1)
            self.assertEqual(original.read_text(encoding="utf-8"), "keep me")
            self.assertIn("already has files", stderr.getvalue())

    def test_review_reports_complete_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a reporting tool"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["review", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            self.assertIn("Readiness score: 100%", stdout.getvalue())
            self.assertIn("Ready for kickoff", stdout.getvalue())

    def test_review_reports_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a finance dashboard"], stdout=io.StringIO())
            (target / "risks.md").unlink()
            stdout = io.StringIO()

            code = main(["review", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            self.assertIn("risks.md", stdout.getvalue())
            self.assertNotIn("Readiness score: 100%", stdout.getvalue())

    def test_next_prints_top_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a hiring platform"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["next", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Recommended next actions", output)
            self.assertIn("1. Write a one-paragraph project brief", output)
            self.assertIn("3. List the top 5 must-have requirements", output)

    def test_ask_returns_risks_with_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["ask", str(target), "What are the top risks?"], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Answer:", output)
            self.assertIn("The project may be too broad", output)
            self.assertIn("Sources:", output)
            self.assertIn("risks.md", output)

    def test_ask_returns_missing_before_kickoff_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a partner portal"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["ask", str(target), "What is missing before kickoff?"], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Who is the primary user", output)
            self.assertIn("open_questions.md", output)

    def test_ask_returns_user_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a customer onboarding tool"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["ask", str(target), "Who is the user?"], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Founder or product manager", output)
            self.assertIn("users.md", output)

    def test_ask_falls_back_without_useful_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            target.mkdir()
            stdout = io.StringIO()

            code = main(["ask", str(target), "What are the risks?"], stdout=stdout)

            self.assertEqual(code, 0)
            self.assertIn("I could not find enough project context", stdout.getvalue())

    def test_summarize_prints_project_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a hiring platform"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["summarize", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Project:", output)
            self.assertIn("Top goals:", output)
            self.assertIn("Top risks:", output)
            self.assertIn("Open questions:", output)
            self.assertIn("Next actions:", output)
            self.assertIn("Build a hiring platform", output)

    def test_summarize_handles_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a finance dashboard"], stdout=io.StringIO())
            (target / "risks.md").unlink()
            stdout = io.StringIO()

            code = main(["summarize", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Top risks:", output)
            self.assertIn("- None", output)

    def test_nonexistent_folder_returns_error_for_ask(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "missing"
            stderr = io.StringIO()

            code = main(["ask", str(target), "What is next?"], stdout=io.StringIO(), stderr=stderr)

            self.assertEqual(code, 1)
            self.assertIn("is not a project folder", stderr.getvalue())

    def test_add_decision_appends_dated_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(
                ["add-decision", str(target), "Version 1 will target support managers"],
                stdout=stdout,
            )

            self.assertEqual(code, 0)
            content = (target / "decisions.md").read_text(encoding="utf-8")
            self.assertIn("Added decision to decisions.md", stdout.getvalue())
            self.assertRegex(content, r"- \d{4}-\d{2}-\d{2}: Version 1 will target support managers")

    def test_add_decision_repairs_missing_heading(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            target.mkdir()
            (target / "decisions.md").write_text("Old note\n", encoding="utf-8")

            code = main(["add-decision", str(target), "Pick a narrow market"], stdout=io.StringIO())

            self.assertEqual(code, 0)
            content = (target / "decisions.md").read_text(encoding="utf-8")
            self.assertIn("# Decisions", content)
            self.assertIn("## Decision Log", content)
            self.assertIn("Pick a narrow market", content)

    def test_add_decision_rejects_empty_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            target.mkdir()
            stderr = io.StringIO()

            code = main(["add-decision", str(target), "   "], stdout=io.StringIO(), stderr=stderr)

            self.assertEqual(code, 1)
            self.assertIn("Please provide a decision", stderr.getvalue())

    def test_add_risk_appends_and_ask_can_find_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())

            code = main(["add-risk", str(target), "Zendesk API access may be delayed"], stdout=io.StringIO())
            ask_output = io.StringIO()
            main(["ask", str(target), "What are the top risks?"], stdout=ask_output)

            self.assertEqual(code, 0)
            self.assertIn("Zendesk API access may be delayed", (target / "risks.md").read_text(encoding="utf-8"))
            self.assertIn("Zendesk API access may be delayed", ask_output.getvalue())

    def test_add_task_appends_next_number(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a hiring platform"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["add-task", str(target), "Interview 3 hiring managers"], stdout=stdout)

            self.assertEqual(code, 0)
            self.assertIn("Added task 6 to tasks.md", stdout.getvalue())
            self.assertIn("6. Interview 3 hiring managers", (target / "tasks.md").read_text(encoding="utf-8"))

    def test_next_can_include_added_task_when_tasks_are_short(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            target.mkdir()
            (target / "tasks.md").write_text("# Tasks\n\n1. Existing task\n", encoding="utf-8")

            main(["add-task", str(target), "Call the first customer"], stdout=io.StringIO())
            stdout = io.StringIO()
            code = main(["next", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            self.assertIn("2. Call the first customer", stdout.getvalue())

    def test_answer_question_adds_answer_under_question(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a customer portal"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(
                ["answer-question", str(target), "1", "The primary user is the operations manager"],
                stdout=stdout,
            )

            self.assertEqual(code, 0)
            content = (target / "open_questions.md").read_text(encoding="utf-8")
            self.assertIn("Answered question 1 in open_questions.md", stdout.getvalue())
            self.assertIn("1. Who is the primary user", content)
            self.assertIn("   Answer: The primary user is the operations manager", content)

    def test_answer_question_errors_for_missing_number(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a customer portal"], stdout=io.StringIO())
            stderr = io.StringIO()

            code = main(
                ["answer-question", str(target), "99", "No answer"],
                stdout=io.StringIO(),
                stderr=stderr,
            )

            self.assertEqual(code, 1)
            self.assertIn("Question 99 was not found", stderr.getvalue())

    def test_summarize_still_reads_after_answer_question(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a customer portal"], stdout=io.StringIO())
            main(
                ["answer-question", str(target), "1", "The primary user is the operations manager"],
                stdout=io.StringIO(),
            )
            stdout = io.StringIO()

            code = main(["summarize", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            self.assertIn("Open questions:", stdout.getvalue())

    def test_health_reports_fresh_workspace_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["health", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Project Health:", output)
            self.assertIn("Strengths:", output)
            self.assertIn("Weak Spots:", output)
            self.assertIn("Recommended Fixes:", output)
            self.assertIn("Project brief is present", output)
            self.assertIn("No decision has been recorded yet", output)
            self.assertIn("add-decision", output)

    def test_health_score_improves_after_decision_and_answer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a customer portal"], stdout=io.StringIO())
            before = io.StringIO()
            main(["health", str(target)], stdout=before)

            main(["add-decision", str(target), "Version 1 targets operations managers"], stdout=io.StringIO())
            main(
                ["answer-question", str(target), "1", "The primary user is the operations manager"],
                stdout=io.StringIO(),
            )
            after = io.StringIO()
            main(["health", str(target)], stdout=after)

            self.assertGreater(_health_score(after.getvalue()), _health_score(before.getvalue()))

    def test_health_reports_missing_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a finance dashboard"], stdout=io.StringIO())
            (target / "requirements.md").unlink()
            stdout = io.StringIO()

            code = main(["health", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            self.assertIn("Requirements are missing", stdout.getvalue())

    def test_health_missing_folder_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "missing"
            stderr = io.StringIO()

            code = main(["health", str(target)], stdout=io.StringIO(), stderr=stderr)

            self.assertEqual(code, 1)
            self.assertIn("is not a project folder", stderr.getvalue())

    def test_health_recommends_command_style_fixes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a partner portal"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["health", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("add-decision", output)
            self.assertIn("answer-question", output)

    def test_kickoff_prints_all_workflow_steps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["kickoff", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Kickoff Workflow", output)
            self.assertIn("Step 1: Project Summary", output)
            self.assertIn("Step 2: Health Check", output)
            self.assertIn("Step 3: Recommended Next Actions", output)
            self.assertIn("Step 4: Suggested Commands", output)

    def test_kickoff_includes_summary_health_actions_and_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a hiring platform"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["kickoff", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Project: Build a Hiring Platform", output)
            self.assertIn("Project Health:", output)
            self.assertIn("No decision has been recorded yet", output)
            self.assertIn("Write a one-paragraph project brief", output)
            self.assertIn("ares add-decision", output)
            self.assertIn("ares answer-question", output)

    def test_kickoff_suggested_commands_reflect_resolved_weak_spots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a customer portal"], stdout=io.StringIO())
            main(["add-decision", str(target), "Version 1 targets operations managers"], stdout=io.StringIO())
            main(
                ["answer-question", str(target), "1", "The primary user is the operations manager"],
                stdout=io.StringIO(),
            )
            stdout = io.StringIO()

            code = main(["kickoff", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertNotIn("ares add-decision", output)
            self.assertNotIn("ares answer-question", output)

    def test_kickoff_missing_folder_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "missing"
            stderr = io.StringIO()

            code = main(["kickoff", str(target)], stdout=io.StringIO(), stderr=stderr)

            self.assertEqual(code, 1)
            self.assertIn("is not a project folder", stderr.getvalue())

    def test_kickoff_does_not_modify_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a finance dashboard"], stdout=io.StringIO())
            before = _file_snapshot(target)

            code = main(["kickoff", str(target)], stdout=io.StringIO())

            self.assertEqual(code, 0)
            self.assertEqual(before, _file_snapshot(target))

    def test_kickoff_graph_prints_trace_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["kickoff-graph", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Graph Kickoff Workflow", output)
            self.assertIn("Trace:", output)
            self.assertLess(output.index("1. summary_node"), output.index("2. health_node"))
            self.assertLess(output.index("2. health_node"), output.index("3. next_actions_node"))
            self.assertLess(output.index("3. next_actions_node"), output.index("4. suggested_commands_node"))
            self.assertLess(output.index("4. suggested_commands_node"), output.index("5. final_report_node"))

    def test_kickoff_graph_includes_core_report_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a hiring platform"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["kickoff-graph", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Project: Build a Hiring Platform", output)
            self.assertIn("Project Health:", output)
            self.assertIn("Weak Spots:", output)
            self.assertIn("Recommended Next Actions", output)
            self.assertIn("Suggested Commands", output)
            self.assertIn("ares add-decision", output)

    def test_kickoff_graph_matches_kickoff_title_and_health_score(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a customer portal"], stdout=io.StringIO())
            kickoff = io.StringIO()
            graph = io.StringIO()

            main(["kickoff", str(target)], stdout=kickoff)
            main(["kickoff-graph", str(target)], stdout=graph)

            self.assertIn("Project: Build a Customer Portal", graph.getvalue())
            self.assertIn("Project: Build a Customer Portal", kickoff.getvalue())
            self.assertEqual(_health_score(kickoff.getvalue()), _health_score(graph.getvalue()))

    def test_kickoff_graph_missing_folder_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "missing"
            stderr = io.StringIO()

            code = main(["kickoff-graph", str(target)], stdout=io.StringIO(), stderr=stderr)

            self.assertEqual(code, 1)
            self.assertIn("is not a project folder", stderr.getvalue())

    def test_kickoff_graph_does_not_modify_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a finance dashboard"], stdout=io.StringIO())
            before = _file_snapshot(target)

            code = main(["kickoff-graph", str(target)], stdout=io.StringIO())

            self.assertEqual(code, 0)
            self.assertEqual(before, _file_snapshot(target))

    def test_kickoff_langgraph_missing_dependency_returns_install_message(self) -> None:
        if _has_langgraph():
            self.skipTest("LangGraph is installed; missing dependency path is not active.")
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stderr = io.StringIO()

            code = main(["kickoff-langgraph", str(target)], stdout=io.StringIO(), stderr=stderr)

            self.assertEqual(code, 1)
            self.assertIn("LangGraph is not installed", stderr.getvalue())
            self.assertIn("pip install langgraph", stderr.getvalue())

    @unittest.skipUnless(importlib.util.find_spec("langgraph"), "LangGraph is not installed.")
    def test_kickoff_langgraph_prints_workflow_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["kickoff-langgraph", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("LangGraph Kickoff Workflow", output)
            self.assertIn("Project: Build a Support Dashboard", output)
            self.assertIn("Project Health:", output)
            self.assertIn("Weak Spots:", output)
            self.assertIn("Suggested Commands", output)

    @unittest.skipUnless(importlib.util.find_spec("langgraph"), "LangGraph is not installed.")
    def test_kickoff_langgraph_matches_graph_health_score(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a customer portal"], stdout=io.StringIO())
            graph = io.StringIO()
            langgraph = io.StringIO()

            main(["kickoff-graph", str(target)], stdout=graph)
            main(["kickoff-langgraph", str(target)], stdout=langgraph)

            self.assertEqual(_health_score(graph.getvalue()), _health_score(langgraph.getvalue()))

    @unittest.skipUnless(importlib.util.find_spec("langgraph"), "LangGraph is not installed.")
    def test_kickoff_langgraph_does_not_modify_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a finance dashboard"], stdout=io.StringIO())
            before = _file_snapshot(target)

            code = main(["kickoff-langgraph", str(target)], stdout=io.StringIO())

            self.assertEqual(code, 0)
            self.assertEqual(before, _file_snapshot(target))

    def test_ask_deep_finds_research_answers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            (target / "research").mkdir(exist_ok=True)
            (target / "research" / "customer-interviews.md").write_text(
                "# Customer Interviews\n\n- Customers complain about slow response time and repeated handoffs.\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()

            code = main(["ask-deep", str(target), "What are customers complaining about?"], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Customers complain about slow response time", output)
            self.assertIn("research/customer-interviews.md", output)

    def test_ask_deep_finds_docs_answers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            (target / "docs").mkdir(exist_ok=True)
            (target / "docs" / "support-process.md").write_text(
                "# Support Process\n\n- Support managers need visibility into overloaded agents.\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()

            code = main(["ask-deep", str(target), "What do support managers need?"], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Support managers need visibility", output)
            self.assertIn("docs/support-process.md", output)

    def test_ask_deep_finds_reports_answers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            (target / "reports").mkdir(exist_ok=True)
            (target / "reports" / "weekly-summary.md").write_text(
                "# Weekly Summary\n\n- Response time worsened during Monday ticket spikes.\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()

            code = main(["ask-deep", str(target), "What happened with response time?"], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Response time worsened", output)
            self.assertIn("reports/weekly-summary.md", output)

    def test_ask_deep_falls_back_without_matching_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["ask-deep", str(target), "What did pilots say about encryption latency?"], stdout=stdout)

            self.assertEqual(code, 0)
            self.assertIn("I could not find enough project context", stdout.getvalue())
            self.assertIn("docs/, research/, or reports/", stdout.getvalue())

    def test_ask_deep_missing_folder_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "missing"
            stderr = io.StringIO()

            code = main(["ask-deep", str(target), "What happened?"], stdout=io.StringIO(), stderr=stderr)

            self.assertEqual(code, 1)
            self.assertIn("is not a project folder", stderr.getvalue())

    def test_ask_deep_empty_question_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            target.mkdir()
            stderr = io.StringIO()

            code = main(["ask-deep", str(target), "   "], stdout=io.StringIO(), stderr=stderr)

            self.assertEqual(code, 1)
            self.assertIn("Please provide a question", stderr.getvalue())

    def test_ask_deep_does_not_modify_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            (target / "research").mkdir(exist_ok=True)
            (target / "research" / "customer-interviews.md").write_text(
                "# Customer Interviews\n\n- Customers complain about slow response time.\n",
                encoding="utf-8",
            )
            before = _file_snapshot(target)

            code = main(["ask-deep", str(target), "What do customers complain about?"], stdout=io.StringIO())

            self.assertEqual(code, 0)
            self.assertEqual(before, _file_snapshot(target))

    def test_ask_still_ignores_nested_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            target.mkdir()
            (target / "research").mkdir()
            (target / "research" / "customer-interviews.md").write_text(
                "# Customer Interviews\n\n- Customers complain about slow response time.\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()

            code = main(["ask", str(target), "What do customers complain about?"], stdout=stdout)

            self.assertEqual(code, 0)
            self.assertIn("I could not find enough project context", stdout.getvalue())

    def test_inspect_data_missing_dependencies_returns_install_message(self) -> None:
        original = data_inspector._load_dependencies

        def missing_dependencies() -> None:
            raise data_inspector.DataInspectionUnavailableError(
                "pandas and NumPy are required for data inspection.\n"
                "Install them with: pip install pandas numpy"
            )

        data_inspector._load_dependencies = missing_dependencies
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                target = Path(temp_dir) / "workspace"
                target.mkdir()
                stderr = io.StringIO()

                code = main(["inspect-data", str(target)], stdout=io.StringIO(), stderr=stderr)

                self.assertEqual(code, 1)
                self.assertIn("pandas and NumPy are required", stderr.getvalue())
                self.assertIn("pip install pandas numpy", stderr.getvalue())
        finally:
            data_inspector._load_dependencies = original

    def test_inspect_data_missing_folder_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "missing"
            stderr = io.StringIO()

            code = main(["inspect-data", str(target)], stdout=io.StringIO(), stderr=stderr)

            self.assertEqual(code, 1)
            self.assertIn("is not a project folder", stderr.getvalue())

    @unittest.skipUnless(HAS_PANDAS_NUMPY, "pandas and NumPy are not installed.")
    def test_inspect_data_no_csv_files_returns_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["inspect-data", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Data Inspection", output)
            self.assertIn("No CSV files found in data/.", output)

    @unittest.skipUnless(HAS_PANDAS_NUMPY, "pandas and NumPy are not installed.")
    def test_inspect_data_reports_csv_shape_and_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            _write_sample_csv(target)
            stdout = io.StringIO()

            code = main(["inspect-data", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("data/support_tickets.csv", output)
            self.assertIn("- Rows: 3", output)
            self.assertIn("- Columns: 6", output)

    @unittest.skipUnless(HAS_PANDAS_NUMPY, "pandas and NumPy are not installed.")
    def test_inspect_data_reports_missing_values_and_column_types(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            _write_sample_csv(target)
            stdout = io.StringIO()

            code = main(["inspect-data", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("customer_region has 1 missing values", output)
            self.assertIn("Numeric columns: response_time_minutes, satisfaction_score, revenue_amount", output)
            self.assertIn("Category/text columns: priority, status, customer_region", output)

    @unittest.skipUnless(HAS_PANDAS_NUMPY, "pandas and NumPy are not installed.")
    def test_inspect_data_suggests_business_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            _write_sample_csv(target)
            stdout = io.StringIO()

            code = main(["inspect-data", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Average response time minutes", output)
            self.assertIn("Average satisfaction score", output)
            self.assertIn("Counts by priority", output)
            self.assertIn("Total and average revenue amount", output)

    @unittest.skipUnless(HAS_PANDAS_NUMPY, "pandas and NumPy are not installed.")
    def test_inspect_data_does_not_modify_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            _write_sample_csv(target)
            before = _all_file_snapshot(target)

            code = main(["inspect-data", str(target)], stdout=io.StringIO())

            self.assertEqual(code, 0)
            self.assertEqual(before, _all_file_snapshot(target))

    def test_demo_script_exists_and_is_executable(self) -> None:
        demo_script = Path(__file__).resolve().parents[1] / "demo.sh"

        self.assertTrue(demo_script.is_file())
        self.assertTrue(demo_script.stat().st_mode & 0o111)

    def test_model_status_prints_setup_guidance(self) -> None:
        original = cli.check_model_status
        cli.check_model_status = lambda: local_models.ModelStatus(
            ollama_installed=True,
            ollama_path="/opt/homebrew/bin/ollama",
            server_reachable=False,
            available_models=[],
            missing_models=local_models.REQUIRED_MODELS,
            setup_commands=local_models.SETUP_COMMANDS,
            error="Could not reach local Ollama.",
        )
        try:
            stdout = io.StringIO()
            code = main(["model-status"], stdout=stdout)
        finally:
            cli.check_model_status = original

        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("Local Model Status", output)
        self.assertIn("ollama pull llama3.2", output)

    def test_chat_returns_setup_message_when_model_missing(self) -> None:
        original = cli.generate_text

        def missing_model(_prompt: str) -> str:
            raise local_models.LocalModelUnavailableError(local_models.setup_message())

        cli.generate_text = missing_model
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                target = Path(temp_dir) / "workspace"
                main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
                stdout = io.StringIO()
                code = main(["chat", str(target), "What next?"], stdout=stdout)
        finally:
            cli.generate_text = original

        self.assertEqual(code, 0)
        self.assertIn("Local models are not ready yet", stdout.getvalue())

    def test_index_creates_local_index_metadata(self) -> None:
        original = local_models.embed_text
        local_models.embed_text = lambda text: [float(len(text) % 7), 1.0]
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                target = Path(temp_dir) / "workspace"
                main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
                stdout = io.StringIO()

                code = main(["index", str(target)], stdout=stdout)

                self.assertEqual(code, 0)
                self.assertTrue((target / ".project_launcher" / "index.json").is_file())
                self.assertIn("Chunks:", stdout.getvalue())
        finally:
            local_models.embed_text = original

    def test_ask_rag_returns_sources_from_index_without_chat_model(self) -> None:
        original_embed = local_models.embed_text
        original_generate = local_models.generate_text

        def fake_embedding(text: str) -> list[float]:
            lowered = text.lower()
            if "customer" in lowered or "complain" in lowered:
                return [1.0, 0.0]
            return [0.0, 1.0]

        local_models.embed_text = fake_embedding

        def missing_chat(_prompt: str, model: str = local_models.DEFAULT_CHAT_MODEL, timeout: float = 60.0) -> str:
            raise local_models.LocalModelUnavailableError(local_models.setup_message())

        local_models.generate_text = missing_chat
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                target = Path(temp_dir) / "workspace"
                main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
                (target / "research" / "customer-interviews.md").write_text(
                    "# Interviews\n\n- Customers complain about slow response time.\n",
                    encoding="utf-8",
                )
                main(["index", str(target)], stdout=io.StringIO())
                stdout = io.StringIO()

                code = main(["ask-rag", str(target), "What are customers complaining about?"], stdout=stdout)
        finally:
            local_models.embed_text = original_embed
            local_models.generate_text = original_generate

        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("Local chat model is not ready", output)
        self.assertIn("research/customer-interviews.md", output)

    @patch.object(local_models, "generate_text", side_effect=local_models.LocalModelUnavailableError("missing"))
    def test_pm_review_defaults_to_fast_agent_sections(self, _mock_generate) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["pm-review", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("PM Review", output)
            self.assertIn("Agent Findings", output)
            self.assertIn("PM Strategist", output)
            self.assertIn("Risk Reviewer", output)
            self.assertIn("Execution Planner", output)
            self.assertNotIn("Founder Clarifier", output)
            self.assertNotIn("Final Reviewer", output)
            self.assertIn("Timing:", output)
            self.assertIn("- Mode: fast", output)
            self.assertIn("- Agents run: 3", output)
            self.assertIn("- Total:", output)

    @patch.object(local_models, "generate_text", side_effect=local_models.LocalModelUnavailableError("missing"))
    def test_pm_review_full_prints_all_agent_sections(self, _mock_generate) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["pm-review", str(target), "--full"], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Founder Clarifier", output)
            self.assertIn("PM Strategist", output)
            self.assertIn("Research Analyst", output)
            self.assertIn("Data Analyst", output)
            self.assertIn("Risk Reviewer", output)
            self.assertIn("Execution Planner", output)
            self.assertIn("Final Reviewer", output)
            self.assertIn("- Mode: full", output)
            self.assertIn("- Agents run: 7", output)

    @patch.object(local_models, "generate_text", side_effect=local_models.LocalModelUnavailableError("missing"))
    def test_pm_review_fast_flag_matches_default(self, _mock_generate) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["pm-review", str(target), "--fast"], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("PM Strategist", output)
            self.assertNotIn("Founder Clarifier", output)
            self.assertIn("- Mode: fast", output)

    def test_pm_review_rejects_conflicting_mode_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())

            with self.assertRaises(SystemExit):
                with contextlib.redirect_stderr(io.StringIO()):
                    main(["pm-review", str(target), "--fast", "--full"], stdout=io.StringIO(), stderr=io.StringIO())

    @patch.object(local_models, "generate_text", side_effect=local_models.LocalModelUnavailableError("missing"))
    def test_super_routes_review_request(self, _mock_generate) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["super", str(target), "Prepare this project for kickoff"], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Superagent Response", output)
            self.assertIn("PM Review", output)
            self.assertIn("Recommended Next Actions", output)
            self.assertIn("- Mode: fast", output)
            self.assertNotIn("Founder Clarifier", output)

    @patch.object(local_models, "generate_text", side_effect=local_models.LocalModelUnavailableError("missing"))
    def test_super_full_routes_review_request_to_full_pm_review(self, _mock_generate) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["super", str(target), "Prepare this project for kickoff", "--full"], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Superagent Response", output)
            self.assertIn("PM Review", output)
            self.assertIn("- Mode: full", output)
            self.assertIn("Founder Clarifier", output)
            self.assertIn("Final Reviewer", output)

    def test_ingest_creates_markdown_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            source = Path(temp_dir) / "notes.txt"
            source.write_text("Customers need faster support visibility.", encoding="utf-8")

            first = io.StringIO()
            second = io.StringIO()
            code1 = main(["ingest", str(target), str(source)], stdout=first)
            code2 = main(["ingest", str(target), str(source)], stdout=second)

            self.assertEqual(code1, 0)
            self.assertEqual(code2, 0)
            self.assertTrue((target / "research" / "ingested" / "notes.md").is_file())
            self.assertTrue((target / "research" / "ingested" / "notes-2.md").is_file())

    def test_quality_gate_reports_rating(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "workspace"
            main(["init", str(target), "Build a support dashboard"], stdout=io.StringIO())
            stdout = io.StringIO()

            code = main(["quality-gate", str(target)], stdout=stdout)

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("Quality Gate Rating:", output)
            self.assertIn("Reviewer Notes:", output)

    def test_e2e_script_exists_and_is_executable(self) -> None:
        script = Path(__file__).resolve().parents[1] / "e2e_user_test.sh"

        self.assertTrue(script.is_file())
        self.assertTrue(script.stat().st_mode & 0o111)


if __name__ == "__main__":
    unittest.main()


def _health_score(output: str) -> int:
    for line in output.splitlines():
        if line.startswith("Project Health:"):
            return int(line.split(":", 1)[1].strip().rstrip("%"))
    raise AssertionError("Missing health score")


def _file_snapshot(folder: Path) -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(folder.glob("*.md"))
    }


def _has_langgraph() -> bool:
    return importlib.util.find_spec("langgraph") is not None


def _write_sample_csv(folder: Path) -> None:
    data_dir = folder / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "support_tickets.csv").write_text(
        "\n".join(
            [
                "priority,status,customer_region,response_time_minutes,satisfaction_score,revenue_amount",
                "high,open,west,45,4.5,100",
                "low,closed,,30,4.0,75",
                "medium,open,east,60,3.5,125",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _all_file_snapshot(folder: Path) -> dict[str, str]:
    return {
        path.relative_to(folder).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }
