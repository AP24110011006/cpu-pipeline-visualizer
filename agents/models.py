"""Data models and lifecycle states for the Full Stack Engineering Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Dict, List, Optional


class TaskState(str, Enum):
    """Rigorous task lifecycle states matching Section 6 specification."""
    PENDING = "Pending"
    ANALYZING = "Analyzing"
    PLANNING = "Planning"
    AWAITING_APPROVAL = "Awaiting Approval"
    IMPLEMENTING = "Implementing"
    TESTING = "Testing"
    FIXING = "Fixing"
    VERIFIED = "Verified"
    FAILED = "Failed"


@dataclass
class PlanStep:
    """A discrete step in an implementation plan."""
    step_num: int
    description: str
    target_files: List[str]
    risks: str = ""
    status: str = "Pending"


@dataclass
class TaskPlan:
    """Structured architectural plan before code modification."""
    task_id: str
    requirement: str
    steps: List[PlanStep]
    files_to_modify: List[str]
    potential_risks: List[str]
    created_at: float = field(default_factory=time.time)


@dataclass
class FileChange:
    """A proposed or applied code modification."""
    filepath: str
    original_content: str
    proposed_content: str
    diff: str
    is_new_file: bool = False
    applied: bool = False
    applied_at: Optional[float] = None


@dataclass
class ExecutionResult:
    """Result of a command or test suite run."""
    command: str
    returncode: int
    stdout: str
    stderr: str
    passed: bool
    duration_sec: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class DiagnosticError:
    """Parsed error from test runner or linter."""
    test_id: str
    file: str
    line_number: Optional[int]
    error_message: str
    traceback: str


@dataclass
class Task:
    """Full lifecycle tracking for a repository development task."""
    task_id: str
    requirement: str
    state: TaskState = TaskState.PENDING
    plan: Optional[TaskPlan] = None
    changes: List[FileChange] = field(default_factory=list)
    execution_logs: List[str] = field(default_factory=list)
    test_results: List[ExecutionResult] = field(default_factory=list)
    diagnostics: List[DiagnosticError] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    final_report: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def log(self, message: str) -> None:
        """Append a timestamped log entry."""
        entry = f"[{time.strftime('%H:%M:%S')}] {message}"
        self.execution_logs.append(entry)
        self.updated_at = time.time()
