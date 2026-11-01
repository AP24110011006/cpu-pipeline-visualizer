"""Hazard analytics: dynamic and static hazard calculations with zero double counting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from simulator.hazards import find_raw_hazards
from simulator.models import DynamicInstruction, Instruction, SimulationResult


@dataclass
class HazardSummary:
    """Rigorous hazard metrics with unambiguous distinction between static and dynamic counts."""

    # Dynamic counts
    dynamic_raw_events: int = 0         # Instances where an instruction in ID needed an in-flight register
    dynamic_load_use_events: int = 0    # Instances where producer was LW in EX
    dynamic_control_hazard_events: int = 0 # Branch taken or jump requiring PC redirection
    branch_hazard_events: int = 0       # Branches that redirected execution
    jump_hazard_events: int = 0         # Jumps that redirected execution

    # Static counts
    static_raw_dependencies: int = 0    # Total static RAW pairs in program text
    unique_static_raw_pairs: List[Tuple[int, int, int]] = field(default_factory=list) # (consumer, producer, reg)


def analyze_hazards(result: SimulationResult) -> HazardSummary:
    """Analyze static dependencies and dynamic hazard events from simulation trace."""
    summary = HazardSummary()

    # 1. Static RAW dependencies
    static_hazards = find_raw_hazards(result.program, result.config.reg_write_first_half)
    summary.static_raw_dependencies = len(static_hazards)
    summary.unique_static_raw_pairs = [
        (h.consumer_index, h.producer_index, h.register) for h in static_hazards
    ]

    # 2. Dynamic analysis from events
    for ev in result.events:
        if ev.kind == "stall":
            # Data hazard stall
            summary.dynamic_raw_events += 1
            if "load-use" in ev.message.lower() or "load only has" in ev.message.lower():
                summary.dynamic_load_use_events += 1
        elif ev.kind == "forward":
            # RAW dependency resolved dynamically via forwarding
            summary.dynamic_raw_events += 1
        elif ev.kind == "flush":
            summary.dynamic_control_hazard_events += 1
            if "branch" in ev.message.lower():
                summary.branch_hazard_events += 1
            elif "jump" in ev.message.lower():
                summary.jump_hazard_events += 1

    return summary
