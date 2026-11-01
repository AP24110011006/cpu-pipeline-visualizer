"""A deliberately simple, NON-pipelined CPU used as the "answer key".

It executes one instruction completely before starting the next. Because it has no
stages, stalls or forwarding, it cannot get hazards wrong. The verifier bot runs the
same program on the pipeline and on this model and compares the final registers and
memory - if they differ, the pipeline has a bug.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from simulator.execute import branch_is_taken, compute_alu_result, to_signed32
from simulator.models import Instruction


@dataclass
class ReferenceResult:
    registers: List[int]
    memory: Dict[int, int]
    executed: int                 # dynamic instruction count
    truncated: bool = False       # True if max_steps was reached (probably an infinite loop)


def run_reference(
    program: List[Instruction],
    initial_registers: Optional[Dict[int, int]] = None,
    initial_memory: Optional[Dict[int, int]] = None,
    max_steps: int = 20000,
) -> ReferenceResult:
    registers = [0] * 32
    for number, value in (initial_registers or {}).items():
        if 0 < number < 32:
            registers[number] = to_signed32(value)
    memory = {address: to_signed32(value) for address, value in (initial_memory or {}).items()}

    pc = 0
    executed = 0
    truncated = False
    while 0 <= pc < len(program):
        if executed >= max_steps:
            truncated = True
            break
        instr = program[pc]
        executed += 1
        next_pc = pc + 1
        values = [registers[number] for number in instr.sources]

        if instr.is_load:
            registers[instr.dest] = memory.get(values[0] + instr.imm, 0)
        elif instr.is_store:
            memory[values[0] + instr.imm] = values[1]
        elif instr.is_branch:
            if branch_is_taken(instr.opcode, values[0], values[1]):
                next_pc = instr.target
        elif instr.is_jump:
            next_pc = instr.target
        elif instr.opcode == "NOP":
            pass
        else:
            registers[instr.dest] = compute_alu_result(instr, values)
        registers[0] = 0                          # R0 can never change
        pc = next_pc
    return ReferenceResult(registers, memory, executed, truncated)
