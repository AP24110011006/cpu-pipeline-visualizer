"""Tests for simulator/metrics.py (Member 7)."""

from tests.helpers import SAMPLE, run


def test_cpi_and_efficiency_without_forwarding():
    _, m = run(SAMPLE, forwarding=False)
    assert m.total_cycles == 11 and m.instructions_retired == 3
    assert abs(m.cpi - 11 / 3) < 1e-9
    assert m.ideal_cycles == 7 and abs(m.efficiency - 7 / 11) < 1e-9
    assert m.non_pipelined_cycles == 15 and abs(m.speedup_vs_non_pipelined - 15 / 11) < 1e-9


def test_perfect_pipeline_metrics():
    _, m = run("ADD R1, R2, R3\nADD R4, R5, R6\nADD R7, R2, R3")
    assert m.efficiency == 1.0 and m.data_stall_cycles == 0 and m.control_penalty_cycles == 0


def test_extra_cycles_are_fully_explained():
    _, m = run("ADDI R1, R0, 3\nloop: ADDI R1, R1, -1\nBNE R1, R0, loop\nNOP")
    assert m.total_cycles == m.ideal_cycles + m.data_stall_cycles + m.control_penalty_cycles


def test_flushed_instructions_do_not_count_as_completed():
    _, m = run("BEQ R0, R0, skip\nADD R1, R1, R1\nADD R2, R2, R2\nskip: NOP")
    assert m.instructions_retired == 2 and m.squashed_instructions == 2


def test_utilization_is_between_zero_and_one():
    _, m = run(SAMPLE, forwarding=False)
    assert all(0 <= value <= 1 for value in m.stage_utilization.values())
    assert m.stage_utilization["WB"] == 3 / 11


def test_metrics_never_invent_numbers_for_empty_runs():
    from simulator.metrics import compute_metrics
    from simulator.pipeline import PipelineSimulator
    m = compute_metrics(PipelineSimulator().run([]))
    assert m.total_cycles == 0 and m.cpi is None and m.speedup_vs_non_pipelined is None
