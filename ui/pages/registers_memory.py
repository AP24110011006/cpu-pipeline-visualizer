"""Registers & Memory Workspace: live architectural register file and RAM inspection."""

from __future__ import annotations

from typing import Optional
import streamlit as st

from simulator.engine import EngineResult
from ui import tables
from ui.helpers import show_df


def render_registers_memory(engine: Optional[EngineResult]) -> None:
    """Render the register file and memory tables for the current or finished cycle."""
    if engine is None or not engine.ok or engine.primary is None:
        st.info("Run a simulation in the **Assembly Simulator** to inspect architectural state.")
        return

    primary = engine.primary
    if not primary.cycles:
        st.info("No cycle data recorded.")
        return

    current_cycle = int(st.session_state.get("cycle_view", 1))
    current_cycle = max(1, min(current_cycle, primary.total_cycles))
    snapshot = primary.cycles[current_cycle - 1]

    st.markdown(f"## 🧮 Architectural State (Clock Cycle {current_cycle})")
    st.caption("Inspect live register contents and memory addresses as updated by the Write-Back (WB) stage.")

    # Cycle slider for fast stepping directly in this page
    c_slider, c_check = st.columns([3, 1])
    with c_slider:
        new_cycle = st.slider(
            "Select Cycle to Inspect State",
            min_value=1,
            max_value=primary.total_cycles,
            value=current_cycle,
            key="reg_state_cycle_slider",
        )
        current_cycle = new_cycle
        st.session_state["cycle_view"] = current_cycle

    with c_check:
        show_all = st.checkbox("Show all 32 registers (R0–R31)", value=False, key="state_show_all_regs")

    # Reference CPU differential validation
    ref = engine.reference
    if ref and not ref.truncated and not primary.truncated:
        if primary.registers == ref.registers and primary.memory == ref.memory:
            st.success("✅ **Reference Check**: Final pipelined architectural state matches non-pipelined Reference CPU exactly.")
        else:
            st.error("❌ **Discrepancy**: Pipelined final state differs from Reference CPU.")

    c_regs, c_mem = st.columns(2)
    with c_regs:
        st.markdown(f"#### 🔢 Register File (Cycle {current_cycle})")
        df_regs = tables.registers_table(snapshot.registers, only_nonzero=not show_all)
        show_df(df_regs)

    with c_mem:
        st.markdown("#### 💾 Memory State (End of Execution)")
        mem_df = tables.memory_table(primary.memory)
        if len(mem_df):
            show_df(mem_df)
        else:
            st.caption("Data memory is unwritten (empty).")
