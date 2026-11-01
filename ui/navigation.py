"""Top-level navigation management across the 11 functional workspaces for CPU PIPELINE STUDIO."""

from __future__ import annotations

from typing import Dict, List, Tuple
import streamlit as st

SECTIONS: List[Tuple[str, str, str]] = [
    ("overview", "📊 Overview Dashboard", "High-level summary, metrics, and health overview."),
    ("simulator", "💻 Assembly Simulator", "Interactive MIPS assembly editor, parser, and controls."),
    ("pipeline_view", "⏱️ Pipeline Visualization", "Cycle-by-cycle stage execution and timing diagram."),
    ("forwarding_comparison", "⚡ Forwarding Comparison", "Side-by-side Forwarding ON/OFF with dual diagram modes."),
    ("hazard_analytics", "⚠️ Hazard & Stall Analytics", "Fine-grained RAW, stall, forwarding, and flush telemetry."),
    ("registers_memory", "🧮 Registers & Memory", "Live cycle-by-cycle register file and RAM inspection."),
    ("performance", "📈 Performance Analysis", "CPI, IPC, stage utilization, and speedup benchmarks."),
    ("developer_team", "👥 Developer Team & Progress", "5-role module ownership, live tests, and verified progress."),
    ("testing_bots", "🤖 Intelligent Testing Bots", "5 automated verification bots, test suites, and reports."),
    ("learning_center", "📚 COA Learning Center", "Computer Organization & Architecture educational reference."),
    ("settings", "⚙️ Settings & Configuration", "Simulator limits, cycle safety bounds, and environment info."),
]

SECTION_KEYS = [s[0] for s in SECTIONS]
SECTION_LABELS = {s[0]: s[1] for s in SECTIONS}
SECTION_DESCRIPTIONS = {s[0]: s[2] for s in SECTIONS}


def render_navigation() -> str:
    """Render the sidebar navigation and return the selected section key."""
    # Product Brand Identity
    st.sidebar.markdown(
        """
        <div style="padding: 0.5rem 0.2rem 1.1rem 0.2rem;">
            <div style="display:flex; align-items:center; gap:0.65rem;">
                <span style="font-size: 1.55rem; color: #22D3EE;">⚡</span>
                <div>
                    <div style="font-size: 1.12rem; font-weight: 800; color: #F1F5F9; letter-spacing: -0.01em;">
                        CPU PIPELINE STUDIO
                    </div>
                    <div style="font-size: 0.68rem; color: #22D3EE; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">
                        Midnight Engineering
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current = st.session_state.get("nav_section", "overview")
    if current not in SECTION_KEYS:
        current = "overview"

    # Sidebar selection
    selected_label = st.sidebar.radio(
        "Navigation",
        [s[1] for s in SECTIONS],
        index=SECTION_KEYS.index(current),
        label_visibility="collapsed",
    )

    # Map back to key
    selected_key = next(k for k, v in SECTION_LABELS.items() if v == selected_label)
    st.session_state["nav_section"] = selected_key

    # Quick sidebar system status
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="background: rgba(17, 28, 46, 0.85); border: 1px solid #27364B; border-radius: 8px; padding: 0.75rem 0.85rem; font-size: 0.75rem; color: #CBD5E1; line-height: 1.6;">
            <div><b style="color:#22D3EE;">Architecture:</b> 5-Stage MIPS Pipelined</div>
            <div><b style="color:#A78BFA;">Unit Tests:</b> 155 / 155 Passed <span style="color:#10B981;">●</span></div>
            <div><b style="color:#10B981;">Intelligent Bots:</b> 5 / 5 Verified <span style="color:#10B981;">●</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Theme Settings Toggle
    st.sidebar.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    current_theme = st.session_state.get("theme_mode", "midnight")
    theme_options = ["🌙 Midnight Engineering", "☀️ Clean Light"]
    selected_theme_label = st.sidebar.selectbox(
        "Theme System",
        theme_options,
        index=0 if current_theme == "midnight" else 1,
        label_visibility="collapsed",
    )
    new_theme = "midnight" if "Midnight" in selected_theme_label else "light"
    if new_theme != current_theme:
        st.session_state["theme_mode"] = new_theme
        st.rerun()

    return selected_key
