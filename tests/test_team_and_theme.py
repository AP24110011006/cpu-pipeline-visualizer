"""Regression tests verifying authoritative developer assignments, theme tokens, and bot isolation."""

from __future__ import annotations

import pytest

from bots.bot_runner import BOT_REGISTRY, run_all_bots, run_single_bot
from ui.charts import STAGE_COLORS as CHART_STAGE_COLORS, STALL_COLOR, FLUSH_COLOR
from ui.pages.developer_team import TEAM_ROLES
from ui.theme import DARK_TOKENS, LIGHT_TOKENS, STAGE_COLORS as THEME_STAGE_COLORS, build_theme_css


def test_authoritative_developer_team_assignments() -> None:
    """Verify Section 5 developer names, modules, and honest progress calculation."""
    expected_team = {
        "parser": ("REHMAN", "simulator/parser.py"),
        "pipeline": ("Likhith", "simulator/pipeline.py, simulator/models.py"),
        "hazards": ("MANIKANTH", "simulator/hazards.py, simulator/analytics/"),
        "forwarding": ("LATHISH", "simulator/forwarding.py, control-flow logic"),
        "ui": ("MADHAN", "app.py, ui/"),
    }

    role_map = {r["id"]: r for r in TEAM_ROLES}
    assert len(role_map) == 5

    for role_id, (expected_name, expected_module) in expected_team.items():
        assert role_id in role_map, f"Missing role ID: {role_id}"
        role = role_map[role_id]
        assert role["member"] == expected_name, f"Role {role_id} name mismatch: {role['member']} != {expected_name}"
        assert role["module"] == expected_module

        # Honest progress verification: must be evidence-based and not fake 100%
        assert 0 < role["progress"] < 100, f"Role {role_id} progress ({role['progress']}%) must reflect active pending backlog."
        assert len(role["completed_tasks"]) > 0
        assert len(role["pending_tasks"]) > 0


def test_midnight_engineering_design_tokens() -> None:
    """Verify exact Midnight Engineering tokens specified in Section 3."""
    assert DARK_TOKENS["bg_main"] == "#0B1220"
    assert DARK_TOKENS["surface_main"] == "#111C2E"
    assert DARK_TOKENS["surface_secondary"] == "#162338"
    assert DARK_TOKENS["border_color"] == "#27364B"
    assert DARK_TOKENS["accent_primary"] == "#22D3EE"
    assert DARK_TOKENS["accent_secondary"] == "#A78BFA"
    assert DARK_TOKENS["status_success"] == "#10B981"
    assert DARK_TOKENS["status_warning"] == "#F59E0B"
    assert DARK_TOKENS["status_error"] == "#F43F5E"
    assert DARK_TOKENS["text_primary"] == "#F1F5F9"
    assert DARK_TOKENS["text_secondary"] == "#94A3B8"
    assert DARK_TOKENS["text_muted"] == "#64748B"


def test_pipeline_stage_colors_unification() -> None:
    """Verify identical stage colors between theme and charts."""
    expected_stages = {
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
    for stage, color in expected_stages.items():
        assert THEME_STAGE_COLORS[stage] == color
        if stage in CHART_STAGE_COLORS:
            assert CHART_STAGE_COLORS[stage] == color

    assert STALL_COLOR == "#EF4444"
    assert FLUSH_COLOR == "#F43F5E"


def test_bot_exception_isolation() -> None:
    """Verify that a failing or throwing bot runner does not crash other bot executions."""
    # Temporarily monkeypatch test_bot to raise an exception
    orig_runner = BOT_REGISTRY["test_bot"]["runner"]
    try:
        BOT_REGISTRY["test_bot"]["runner"] = lambda: (_ for _ in ()).throw(RuntimeError("Simulated Hardware Sensor Failure"))
        crashed_report = run_single_bot("test_bot")
        assert not crashed_report.all_passed
        assert crashed_report.stats.get("crashed") is True
        assert any("Simulated Hardware Sensor Failure" in f for f in crashed_report.failures)
    finally:
        BOT_REGISTRY["test_bot"]["runner"] = orig_runner


def test_metrics_table_input_flexibility() -> None:
    """Verify metrics_table accepts single PerformanceMetrics object and dict."""
    from simulator.engine import run_pipeline_engine
    from simulator.models import PipelineConfig
    from ui.tables import metrics_table

    res = run_pipeline_engine("ADD R1, R2, R3", "", "", config=PipelineConfig())
    assert res.ok

    # Single PerformanceMetrics object
    df_single = metrics_table(res.metrics_primary)
    assert not df_single.empty
    assert "Metric" in df_single.columns

    # Dict of PerformanceMetrics
    df_dict = metrics_table({"ON": res.metrics_on, "OFF": res.metrics_off})
    assert not df_dict.empty
    assert "ON" in df_dict.columns
    assert "OFF" in df_dict.columns
