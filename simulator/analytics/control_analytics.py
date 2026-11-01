"""Control hazard analytics: branch predictions, jumps, flushes, and squashes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from simulator.models import DynamicInstruction, PipelineEvent, SimulationResult


@dataclass
class ControlSummary:
    """Detailed control-flow and branch hazard metrics."""

    total_branches_executed: int = 0
    branches_taken: int = 0
    branches_not_taken: int = 0
    jump_instructions_executed: int = 0
    pipeline_flush_events: int = 0
    flushed_instructions_count: int = 0
    control_related_stalls: int = 0


def analyze_control_flow(result: SimulationResult) -> ControlSummary:
    """Analyze branches, jumps, and squashes from dynamic instruction execution."""
    summary = ControlSummary()

    for dyn in result.instructions:
        if dyn.instr.is_branch:
            # Only count dynamic branches that were not themselves squashed before execution
            if not dyn.squashed or dyn.retired:
                summary.total_branches_executed += 1
                if dyn.taken:
                    summary.branches_taken += 1
                else:
                    summary.branches_not_taken += 1
        elif dyn.instr.is_jump:
            if not dyn.squashed or dyn.retired:
                summary.jump_instructions_executed += 1

        if dyn.squashed:
            summary.flushed_instructions_count += 1

    for ev in result.events:
        if ev.kind == "flush":
            summary.pipeline_flush_events += 1
        elif ev.kind == "control_stall":
            summary.control_related_stalls += 1

    return summary
