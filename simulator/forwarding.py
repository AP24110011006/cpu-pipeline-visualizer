"""Forwarding (bypassing) logic.   (Member 5)

Idea: the result of an ALU instruction exists at the end of EX, long before it is
written back to the register file in WB. Forwarding sends it straight to the
instruction that needs it.

                    cycle:  1    2    3    4    5
    ADD R1,R2,R3            IF   ID   EX   MEM  WB
    SUB R4,R1,R5                 IF   ID   EX   MEM     <- needs R1 at the start of its EX

Two forwarding paths exist for an instruction that is in EX:
    EX/MEM  : result of the instruction that is now in MEM (1 instruction ahead)
    MEM/WB  : result of the instruction that is now in WB  (2 instructions ahead)

A *load* only has its value at the end of MEM, so the EX/MEM path cannot supply it;
that is why a load followed by a dependent instruction still needs one stall cycle.
(That stall decision is made by hazards.detect_data_stall.)

TODO (extension idea): forward into the MEM stage for store data (MEM-to-MEM copy).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from simulator.models import DynamicInstruction, Slot, is_real


class ForwardingError(RuntimeError):
    """Raised if forwarding is asked to use a value that does not exist yet.

    This signals a bug in the stall logic, so the verifier bot reports it loudly.
    """


@dataclass
class ForwardingDecision:
    register: int
    source_stage: str                  # "EX/MEM" or "MEM/WB"
    producer: DynamicInstruction
    value: int


def find_forwarding_source(register: int, mem_slot: Slot, wb_slot: Slot) -> Optional[ForwardingDecision]:
    """Look for a newer value of `register` than the one read in ID.

    mem_slot: instruction currently in MEM (its ALU result sits in the EX/MEM latch)
    wb_slot : instruction currently in WB  (its result sits in the MEM/WB latch)
    The nearer instruction (EX/MEM) wins because it holds the most recent value.
    """
    for path, slot in (("EX/MEM", mem_slot), ("MEM/WB", wb_slot)):
        if is_real(slot) and slot.instr.writes_register and slot.instr.dest == register:
            if slot.result is None:
                raise ForwardingError(
                    f"{slot.short_label} ({slot.instr.text}) has no result yet, "
                    f"so R{register} cannot be forwarded from {path}"
                )
            return ForwardingDecision(register, path, slot, slot.result)
    return None
