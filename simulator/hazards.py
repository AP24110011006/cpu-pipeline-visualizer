"""Hazard detection.   (Member 4: data hazards, stalls, bubbles)

Data hazard (RAW = Read After Write)
    An instruction needs a register that an earlier, still-unfinished instruction
    has not written yet.

    ADD R1, R2, R3     <- producer (writes R1 in WB)
    SUB R4, R1, R5     <- consumer (needs R1 in ID/EX)  => RAW hazard on R1

Without forwarding the consumer must *stall* in ID: the pipeline inserts
*bubbles* (empty slots) into EX until the value is in the register file.

Why only RAW?  In this simple in-order 5-stage pipeline, WAR and WAW hazards
cannot happen because registers are read early (ID) and written late (WB), in order.

Two kinds of function live here:
    * detect_data_stall()   - used *during* simulation, cycle by cycle
    * find_raw_hazards()    - static analysis of the whole program for the UI/teaching
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from simulator.models import DynamicInstruction, Instruction, Slot, is_real


# --------------------------------------------------------------------------- dynamic detection
@dataclass
class StallInfo:
    """Why the instruction in ID has to wait this cycle."""

    consumer: DynamicInstruction
    producer: DynamicInstruction
    register: int
    producer_stage: str            # where the producer is right now: EX, MEM or WB
    reason: str


def _nearest_producer(register: int, ex: Slot, mem: Slot, wb: Slot) -> Optional[Tuple[str, DynamicInstruction]]:
    """Find the closest older instruction (EX, then MEM, then WB) that writes `register`.

    The closest one holds the newest value, so it is the only one that matters.
    """
    for stage, slot in (("EX", ex), ("MEM", mem), ("WB", wb)):
        if is_real(slot) and slot.instr.writes_register and slot.instr.dest == register:
            return stage, slot
    return None


def detect_data_stall(
    consumer: DynamicInstruction,
    ex: Slot,
    mem: Slot,
    wb: Slot,
    forwarding: bool,
    reg_write_first_half: bool,
) -> Optional[StallInfo]:
    """Decide whether the instruction in ID must stall this cycle.

    ex / mem / wb are what those stages hold *this* cycle (the older instructions).
    Returns None when the consumer may advance.
    """
    for register in consumer.instr.hazard_sources:
        found = _nearest_producer(register, ex, mem, wb)
        if found is None:
            continue
        stage, producer = found
        who = f"{consumer.short_label} needs R{register} from {producer.short_label}"

        if forwarding:
            # With forwarding only two situations still need a bubble.
            if stage == "EX" and producer.instr.is_load:
                return StallInfo(consumer, producer, register, stage,
                                 f"{who}, but a load only has its data at the end of MEM - "
                                 f"forwarding cannot help yet (load-use hazard)")
            if stage == "WB" and not reg_write_first_half:
                return StallInfo(consumer, producer, register, stage,
                                 f"{who}, which is being written back this cycle but the register "
                                 f"file is only readable next cycle")
        else:
            if stage in ("EX", "MEM"):
                return StallInfo(consumer, producer, register, stage,
                                 f"{who}, which is still in {stage} and has not reached write-back")
            if stage == "WB" and not reg_write_first_half:
                return StallInfo(consumer, producer, register, stage,
                                 f"{who}, which is in WB but the register file is only readable next cycle")
    return None


# --------------------------------------------------------------------------- static analysis
@dataclass(frozen=True)
class RawHazard:
    """A RAW dependency between two instructions found by reading the program in order."""

    producer_index: int
    consumer_index: int
    register: int
    distance: int                      # 1 = adjacent instructions
    producer_is_load: bool
    stalls_without_forwarding: int
    stalls_with_forwarding: int

    @property
    def kind(self) -> str:
        return "Load-use" if self.producer_is_load and self.distance == 1 else "RAW"


def find_raw_hazards(program: List[Instruction], reg_write_first_half: bool = True) -> List[RawHazard]:
    """List RAW dependencies between instructions that are at most 3 apart.

    Notes: this reads the program top to bottom and ignores jumps/branches, so it is
    a teaching aid. The cycle-by-cycle simulation is what actually decides stalls.
    """
    found: List[RawHazard] = []
    for consumer_index, consumer in enumerate(program):
        seen = set()
        for register in consumer.hazard_sources:
            if register in seen:
                continue
            seen.add(register)
            for distance in (1, 2, 3):
                producer_index = consumer_index - distance
                if producer_index < 0:
                    break
                producer = program[producer_index]
                if producer.writes_register and producer.dest == register:
                    base = 3 if not reg_write_first_half else 2          # stalls needed at distance 1
                    without = max(0, base - (distance - 1))
                    with_fwd = 1 if (producer.is_load and distance == 1) else 0
                    if distance == 3 and not reg_write_first_half:
                        with_fwd = max(with_fwd, 1)
                    found.append(RawHazard(producer_index, consumer_index, register, distance,
                                           producer.is_load, without, with_fwd))
                    break                                               # nearest producer only
    return found


# --------------------------------------------------------------------------- control hazards
def find_control_instructions(program: List[Instruction]) -> List[Instruction]:
    """Branches and jumps: instructions that can change the PC (control hazards)."""
    return [instr for instr in program if instr.is_control]
