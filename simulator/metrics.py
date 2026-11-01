"""Performance metrics.   (Member 7)

All numbers are *measured from a finished simulation* - nothing is estimated or hard-coded.

Definitions
    total cycles        clock cycles from the first fetch to the last write-back
    instructions        dynamic instructions that reached WB (flushed ones do not count)
    CPI                 cycles per instruction = total cycles / instructions
    ideal cycles        instructions + 4   (a hazard-free pipeline needs 4 cycles to fill)
    data stall cycles   cycles in which the instruction in ID had to wait (RAW hazards)
    control penalty     extra cycles = total - ideal - data stalls (wasted fetches after branches/jumps)
    efficiency          ideal cycles / total cycles  (1.0 = no hazards at all)
    speedup             (5 x instructions) / total cycles, compared with a CPU that finishes one
                        whole instruction (5 cycles) before starting the next
    utilization         share of cycles a stage held a *useful* (not stalled, not flushed) instruction
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from simulator.models import STAGES, SimulationResult


@dataclass
class PerformanceMetrics:
    total_cycles: int
    instructions_retired: int
    squashed_instructions: int
    cpi: Optional[float]
    ipc: Optional[float]
    ideal_cycles: int
    data_stall_cycles: int
    control_penalty_cycles: int
    forwarding_events: int
    efficiency: Optional[float]
    non_pipelined_cycles: int
    speedup_vs_non_pipelined: Optional[float]
    stage_utilization: Dict[str, float]

    def as_rows(self) -> Dict[str, object]:
        """Flat dictionary used for tables."""
        return {
            "Total cycles": self.total_cycles,
            "Instructions completed": self.instructions_retired,
            "CPI": None if self.cpi is None else round(self.cpi, 3),
            "IPC": None if self.ipc is None else round(self.ipc, 3),
            "Ideal cycles (no hazards)": self.ideal_cycles,
            "Data stall cycles": self.data_stall_cycles,
            "Control penalty cycles": self.control_penalty_cycles,
            "Forwarding events": self.forwarding_events,
            "Pipeline efficiency": None if self.efficiency is None else round(self.efficiency, 3),
            "Non-pipelined cycles": self.non_pipelined_cycles,
            "Speedup vs non-pipelined": None if self.speedup_vs_non_pipelined is None
            else round(self.speedup_vs_non_pipelined, 3),
        }


def compute_metrics(result: SimulationResult) -> PerformanceMetrics:
    """Compute every metric from a finished SimulationResult."""
    total = result.total_cycles
    retired = sum(1 for dyn in result.instructions if dyn.retired)
    squashed = sum(1 for dyn in result.instructions if dyn.squashed)
    data_stalls = len(result.events_of("stall"))
    forwards = len(result.events_of("forward"))
    ideal = retired + 4 if retired else 0
    control_penalty = max(0, total - ideal - data_stalls) if retired else 0

    useful = {stage: 0 for stage in STAGES}
    for dyn in result.instructions:
        if dyn.squashed:
            continue
        for _cycle, stage, state in dyn.history:
            if state == "normal":
                useful[stage] += 1
    utilization = {stage: (useful[stage] / total if total else 0.0) for stage in STAGES}

    return PerformanceMetrics(
        total_cycles=total,
        instructions_retired=retired,
        squashed_instructions=squashed,
        cpi=(total / retired) if retired else None,
        ipc=(retired / total) if total else None,
        ideal_cycles=ideal,
        data_stall_cycles=data_stalls,
        control_penalty_cycles=control_penalty,
        forwarding_events=forwards,
        efficiency=(ideal / total) if total and retired else None,
        non_pipelined_cycles=5 * retired,
        speedup_vs_non_pipelined=(5 * retired / total) if total and retired else None,
        stage_utilization=utilization,
    )
