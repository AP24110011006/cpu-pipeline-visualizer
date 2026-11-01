"""Five-stage pipeline engine.   (Member 3)

The simulator advances the pipeline one clock cycle at a time.  In every cycle:

    1. WB  : the instruction in WB writes its result into the register file
    2. EX  : the instruction in EX computes (using forwarded values if enabled)
    3. MEM : the instruction in MEM reads/writes data memory
    4. ID  : hazard check - may the instruction in ID move on, or must it stall?
    5. Control : taken branches / jumps decide whether instructions are flushed
    6. Shift every instruction one stage forward and fetch a new one

Stalls are modelled the way real hardware does it: the instructions in IF and ID
are *held*, and a bubble (empty slot) is inserted into EX.

Control hazards
    * Jumps are resolved in ID  -> 1 wasted fetch slot.
    * Branches are resolved in EX -> 2 wasted fetch slots when the branch is taken
      ("predict not-taken", wrong-path instructions are flushed) or always
      ("stall" policy, fetch simply waits for the branch).

The engine records a full history, so the UI can replay any cycle without re-running.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from simulator.execute import branch_is_taken, compute_alu_result, to_signed32
from simulator.forwarding import find_forwarding_source
from simulator.hazards import detect_data_stall
from simulator.models import (
    BRANCH_PREDICT_NOT_TAKEN,
    BRANCH_STALL,
    EMPTY,
    STAGES,
    Bubble,
    CycleSnapshot,
    DynamicInstruction,
    Instruction,
    PipelineConfig,
    PipelineEvent,
    SimulationResult,
    Slot,
    is_real,
)

_BUBBLE_TEXT = {
    "empty": "—",
    "stall": "bubble (stall)",
    "flush": "bubble (flushed)",
    "control": "bubble (waiting for branch)",
}


def _slot_text(slot: Slot) -> str:
    return slot.label if is_real(slot) else _BUBBLE_TEXT[slot.reason]


class PipelineSimulator:
    """Cycle-by-cycle simulator of the classic MIPS-style five-stage pipeline."""

    def __init__(self, config: Optional[PipelineConfig] = None) -> None:
        self.config = config or PipelineConfig()

    # ------------------------------------------------------------------ public API
    def run(
        self,
        program: List[Instruction],
        initial_registers: Optional[Dict[int, int]] = None,
        initial_memory: Optional[Dict[int, int]] = None,
    ) -> SimulationResult:
        """Simulate `program` until every instruction has left the pipeline."""
        cfg = self.config
        registers = [0] * 32
        for number, value in (initial_registers or {}).items():
            if 0 < number < 32:                       # R0 is hard-wired to zero
                registers[number] = to_signed32(value)
        memory = {address: to_signed32(value) for address, value in (initial_memory or {}).items()}

        dynamic: List[DynamicInstruction] = []
        snapshots: List[CycleSnapshot] = []
        events: List[PipelineEvent] = []
        pc = 0

        def fetch(cycle: int) -> Slot:
            """IF stage: create the next dynamic instruction (or an empty slot at program end)."""
            nonlocal pc
            if pc < len(program):
                instruction = DynamicInstruction(seq=len(dynamic) + 1, instr=program[pc], fetch_cycle=cycle)
                dynamic.append(instruction)
                pc += 1
                return instruction
            return EMPTY

        slots: Dict[str, Slot] = {"IF": fetch(1), "ID": EMPTY, "EX": EMPTY, "MEM": EMPTY, "WB": EMPTY}
        truncated = False
        cycle = 0

        while any(is_real(slot) for slot in slots.values()):
            cycle += 1
            if cycle > cfg.max_cycles:
                truncated = True
                cycle -= 1
                break

            if_slot, id_slot, ex_slot, mem_slot, wb_slot = (slots[stage] for stage in STAGES)
            notes: List[str] = []

            # 1) WB ---------------------------------------------------------------
            if is_real(wb_slot):
                wb_slot.retired = True
                if wb_slot.instr.writes_register:
                    registers[wb_slot.instr.dest] = wb_slot.result
                    notes.append(f"WB: {wb_slot.short_label} writes R{wb_slot.instr.dest} = {wb_slot.result}")
                else:
                    notes.append(f"WB: {wb_slot.short_label} finishes (no register to write)")

            # 2) EX ---------------------------------------------------------------
            if is_real(ex_slot):
                self._execute(ex_slot, mem_slot, wb_slot, cycle, events, notes)

            # 3) MEM --------------------------------------------------------------
            if is_real(mem_slot):
                if mem_slot.instr.is_load:
                    mem_slot.result = memory.get(mem_slot.mem_addr, 0)
                    notes.append(f"MEM: {mem_slot.short_label} loads {mem_slot.result} from address {mem_slot.mem_addr}")
                elif mem_slot.instr.is_store:
                    memory[mem_slot.mem_addr] = mem_slot.store_value
                    notes.append(f"MEM: {mem_slot.short_label} stores {mem_slot.store_value} to address {mem_slot.mem_addr}")

            # 4) Control hazards: does anything redirect the PC? -------------------
            redirect: Optional[int] = None
            squash_if = squash_id = False
            redirect_cause: Optional[DynamicInstruction] = None
            if is_real(ex_slot) and ex_slot.instr.is_branch and ex_slot.taken:
                redirect, redirect_cause = ex_slot.instr.target, ex_slot
                if cfg.branch_policy == BRANCH_PREDICT_NOT_TAKEN:
                    squash_if = squash_id = True              # wrong-path instructions in IF and ID
            elif is_real(id_slot) and id_slot.instr.is_jump:
                redirect, redirect_cause = id_slot.instr.target, id_slot
                id_slot.taken = True
                squash_if = True                              # the instruction fetched behind the jump

            # 5) ID: hazard check ---------------------------------------------------
            stall = None
            if is_real(id_slot) and not squash_id:
                stall = detect_data_stall(id_slot, ex_slot, mem_slot, wb_slot,
                                          cfg.forwarding, cfg.reg_write_first_half)
                if stall is None:                             # leaving ID: read the register file now
                    id_slot.operands = [registers[number] for number in id_slot.instr.sources]
            stalled = stall is not None

            # record history for the timing diagram
            for stage in STAGES:
                slot = slots[stage]
                if is_real(slot):
                    state = "stall" if stalled and stage in ("IF", "ID") else "normal"
                    slot.history.append((cycle, stage, state))

            if stalled:
                message = f"Stall: {stall.reason}. A bubble enters EX; IF and ID are held."
                events.append(PipelineEvent(cycle, "stall", message, stall.consumer.seq, stall.producer.seq, stall.register))
                notes.append("STALL: " + message)

            # 6) Move instructions forward ------------------------------------------
            if stalled:
                next_slots: Dict[str, Slot] = {"WB": mem_slot, "MEM": ex_slot, "EX": Bubble("stall"),
                                               "ID": id_slot, "IF": if_slot}
            else:
                next_slots = {
                    "WB": mem_slot,
                    "MEM": ex_slot,
                    "EX": Bubble("flush") if squash_id else id_slot,
                    "ID": Bubble("flush") if (squash_if or squash_id) else if_slot,
                }
                flushed: List[DynamicInstruction] = []
                if squash_id and is_real(id_slot):
                    id_slot.squashed = True
                    id_slot.history.append((cycle + 1, "EX", "flushed"))
                    flushed.append(id_slot)
                if (squash_if or squash_id) and is_real(if_slot):
                    if_slot.squashed = True
                    if_slot.history.append((cycle + 1, "ID", "flushed"))
                    flushed.append(if_slot)

                if redirect is not None:
                    pc = redirect
                    names = ", ".join(item.short_label for item in flushed) or "nothing useful"
                    message = (f"Control hazard: {redirect_cause.short_label} ({redirect_cause.instr.text}) redirects "
                               f"fetch to instruction {redirect + 1}; flushed {names}.")
                    events.append(PipelineEvent(cycle, "flush", message, redirect_cause.seq))
                    notes.append("FLUSH: " + message)
                    gate = False
                else:
                    gate = cfg.branch_policy == BRANCH_STALL and (
                        (is_real(if_slot) and if_slot.instr.is_branch) or (is_real(id_slot) and id_slot.instr.is_branch)
                    )

                if gate:
                    next_slots["IF"] = Bubble("control")
                    waiting_for = if_slot if (is_real(if_slot) and if_slot.instr.is_branch) else id_slot
                    message = f"Fetch paused: waiting for branch {waiting_for.short_label} to be resolved in EX."
                    events.append(PipelineEvent(cycle, "control_stall", message, waiting_for.seq))
                    notes.append("WAIT: " + message)
                else:
                    next_slots["IF"] = fetch(cycle + 1)

            snapshots.append(CycleSnapshot(
                cycle=cycle,
                stages={stage: _slot_text(slots[stage]) for stage in STAGES},
                stage_seq={stage: (slots[stage].seq if is_real(slots[stage]) else None) for stage in STAGES},
                stalled=stalled,
                notes=notes,
                registers=list(registers),
            ))
            slots = next_slots

        return SimulationResult(cfg, list(program), dynamic, snapshots, events, registers, memory, truncated)

    # ------------------------------------------------------------------ EX stage
    def _execute(
        self,
        dyn: DynamicInstruction,
        mem_slot: Slot,
        wb_slot: Slot,
        cycle: int,
        events: List[PipelineEvent],
        notes: List[str],
    ) -> None:
        """Run the EX stage: apply forwarding, then do the ALU / address / branch work."""
        instr = dyn.instr
        values = list(dyn.operands)

        if self.config.forwarding:
            for position, register in enumerate(instr.sources):
                if register == 0:
                    continue
                decision = find_forwarding_source(register, mem_slot, wb_slot)
                if decision is not None:
                    values[position] = decision.value
                    message = (f"Forwarding: R{register} = {decision.value} goes from {decision.source_stage} "
                               f"({decision.producer.short_label}) to {dyn.short_label} in EX.")
                    events.append(PipelineEvent(cycle, "forward", message, dyn.seq, decision.producer.seq, register))
                    notes.append("FORWARD: " + message)
        dyn.operands = values

        if instr.is_load:
            dyn.mem_addr = values[0] + instr.imm
        elif instr.is_store:
            dyn.mem_addr = values[0] + instr.imm
            dyn.store_value = values[1]
        elif instr.is_branch:
            dyn.taken = branch_is_taken(instr.opcode, values[0], values[1])
            notes.append(f"EX: {dyn.short_label} branch is {'TAKEN' if dyn.taken else 'not taken'}")
        elif instr.is_jump or instr.opcode == "NOP":
            pass
        else:
            dyn.result = compute_alu_result(instr, values)
