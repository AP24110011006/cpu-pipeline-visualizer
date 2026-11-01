"""COA Learning Center: educational guide to computer organization and pipeline concepts."""

from __future__ import annotations

import streamlit as st
from ui.guide import render_guide


def render_learning_center() -> None:
    """Render the educational Computer Organization & Architecture guide."""
    st.markdown("## 📚 Computer Organization & Architecture (COA) Learning Center")
    st.caption("Interactive curriculum covering pipeline stages, data hazards, hardware bypass, and quantitative metrics.")

    tab_guide, tab_formulas, tab_glossary = st.tabs([
        "📖 Pipeline Architecture Guide",
        "📐 Quantitative COA Formulas",
        "🗂️ Microarchitecture Glossary",
    ])

    with tab_guide:
        render_guide()

    with tab_formulas:
        st.markdown(
            r"""
            ### Fundamental Performance Equations

            #### 1. Execution Time ($T$)
            \[
            T = I \times \text{CPI} \times \tau
            \]
            where:
            - $I$ = Instruction count (dynamic)
            - $\text{CPI}$ = Clock Cycles Per Instruction
            - $\tau$ = Clock cycle time (inverse of clock frequency $f$)

            #### 2. Cycles Per Instruction (CPI) in a Pipelined Processor
            \[
            \text{CPI} = \text{CPI}_{\text{ideal}} + \text{Stalls}_{\text{data}} + \text{Penalty}_{\text{branch}} + \text{Stalls}_{\text{structural}}
            \]
            For an ideal classic 5-stage pipeline with no stalls, $\text{CPI}_{\text{ideal}} = 1.0$ at steady state.

            #### 3. Theoretical Speedup ($S$)
            \[
            S = \frac{\text{CPI}_{\text{unpipelined}}}{\text{CPI}_{\text{pipelined}}} \times \frac{\tau_{\text{unpipelined}}}{\tau_{\text{pipelined}}}
            \]
            If stage delays are perfectly balanced without pipeline latch overhead:
            \[
            S \to k \quad (\text{where } k \text{ is the number of pipeline stages, e.g. } 5)
            \]

            #### 4. Pipeline Efficiency ($\eta$)
            \[
            \eta = \frac{\text{Ideal Cycles}}{\text{Total Actual Cycles}} = \frac{N + (k - 1)}{\text{Cycles}_{\text{actual}}}
            \]
            """
        )

    with tab_glossary:
        st.markdown(
            """
            ### Key Architectural Terms

            - **RAW (Read-After-Write)**: True data dependency where a consumer instruction tries to read a register before an earlier producer writes to it.
            - **Load-Use Hazard**: A RAW hazard where the producer is a Load Word (`LW`) instruction. Since data is only retrieved from memory at the end of the `MEM` stage, forwarding cannot supply the value to the consumer's `EX` stage in the immediately following cycle, requiring at least one mandatory bubble.
            - **Forwarding (Bypassing)**: Routing an ALU or memory result from pipeline register latches (`EX/MEM` or `MEM/WB`) directly to the ALU inputs, avoiding stall cycles.
            - **Pipeline Bubble**: An inserted `NOP` or idle state inside a pipeline stage caused by hazard resolution hardware.
            - **Branch Penalty**: Clock cycles lost when speculative instruction fetching must be flushed due to a taken branch or incorrect prediction.
            - **Split-Phase Register File**: Designing the register file so writes occur during the first half of the clock cycle and reads occur during the second half, allowing same-cycle data transfer between WB and ID.
            """
        )
