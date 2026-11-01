"""Unified Midnight Engineering Design System and Token System for CPU PIPELINE STUDIO.

Implements exact design tokens from Section 3:
- Primary theme: MIDNIGHT ENGINEERING (Dark)
- Optional theme: CLEAN ENGINEERING (Light)
- Unified Pipeline Stage Colors across the entire application
- Theme-mode toggle stored in st.session_state["theme_mode"]
"""

from __future__ import annotations

from typing import Dict
import streamlit as st

# =========================================================================== Design Tokens
# Exact Midnight Engineering Palette
DARK_TOKENS: Dict[str, str] = {
    "bg_main": "#0B1220",
    "surface_main": "#111C2E",
    "surface_secondary": "#162338",
    "border_color": "#27364B",
    "accent_primary": "#22D3EE",
    "accent_secondary": "#A78BFA",
    "status_success": "#10B981",
    "status_warning": "#F59E0B",
    "status_error": "#F43F5E",
    "text_primary": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
}

# Optional Clean Engineering Light Palette
LIGHT_TOKENS: Dict[str, str] = {
    "bg_main": "#F4F7FB",
    "surface_main": "#FFFFFF",
    "surface_secondary": "#F1F5F9",
    "border_color": "#CBD5E1",
    "accent_primary": "#2563EB",
    "accent_secondary": "#0D9488",
    "status_success": "#10B981",
    "status_warning": "#F59E0B",
    "status_error": "#F43F5E",
    "text_primary": "#172554",
    "text_secondary": "#475569",
    "text_muted": "#64748B",
}

# Canonical Pipeline Stage Colors (identical in both themes)
STAGE_COLORS: Dict[str, str] = {
    "IF": "#3B82F6",
    "ID": "#8B5CF6",
    "EX": "#F59E0B",
    "MEM": "#06B6D4",
    "WB": "#10B981",
    "STALL": "#EF4444",
    "BUBBLE": "#64748B",
    "FORWARDING": "#22D3EE",
    "FLUSH": "#F43F5E",
}


def get_current_theme() -> str:
    """Return 'midnight' (default) or 'light'."""
    return st.session_state.get("theme_mode", "midnight")


def build_theme_css(theme_mode: str = "midnight") -> str:
    """Generate scoped CSS variables and rules for the active theme."""
    tokens = LIGHT_TOKENS if theme_mode == "light" else DARK_TOKENS

    is_dark = theme_mode != "light"
    banner_bg = "linear-gradient(135deg, #111C2E 0%, #162338 100%)" if is_dark else "linear-gradient(135deg, #FFFFFF 0%, #F1F5F9 100%)"
    sidebar_bg = "#0D1525" if is_dark else "#FFFFFF"
    card_shadow = "0 8px 24px rgba(0, 0, 0, 0.45)" if is_dark else "0 4px 16px rgba(0, 0, 0, 0.06)"

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    :root {{
        --bg-main: {tokens['bg_main']};
        --surface-main: {tokens['surface_main']};
        --surface-secondary: {tokens['surface_secondary']};
        --border-color: {tokens['border_color']};
        --accent-primary: {tokens['accent_primary']};
        --accent-secondary: {tokens['accent_secondary']};
        --status-success: {tokens['status_success']};
        --status-warning: {tokens['status_warning']};
        --status-error: {tokens['status_error']};
        --text-primary: {tokens['text_primary']};
        --text-secondary: {tokens['text_secondary']};
        --text-muted: {tokens['text_muted']};
        --card-shadow: {card_shadow};
    }}

    /* Global Body & Typography */
    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-size: 14px;
        color: var(--text-primary) !important;
    }}

    code, kbd, samp, pre {{
        font-family: 'JetBrains Mono', Consolas, monospace !important;
        font-size: 13px !important;
    }}

    .stApp {{
        background-color: var(--bg-main) !important;
        background-image: radial-gradient(circle at 15% 15%, rgba(34, 211, 238, 0.05) 0%, transparent 40%),
                          radial-gradient(circle at 85% 85%, rgba(167, 139, 250, 0.04) 0%, transparent 40%) !important;
        background-attachment: fixed !important;
    }}

    .block-container {{
        padding-top: 1.0rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1440px !important;
    }}

    /* Sidebar Navigation */
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        border-right: 1px solid var(--border-color) !important;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.25) !important;
    }}

    [data-testid="stSidebar"] .stRadio > label {{
        font-size: 11.5px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: var(--accent-primary) !important;
    }}

    /* Header Banner */
    .pro-banner {{
        background: {banner_bg} !important;
        border: 1px solid var(--border-color) !important;
        border-left: 5px solid var(--accent-primary) !important;
        border-radius: 12px !important;
        padding: 1.1rem 1.5rem !important;
        margin-bottom: 1.2rem !important;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: var(--card-shadow) !important;
    }}

    .pro-banner-title {{
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
        margin: 0 !important;
        color: var(--text-primary) !important;
    }}

    .pro-banner-desc {{
        font-size: 0.88rem !important;
        color: var(--text-secondary) !important;
        margin: 0.2rem 0 0 0 !important;
        font-weight: 500 !important;
    }}

    .pro-banner-badge {{
        background: rgba(34, 211, 238, 0.12) !important;
        color: var(--accent-primary) !important;
        border: 1px solid rgba(34, 211, 238, 0.3) !important;
        padding: 0.35rem 0.8rem !important;
        border-radius: 6px !important;
        font-size: 0.8rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
    }}

    /* Metric KPI Cards */
    .metric-card {{
        background: var(--surface-main) !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: var(--card-shadow) !important;
        border-radius: 10px !important;
        padding: 0.9rem 1.1rem !important;
        margin-bottom: 0.75rem !important;
        transition: transform 0.15s ease, border-color 0.15s ease !important;
    }}

    .metric-card:hover {{
        transform: translateY(-2px);
        border-color: var(--accent-primary) !important;
    }}

    .metric-label {{
        font-size: 0.76rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        color: var(--text-secondary) !important;
        margin-bottom: 0.25rem !important;
    }}

    .metric-value {{
        font-size: 1.55rem !important;
        font-weight: 800 !important;
        line-height: 1.15 !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.01em !important;
    }}

    .metric-sub {{
        font-size: 0.78rem !important;
        color: var(--text-muted) !important;
        margin-top: 0.25rem !important;
        font-weight: 500 !important;
    }}

    /* Stage Slot Cards */
    .stage-slot {{
        background: var(--surface-main) !important;
        border: 1px solid var(--border-color) !important;
        border-top: 3.5px solid var(--accent-primary) !important;
        border-radius: 8px !important;
        padding: 0.75rem 0.85rem !important;
        min-height: 88px !important;
        box-shadow: var(--card-shadow) !important;
    }}

    .stage-slot-name {{
        font-size: 0.74rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: var(--text-secondary) !important;
        margin-bottom: 0.3rem !important;
    }}

    .stage-slot-content {{
        font-size: 0.88rem !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        word-break: break-all !important;
    }}

    /* Developer Cards */
    .dev-card {{
        background: var(--surface-main) !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: var(--card-shadow) !important;
        border-radius: 10px !important;
        padding: 1.05rem 1.25rem !important;
        margin-bottom: 0.9rem !important;
    }}

    .dev-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.65rem;
    }}

    .dev-member {{
        display: flex;
        align-items: center;
        gap: 0.85rem;
    }}

    .dev-avatar {{
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: linear-gradient(135deg, rgba(34, 211, 238, 0.25) 0%, rgba(167, 139, 250, 0.25) 100%);
        border: 1.5px solid var(--accent-primary);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.85rem;
        color: var(--text-primary);
    }}

    .dev-title {{
        font-size: 1.0rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
    }}

    .dev-subtitle {{
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin: 0.15rem 0 0 0;
    }}

    .dev-status-badge {{
        padding: 0.2rem 0.65rem;
        border-radius: 5px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    .badge-verified {{
        background: rgba(16, 185, 129, 0.15) !important;
        color: #10B981 !important;
        border: 1px solid rgba(16, 185, 129, 0.35) !important;
    }}

    /* Buttons */
    .stButton > button {{
        background: var(--surface-secondary) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
        transition: all 0.15s ease !important;
    }}

    .stButton > button:hover {{
        border-color: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
        transform: translateY(-1px) !important;
    }}

    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #0284C7 0%, #2563EB 100%) !important;
        border: 1px solid rgba(34, 211, 238, 0.4) !important;
        color: #FFFFFF !important;
    }}

    /* Sliders - Precision Custom Theme Styling */
    div[data-baseweb="slider"] {{
        margin-top: 0.4rem !important;
    }}
    div[data-baseweb="slider"] div[role="slider"] {{
        background-color: var(--accent-primary) !important;
        border: 2px solid #FFFFFF !important;
        box-shadow: 0 0 10px rgba(34, 211, 238, 0.6) !important;
        width: 18px !important;
        height: 18px !important;
    }}
    .stSlider [data-baseweb="slider"] > div:first-child > div:first-child {{
        background: var(--surface-secondary) !important;
        border: 1px solid var(--border-color) !important;
        height: 7px !important;
        border-radius: 4px !important;
    }}
    .stSlider [data-baseweb="slider"] > div:first-child > div:first-child > div {{
        background: linear-gradient(90deg, #22D3EE, #10B981) !important;
        border-radius: 4px !important;
    }}

    /* Radio Buttons - Midnight Engineering Styling */
    div[data-testid="stRadio"] {{
        background: var(--surface-main) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.8rem !important;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] {{
        gap: 0.8rem !important;
    }}
    div[data-testid="stRadio"] label {{
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 0.84rem !important;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] input:checked + div {{
        border-color: var(--accent-primary) !important;
        background-color: var(--accent-primary) !important;
        box-shadow: 0 0 8px rgba(34, 211, 238, 0.5) !important;
    }}

    /* Toggle Switch */
    div[data-testid="stToggle"] label span {{
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }}

    /* Selectboxes */
    div[data-baseweb="select"] > div {{
        background: var(--surface-main) !important;
        border-color: var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 6px !important;
    }}

    /* Inputs & Code Areas */
    .stTextArea textarea {{
        background: var(--surface-main) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 13.5px !important;
    }}

    .stTextArea textarea:focus {{
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 10px rgba(34, 211, 238, 0.25) !important;
    }}

    .stTextInput input {{
        background: var(--surface-main) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
        color: var(--text-primary) !important;
    }}

    .stTextInput input:focus {{
        border-color: var(--accent-primary) !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background: var(--surface-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 0.25rem !important;
        gap: 0.35rem !important;
    }}

    .stTabs [data-baseweb="tab"] {{
        border-radius: 6px !important;
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 0.84rem !important;
        padding: 0.4rem 0.9rem !important;
        border: none !important;
        background: transparent !important;
    }}

    .stTabs [aria-selected="true"] {{
        color: var(--accent-primary) !important;
        background: var(--surface-main) !important;
        border: 1px solid var(--border-color) !important;
    }}

    /* DataTables & DataFrames */
    [data-testid="stDataFrame"] {{
        background: var(--surface-main) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }}

    /* Expanders */
    [data-testid="stExpander"] {{
        background: var(--surface-main) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }}
    </style>
    """


def inject_theme() -> None:
    """Inject active theme CSS into the Streamlit app session."""
    mode = get_current_theme()
    st.markdown(build_theme_css(mode), unsafe_allow_html=True)
