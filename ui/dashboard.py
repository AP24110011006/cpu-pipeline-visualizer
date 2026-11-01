"""Master Streamlit Dashboard Router for CPU Pipeline Execution Visualizer.

Orchestrates navigation across the 11 professional engineering workspaces:
1. Overview Dashboard
2. Assembly Simulator
3. Pipeline Visualization
4. Forwarding Comparison
5. Hazard & Stall Analytics
6. Registers & Memory
7. Performance Analysis
8. Developer Team & Progress
9. Intelligent Testing Bots
10. COA Learning Center
11. Settings & Configuration
"""

from __future__ import annotations

from typing import Optional
import streamlit as st

from simulator.engine import EngineResult, run_pipeline_engine
from simulator.models import PipelineConfig
from simulator.samples import DEFAULT_SAMPLE, SAMPLES
from ui.navigation import render_navigation
from ui.pages.developer_team import render_developer_team
from ui.pages.forwarding_comparison import render_forwarding_comparison
from ui.pages.hazard_analytics import render_hazard_analytics
from ui.pages.learning_center import render_learning_center
from ui.pages.overview import render_overview
from ui.pages.performance import render_performance
from ui.pages.pipeline_view import render_pipeline_view
from ui.pages.registers_memory import render_registers_memory
from ui.pages.settings import render_settings
from ui.pages.simulator import render_simulator
from ui.pages.testing_bots import render_testing_bots
from ui.theme import inject_theme


# =========================================================================== State Management
def _init_state() -> None:
    sample = SAMPLES[DEFAULT_SAMPLE]
    st.session_state.setdefault("sample_choice", DEFAULT_SAMPLE)
    st.session_state.setdefault("code_input", sample.code)
    st.session_state.setdefault("init_regs", sample.registers)
    st.session_state.setdefault("init_mem", sample.memory)
    st.session_state.setdefault("engine_result", None)
    st.session_state.setdefault("cycle_view", 1)
    st.session_state.setdefault("nav_section", "overview")

    # Initial auto-run on first load if not simulated yet
    if st.session_state.get("engine_result") is None:
        _execute_simulation()


def _on_sample_change() -> None:
    choice = st.session_state.get("sample_choice", DEFAULT_SAMPLE)
    if choice in SAMPLES:
        sample = SAMPLES[choice]
        st.session_state["code_input"] = sample.code
        st.session_state["init_regs"] = sample.registers
        st.session_state["init_mem"] = sample.memory
        _execute_simulation()


def _on_file_upload() -> None:
    uploaded = st.session_state.get("file_uploader")
    if uploaded is not None:
        try:
            content = uploaded.getvalue().decode("utf-8")
            st.session_state["code_input"] = content
            _execute_simulation()
        except Exception as e:
            st.error(f"Failed to read uploaded file: {e}")


def _execute_simulation() -> None:
    """Executes the pipeline simulation engine once and caches the dual-mode result."""
    code = st.session_state.get("code_input", "")
    regs = st.session_state.get("init_regs", "")
    mem = st.session_state.get("init_mem", "")

    config = PipelineConfig(
        forwarding=bool(st.session_state.get("opt_forwarding", True)),
        reg_write_first_half=bool(st.session_state.get("opt_first_half", True)),
        branch_policy=st.session_state.get("opt_policy", "predict_not_taken"),
        max_cycles=int(st.session_state.get("opt_max_cycles", 500)),
    )
    max_instr = int(st.session_state.get("opt_max_instructions", 2000))

    result = run_pipeline_engine(
        code=code,
        init_regs_str=regs,
        init_mem_str=mem,
        config=config,
        max_instructions=max_instr,
    )
    st.session_state["engine_result"] = result

    # Set cycle view to 1
    if result.ok and result.primary and result.primary.total_cycles > 0:
        st.session_state["cycle_view"] = 1


# =========================================================================== Main Entry Point
def render_dashboard() -> None:
    """Master entry point invoked by app.py."""
    inject_theme()
    _init_state()

    # Sidebar Navigation Router
    active_section = render_navigation()
    engine_res: Optional[EngineResult] = st.session_state.get("engine_result")

    # Route to selected page
    if active_section == "overview":
        render_overview(engine_res)
    elif active_section == "simulator":
        render_simulator(engine_res, _execute_simulation, _on_sample_change, _on_file_upload)
    elif active_section == "pipeline_view":
        render_pipeline_view(engine_res)
    elif active_section == "forwarding_comparison":
        render_forwarding_comparison(engine_res)
    elif active_section == "hazard_analytics":
        render_hazard_analytics(engine_res)
    elif active_section == "registers_memory":
        render_registers_memory(engine_res)
    elif active_section == "performance":
        render_performance(engine_res)
    elif active_section == "developer_team":
        render_developer_team()
    elif active_section == "testing_bots":
        render_testing_bots(engine_res)
    elif active_section == "learning_center":
        render_learning_center()
    elif active_section == "settings":
        render_settings()
    else:
        render_overview(engine_res)
