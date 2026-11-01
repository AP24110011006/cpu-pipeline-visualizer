"""Comprehensive unit and integration test suite for Full Stack Engineering Agent."""

from __future__ import annotations

from pathlib import Path
import pytest

from agents.execution import CodeExecutor
from agents.models import TaskState
from agents.orchestrator import FullStackEngineeringAgent
from agents.planning import Planner
from agents.repo_intelligence import RepoInspector


def test_repo_inspector_and_dependencies() -> None:
    """Verify RepoInspector lists files and maps module responsibilities."""
    inspector = RepoInspector()
    files = inspector.list_files()
    assert len(files) > 10
    assert any("simulator/pipeline.py" in f for f in files)
    assert any("ui/theme.py" in f for f in files)

    responsibilities = inspector.get_module_responsibilities()
    assert "simulator/" in responsibilities
    assert "ui/" in responsibilities

    # Verify no broken local imports in the active repository
    broken = inspector.check_broken_imports()
    assert len(broken) == 0, f"Discovered broken imports: {broken}"


def test_code_executor_sandbox_and_security(tmp_path: Path) -> None:
    """Verify CodeExecutor blocks path traversal and forbidden commands."""
    executor = CodeExecutor(root_dir=tmp_path)

    # Path traversal block
    with pytest.raises(PermissionError):
        executor._resolve_safe_path("../../../etc/passwd")

    # Command whitelist enforcement
    res = executor.run_safe_command("rm -rf /")
    assert not res.passed
    assert "Security Policy" in res.stderr

    res_forbidden = executor.run_safe_command("curl http://example.com")
    assert not res_forbidden.passed


def test_code_executor_staging_diff_and_rollback(tmp_path: Path) -> None:
    """Verify staging changes, diff generation, and safe rollback."""
    executor = CodeExecutor(root_dir=tmp_path)
    sample_file = tmp_path / "hello.py"
    sample_file.write_text("print('hello')\n", encoding="utf-8")

    # Stage modification
    change = executor.stage_change("hello.py", "print('hello world')\n")
    assert not change.applied
    assert "+print('hello world')" in change.diff

    # Apply change
    assert executor.apply_change(change)
    assert change.applied
    assert sample_file.read_text(encoding="utf-8") == "print('hello world')\n"

    # Rollback change
    assert executor.rollback_change(change)
    assert not change.applied
    assert sample_file.read_text(encoding="utf-8") == "print('hello')\n"


def test_full_stack_agent_end_to_end_lifecycle(tmp_path: Path) -> None:
    """Section 13 Step 4: End-to-end autonomous agent workflow in a temporary test repository.
    
    1. Inspects files
    2. Creates plan
    3. Identifies a deliberately introduced bug
    4. Applies targeted fix
    5. Reruns tests and verifies success
    6. Produces truthful final report
    """
    # Create mini test repository
    src_file = tmp_path / "calc.py"
    src_file.write_text("def add(a: int, b: int) -> int:\n    return a - b  # Deliberate bug!\n", encoding="utf-8")

    test_file = tmp_path / "test_calc.py"
    test_file.write_text(
        "import pytest\nfrom calc import add\n\n"
        "def test_add_correctness():\n    assert add(2, 3) == 5\n",
        encoding="utf-8",
    )

    agent = FullStackEngineeringAgent(root_dir=tmp_path)
    task = agent.create_task("Fix arithmetic add function so that unit test test_add_correctness passes")
    assert task.state == TaskState.PENDING

    # Step 1: Analyze
    agent.analyze(task)
    assert task.state == TaskState.PLANNING

    # Step 2: Plan
    plan = agent.plan(task)
    assert task.state == TaskState.AWAITING_APPROVAL
    assert len(plan.steps) >= 3

    # Step 3: Run initial tests (expect failure due to deliberate bug)
    init_res = agent.run_tests(task, test_filter="test_calc.py")
    assert not init_res.passed
    assert task.state == TaskState.FIXING
    assert len(task.diagnostics) >= 1
    assert "test_add_correctness" in task.diagnostics[0].test_id

    # Step 4: Auto-fix and verify with bounded retry
    def fix_generator(t):
        return {"calc.py": "def add(a: int, b: int) -> int:\n    return a + b\n"}

    success = agent.auto_fix_and_verify(task, test_filter="test_calc.py", fix_generator=fix_generator)
    assert success is True
    assert task.state == TaskState.VERIFIED
    assert task.retry_count == 1

    # Verify report contents
    report = agent.generate_final_report(task)
    assert "Full Stack Engineering Agent Report" in report
    assert "Verified" in report
    assert "+    return a + b" in report
    assert "PASSED ✅" in report
