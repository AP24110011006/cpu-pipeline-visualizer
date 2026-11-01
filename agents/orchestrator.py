"""Master orchestrator for the Full Stack Engineering Agent."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Callable, Dict, List, Optional
import uuid

from agents.execution import CodeExecutor
from agents.models import DiagnosticError, ExecutionResult, FileChange, Task, TaskPlan, TaskState
from agents.planning import Planner
from agents.provider import LLMProvider, get_active_provider
from agents.repo_intelligence import RepoInspector


class FullStackEngineeringAgent:
    """Autonomous Full Stack Engineering Agent for repository development and verification.
    
    Orchestrates the entire development lifecycle:
    Pending -> Analyzing -> Planning -> Awaiting Approval -> Implementing -> Testing -> Fixing -> Verified / Failed.
    """

    def __init__(self, root_dir: Optional[Path] = None, provider: Optional[LLMProvider] = None) -> None:
        self.inspector = RepoInspector(root_dir)
        self.planner = Planner(self.inspector)
        self.executor = CodeExecutor(root_dir)
        if provider is None:
            self.provider, self.provider_name = get_active_provider()
        else:
            self.provider = provider
            self.provider_name = type(provider).__name__

    def create_task(self, requirement: str) -> Task:
        """Create a new task in PENDING state."""
        task_id = str(uuid.uuid4())[:8]
        task = Task(task_id=task_id, requirement=requirement, state=TaskState.PENDING)
        task.log(f"Task created with requirement: '{requirement}'")
        return task

    def analyze(self, task: Task) -> Dict[str, str]:
        """Perform repository intelligence analysis for the task."""
        task.state = TaskState.ANALYZING
        task.log("Analyzing repository structure and target modules...")

        modules = self.inspector.get_module_responsibilities()
        broken = self.inspector.check_broken_imports()
        if broken:
            task.log(f"Warning: Discovered {len(broken)} unresolved imports.")
        else:
            task.log("Repository integrity check: All local module imports resolved successfully.")

        task.state = TaskState.PLANNING
        return modules

    def plan(self, task: Task) -> TaskPlan:
        """Generate structured task plan and transition to AWAITING_APPROVAL."""
        task.state = TaskState.PLANNING
        task.log("Synthesizing step-by-step implementation plan...")

        plan = self.planner.generate_plan(task.requirement)
        task.plan = plan
        task.log(f"Plan generated with {len(plan.steps)} steps across files: {', '.join(plan.files_to_modify)}")

        # Transition to AWAITING_APPROVAL requiring explicit user or programmatic approval
        task.state = TaskState.AWAITING_APPROVAL
        task.log("Awaiting engineer approval before staging file modifications.")
        return plan

    def stage_modifications(self, task: Task, modifications: Dict[str, str]) -> List[FileChange]:
        """Stage proposed file modifications and generate unified git diffs."""
        task.changes.clear()
        for filepath, proposed_code in modifications.items():
            change = self.executor.stage_change(filepath, proposed_code)
            task.changes.append(change)
            task.log(f"Staged modification for '{filepath}' ({len(proposed_code)} chars). Diff generated.")
        return task.changes

    def approve_and_implement(self, task: Task) -> bool:
        """Approve and apply all staged file changes to disk."""
        if not task.changes:
            task.log("Error: No file changes staged for implementation.")
            task.state = TaskState.FAILED
            return False

        task.state = TaskState.IMPLEMENTING
        task.log(f"Engineer approved changes. Applying {len(task.changes)} file modifications to disk...")

        for change in task.changes:
            try:
                self.executor.apply_change(change)
                task.log(f"Applied change to '{change.filepath}'.")
            except Exception as err:
                task.log(f"Failed to apply change to '{change.filepath}': {err}")
                task.state = TaskState.FAILED
                return False

        task.log("All changes successfully applied to disk.")
        return True

    def run_tests(self, task: Task, test_filter: Optional[str] = None) -> ExecutionResult:
        """Execute regression tests and update task state."""
        task.state = TaskState.TESTING
        task.log(f"Running automated test suite (filter: {test_filter or 'all'})...")

        result = self.executor.run_pytest(test_filter)
        task.test_results.append(result)

        if result.passed:
            task.log(f"Tests PASSED in {result.duration_sec:.2f}s.")
            task.state = TaskState.VERIFIED
            task.final_report = self.generate_final_report(task)
        else:
            task.log(f"Tests FAILED with return code {result.returncode} in {result.duration_sec:.2f}s.")
            diagnostics = self.executor.parse_diagnostics(result.stdout + result.stderr)
            task.diagnostics = diagnostics
            task.log(f"Parsed {len(diagnostics)} diagnostic failure points.")
            task.state = TaskState.FIXING

        return result

    def auto_fix_and_verify(
        self,
        task: Task,
        test_filter: Optional[str] = None,
        fix_generator: Optional[Callable[[Task], Dict[str, str]]] = None,
    ) -> bool:
        """Diagnose failures, apply targeted correction, and rerun tests with bounded retries."""
        while task.state == TaskState.FIXING and task.retry_count < task.max_retries:
            task.retry_count += 1
            task.log(f"Executing bounded repair cycle {task.retry_count} of {task.max_retries}...")

            if fix_generator:
                fixes = fix_generator(task)
                if fixes:
                    self.stage_modifications(task, fixes)
                    self.approve_and_implement(task)

            # Rerun tests
            res = self.run_tests(task, test_filter)
            if res.passed:
                task.log(f"Verification successful on retry {task.retry_count}!")
                task.state = TaskState.VERIFIED
                task.final_report = self.generate_final_report(task)
                return True

        if task.state != TaskState.VERIFIED:
            task.state = TaskState.FAILED
            task.log(f"Repair exhausted {task.max_retries} retries without passing tests. Task FAILED.")
            task.final_report = self.generate_final_report(task)
            return False

        return True

    def rollback_task(self, task: Task) -> None:
        """Revert all applied file changes from backup."""
        task.log("Rolling back all changes made by task...")
        for change in reversed(task.changes):
            if change.applied:
                self.executor.rollback_change(change)
                task.log(f"Reverted '{change.filepath}'.")
        task.state = TaskState.PENDING
        task.log("Rollback complete.")

    def generate_final_report(self, task: Task) -> str:
        """Generate a complete Markdown audit report of the task execution."""
        lines = [
            f"# 🤖 Full Stack Engineering Agent Report — Task `{task.task_id}`",
            "",
            f"**Requirement**: {task.requirement}",
            f"**Final Status**: `{task.state.value}`",
            f"**Retries Used**: {task.retry_count} / {task.max_retries}",
            f"**Provider**: {self.provider_name}",
            "",
            "## 📋 Implementation Plan",
        ]
        if task.plan:
            for s in task.plan.steps:
                lines.append(f"{s.step_num}. **{s.description}** (Files: `{', '.join(s.target_files)}`)")
            if task.plan.potential_risks:
                lines.append("\n**Identified Risks**:")
                for r in task.plan.potential_risks:
                    lines.append(f"- ⚠️ {r}")
        lines.append("")
        lines.append("## 📁 Modified Files & Diffs")
        if task.changes:
            for c in task.changes:
                lines.append(f"### `{c.filepath}` ({'New File' if c.is_new_file else 'Modified'})")
                if c.diff:
                    lines.append("```diff")
                    lines.append(c.diff)
                    lines.append("```")
                else:
                    lines.append("*No textual differences.*")
        else:
            lines.append("*No files modified.*")

        lines.append("")
        lines.append("## 🧪 Verification & Test Results")
        if task.test_results:
            last_res = task.test_results[-1]
            status_text = "PASSED ✅" if last_res.passed else "FAILED ❌"
            lines.append(f"- **Final Command**: `{last_res.command}`")
            lines.append(f"- **Status**: {status_text} (Duration: {last_res.duration_sec:.2f}s)")
            if task.diagnostics:
                lines.append(f"- **Diagnostic Failure Count**: {len(task.diagnostics)}")
                for d in task.diagnostics:
                    lines.append(f"  - `{d.test_id}`: {d.error_message}")
        else:
            lines.append("*No test runs recorded.*")

        lines.append("")
        lines.append("## 📜 Execution Audit Log")
        for log_entry in task.execution_logs:
            lines.append(f"- {log_entry}")

        return "\n".join(lines)
