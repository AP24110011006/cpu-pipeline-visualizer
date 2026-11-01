"""Small wrappers that keep the UI code working across Streamlit versions."""

from __future__ import annotations

import streamlit as st


def _streamlit_at_least(major: int, minor: int) -> bool:
    try:
        parts = tuple(int(piece) for piece in st.__version__.split(".")[:2])
    except ValueError:
        return True
    return parts >= (major, minor)


_NEW_WIDTH_API = _streamlit_at_least(1, 50)


def show_df(dataframe, **kwargs) -> None:
    """Full-width table without the index column."""
    if _NEW_WIDTH_API:
        st.dataframe(dataframe, hide_index=True, width="stretch", **kwargs)
    else:
        st.dataframe(dataframe, hide_index=True, use_container_width=True, **kwargs)


def show_chart(figure, key: str) -> None:
    """Full-width high-performance Plotly chart with minimal DOM overhead."""
    config = {"displayModeBar": False, "responsive": True}
    if _NEW_WIDTH_API:
        st.plotly_chart(figure, width="stretch", key=key, config=config)
    else:
        st.plotly_chart(figure, use_container_width=True, key=key, config=config)
