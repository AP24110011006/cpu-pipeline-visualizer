"""Tests for simulator/hazards.py (Member 4): RAW detection, stalls and bubbles."""

from simulator.hazards import find_control_instructions, find_raw_hazards
from simulator.parser import parse_program
from tests.helpers import SAMPLE, run


def hazards_of(code, **kwargs):
    return find_raw_hazards(parse_program(code).instructions, **kwargs)


def test_sample_has_two_adjacent_raw_hazards():
    found = hazards_of(SAMPLE)
    assert [(h.producer_index, h.consumer_index, h.register, h.distance) for h in found] == [(0, 1, 1, 1), (1, 2, 4, 1)]
    assert all(h.stalls_without_forwarding == 2 and h.stalls_with_forwarding == 0 for h in found)


def test_distance_decides_stall_count():
    found = hazards_of("ADD R1, R2, R3\nNOP\nSUB R4, R1, R5\nNOP\nNOP\nSUB R6, R1, R5")
    by_distance = {h.distance: h.stalls_without_forwarding for h in found}
    assert by_distance == {2: 1}                         # distance 5 is too far to matter
    far = hazards_of("ADD R1, R2, R3\nNOP\nNOP\nSUB R4, R1, R5")
    assert far[0].distance == 3 and far[0].stalls_without_forwarding == 0


def test_load_use_needs_a_stall_even_with_forwarding():
    found = hazards_of("LW R1, 0(R2)\nADD R3, R1, R4")
    assert found[0].kind == "Load-use" and found[0].stalls_with_forwarding == 1


def test_r0_and_unrelated_registers_do_not_create_hazards():
    assert hazards_of("ADD R0, R1, R2\nADD R3, R0, R0") == []
    assert hazards_of("ADD R1, R2, R3\nADD R4, R5, R6") == []


def test_nearest_producer_only():
    found = hazards_of("ADD R1, R2, R3\nADD R1, R4, R5\nSUB R6, R1, R7")
    assert [(h.producer_index, h.consumer_index) for h in found] == [(1, 2)]


def test_simulation_stalls_match_static_prediction_for_isolated_hazards():
    _, metrics = run("ADD R1, R2, R3\nSUB R4, R1, R5", forwarding=False)
    assert metrics.data_stall_cycles == 2
    _, metrics = run("LW R1, 0(R2)\nADD R3, R1, R4", forwarding=True)
    assert metrics.data_stall_cycles == 1


def test_stall_events_explain_the_hazard():
    result, _ = run(SAMPLE, forwarding=False)
    stalls = result.events_of("stall")
    assert len(stalls) == 4 and stalls[0].consumer == 2 and stalls[0].producer == 1 and stalls[0].register == 1
    assert "R1" in stalls[0].message


def test_control_instruction_listing():
    program = parse_program("a: ADD R1, R1, R1\nBEQ R1, R2, a\nJ a").instructions
    assert [i.opcode for i in find_control_instructions(program)] == ["BEQ", "J"]
