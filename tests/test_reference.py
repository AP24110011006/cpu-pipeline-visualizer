"""Tests for the sequential reference CPU used as the answer key."""

from simulator.parser import parse_program
from simulator.reference import run_reference


def test_reference_executes_a_loop():
    program = parse_program("ADDI R1, R0, 4\nloop: ADDI R2, R2, 5\nADDI R1, R1, -1\nBNE R1, R0, loop").instructions
    result = run_reference(program)
    assert result.registers[2] == 20 and result.registers[1] == 0 and result.executed == 1 + 4 * 3


def test_reference_detects_endless_loop():
    result = run_reference(parse_program("a: J a").instructions, max_steps=50)
    assert result.truncated


def test_reference_memory_and_r0():
    program = parse_program("SW R5, 4(R2)\nLW R6, 4(R2)\nADD R0, R6, R6").instructions
    result = run_reference(program, {2: 100, 5: 7})
    assert result.memory[104] == 7 and result.registers[6] == 7 and result.registers[0] == 0


def test_signed_32_bit_wraparound():
    program = parse_program("ADD R3, R1, R2").instructions
    assert run_reference(program, {1: 2**31 - 1, 2: 1}).registers[3] == -(2**31)
