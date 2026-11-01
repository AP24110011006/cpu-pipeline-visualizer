"""Pipeline Visualization Workspace: stage cards, timing diagram, and pedagogical explainer."""

from __future__ import annotations

import html
from typing import Optional
import streamlit as st

from simulator.engine import EngineResult
from simulator.explainer import explain_cycle
from simulator.models import STAGE_INFO, STAGES
from ui import charts
from ui.helpers import show_chart
from ui.theme import STAGE_COLORS


def render_pipeline_view(engine: Optional[EngineResult]) -> None:
    """Render the cycle-by-cycle stage cards, navigation controls, and timing diagram."""
    if engine is None or not engine.ok or engine.primary is None:
        st.info("Please run a simulation in the **Assembly Simulator** first.")
        return

    primary = engine.primary
    if primary.total_cycles == 0:
        st.warning("No execution cycles were generated.")
        return

    st.markdown("## ⏱️ Pipeline Execution Visualization")
    st.caption("Cycle-by-cycle microarchitectural stage state, hardware bypass signals, and interactive timing diagram.")

    # Cycle Navigation Controls
    total_cycles = primary.total_cycles

    # Initialize cycle_view safely
    if "cycle_view" not in st.session_state:
        st.session_state["cycle_view"] = 1

    current_cycle = int(st.session_state.get("cycle_view", 1))
    current_cycle = max(1, min(current_cycle, total_cycles))
    st.session_state["cycle_view"] = current_cycle

    # Synchronize slider_cycle with cycle_view before widget rendering
    if "slider_cycle" not in st.session_state or st.session_state["slider_cycle"] != current_cycle:
        st.session_state["slider_cycle"] = current_cycle

    def _step(delta: int) -> None:
        val = max(1, min(total_cycles, int(st.session_state.get("cycle_view", 1)) + delta))
        st.session_state["cycle_view"] = val
        st.session_state["slider_cycle"] = val

    def _reset_step() -> None:
        st.session_state["cycle_view"] = 1
        st.session_state["slider_cycle"] = 1

    def _slider_step() -> None:
        val = int(st.session_state.get("slider_cycle", 1))
        st.session_state["cycle_view"] = max(1, min(val, total_cycles))

    # Stepper Control Bar with -5, -1, slider, +1, +5, and reset
    c_m5, c_prev, c_slider, c_next, c_p5, c_reset = st.columns([1, 1, 4, 1, 1, 1])
    with c_m5:
        st.button("⏮️ -5", on_click=_step, args=(-5,), disabled=(current_cycle <= 1), use_container_width=True)
    with c_prev:
        st.button("◀ Prev", on_click=_step, args=(-1,), disabled=(current_cycle <= 1), use_container_width=True)
    with c_slider:
        st.slider(
            "Clock Cycle",
            min_value=1,
            max_value=total_cycles,
            key="slider_cycle",
            on_change=_slider_step,
            label_visibility="collapsed",
        )
    with c_next:
        st.button("Next ▶", on_click=_step, args=(1,), disabled=(current_cycle >= total_cycles), use_container_width=True)
    with c_p5:
        st.button("+5 ⏭️", on_click=_step, args=(5,), disabled=(current_cycle >= total_cycles), use_container_width=True)
    with c_reset:
        st.button("Reset (C1)", on_click=_reset_step, use_container_width=True)

    # Re-read active cycle after potential callback execution
    current_cycle = int(st.session_state.get("cycle_view", 1))
    current_cycle = max(1, min(current_cycle, total_cycles))

    st.markdown(
        f"<div style='text-align:center; font-weight:800; font-size:1.05rem; color:#22D3EE; margin-bottom:0.75rem;'>"
        f"⚡ Inspecting Clock Cycle: {current_cycle} of {total_cycles}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # 5 Pipeline Stage Cards with canonical Midnight Engineering tokens
    snapshot = primary.cycles[current_cycle - 1]
    stage_cols = st.columns(5)
    for idx, stage in enumerate(STAGES):
        text = snapshot.stages.get(stage, "—")
        fullName, purpose = STAGE_INFO.get(stage, (stage, ""))

        with stage_cols[idx]:
            is_bubble = "bubble" in text.lower() or text == "—"
            if is_bubble and "stall" in text.lower():
                border_color = "#EF4444"
                glow = "box-shadow: 0 0 14px rgba(239, 68, 68, 0.4);"
            elif is_bubble:
                border_color = "#64748B"
                glow = ""
            else:
                border_color = STAGE_COLORS.get(stage, "#22D3EE")
                glow = f"box-shadow: 0 0 15px {border_color}33;"

            st.markdown(
                f"""
                <div class="stage-slot" style="border-top: 3.5px solid {border_color}; {glow}">
                    <div class="stage-slot-name" style="color: {border_color};">{stage} · {fullName}</div>
                    <div class="stage-slot-content">{html.escape(text)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Pedagogical Explainer Glass Card (Always visible, high-contrast clarity)
    exp = explain_cycle(primary, current_cycle)
    haz_text = f"<span style='color:#EF4444; font-weight:600;'>{html.escape(exp.hazard_summary)}</span>" if exp.hazard_summary else "<span style='color:#10B981; font-weight:600;'>No pipeline stalls active in this cycle.</span>"
    fwd_text = f"<span style='color:#22D3EE; font-weight:600;'>{html.escape(exp.forwarding_summary)}</span>" if exp.forwarding_summary else "<span style='color:#94A3B8;'>No hardware bypass active.</span>"
    state_text = f"<div style='margin-top:0.35rem;'><b>State Writes:</b> {html.escape(', '.join(exp.state_changes))}</div>" if exp.state_changes else ""
    preview_text = html.escape(exp.next_cycle_preview or "Pipeline advances.")

    st.markdown(
        f"""
        <div style="background: #111C2E; border: 1px solid #27364B; border-left: 4.5px solid #22D3EE; border-radius: 10px; padding: 1.0rem 1.35rem; margin-top: 0.9rem; margin-bottom: 1.25rem; box-shadow: 0 8px 24px rgba(0,0,0,0.35);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.4rem;">
                <div style="font-size: 0.82rem; font-weight: 800; color: #22D3EE; text-transform: uppercase; letter-spacing: 0.06em;">
                    🔍 Pedagogical Cycle Explanation · Clock Cycle {current_cycle}
                </div>
                <div style="font-size: 0.78rem; background: rgba(34, 211, 238, 0.12); color: #22D3EE; border: 1px solid rgba(34, 211, 238, 0.3); border-radius: 6px; padding: 0.15rem 0.6rem; font-weight:700;">
                    Stage Diagnostics
                </div>
            </div>
            <div style="font-size: 0.95rem; font-weight: 600; color: #F1F5F9; margin-bottom: 0.6rem;">
                {html.escape(exp.simple_summary)}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; font-size: 0.86rem; color: #CBD5E1; border-top: 1px solid #27364B; padding-top: 0.6rem;">
                <div>
                    <div><b>Hazard Status:</b> {haz_text}</div>
                    {state_text}
                </div>
                <div>
                    <div><b>Hardware Bypass:</b> {fwd_text}</div>
                    <div style="margin-top:0.35rem;"><b>Next Cycle Preview:</b> <span style="color:#A78BFA;">{preview_text}</span></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Interactive Timing Diagram
    st.markdown("### 📊 Pipeline Timing Diagram")
    c_diag_opt, c_legend = st.columns([2, 1])
    with c_diag_opt:
        diag_mode = st.radio(
            "Diagram View Mode",
            ["Window around cycle (Fast)", "Full program"],
            index=0 if primary.total_cycles > 30 else 1,
            horizontal=True,
            key="pipe_diag_mode",
        )
    with c_legend:
        st.markdown(charts.legend_html(), unsafe_allow_html=True)

    window = None
    if diag_mode.startswith("Window"):
        start = max(1, current_cycle - 15)
        end = min(total_cycles, current_cycle + 15)
        window = (start, end)

    fig = charts.timing_diagram(
        primary,
        title=f"Pipeline Timing Diagram (Clock Cycle {current_cycle} of {total_cycles})",
        highlight_cycle=current_cycle,
        cycle_window=window,
    )
    show_chart(fig, key=f"pipe_view_fig_{current_cycle}_{diag_mode}")
