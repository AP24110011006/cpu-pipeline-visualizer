"""Professional Assembly Simulator Workspace."""

from __future__ import annotations

from typing import Callable, Optional
import streamlit as st

from simulator.engine import EngineResult
from simulator.models import BRANCH_POLICY_LABELS, PipelineConfig
from simulator.samples import DEFAULT_SAMPLE, SAMPLES


def render_simulator(
    engine: Optional[EngineResult],
    on_run_simulation: Callable[[], None],
    on_sample_change: Callable[[], None],
    on_file_upload: Callable[[], None],
) -> None:
    """Render the assembly code editor, presets, hardware configuration, and compile triggers."""
    st.markdown("## 💻 Assembly Simulator Workspace")
    st.caption("Write MIPS-style assembly, configure architectural timing, and execute the cycle-accurate pipeline.")

    # Top controls row: Presets & Upload
    col_preset, col_upload = st.columns([2, 1])
    with col_preset:
        st.selectbox(
            "Load Example Program",
            list(SAMPLES),
            key="sample_choice",
            on_change=on_sample_change,
            help="Select an educational textbook program.",
        )
        if st.session_state.get("sample_choice") in SAMPLES:
            st.caption(f"ℹ️ {SAMPLES[st.session_state['sample_choice']].description}")

    with col_upload:
        st.file_uploader(
            "Upload Assembly File (.s, .asm, .txt)",
            type=["s", "asm", "txt"],
            key="file_uploader",
            on_change=on_file_upload,
            help="Upload an assembly source file from disk.",
        )

    # Code Editor with Clear/Reset buttons
    c_btn1, c_btn2, _ = st.columns([1, 1, 4])
    with c_btn1:
        if st.button("🧹 Clear Editor"):
            st.session_state["code_input"] = ""
            st.rerun()
    with c_btn2:
        if st.button("🔄 Reset to Default"):
            sample = SAMPLES[DEFAULT_SAMPLE]
            st.session_state["sample_choice"] = DEFAULT_SAMPLE
            st.session_state["code_input"] = sample.code
            st.session_state["init_regs"] = sample.registers
            st.session_state["init_mem"] = sample.memory
            on_run_simulation()
            st.rerun()

    st.text_area(
        "Assembly Program (MIPS syntax: ADD, SUB, AND, OR, XOR, SLT, ADDI, LW, SW, BEQ, BNE, J, NOP)",
        key="code_input",
        height=220,
        help="One instruction per line. Comments start with # or ;. Labels end with :",
    )

    # Register & Memory Initial States
    col_regs, col_mem = st.columns(2)
    col_regs.text_input(
        "Initial Registers (comma-separated, e.g. R2=10, R3=5, R4=0x10)",
        key="init_regs",
        placeholder="R2=10, R3=5",
    )
    col_mem.text_input(
        "Initial Memory (comma-separated, e.g. 100=35, 104=42)",
        key="init_mem",
        placeholder="100=35, 104=42",
    )

    # Architectural Configuration
    with st.expander("⚙️ Advanced Pipeline Architecture Settings", expanded=True):
        c1, c2 = st.columns(2)
        c1.toggle(
            "Enable Data Forwarding (Hardware Bypass)",
            value=True,
            key="opt_forwarding",
            help="Bypasses results directly from EX/MEM and MEM/WB latches to EX ALU inputs.",
        )
        c2.toggle(
            "Register File Split Phase (Write in 1st half, Read in 2nd half)",
            value=True,
            key="opt_first_half",
            help="Textbook MIPS timing: allows ID to read what WB writes during the exact same cycle.",
        )

        c3, c4 = st.columns(2)
        labels = list(BRANCH_POLICY_LABELS.values())
        chosen = c3.selectbox(
            "Branch Resolution Policy",
            labels,
            index=0,
            key="opt_policy_label",
            help="How control hazards are handled when conditional branches are evaluated in EX.",
        )
        policy_key = next(k for k, v in BRANCH_POLICY_LABELS.items() if v == chosen)
        st.session_state["opt_policy"] = policy_key

        c4.number_input(
            "Maximum Simulation Cycle Bound",
            min_value=20,
            max_value=10000,
            value=500,
            step=50,
            key="opt_max_cycles",
            help="Safety threshold stopping infinite loops.",
        )

    st.button("🚀 Run Simulation", type="primary", on_click=on_run_simulation, use_container_width=True)

    # Compilation & Validation Feedback
    if engine is None:
        st.info("Click **Run Simulation** above to execute the pipeline.")
    elif not engine.ok:
        st.error("### ⚠️ Compilation & Assembly Errors:")
        for err in engine.errors:
            st.error(f"• {err}")
    else:
        st.success(
            f"✅ **Simulation Compiled & Executed Successfully**: {len(engine.program)} instruction(s), "
            f"{engine.primary.total_cycles} cycles executed ({engine.config.describe()})."
        )
