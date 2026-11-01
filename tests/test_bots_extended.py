"""Tests for extended intelligent bots and runner."""

from bots.bot_runner import export_reports_json, export_reports_markdown, run_single_bot
from bots.hazard_bot import run_hazard_bot
from bots.stress_bot import run_stress_bot


def test_hazard_bot_execution():
    rep = run_hazard_bot()
    assert rep.total == 64
    assert rep.all_passed


def test_stress_bot_execution():
    rep = run_stress_bot(max_scale=1000)
    assert rep.all_passed
    assert rep.passed >= 6


def test_bot_runner_and_export():
    rep_test = run_single_bot("test_bot")
    assert rep_test.all_passed

    json_str = export_reports_json([rep_test])
    assert "Test Bot" in json_str

    md_str = export_reports_markdown([rep_test])
    assert "Test Bot" in md_str
