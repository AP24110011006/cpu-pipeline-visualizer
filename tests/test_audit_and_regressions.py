"""Audit regression tests covering edge cases and architectural invariants.

Tests:
- NoneType CPI formatting safety in empty/non-retiring runs
- Explainer next-cycle preview bubble filtering
- WAW register overwriting in DAG schedule scoring
- Large workload scalability (5,000 instructions)
- Combined control-flow + data-hazard loops
- Memory alias ordering across address patterns
- State isolation between consecutive runs
"""

from __future__ import annotations

import pytest

from bots.dev_bot import DevBot, _score_schedule, optimize_schedule
from simulator.engine import run_pipeline_engine
from simulator.explainer import explain_cycle
from simulator.models import PipelineConfig
from simulator.parser import parse_program
from simulator.pipeline import PipelineSimulator
from simulator.reference import run_reference
from tests.benchmark import generate_benchmark_program


def test_compare_tab_cpi_none_safety():
    """Verify metrics and formatting when 0 instructions retire (e.g. cycle limit hit before first retirement)."""
    code = "ADD R1, R2, R3\nADD R4, R5, R6"
    engine = run_pipeline_engine(
        code=code,
        init_regs_str="",
        init_mem_str="",
        config=PipelineConfig(max_cycles=3),
    )
    assert engine.ok
    assert engine.primary.truncated
    assert engine.metrics_primary.instructions_retired == 0
    assert engine.metrics_primary.cpi is None

    # Verify formatting logic produces safe strings without TypeError
    cpi_str = f"{engine.metrics_primary.cpi:.2f}" if engine.metrics_primary.cpi is not None else "n/a"
    assert cpi_str == "n/a"


def test_explainer_bubble_advance_safety():
    """Ensure bubbles are never reported as real instructions advancing stages in preview."""
    # BEQ stall policy causes 'bubble (waiting for branch)' to enter pipeline
    code = "BEQ R0, R0, target\nADD R1, R2, R3\ntarget:\nNOP"
    config = PipelineConfig(branch_policy="stall")
    sim = PipelineSimulator(config)
    res = sim.run(parse_program(code).instructions)

    for cycle in range(1, res.total_cycles + 1):
        exp = explain_cycle(res, cycle)
        if exp.next_cycle_preview:
            assert "bubble" not in exp.next_cycle_preview.lower(), (
                f"Cycle {cycle} reported bubble advancing: {exp.next_cycle_preview}"
            )


def test_waw_shadow_raw_distance2_penalty():
    """Verify that if distance-1 and distance-2 both write the same register (WAW),

    only the nearer producer (distance 1) is penalized.
    """
    code = "ADDI R1, R0, 1\nADDI R1, R0, 2\nADD R2, R1, R0"
    parsed = parse_program(code)
    assert parsed.ok
    block = parsed.instructions
    # Original schedule: 0 -> 1 -> 2
    # At index 2 (ADD R2, R1, R0): prev1 is ADDI R1, R0, 2; prev2 is ADDI R1, R0, 1
    # Because prev1 overwrote R1, distance 2 should not add an extra penalty for R1
    score = _score_schedule([0, 1, 2], block)
    load_use_stalls, raw_stalls, _ = score
    # RAW stalls without forwarding should be 2 (from distance-1 prev1), not 3
    assert raw_stalls == 2


def test_large_workload_5000_instructions():
    """Verify simulator and parser handle 5,000 instructions accurately and stably."""
    code = generate_benchmark_program(5000)
    parsed = parse_program(code, max_instructions=10000)
    assert parsed.ok
    assert len(parsed.instructions) == 5000

    config = PipelineConfig(forwarding=True, max_cycles=20000)
    sim = PipelineSimulator(config)
    result = sim.run(parsed.instructions)
    assert not result.truncated
    assert result.total_cycles == 5004

    # Verify final registers match reference CPU
    ref = run_reference(parsed.instructions, max_steps=20000)
    assert not ref.truncated
    assert result.registers == ref.registers


def test_control_flow_with_tight_hazards_and_branches():
    """Complex multi-iteration loop with load-use hazard inside loop body."""
    code = (
        "ADDI R1, R0, 5\n"       # Loop counter = 5
        "ADDI R2, R0, 0\n"       # Sum = 0
        "ADDI R3, R0, 100\n"     # Memory base
        "loop:\n"
        "SW R1, 0(R3)\n"         # Store counter to memory
        "LW R4, 0(R3)\n"         # Load-use hazard
        "ADD R2, R2, R4\n"       # Consumer (stalls 1 cycle with forwarding)
        "ADDI R1, R1, -1\n"      # Decrement
        "BNE R1, R0, loop\n"     # Branch back
        "SW R2, 4(R3)\n"         # Store final sum at 104
    )
    parsed = parse_program(code)
    assert parsed.ok

    # Pipelined execution
    sim = PipelineSimulator(PipelineConfig(forwarding=True))
    p_res = sim.run(parsed.instructions)
    assert not p_res.truncated

    # Sequential reference execution
    r_res = run_reference(parsed.instructions)
    assert not r_res.truncated

    # Final register and memory match
    assert p_res.registers == r_res.registers
    assert p_res.memory == r_res.memory
    # Sum should be 5 + 4 + 3 + 2 + 1 = 15 stored at address 104
    assert p_res.memory[104] == 15


def test_memory_aliasing_complex_patterns():
    """Verify optimizer strictly preserves memory ordering across distinct pointers."""
    code = (
        "ADDI R1, R0, 100\n"
        "ADDI R2, R0, 42\n"
        "SW R2, 0(R1)\n"
        "LW R3, 0(R1)\n"
        "ADDI R4, R3, 1\n"
        "SW R4, 0(R1)\n"
        "LW R5, 0(R1)\n"
    )
    opt_code, opt_info = optimize_schedule(code)
    assert opt_info["ok"]
    assert opt_info["verified"]

    # Verify reference CPU produces exact same memory and registers
    parsed_orig = parse_program(code)
    parsed_opt = parse_program(opt_code)
    ref_orig = run_reference(parsed_orig.instructions)
    ref_opt = run_reference(parsed_opt.instructions)
    assert ref_orig.registers == ref_opt.registers
    assert ref_orig.memory == ref_opt.memory


def test_state_isolation_between_consecutive_runs():
    """Confirm consecutive simulation runs do not leak mutable state across executions."""
    code1 = "ADDI R1, R0, 999\nSW R1, 0(R0)"
    code2 = "ADD R2, R0, R0\nLW R3, 0(R0)"

    engine1 = run_pipeline_engine(code1, "", "", PipelineConfig())
    engine2 = run_pipeline_engine(code2, "", "", PipelineConfig())

    assert engine1.primary.registers[1] == 999
    assert engine1.primary.memory[0] == 999

    # In engine2, initial memory was empty and R1 was never set
    assert engine2.primary.registers[1] == 0
    assert engine2.primary.registers[3] == 0
    assert 0 not in engine2.primary.memory


def test_advanced_array_stress_pipeline_execution():
    """Verify the user's Advanced Array Processing & Loop stress test executes accurately."""
    from simulator.samples import SAMPLES

    stress_sample = SAMPLES["Advanced Stress Test: Array Processing & Loop"]
    engine = run_pipeline_engine(
        code=stress_sample.code,
        init_regs_str="",
        init_mem_str="",
        config=PipelineConfig(forwarding=True),
    )

    assert engine.ok, f"Compilation errors: {engine.errors}"
    assert not engine.primary.truncated, "Execution should not truncate under 500 cycles"
    assert engine.primary.total_cycles == 135
    assert len(engine.primary.instructions) == 126

    # Verify algorithmic correctness:
    # 5 array elements: 10, 20, 30, 40, 50
    # Sum in R4: 150
    # Even count in R6: 5
    # R15 = R4 + R6 = 155
    # Memory[120] = R4 = 150
    # Memory[124] = R6 = 5
    # Memory[128] = R15 = 155
    # Final dependency chain R27 = 165
    assert engine.primary.registers[4] == 150
    assert engine.primary.registers[6] == 5
    assert engine.primary.registers[15] == 155
    assert engine.primary.registers[27] == 165
    assert engine.primary.memory[120] == 150
    assert engine.primary.memory[124] == 5
    assert engine.primary.memory[128] == 155

    # Parity check against Reference CPU
    assert engine.primary.registers == engine.reference.registers
    assert engine.primary.memory == engine.reference.memory

    # Forwarding comparison: Forwarding OFF must be slower due to RAW stalls
    assert engine.off.total_cycles > engine.on.total_cycles
    assert engine.metrics_off.data_stall_cycles > engine.metrics_on.data_stall_cycles
