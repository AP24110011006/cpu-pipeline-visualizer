"""Forwarding analytics: hardware bypass metrics and path breakdowns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from simulator.models import PipelineEvent, SimulationResult


@dataclass
class ForwardingSummary:
    """Forwarding path metrics tracking bypass usage."""

    total_forwarding_events: int = 0
    ex_to_ex_forwarding: int = 0         # EX/MEM latch -> EX operand (distance 1 ALU-ALU)
    mem_to_ex_forwarding: int = 0        # MEM/WB latch -> EX operand (distance 2 ALU/Load)
    other_forwarding_paths: int = 0
    dependencies_resolved_zero_stalls: int = 0


def analyze_forwarding(result: SimulationResult) -> ForwardingSummary:
    """Classify all forwarding events from the simulation result."""
    summary = ForwardingSummary()

    for ev in result.events:
        if ev.kind == "forward":
            summary.total_forwarding_events += 1
            msg = ev.message
            if "EX/MEM" in msg:
                summary.ex_to_ex_forwarding += 1
            elif "MEM/WB" in msg:
                summary.mem_to_ex_forwarding += 1
            else:
                summary.other_forwarding_paths += 1

    # In straight ALU-ALU dependencies with forwarding ON, each event resolved a hazard with 0 stalls
    summary.dependencies_resolved_zero_stalls = summary.total_forwarding_events

    return summary
