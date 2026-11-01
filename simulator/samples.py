"""Ready-made example programs shown in the UI drop-down."""

from __future__ import annotations

from typing import Dict, NamedTuple


class Sample(NamedTuple):
    description: str
    code: str
    registers: str = ""
    memory: str = ""


SAMPLES: Dict[str, Sample] = {
    "Basic RAW hazard chain (assignment sample)": Sample(
        "Each instruction needs the result of the one before it - a chain of RAW hazards.",
        "ADD R1, R2, R3\nSUB R4, R1, R5\nAND R6, R4, R7",
        "R2=10, R3=5, R5=2, R7=12",
    ),
    "Load-use hazard": Sample(
        "A load followed directly by its user: even forwarding needs one stall cycle.",
        "LW  R1, 0(R2)\nADD R3, R1, R4\nSUB R5, R3, R4",
        "R2=100, R4=7",
        "100=35",
    ),
    "No hazards (independent instructions)": Sample(
        "No instruction uses a register written by a nearby instruction: the ideal pipeline.",
        "ADD R1, R2, R3\nADD R4, R5, R6\nADD R7, R2, R5\nSUB R8, R3, R6",
        "R2=1, R3=2, R5=3, R6=4",
    ),
    "Store then load (memory)": Sample(
        "Writes a value to memory and reads it back.",
        "SW R5, 0(R2)\nLW R6, 0(R2)\nADD R7, R6, R6",
        "R2=200, R5=42",
    ),
    "Taken branch (control hazard)": Sample(
        "BEQ jumps over two instructions; wrong-path instructions are flushed.",
        "BEQ R1, R1, skip\nADD R2, R2, R2\nADD R3, R3, R3\nskip: ADD R4, R4, R4",
        "R1=5, R2=1, R3=1, R4=1",
    ),
    "Unconditional jump": Sample(
        "J skips an instruction; the pipeline loses one fetch slot.",
        "J end\nADD R1, R1, R1\nend: ADD R2, R2, R2",
        "R1=1, R2=1",
    ),
    "Countdown loop": Sample(
        "A loop that runs three times: data hazards and branch penalties together.",
        "ADDI R1, R0, 3\nloop: ADDI R1, R1, -1\nADDI R2, R2, 10\nBNE R1, R0, loop\nADD R3, R2, R2",
        "",
    ),
    "Advanced Stress Test: Array Processing & Loop": Sample(
        "Complex 5-element array traversal, conditional branches (even/odd), memory loads/stores, and RAW dependency cascades.",
        """# Initialize registers
ADDI R1, R0, 100       # Array base address
ADDI R2, R0, 5         # Number of elements
ADDI R3, R0, 0         # Index
ADDI R4, R0, 0         # Sum
ADDI R5, R0, 1         # Increment value
ADDI R6, R0, 0         # Even count

# Initialize array in memory
ADDI R10, R0, 10
SW R10, 0(R1)
ADDI R10, R0, 20
SW R10, 4(R1)
ADDI R10, R0, 30
SW R10, 8(R1)
ADDI R10, R0, 40
SW R10, 12(R1)
ADDI R10, R0, 50
SW R10, 16(R1)

# Main array processing loop
loop:
BEQ R3, R2, finish

# Calculate current array address (R7 = R1 + 4*R3)
ADD R7, R1, R3
ADD R7, R7, R3
ADD R7, R7, R3
ADD R7, R7, R3

# Load array element & accumulate
LW R8, 0(R7)
ADD R4, R4, R8

# Dependency chain
ADD R9, R8, R5
ADD R11, R9, R4
SUB R12, R11, R8

# Check whether element is even
ANDI R13, R8, 1
BNE R13, R0, odd

# Count even elements
ADD R6, R6, R5
J continue

odd:
ADDI R14, R0, 1

continue:
ADD R3, R3, R5
J loop

finish:
ADD R15, R4, R6
SUB R16, R15, R3
AND R17, R4, R2
OR R18, R4, R6
XOR R19, R15, R16
SLT R20, R6, R2

# Store final results
SW R4, 20(R1)
SW R6, 24(R1)
SW R15, 28(R1)

# Load stored values
LW R21, 20(R1)
LW R22, 24(R1)
LW R23, 28(R1)

# Final dependency chain
ADD R24, R21, R22
ADD R25, R24, R23
SUB R26, R25, R4
ADD R27, R26, R6
NOP""",
        "",
        "",
    ),
}

DEFAULT_SAMPLE = "Basic RAW hazard chain (assignment sample)"
