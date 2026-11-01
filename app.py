"""CPU Pipeline Execution Visualizer - Streamlit entry point.

Run with:  streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="CPU PIPELINE STUDIO — Engineering Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.dashboard import render_dashboard  # noqa: E402  (must come after set_page_config)

render_dashboard()
