"""Tests for simulator/forwarding.py (Member 5)."""

from simulator.forwarding import ForwardingError, find_forwarding_source
from simulator.models import EMPTY, DynamicInstruction
from simulator.parser import parse_program
from tests.helpers import SAMPLE, run


def dyn(code, seq=1, result=None):
    d = DynamicInstruction(seq=seq, instr=parse_program(code).instructions[0], fetch_cycle=1)
    d.result = result
    return d


def test_forwarding_removes_alu_stalls():
    _, off = run(SAMPLE, forwarding=False)
    _, on = run(SAMPLE, forwarding=True)
    assert (off.total_cycles, on.total_cycles) == (11, 7)
    assert on.data_stall_cycles == 0 and on.forwarding_events == 2


def test_forwarding_sources_and_priority():
    newer = dyn("ADD R1, R2, R3", seq=2, result=99)       # in MEM (EX/MEM latch)
    older = dyn("ADD R1, R2, R3", seq=1, result=5)        # in WB  (MEM/WB latch)
    decision = find_forwarding_source(1, newer, older)
    assert decision.source_stage == "EX/MEM" and decision.value == 99
    assert find_forwarding_source(1, EMPTY, older).source_stage == "MEM/WB"
    assert find_forwarding_source(4, newer, older) is None


def test_load_value_cannot_be_forwarded_from_mem_stage():
    load_in_mem = dyn("LW R1, 0(R2)", result=None)
    try:
        find_forwarding_source(1, load_in_mem, EMPTY)
    except ForwardingError:
        return
    raise AssertionError("expected ForwardingError")


def test_load_use_costs_exactly_one_stall_with_forwarding():
    result, metrics = run("LW R1, 0(R2)\nADD R3, R1, R4\nSUB R5, R3, R4", registers="R2=100, R4=1")
    assert metrics.data_stall_cycles == 1
    assert result.events_of("stall")[0].register == 1


def test_forwarded_values_are_correct():
    result, _ = run("ADD R1, R2, R3\nADD R4, R1, R1\nADD R5, R4, R1", registers="R2=1, R3=2")
    assert result.registers[1] == 3 and result.registers[4] == 6 and result.registers[5] == 9


def test_newest_value_wins_when_register_is_rewritten():
    result, _ = run("ADDI R1, R0, 1\nADDI R1, R0, 2\nADD R2, R1, R1")
    assert result.registers[2] == 4
