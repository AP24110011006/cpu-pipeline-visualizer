"""Full Stack Engineering Agent Package.

Provides autonomous repository intelligence, safe task planning, controlled code modification,
diagnostic test parsing, bounded error repair, and verified delivery.
"""

from __future__ import annotations

from agents.execution import CodeExecutor
from agents.models import (
    DiagnosticError,
    ExecutionResult,
    FileChange,
    PlanStep,
    Task,
    TaskPlan,
    TaskState,
)
from agents.orchestrator import FullStackEngineeringAgent
from agents.planning import Planner
from agents.provider import (
    AnthropicProvider,
    LLMProvider,
    LocalDeterministicProvider,
    OpenAIProvider,
    get_active_provider,
)
from agents.repo_intelligence import RepoInspector

__all__ = [
    "AnthropicProvider",
    "CodeExecutor",
    "DiagnosticError",
    "ExecutionResult",
    "FileChange",
    "FullStackEngineeringAgent",
    "LLMProvider",
    "LocalDeterministicProvider",
    "OpenAIProvider",
    "PlanStep",
    "Planner",
    "RepoInspector",
    "Task",
    "TaskPlan",
    "TaskState",
    "get_active_provider",
]
