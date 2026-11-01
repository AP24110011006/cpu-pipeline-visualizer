"""Arithmetic shared by the pipeline engine and the sequential reference model.

Keeping the ALU in one place guarantees that both models agree on what an
instruction *means*; the pipeline tests then only have to prove that the
*timing machinery* (stalls, forwarding, flushes) never changes the answer.
"""

from __future__ import annotations

from typing import Sequence

from simulator.models import I_TYPE_OPCODES, Instruction

_ALU_BASE = {"ADDI": "ADD", "ANDI": "AND", "ORI": "OR", "XORI": "XOR", "SLTI": "SLT"}


def to_signed32(value: int) -> int:
    """Wrap a Python int into a signed 32-bit integer (like real hardware)."""
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & 0x80000000 else value


def alu(operation: str, a: int, b: int) -> int:
    """Perform one ALU operation on two signed 32-bit values."""
    if operation == "ADD":
        result = a + b
    elif operation == "SUB":
        result = a - b
    elif operation == "AND":
        result = a & b
    elif operation == "OR":
        result = a | b
    elif operation == "XOR":
        result = a ^ b
    elif operation == "SLT":
        result = 1 if a < b else 0
    else:
        raise ValueError(f"Unknown ALU operation: {operation}")
    return to_signed32(result)


def compute_alu_result(instr: Instruction, values: Sequence[int]) -> int:
    """Result of an R-type or I-type instruction given its source values."""
    a = values[0]
    b = instr.imm if instr.opcode in I_TYPE_OPCODES else values[1]
    return alu(_ALU_BASE.get(instr.opcode, instr.opcode), a, b)


def branch_is_taken(opcode: str, a: int, b: int) -> bool:
    """Evaluate a BEQ / BNE condition."""
    return a == b if opcode == "BEQ" else a != b
