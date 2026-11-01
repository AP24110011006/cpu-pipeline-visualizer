"""Shared data models for the pipeline simulator.

Everything the other modules exchange lives here, so each team member can work on
their own module and still agree on the data format.

Vocabulary used throughout the project
--------------------------------------
Instruction          A *static* instruction: one line of the assembly program.
DynamicInstruction   One *execution* of an instruction (a loop body creates many of
                     these from a single static Instruction). Carries operand values
                     and a history of the stages it visited.
Bubble               An empty pipeline slot (nothing useful is in that stage).
Slot                 What a pipeline stage holds in one cycle: a DynamicInstruction or a Bubble.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

# --------------------------------------------------------------------------- stages
STAGES: List[str] = ["IF", "ID", "EX", "MEM", "WB"]

STAGE_INFO: Dict[str, Tuple[str, str]] = {
    "IF": ("Instruction Fetch", "Read the instruction at the program counter (PC) and move the PC forward."),
    "ID": ("Instruction Decode", "Decode the instruction, read the source registers and look for hazards."),
    "EX": ("Execute", "The ALU computes the result, the memory address, or the branch condition."),
    "MEM": ("Memory Access", "Loads read data memory and stores write it. Other instructions just pass through."),
    "WB": ("Write Back", "The result is written into the destination register."),
}

# --------------------------------------------------------------------------- instruction set
R_TYPE_OPCODES = ("ADD", "SUB", "AND", "OR", "XOR", "SLT")
I_TYPE_OPCODES = ("ADDI", "ANDI", "ORI", "XORI", "SLTI")
LOAD_OPCODE = "LW"
STORE_OPCODE = "SW"
BRANCH_OPCODES = ("BEQ", "BNE")
JUMP_OPCODE = "J"
NOP_OPCODE = "NOP"
ALL_OPCODES = (
    R_TYPE_OPCODES + I_TYPE_OPCODES + (LOAD_OPCODE, STORE_OPCODE) + BRANCH_OPCODES + (JUMP_OPCODE, NOP_OPCODE)
)

# --------------------------------------------------------------------------- configuration
BRANCH_PREDICT_NOT_TAKEN = "predict_not_taken"
BRANCH_STALL = "stall"
BRANCH_POLICY_LABELS: Dict[str, str] = {
    BRANCH_PREDICT_NOT_TAKEN: "Predict not-taken (flush if taken)",
    BRANCH_STALL: "Stall until the branch is resolved",
}


@dataclass(frozen=True)
class PipelineConfig:
    """Switches that change how the pipeline behaves.

    forwarding            True  -> results are bypassed from later stages (EX/MEM, MEM/WB).
                          False -> dependent instructions must wait in ID (stall).
    reg_write_first_half  True  -> the register file is written in the first half of the cycle
                          and read in the second half, so an instruction in ID can read what the
                          instruction in WB writes in the same cycle (classic textbook design).
    branch_policy         How control hazards are handled (see BRANCH_POLICY_LABELS).
    max_cycles            Safety limit so an infinite loop cannot hang the app.
    """

    forwarding: bool = True
    reg_write_first_half: bool = True
    branch_policy: str = BRANCH_PREDICT_NOT_TAKEN
    max_cycles: int = 500

    def describe(self) -> str:
        fwd = "Forwarding ON" if self.forwarding else "Forwarding OFF"
        return f"{fwd} · {BRANCH_POLICY_LABELS.get(self.branch_policy, self.branch_policy)}"


# --------------------------------------------------------------------------- instructions
@dataclass(frozen=True)
class Instruction:
    """One parsed assembly instruction (static)."""

    index: int                       # position in the program (0-based)
    opcode: str                      # e.g. "ADD"
    text: str                        # normalised text, e.g. "ADD R1, R2, R3"
    dest: Optional[int] = None       # destination register number, if any
    sources: Tuple[int, ...] = ()    # source register numbers, in operand order
    imm: int = 0                     # immediate / memory offset
    target: Optional[int] = None     # branch/jump target (instruction index)
    line_no: int = 0                 # line in the user's text (for error messages)

    @property
    def is_load(self) -> bool:
        return self.opcode == LOAD_OPCODE

    @property
    def is_store(self) -> bool:
        return self.opcode == STORE_OPCODE

    @property
    def is_branch(self) -> bool:
        return self.opcode in BRANCH_OPCODES

    @property
    def is_jump(self) -> bool:
        return self.opcode == JUMP_OPCODE

    @property
    def is_control(self) -> bool:
        return self.is_branch or self.is_jump

    @property
    def writes_register(self) -> bool:
        """True if the instruction changes a register (R0 is hard-wired to zero)."""
        return self.dest is not None and self.dest != 0

    @property
    def hazard_sources(self) -> Tuple[int, ...]:
        """Source registers that can take part in a data hazard (R0 never does)."""
        return tuple(reg for reg in self.sources if reg != 0)


@dataclass
class DynamicInstruction:
    """One execution of an instruction travelling through the pipeline."""

    seq: int                                   # 1, 2, 3 ... in fetch order
    instr: Instruction
    fetch_cycle: int
    operands: List[int] = field(default_factory=list)
    result: Optional[int] = None
    mem_addr: Optional[int] = None
    store_value: Optional[int] = None
    taken: bool = False
    retired: bool = False                      # reached WB
    squashed: bool = False                     # flushed (wrong-path instruction)
    # (cycle, stage, state) with state in {"normal", "stall", "flushed"}
    history: List[Tuple[int, str, str]] = field(default_factory=list)

    @property
    def short_label(self) -> str:
        return f"I{self.seq}"

    @property
    def label(self) -> str:
        return f"I{self.seq}: {self.instr.text}"


@dataclass(frozen=True)
class Bubble:
    """An empty pipeline slot. reason: empty | stall | flush | control."""

    reason: str = "empty"


Slot = Union[DynamicInstruction, Bubble]
EMPTY = Bubble("empty")


def is_real(slot: Slot) -> bool:
    """True when the slot holds a real instruction (not a bubble)."""
    return isinstance(slot, DynamicInstruction)


# --------------------------------------------------------------------------- results
@dataclass
class PipelineEvent:
    """Something interesting that happened in one cycle (stall, forward, flush...)."""

    cycle: int
    kind: str                                  # "stall" | "forward" | "flush" | "control_stall"
    message: str
    consumer: Optional[int] = None             # seq of the dependent instruction
    producer: Optional[int] = None             # seq of the instruction producing the value
    register: Optional[int] = None


@dataclass
class CycleSnapshot:
    """What the pipeline looked like during one clock cycle."""

    cycle: int
    stages: Dict[str, str]                     # stage -> text shown in the UI
    stage_seq: Dict[str, Optional[int]]        # stage -> seq of the instruction (None for bubbles)
    stalled: bool
    notes: List[str]
    registers: List[int]                       # register file after this cycle's write-back


@dataclass
class SimulationResult:
    """Everything produced by one simulation run."""

    config: PipelineConfig
    program: List[Instruction]
    instructions: List[DynamicInstruction]
    cycles: List[CycleSnapshot]
    events: List[PipelineEvent]
    registers: List[int]
    memory: Dict[int, int]
    truncated: bool = False                    # True if max_cycles was hit

    @property
    def total_cycles(self) -> int:
        return len(self.cycles)

    def events_of(self, kind: str) -> List[PipelineEvent]:
        return [event for event in self.events if event.kind == kind]
