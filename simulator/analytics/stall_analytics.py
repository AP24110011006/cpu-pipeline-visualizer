"""Stall analytics: distinguishing stall events, stall cycles, and avoided stalls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from simulator.models import PipelineEvent, SimulationResult


@dataclass
class StallSummary:
    """Comprehensive stall metrics distinguishing events from clock cycles."""

    total_stall_events: int = 0         # Number of distinct stall occurrences triggered
    total_stall_cycles: int = 0         # Total cycles where the pipeline stalled (ID/IF held)
    data_hazard_stall_cycles: int = 0   # Cycles stalled due to RAW dependencies
    load_use_stall_cycles: int = 0      # Cycles stalled specifically due to load-use dependencies
    control_stall_cycles: int = 0       # Cycles stalled due to control hazards (e.g. stall policy)
    stalls_avoided_forwarding: int = 0  # Stalls eliminated thanks to hardware bypass paths


def analyze_stalls(
    result: SimulationResult,
    reference_off_result: Optional[SimulationResult] = None,
) -> StallSummary:
    """Extract stall metrics from a simulation run."""
    summary = StallSummary()

    # Track consecutive stall cycles to count discrete stall events
    in_data_stall = False
    in_control_stall = False

    for ev in result.events:
        if ev.kind == "stall":
            summary.data_hazard_stall_cycles += 1
            summary.total_stall_cycles += 1
            if "load-use" in ev.message.lower() or "load only has" in ev.message.lower():
                summary.load_use_stall_cycles += 1
        elif ev.kind == "control_stall":
            summary.control_stall_cycles += 1
            summary.total_stall_cycles += 1

    # Discrete events count
    for snap in result.cycles:
        if snap.stalled:
            if not in_data_stall:
                summary.total_stall_events += 1
                in_data_stall = True
        else:
            in_data_stall = False

    # Avoided stalls: if result is with forwarding ON and reference_off_result is available
    if reference_off_result is not None:
        off_stalls = sum(1 for ev in reference_off_result.events if ev.kind == "stall")
        on_stalls = summary.data_hazard_stall_cycles
        summary.stalls_avoided_forwarding = max(0, off_stalls - on_stalls)

    return summary
