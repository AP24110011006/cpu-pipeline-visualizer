"""Unified report builder compiling complete hazard, stall, and performance analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from simulator.analytics.control_analytics import ControlSummary, analyze_control_flow
from simulator.analytics.event_tracker import DetailedPipelineEvent, EventTracker
from simulator.analytics.forwarding_analytics import ForwardingSummary, analyze_forwarding
from simulator.analytics.hazard_analytics import HazardSummary, analyze_hazards
from simulator.analytics.stall_analytics import StallSummary, analyze_stalls
from simulator.metrics import PerformanceMetrics, compute_metrics
from simulator.models import STAGES, SimulationResult


@dataclass
class PipelineAnalyticsReport:
    """Full comprehensive analytics suite combining all microarchitectural telemetry."""

    hazard_summary: HazardSummary
    stall_summary: StallSummary
    forwarding_summary: ForwardingSummary
    control_summary: ControlSummary
    performance_metrics: PerformanceMetrics
    event_history: List[DetailedPipelineEvent] = field(default_factory=list)

    # General pipeline slot statistics
    total_cycles: int = 0
    total_dynamic_instructions: int = 0
    total_retired_instructions: int = 0
    total_squashed_instructions: int = 0
    total_pipeline_slots: int = 0
    total_bubble_slots: int = 0
    total_useful_slots: int = 0
    pipeline_stage_slots: Dict[str, int] = field(default_factory=dict)
    stage_utilization_pct: Dict[str, float] = field(default_factory=dict)

    def to_summary_dict(self) -> Dict[str, Any]:
        """Dictionary of top-level metrics for cards and dashboard badges."""
        return {
            "Dynamic RAW Events": self.hazard_summary.dynamic_raw_events,
            "Unique Static RAW Dependencies": self.hazard_summary.static_raw_dependencies,
            "Load-Use Events": self.hazard_summary.dynamic_load_use_events,
            "Control Hazard Events": self.hazard_summary.dynamic_control_hazard_events,
            "Total Stall Events": self.stall_summary.total_stall_events,
            "Total Stall Cycles": self.stall_summary.total_stall_cycles,
            "Data Stall Cycles": self.stall_summary.data_hazard_stall_cycles,
            "Control Stall Cycles": self.stall_summary.control_stall_cycles,
            "Stalls Avoided (Forwarding)": self.stall_summary.stalls_avoided_forwarding,
            "Total Forwarding Events": self.forwarding_summary.total_forwarding_events,
            "EX-to-EX Forwarding": self.forwarding_summary.ex_to_ex_forwarding,
            "MEM-to-EX Forwarding": self.forwarding_summary.mem_to_ex_forwarding,
            "Total Branches": self.control_summary.total_branches_executed,
            "Branches Taken": self.control_summary.branches_taken,
            "Branches Not Taken": self.control_summary.branches_not_taken,
            "Total Jumps": self.control_summary.jump_instructions_executed,
            "Pipeline Flushes": self.control_summary.pipeline_flush_events,
            "Flushed Instructions": self.control_summary.flushed_instructions_count,
            "Total Cycles": self.total_cycles,
            "CPI": self.performance_metrics.cpi,
            "IPC": self.performance_metrics.ipc,
            "Efficiency": self.performance_metrics.efficiency,
            "Speedup vs Unpipelined": self.performance_metrics.speedup_vs_non_pipelined,
        }


def build_analytics_report(
    result: SimulationResult,
    reference_off_result: Optional[SimulationResult] = None,
) -> PipelineAnalyticsReport:
    """Compile a full analytics report from a finished simulation."""
    hazard_sum = analyze_hazards(result)
    stall_sum = analyze_stalls(result, reference_off_result)
    fwd_sum = analyze_forwarding(result)
    ctrl_sum = analyze_control_flow(result)
    perf_metrics = compute_metrics(result)

    # Calculate exact stage slots & bubbles
    total_cycles = result.total_cycles
    total_slots = total_cycles * len(STAGES)
    useful_count = 0
    stage_slots = {stage: 0 for stage in STAGES}

    for dyn in result.instructions:
        if dyn.squashed:
            continue
        for _cycle, stage, state in dyn.history:
            if state == "normal":
                useful_count += 1
                stage_slots[stage] += 1

    bubble_count = max(0, total_slots - useful_count)
    utilization_pct = {
        stage: (stage_slots[stage] / total_cycles * 100.0 if total_cycles > 0 else 0.0)
        for stage in STAGES
    }

    # Build event history
    tracker = EventTracker()
    for ev in result.events:
        instr_text = ""
        dyn_item = None
        if ev.consumer:
            for d in result.instructions:
                if d.seq == ev.consumer:
                    dyn_item = d
                    instr_text = d.instr.text
                    break

        hazard_type = "None"
        resolution = "Normal"
        fwd_path = None
        stalls = 0

        if ev.kind == "stall":
            hazard_type = "Load-Use" if "load-use" in ev.message.lower() else "RAW"
            resolution = "Stall (Bubble inserted)"
            stalls = 1
        elif ev.kind == "forward":
            hazard_type = "RAW"
            fwd_path = "EX/MEM -> EX" if "EX/MEM" in ev.message else "MEM/WB -> EX"
            resolution = f"Forwarded via {fwd_path}"
        elif ev.kind == "flush":
            hazard_type = "Control (Branch)" if "branch" in ev.message.lower() else "Control (Jump)"
            resolution = "Pipeline Flush (Wrong path squashed)"
        elif ev.kind == "control_stall":
            hazard_type = "Control (Branch Wait)"
            resolution = "Branch Delay Stall"
            stalls = 1

        tracker.record(
            cycle=ev.cycle,
            instruction_seq=ev.consumer or (dyn_item.seq if dyn_item else 0),
            instruction_text=instr_text or (dyn_item.instr.text if dyn_item else "—"),
            hazard_type=hazard_type,
            stage="ID" if ev.kind in ("stall", "control_stall") else ("EX" if ev.kind == "forward" else "ID/IF"),
            producer_seq=ev.producer,
            consumer_seq=ev.consumer,
            register_dependency=f"R{ev.register}" if ev.register is not None else None,
            resolution_method=resolution,
            stall_cycles=stalls,
            forwarding_path=fwd_path,
            notes=ev.message,
        )

    return PipelineAnalyticsReport(
        hazard_summary=hazard_sum,
        stall_summary=stall_sum,
        forwarding_summary=fwd_sum,
        control_summary=ctrl_sum,
        performance_metrics=perf_metrics,
        event_history=tracker.events,
        total_cycles=total_cycles,
        total_dynamic_instructions=len(result.instructions),
        total_retired_instructions=perf_metrics.instructions_retired,
        total_squashed_instructions=perf_metrics.squashed_instructions,
        total_pipeline_slots=total_slots,
        total_bubble_slots=bubble_count,
        total_useful_slots=useful_count,
        pipeline_stage_slots=stage_slots,
        stage_utilization_pct=utilization_pct,
    )
