"""Settings & Configuration Workspace: simulator resource limits and environment diagnostics."""

from __future__ import annotations

import platform
import sys
import streamlit as st


def render_settings() -> None:
    """Render the configuration, execution limits, and environment diagnostics."""
    st.markdown("## ⚙️ Settings & Configuration")
    st.caption("Manage execution safety limits, clear session cache, and inspect runtime environment diagnostics.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🛡️ Safety & Execution Bounds")
        st.number_input(
            "Default Maximum Cycles Limit",
            min_value=50,
            max_value=20000,
            value=int(st.session_state.get("opt_max_cycles", 500)),
            step=100,
            key="cfg_max_cycles",
            help="Threshold to terminate execution if an infinite loop is simulated.",
        )
        st.number_input(
            "Default Maximum Static Instructions",
            min_value=50,
            max_value=10000,
            value=int(st.session_state.get("opt_max_instructions", 2000)),
            step=250,
            key="cfg_max_instructions",
            help="Safety threshold for parsing large programs.",
        )

        if st.button("Apply Safety Settings", type="primary"):
            st.session_state["opt_max_cycles"] = st.session_state["cfg_max_cycles"]
            st.session_state["opt_max_instructions"] = st.session_state["cfg_max_instructions"]
            st.success("Safety configuration updated successfully.")

    with c2:
        st.markdown("### 🧹 Session & Cache Management")
        st.caption("Reset application session state, clear cached simulation traces, and free browser memory.")
        if st.button("Clear Session State & Cache", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.success("Session state cleared. Reloading application...")
            st.rerun()

    st.markdown("---")
    st.markdown("### 💻 Environment Diagnostics")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Python Runtime", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    d2.metric("Streamlit Version", st.__version__)
    d3.metric("Operating System", platform.system())
    d4.metric("Architecture", platform.machine())
