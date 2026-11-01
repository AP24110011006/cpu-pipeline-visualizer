"""Static teaching content shown in the Guide tab."""

import streamlit as st

from simulator.models import STAGE_INFO, STAGES

HAZARD_TEXT = """
**Data hazard (RAW - Read After Write).** An instruction needs a value that an earlier instruction has not
written yet. Example: `SUB R4, R1, R5` right after `ADD R1, R2, R3`.

**Stall / bubble.** Without forwarding, the dependent instruction waits in ID. The pipeline inserts empty
slots (*bubbles*) into EX until the register file holds the new value.

**Forwarding (bypassing).** The ALU result is sent straight from the EX/MEM or MEM/WB pipeline register to
the next instruction's EX stage, so most RAW hazards cost zero cycles.

**Load-use hazard.** A load only has its data at the end of MEM, so a dependent instruction directly behind it
must still wait **one** cycle, even with forwarding.

**Control hazard.** A branch or jump changes the program counter, but the pipeline has already fetched the
following instructions. Jumps are resolved in ID (1 wasted slot); branches in EX (2 wasted slots).
*Predict not-taken* keeps fetching and flushes the wrong-path instructions if the branch is taken; the
*stall* policy simply stops fetching until the branch is resolved.

**Register file timing.** The classic design writes registers in the first half of a cycle and reads them in
the second half, so an instruction in ID can read what the instruction in WB writes in the same cycle.
Turn this off in the sidebar to see one extra stall for distance-3 dependencies.
"""

ISA_TABLE = """
| Format | Instructions | Example |
|---|---|---|
| R-type | `ADD SUB AND OR XOR SLT` | `ADD R1, R2, R3` |
| I-type | `ADDI ANDI ORI XORI SLTI` | `ADDI R1, R2, -5` |
| Load / store | `LW SW` | `LW R1, 8(R2)` |
| Branch | `BEQ BNE` | `BEQ R1, R2, loop` |
| Jump | `J` | `J done` |
| Other | `NOP` | `NOP` |

Registers are `R0`-`R31` (`R0` is always 0). Labels end with a colon (`loop:`).
Comments start with `#`, `;` or `//`.
"""

SIMPLIFICATIONS = """
- Registers and memory hold signed 32-bit integers; memory is addressed in single units (no byte/word alignment).
- Stores need both the base register and the data register in EX, so a load followed directly by a store of the
  loaded value takes one stall (a real CPU can use MEM-to-MEM forwarding).
- Instruction memory and data memory are separate, so there are no structural hazards.
- Branch handling has two policies only (stall, predict not-taken); there is no dynamic branch predictor.
"""


def render_guide() -> None:
    st.markdown("### The five pipeline stages")
    st.table({"Stage": STAGES,
              "Name": [STAGE_INFO[stage][0] for stage in STAGES],
              "What happens": [STAGE_INFO[stage][1] for stage in STAGES]})
    st.markdown("### Hazards explained")
    st.markdown(HAZARD_TEXT)
    st.markdown("### Supported instructions")
    st.markdown(ISA_TABLE)
    st.markdown("### Simplifications in this simulator")
    st.markdown(SIMPLIFICATIONS)
