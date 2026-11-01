"""Forwarding ON/OFF Comparison Workspace with independent diagram view modes."""

from __future__ import annotations

from typing import Optional, Tuple
import streamlit as st

from simulator.engine import EngineResult
from ui import charts
from ui.helpers import show_chart


def render_forwarding_comparison(engine: Optional[EngineResult]) -> None:
    """Render side-by-side Forwarding ON vs OFF comparison with independent view modes and fluid cycle stepping."""
    if engine is None or not engine.ok or engine.on is None or engine.off is None:
        st.info("Please run a simulation in the **Assembly Simulator** to generate comparison telemetry.")
        return

    st.markdown("## ⚡ Forwarding ON vs Forwarding OFF Comparison")
    st.caption("Measure the architectural performance impact of hardware data forwarding and bypassing.")

    res_on = engine.on
    res_off = engine.off
    met_on = engine.metrics_on
    met_off = engine.metrics_off

    # Top Comparative Metrics Bar
    saved_cycles = max(0, res_off.total_cycles - res_on.total_cycles)
    stall_reduction = max(0, met_off.data_stall_cycles - met_on.data_stall_cycles)
    speedup_pct = (
        ((res_off.total_cycles - res_on.total_cycles) / res_off.total_cycles * 100.0)
        if res_off.total_cycles > 0
        else 0.0
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Execution Cycles</div>
                <div class="metric-value" style="color:#22D3EE;">{res_on.total_cycles} <span style="font-size:0.92rem; color:#94A3B8;">vs {res_off.total_cycles}</span></div>
                <div class="metric-sub" style="color:#10B981;">Saved: {saved_cycles} cycles ({speedup_pct:.1f}% faster)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Data Stall Cycles</div>
                <div class="metric-value" style="color:#F43F5E;">{met_on.data_stall_cycles} <span style="font-size:0.92rem; color:#94A3B8;">vs {met_off.data_stall_cycles}</span></div>
                <div class="metric-sub" style="color:#10B981;">Eliminated: {stall_reduction} stalls</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        cpi_on = f"{met_on.cpi:.2f}" if met_on.cpi is not None else "n/a"
        cpi_off = f"{met_off.cpi:.2f}" if met_off.cpi is not None else "n/a"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">CPI Comparison</div>
                <div class="metric-value" style="color:#A78BFA;">{cpi_on} <span style="font-size:0.92rem; color:#94A3B8;">vs {cpi_off}</span></div>
                <div class="metric-sub">Lower is better</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Forwarding Events</div>
                <div class="metric-value" style="color:#10B981;">{met_on.forwarding_events} <span style="font-size:0.92rem; color:#94A3B8;">vs 0</span></div>
                <div class="metric-sub">EX/MEM + MEM/WB paths</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Synchronization Control
    sync_cycles = st.toggle(
        "🔗 Synchronize Cycle Navigation Between Modes",
        value=st.session_state.get("compare_sync_toggle", True),
        key="compare_sync_toggle",
    )

    # Initialize cycle states
    max_on = max(1, res_on.total_cycles)
    max_off = max(1, res_off.total_cycles)
    max_shared = max(max_on, max_off)

    if "comp_sync_cycle" not in st.session_state:
        st.session_state["comp_sync_cycle"] = 1
    if "comp_cycle_on" not in st.session_state:
        st.session_state["comp_cycle_on"] = 1
    if "comp_cycle_off" not in st.session_state:
        st.session_state["comp_cycle_off"] = 1

    # ---------------- Synchronized Global Stepper
    if sync_cycles:
        cur_sync = int(st.session_state["comp_sync_cycle"])
        cur_sync = max(1, min(cur_sync, max_shared))
        st.session_state["comp_sync_cycle"] = cur_sync

        def _step_sync(delta: int) -> None:
            new_val = max(1, min(max_shared, int(st.session_state["comp_sync_cycle"]) + delta))
            st.session_state["comp_sync_cycle"] = new_val
            st.session_state["comp_cycle_on"] = min(new_val, max_on)
            st.session_state["comp_cycle_off"] = min(new_val, max_off)

        def _reset_sync() -> None:
            st.session_state["comp_sync_cycle"] = 1
            st.session_state["comp_cycle_on"] = 1
            st.session_state["comp_cycle_off"] = 1

        def _slider_sync() -> None:
            val = int(st.session_state.get("slider_comp_sync", 1))
            st.session_state["comp_sync_cycle"] = val
            st.session_state["comp_cycle_on"] = min(val, max_on)
            st.session_state["comp_cycle_off"] = min(val, max_off)

        st.markdown(
            f"""
            <div style="background: rgba(17, 28, 46, 0.7); border: 1px solid #27364B; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.75rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:700; color:#22D3EE;">🔗 Synchronized Cycle Navigator</span>
                    <span style="font-size:0.85rem; color:#94A3B8;">Cycle <b>{cur_sync}</b> (Side A: {min(cur_sync, max_on)}/{max_on} · Side B: {min(cur_sync, max_off)}/{max_off})</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        b1, b2, b_slide, b3, b4, b5 = st.columns([1, 1, 4, 1, 1, 1])
        with b1:
            st.button("⏮️ -5", on_click=_step_sync, args=(-5,), key="btn_sync_m5", use_container_width=True)
        with b2:
            st.button("◀ Prev", on_click=_step_sync, args=(-1,), key="btn_sync_p1", use_container_width=True)
        with b_slide:
            st.slider(
                "Synchronized Clock Cycle",
                min_value=1,
                max_value=max_shared,
                value=cur_sync,
                key="slider_comp_sync",
                on_change=_slider_sync,
                label_visibility="collapsed",
            )
        with b3:
            st.button("Next ▶", on_click=_step_sync, args=(1,), key="btn_sync_n1", use_container_width=True)
        with b4:
            st.button("+5 ⏭️", on_click=_step_sync, args=(5,), key="btn_sync_p5", use_container_width=True)
        with b5:
            st.button("Reset (C1)", on_click=_reset_sync, key="btn_sync_rst", use_container_width=True)

        cycle_on = min(int(st.session_state["comp_sync_cycle"]), max_on)
        cycle_off = min(int(st.session_state["comp_sync_cycle"]), max_off)
    else:
        # Independent cycles
        cycle_on = int(st.session_state.get("comp_cycle_on", 1))
        cycle_off = int(st.session_state.get("comp_cycle_off", 1))

    # Split Comparison Columns
    col_on, col_off = st.columns(2)

    # ---------------- Side A: Forwarding ON
    with col_on:
        st.markdown("### ⚡ Side A: Forwarding ON")
        st.caption(f"Hardware bypass enabled · Total Cycles: {res_on.total_cycles}")

        # Independent Diagram View Mode
        mode_on = st.radio(
            "Diagram View Mode (Forwarding ON)",
            ["Window around cycle (Fast)", "Full program"],
            index=0 if res_on.total_cycles > 25 else 1,
            key="compare_mode_on",
            horizontal=True,
        )

        # Independent Stepper for Side A if not synchronized
        if not sync_cycles:
            def _step_on(delta: int) -> None:
                val = max(1, min(max_on, int(st.session_state.get("comp_cycle_on", 1)) + delta))
                st.session_state["comp_cycle_on"] = val

            def _slider_on_changed() -> None:
                val = int(st.session_state.get("slider_on_raw", 1))
                st.session_state["comp_cycle_on"] = max(1, min(val, max_on))

            c_on_p, c_on_s, c_on_n = st.columns([1, 3, 1])
            with c_on_p:
                st.button("◀ Prev (ON)", on_click=_step_on, args=(-1,), key="btn_on_prev", use_container_width=True)
            with c_on_s:
                st.slider(
                    "Cycle (Forwarding ON)",
                    min_value=1,
                    max_value=max_on,
                    value=cycle_on,
                    key="slider_on_raw",
                    on_change=_slider_on_changed,
                    label_visibility="collapsed",
                )
            with c_on_n:
                st.button("Next (ON) ▶", on_click=_step_on, args=(1,), key="btn_on_next", use_container_width=True)
            cycle_on = int(st.session_state.get("comp_cycle_on", 1))

        st.markdown(
            f"<div style='font-size:0.85rem; color:#22D3EE; font-weight:700; margin-bottom:0.5rem;'>Inspecting Cycle: {cycle_on} / {max_on}</div>",
            unsafe_allow_html=True,
        )

        window_on: Optional[Tuple[int, int]] = None
        if mode_on == "Window around cycle (Fast)":
            start = max(1, cycle_on - 12)
            end = min(res_on.total_cycles, cycle_on + 12)
            window_on = (start, end)

        fig_on = charts.timing_diagram(
            res_on,
            title=f"Forwarding ON (Cycle {cycle_on})",
            highlight_cycle=cycle_on,
            cycle_window=window_on,
        )
        show_chart(fig_on, key=f"comp_fig_on_{cycle_on}_{mode_on}")

    # ---------------- Side B: Forwarding OFF
    with col_off:
        st.markdown("### 🛑 Side B: Forwarding OFF")
        st.caption(f"Pure stall & bubble insertion · Total Cycles: {res_off.total_cycles}")

        # Independent Diagram View Mode
        mode_off = st.radio(
            "Diagram View Mode (Forwarding OFF)",
            ["Window around cycle (Fast)", "Full program"],
            index=0 if res_off.total_cycles > 25 else 1,
            key="compare_mode_off",
            horizontal=True,
        )

        # Independent Stepper for Side B if not synchronized (ALWAYS FULLY OPERATIONAL!)
        if not sync_cycles:
            def _step_off(delta: int) -> None:
                val = max(1, min(max_off, int(st.session_state.get("comp_cycle_off", 1)) + delta))
                st.session_state["comp_cycle_off"] = val

            def _slider_off_changed() -> None:
                val = int(st.session_state.get("slider_off_raw", 1))
                st.session_state["comp_cycle_off"] = max(1, min(val, max_off))

            c_off_p, c_off_s, c_off_n = st.columns([1, 3, 1])
            with c_off_p:
                st.button("◀ Prev (OFF)", on_click=_step_off, args=(-1,), key="btn_off_prev", use_container_width=True)
            with c_off_s:
                st.slider(
                    "Cycle (Forwarding OFF)",
                    min_value=1,
                    max_value=max_off,
                    value=cycle_off,
                    key="slider_off_raw",
                    on_change=_slider_off_changed,
                    label_visibility="collapsed",
                )
            with c_off_n:
                st.button("Next (OFF) ▶", on_click=_step_off, args=(1,), key="btn_off_next", use_container_width=True)
            cycle_off = int(st.session_state.get("comp_cycle_off", 1))

        st.markdown(
            f"<div style='font-size:0.85rem; color:#F43F5E; font-weight:700; margin-bottom:0.5rem;'>Inspecting Cycle: {cycle_off} / {max_off}</div>",
            unsafe_allow_html=True,
        )

        window_off: Optional[Tuple[int, int]] = None
        if mode_off == "Window around cycle (Fast)":
            start = max(1, cycle_off - 12)
            end = min(res_off.total_cycles, cycle_off + 12)
            window_off = (start, end)

        fig_off = charts.timing_diagram(
            res_off,
            title=f"Forwarding OFF (Cycle {cycle_off})",
            highlight_cycle=cycle_off,
            cycle_window=window_off,
        )
        show_chart(fig_off, key=f"comp_fig_off_{cycle_off}_{mode_off}")
