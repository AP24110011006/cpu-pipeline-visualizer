"""Performance Analysis Workspace: CPI, IPC, stage utilization, and hardware efficiency."""

from __future__ import annotations

from typing import Optional
import pandas as pd
import streamlit as st

from simulator.engine import EngineResult
from simulator.models import STAGES
from ui import charts, tables
from ui.helpers import show_chart, show_df


def render_performance(engine: Optional[EngineResult]) -> None:
    """Render comprehensive performance analysis and hardware utilization charts."""
    if engine is None or not engine.ok or engine.metrics_primary is None:
        st.info("Run a simulation in the **Assembly Simulator** to evaluate pipeline performance.")
        return

    primary = engine.primary
    metrics = engine.metrics_primary
    analytics = engine.analytics_primary

    st.markdown("## 📈 Performance & Hardware Utilization Analysis")
    st.caption("Quantitative evaluation of execution throughput, stage activity, and pipeline speedup.")

    # Core Performance KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        cpi_str = f"{metrics.cpi:.2f}" if metrics.cpi is not None else "n/a"
        c1.metric("CPI (Cycles / Instruction)", cpi_str, help="Average clock cycles required to retire one instruction.")
    with c2:
        ipc_str = f"{metrics.ipc:.2f}" if metrics.ipc is not None else "n/a"
        c2.metric("IPC (Instructions / Cycle)", ipc_str, help="Instructions retired per clock cycle.")
    with c3:
        eff_str = f"{metrics.efficiency * 100:.1f}%" if metrics.efficiency is not None else "n/a"
        c3.metric("Pipeline Efficiency", eff_str, help="Ratio of ideal hazard-free execution cycles to actual cycles.")
    with c4:
        spd_str = f"{metrics.speedup_vs_non_pipelined:.2f}x" if metrics.speedup_vs_non_pipelined is not None else "n/a"
        c4.metric("Speedup vs Unpipelined", spd_str, help="Speedup compared to a single-cycle or multi-cycle non-pipelined CPU.")

    st.markdown("---")

    # Hardware Stage Utilization Chart & Table
    col_chart, col_table = st.columns([3, 2])
    with col_chart:
        st.markdown("### 📊 Hardware Stage Utilization")
        if engine.metrics_on and engine.metrics_off:
            util_data = {
                "Forwarding ON": engine.metrics_on.stage_utilization,
                "Forwarding OFF": engine.metrics_off.stage_utilization,
            }
            fig_util = charts.utilization_chart(
                util_data,
                colors={"Forwarding ON": "#10B981", "Forwarding OFF": "#EF4444"},
            )
        else:
            fig_util = charts.utilization_chart(metrics)
        show_chart(fig_util, key="perf_util_chart")

    with col_table:
        st.markdown("### 📋 Performance Breakdown")
        if engine.metrics_on and engine.metrics_off:
            df_metrics = tables.metrics_table({
                "Forwarding ON": engine.metrics_on,
                "Forwarding OFF": engine.metrics_off,
            })
        else:
            df_metrics = tables.metrics_table(metrics)
        show_df(df_metrics)

    # Detailed Slot Auditing
    if analytics:
        st.markdown("---")
        st.markdown("### 🔬 Microarchitectural Slot Accounting")
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Total Stage Slots", analytics.total_pipeline_slots, help="5 stages * Total cycles")
        sc2.metric("Useful Instruction Slots", analytics.total_useful_slots, help="Slots actively advancing valid instructions")
        sc3.metric("Bubble (Empty) Slots", analytics.total_bubble_slots, help="Slots stalled, flushed, or empty")
        bubble_pct = (
            analytics.total_bubble_slots / analytics.total_pipeline_slots * 100.0
            if analytics.total_pipeline_slots > 0
            else 0.0
        )
        sc4.metric("Pipeline Overhead", f"{bubble_pct:.1f}%", help="Percentage of slots lost to hazards and ramp-up/down")
