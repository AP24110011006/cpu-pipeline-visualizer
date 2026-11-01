"""Tests for simulator/engine.py and simulator/explainer.py."""

from simulator.engine import run_pipeline_engine
from simulator.explainer import explain_cycle
from simulator.models import PipelineConfig
from simulator.parser import parse_program
from simulator.pipeline import PipelineSimulator


def test_engine_successful_simulation():
    code = "ADD R1, R2, R3\nSUB R4, R1, R5"
    engine = run_pipeline_engine(
        code=code,
        init_regs_str="R2=5, R3=10, R5=2",
        init_mem_str="",
        config=PipelineConfig(forwarding=True),
    )
    assert engine.ok
    assert len(engine.program) == 2
    assert engine.primary is not None
    assert engine.primary.total_cycles == 6
    assert engine.metrics_primary.total_cycles == 6
    assert engine.reference is not None
    assert engine.reference.registers[1] == 15
    assert engine.reference.registers[4] == 13


def test_engine_compilation_errors():
    engine = run_pipeline_engine(
        code="INVALID_OP R1, R2\nADD R1",
        init_regs_str="invalid_reg",
        init_mem_str="",
        config=PipelineConfig(),
    )
    assert not engine.ok
    assert len(engine.errors) > 0


def test_explainer_generates_pedagogical_details():
    code = "ADD R1, R2, R3\nSUB R4, R1, R5\nAND R6, R4, R7"
    sim = PipelineSimulator(PipelineConfig(forwarding=False))
    parsed = parse_program(code)
    res = sim.run(parsed.instructions)

    # Cycle 1: Fetching first instruction
    exp1 = explain_cycle(res, 1)
    assert exp1.cycle == 1
    assert exp1.stages["IF"].status == "active"
    assert "ADD" in exp1.stages["IF"].instruction

    # Cycle 3: ADD is in EX, SUB is in ID (stalled waiting for R1)
    exp3 = explain_cycle(res, 3)
    assert exp3.stages["ID"].status == "stalled"
    assert exp3.stages["EX"].status == "active"
    assert exp3.hazard_summary is not None
    assert "Data Hazard" in exp3.hazard_summary

    # Cycle 4: ADD advances to MEM, stall bubble enters EX, SUB is still held in ID
    exp4 = explain_cycle(res, 4)
    assert exp4.stages["ID"].status == "stalled"
    assert exp4.stages["EX"].status in ("stalled", "bubble")


def test_explainer_handles_out_of_range():
    code = "NOP"
    sim = PipelineSimulator(PipelineConfig())
    res = sim.run(parse_program(code).instructions)

    exp_invalid = explain_cycle(res, 999)
    assert exp_invalid.stages == {}
    assert "No simulation data" in exp_invalid.simple_summary


def test_pipeline_view_explainer_integration():
    """Verify that all cycles in a complex program generate valid explainer objects without error."""
    code = "ADDI R1, R0, 10\nloop: ADDI R1, R1, -1\nBNE R1, R0, loop"
    engine = run_pipeline_engine(code, "", "", PipelineConfig())
    assert engine.ok
    primary = engine.primary

    for cycle in range(1, primary.total_cycles + 1):
        exp = explain_cycle(primary, cycle)
        assert exp.cycle == cycle
        assert exp.simple_summary != ""
        assert isinstance(exp.stages, dict)

