"""Dedicated Hazard & Stall Analytics Workspace: fine-grained microarchitectural telemetry."""

from __future__ import annotations

from typing import Optional
import pandas as pd
import streamlit as st

from simulator.engine import EngineResult


def render_hazard_analytics(engine: Optional[EngineResult]) -> None:
    """Render comprehensive hazard counters, stall breakdowns, and interactive event history."""
    if engine is None or not engine.ok or engine.analytics_primary is None:
        st.info("Run a simulation in **Assembly Simulator** to generate hazard telemetry.")
        return

    analytics = engine.analytics_primary
    h_sum = analytics.hazard_summary
    s_sum = analytics.stall_summary
    f_sum = analytics.forwarding_summary
    c_sum = analytics.control_summary
    perf = analytics.performance_metrics

    st.markdown("## ⚠️ Dedicated Hazard & Stall Analytics Workspace")
    st.caption("Microarchitectural accounting: static dependencies vs dynamic events with zero double-counting.")

    # 4 Structured Analytical Subsections
    tab_hazards, tab_stalls, tab_fwd, tab_control, tab_history = st.tabs([
        "⚠️ Hazard Counters",
        "🛑 Stall Counters",
        "⚡ Forwarding Analytics",
        "🔀 Control Flow & Flushes",
        "📜 Hazard Event History",
    ])

    # ---------------- TAB 1: Hazard Counters
    with tab_hazards:
        st.markdown("### A · Dynamic & Static Hazard Counters")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Dynamic RAW Events", h_sum.dynamic_raw_events, help="Instances where an instruction in ID needed an in-flight operand.")
        c2.metric("Static RAW Dependencies", h_sum.static_raw_dependencies, help="Unique static RAW producer-consumer pairs in program text.")
        c3.metric("Load-Use Hazards", h_sum.dynamic_load_use_events, help="Instances where producer was LW in EX stage.")
        c4.metric("Control Hazard Events", h_sum.dynamic_control_hazard_events, help="Branches taken or jumps causing pipeline redirection.")

        st.markdown("#### 🔍 Static RAW Dependency Inspection")
        if h_sum.unique_static_raw_pairs:
            pairs_data = [
                {
                    "Consumer (I#)": f"I{consumer_idx + 1}: {engine.program[consumer_idx].text}",
                    "Producer (I#)": f"I{prod_idx + 1}: {engine.program[prod_idx].text}",
                    "Register": f"R{reg}",
                    "Static Distance": consumer_idx - prod_idx,
                }
                for consumer_idx, prod_idx, reg in h_sum.unique_static_raw_pairs
            ]
            st.dataframe(pd.DataFrame(pairs_data), use_container_width=True)
        else:
            st.caption("No static RAW dependencies detected in program text.")

    # ---------------- TAB 2: Stall Counters
    with tab_stalls:
        st.markdown("### B · Stall Events vs Stall Clock Cycles")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Stall Events", s_sum.total_stall_events, help="Distinct hazard events that triggered a pipeline hold.")
        c2.metric("Total Stall Cycles", s_sum.total_stall_cycles, help="Clock cycles where ID and IF were held stalled.")
        c3.metric("Data Stall Cycles", s_sum.data_hazard_stall_cycles, help="Cycles stalled purely due to RAW register dependencies.")
        c4.metric("Stalls Avoided (Forwarding)", s_sum.stalls_avoided_forwarding, help="Cycles saved by bypassing operands instead of stalling.")

        c5, c6 = st.columns(2)
        c5.metric("Load-Use Stall Cycles", s_sum.load_use_stall_cycles, help="Cycles stalled waiting for memory read in MEM stage.")
        c6.metric("Control Stall Cycles", s_sum.control_stall_cycles, help="Cycles stalled waiting for branch resolution (stall policy).")

    # ---------------- TAB 3: Forwarding Counters
    with tab_fwd:
        st.markdown("### C · Forwarding Paths & Stalls Avoided")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Forwarding Events", f_sum.total_forwarding_events)
        c2.metric("EX-to-EX Forwarding", f_sum.ex_to_ex_forwarding, help="Forwarded from EX/MEM latch to EX ALU operand.")
        c3.metric("MEM-to-EX Forwarding", f_sum.mem_to_ex_forwarding, help="Forwarded from MEM/WB latch to EX ALU operand.")
        c4.metric("Zero-Stall Resolutions", f_sum.dependencies_resolved_zero_stalls)

    # ---------------- TAB 4: Control Analytics
    with tab_control:
        st.markdown("### D · Branch Resolution & Flush Telemetry")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Branches Executed", c_sum.total_branches_executed)
        c2.metric("Branches Taken", c_sum.branches_taken)
        c3.metric("Branches Not Taken", c_sum.branches_not_taken)
        c4.metric("Jumps Executed", c_sum.jump_instructions_executed)

        c5, c6, c7 = st.columns(3)
        c5.metric("Pipeline Flush Events", c_sum.pipeline_flush_events, help="Times wrong-path instructions were purged.")
        c6.metric("Flushed Instructions", c_sum.flushed_instructions_count, help="Total speculative instructions converted to bubbles.")
        c7.metric("Control Delay Stalls", c_sum.control_related_stalls)

    # ---------------- TAB 5: Hazard Event History Table
    with tab_history:
        st.markdown("### F · Microarchitectural Event History Table")
        st.caption("Inspect and filter every discrete hazard, stall, bypass, and squash event.")

        # Interactive filters
        f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
        with f_col1:
            h_types = ["All", "RAW", "Load-Use", "Control (Branch)", "Control (Jump)"]
            sel_type = st.selectbox("Filter Hazard Type", h_types, key="filter_haz_type")
        with f_col2:
            stages = ["All", "ID", "EX", "MEM", "WB"]
            sel_stage = st.selectbox("Filter Stage", stages, key="filter_stage")
        with f_col3:
            search_txt = st.text_input("Search (Instruction, Register, or Event ID)", key="filter_search")

        # Filter events
        filtered_events = analytics.event_history
        if sel_type != "All":
            filtered_events = [e for e in filtered_events if sel_type.lower() in e.hazard_type.lower()]
        if sel_stage != "All":
            filtered_events = [e for e in filtered_events if sel_stage.lower() in e.stage.lower()]
        if search_txt:
            q = search_txt.lower()
            filtered_events = [
                e for e in filtered_events
                if q in e.event_id.lower()
                or q in e.instruction_text.lower()
                or q in (e.register_dependency or "").lower()
                or q in e.resolution_method.lower()
                or q in e.notes.lower()
            ]

        if filtered_events:
            table_rows = [
                {
                    "Event ID": e.event_id,
                    "Cycle": e.cycle,
                    "Stage": e.stage,
                    "Instruction": f"I{e.instruction_seq}: {e.instruction_text}",
                    "Hazard Type": e.hazard_type,
                    "Register": e.register_dependency or "—",
                    "Resolution": e.resolution_method,
                    "Bypass Path": e.forwarding_path or "—",
                    "Stall Cycles": e.stall_cycles,
                    "Notes": e.notes,
                }
                for e in filtered_events
            ]
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, height=350)
        else:
            st.caption("No hazard events match the selected filters.")
