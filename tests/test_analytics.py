"""Unit tests for the microarchitectural analytics engine."""

import pytest

from simulator.analytics import (
    EventTracker,
    analyze_control_flow,
    analyze_forwarding,
    analyze_hazards,
    analyze_stalls,
    build_analytics_report,
)
from simulator.models import PipelineConfig
from simulator.parser import parse_program
from simulator.pipeline import PipelineSimulator


def test_hazard_analytics_raw_cascade():
    code = "ADD R1, R2, R3\nSUB R4, R1, R5\nAND R6, R4, R7"
    parsed = parse_program(code)

    # Forwarding ON
    sim_on = PipelineSimulator(PipelineConfig(forwarding=True))
    res_on = sim_on.run(parsed.instructions)
    haz_on = analyze_hazards(res_on)
    fwd_on = analyze_forwarding(res_on)
    stall_on = analyze_stalls(res_on)

    assert haz_on.static_raw_dependencies == 2
    assert haz_on.dynamic_raw_events == 2
    assert fwd_on.total_forwarding_events == 2
    assert stall_on.total_stall_cycles == 0

    # Forwarding OFF
    sim_off = PipelineSimulator(PipelineConfig(forwarding=False))
    res_off = sim_off.run(parsed.instructions)
    haz_off = analyze_hazards(res_off)
    stall_off = analyze_stalls(res_off)

    assert haz_off.dynamic_raw_events == 4
    assert stall_off.data_hazard_stall_cycles == 4
    assert stall_off.total_stall_cycles == 4


def test_load_use_hazard_analytics():
    code = "LW R1, 0(R2)\nADD R3, R1, R4"
    parsed = parse_program(code)

    sim = PipelineSimulator(PipelineConfig(forwarding=True))
    res = sim.run(parsed.instructions)
    rep = build_analytics_report(res)

    assert rep.hazard_summary.dynamic_load_use_events == 1
    assert rep.stall_summary.load_use_stall_cycles == 1
    assert rep.stall_summary.data_hazard_stall_cycles == 1
    assert rep.forwarding_summary.total_forwarding_events == 1
    assert rep.total_cycles == 7


def test_control_hazard_analytics():
    code = "ADDI R1, R0, 1\nBEQ R1, R1, target\nADD R2, R2, R2\ntarget: ADDI R3, R0, 42"
    parsed = parse_program(code)

    sim = PipelineSimulator(PipelineConfig(forwarding=True))
    res = sim.run(parsed.instructions)
    ctrl = analyze_control_flow(res)

    assert ctrl.total_branches_executed == 1
    assert ctrl.branches_taken == 1
    assert ctrl.pipeline_flush_events == 1
    assert ctrl.flushed_instructions_count == 2


def test_event_tracker_filtering():
    tracker = EventTracker()
    tracker.record(1, 1, "ADD R1, R2, R3", "RAW", "ID", register_dependency="R1")
    tracker.record(2, 2, "LW R2, 0(R1)", "Load-Use", "ID", register_dependency="R2")
    tracker.record(3, 3, "BEQ R1, R2, target", "Control (Branch)", "EX")

    assert len(tracker.events) == 3
    assert len(tracker.filter(hazard_type="RAW")) == 1
    assert len(tracker.filter(hazard_type="Control (Branch)")) == 1
    assert len(tracker.filter(search_query="target")) == 1
    assert len(tracker.filter(stage="ID")) == 2
