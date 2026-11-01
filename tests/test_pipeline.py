"""Tests for simulator/pipeline.py (Member 3) - the cycle-by-cycle engine."""

from simulator.models import BRANCH_STALL
from tests.helpers import SAMPLE, run, stage_of


def test_single_instruction_takes_five_cycles():
    result, metrics = run("ADD R1, R2, R3")
    assert metrics.total_cycles == 5
    assert [stage_of(result, 1, c) for c in range(1, 6)] == ["IF", "ID", "EX", "MEM", "WB"]


def test_independent_instructions_overlap_perfectly():
    result, metrics = run("ADD R1, R2, R3\nADD R4, R5, R6\nADD R7, R2, R3")
    assert metrics.total_cycles == 7                       # n + 4
    assert stage_of(result, 3, 5) == "EX" and stage_of(result, 1, 5) == "WB"


def test_each_stage_holds_at_most_one_instruction_per_cycle():
    result, _ = run(SAMPLE, forwarding=False)
    for snapshot in result.cycles:
        seqs = [s for s in snapshot.stage_seq.values() if s is not None]
        assert len(seqs) == len(set(seqs))


def test_computes_correct_values():
    result, _ = run(SAMPLE, registers="R2=10, R3=5, R5=2, R7=12")
    assert result.registers[1] == 15 and result.registers[4] == 13 and result.registers[6] == 12


def test_stall_holds_if_and_id_and_inserts_a_bubble():
    result, _ = run(SAMPLE, forwarding=False)
    stalled = [s for s in result.cycles if s.stalled]
    assert len(stalled) == 4
    assert result.cycles[2].stages["EX"].startswith("I1") or "bubble" in result.cycles[3].stages["EX"]
    assert any("bubble (stall)" in s.stages["EX"] for s in result.cycles)


def test_load_and_store_use_memory():
    result, _ = run("SW R5, 0(R2)\nLW R6, 0(R2)\nADD R7, R6, R6", registers="R2=100, R5=21")
    assert result.memory[100] == 21 and result.registers[6] == 21 and result.registers[7] == 42


def test_r0_stays_zero():
    result, _ = run("ADD R0, R1, R2", registers="R1=3, R2=4")
    assert result.registers[0] == 0


def test_taken_branch_flushes_wrong_path():
    result, metrics = run("BEQ R0, R0, skip\nADD R1, R1, R1\nADD R2, R2, R2\nskip: ADD R3, R3, R3")
    assert [d.squashed for d in result.instructions[1:3]] == [True, True]
    assert metrics.instructions_retired == 2 and metrics.total_cycles == 8
    assert result.registers[1] == 0 and result.registers[2] == 0 and result.registers[3] == 0


def test_branch_stall_policy_waits_even_when_not_taken():
    code = "BNE R0, R0, skip\nADD R1, R1, R1\nADD R2, R2, R2\nskip: ADD R3, R3, R3"
    _, predict = run(code)
    _, wait = run(code, branch_policy=BRANCH_STALL)
    assert predict.total_cycles == 8 and wait.total_cycles == 10


def test_jump_costs_one_slot():
    _, metrics = run("J end\nADD R1, R1, R1\nend: ADD R2, R2, R2")
    assert metrics.total_cycles == 7 and metrics.control_penalty_cycles == 1


def test_loop_runs_the_right_number_of_times():
    result, metrics = run("ADDI R1, R0, 3\nloop: ADDI R2, R2, 10\nADDI R1, R1, -1\nBNE R1, R0, loop")
    assert result.registers[2] == 30 and result.registers[1] == 0
    assert metrics.instructions_retired == 1 + 3 * 3


def test_endless_loop_stops_at_cycle_limit():
    result, _ = run("loop: J loop", max_cycles=40)
    assert result.truncated and result.total_cycles == 40


def test_register_write_timing_option():
    code = "ADD R1, R2, R3\nADD R8, R5, R6\nADD R9, R5, R6\nSUB R4, R1, R5"
    _, first_half = run(code, forwarding=False, reg_write_first_half=True)
    _, late = run(code, forwarding=False, reg_write_first_half=False)
    assert first_half.data_stall_cycles == 0 and late.data_stall_cycles == 1
