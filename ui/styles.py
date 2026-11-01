"""Design System & Styles Bridge.

Delegates to ui.theme for unified Midnight Engineering design tokens.
Preserved for backward-compatibility with any legacy imports.
"""

from __future__ import annotations

from ui.theme import DARK_TOKENS, LIGHT_TOKENS, STAGE_COLORS, build_theme_css, inject_theme

CSS = build_theme_css("midnight")

__all__ = [
    "CSS",
    "DARK_TOKENS",
    "LIGHT_TOKENS",
    "STAGE_COLORS",
    "build_theme_css",
    "inject_theme",
]
