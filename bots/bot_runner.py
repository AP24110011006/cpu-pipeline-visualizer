"""Unified Bot Runner: orchestrates TestBot, VerifierBot, Assembly Optimization Bot, StressBot, and HazardBot."""

from __future__ import annotations

import json
import time
import traceback
from typing import Callable, Dict, List, Optional

from bots.dev_bot import run_dev_bot
from bots.hazard_bot import run_hazard_bot
from bots.report import BotReport
from bots.stress_bot import run_stress_bot
from bots.test_bot import run_test_bot
from bots.verifier_bot import run_verifier_bot

BOT_REGISTRY: Dict[str, Dict[str, object]] = {
    "test_bot": {
        "name": "Bot 1: Testing Bot (Scenario & Negative Tests)",
        "runner": lambda: run_test_bot(),
        "description": "27 regression scenarios and 10 syntax edge-case rejections.",
    },
    "verifier_bot": {
        "name": "Bot 2: Verification Bot (Differential & Invariants)",
        "runner": lambda: run_verifier_bot(programs=100, seed=1),
        "description": "Differential validation against reference CPU across 800 pipeline runs.",
    },
    "dev_bot": {
        "name": "Bot 3: Assembly Optimization Bot (Scheduler & Synthesizer)",
        "runner": lambda: run_dev_bot(),
        "description": "DAG topological instruction scheduler, RAW/WAR/WAW preservation, code synthesis.",
    },
    "stress_bot": {
        "name": "Bot 4: Stress Testing Bot (Scalability & Limits)",
        "runner": lambda: run_stress_bot(max_scale=2000),
        "description": "High-throughput workload generation, memory tracking, and safety bounds.",
    },
    "hazard_bot": {
        "name": "Bot 5: Hazard Analysis Bot (Conservation & Audits)",
        "runner": lambda: run_hazard_bot(),
        "description": "Mathematical pipeline conservation, slot audits, and zero double-counting checks.",
    },
}


def run_single_bot(bot_key: str) -> BotReport:
    """Run a specific bot by key with isolated exception handling."""
    if bot_key not in BOT_REGISTRY:
        raise ValueError(f"Unknown bot: {bot_key}. Available: {list(BOT_REGISTRY.keys())}")

    bot_info = BOT_REGISTRY[bot_key]
    bot_name = str(bot_info.get("name", bot_key))
    runner_fn = bot_info["runner"]

    t0 = time.perf_counter()
    try:
        report = runner_fn()  # type: ignore
        return report
    except Exception as err:
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        error_tb = traceback.format_exc()
        crash_report = BotReport(bot=bot_name)
        crash_report.add("Bot Runtime Execution", False, f"Exception: {err}")
        crash_report.failures.append(f"Bot '{bot_key}' crashed:\n{error_tb}")
        crash_report.stats = {"runtime_ms": elapsed, "crashed": True}
        return crash_report


def run_all_bots() -> List[BotReport]:
    """Execute all 5 bots in sequence with per-bot failure isolation."""
    reports: List[BotReport] = []
    for key in BOT_REGISTRY:
        reports.append(run_single_bot(key))
    return reports


def export_reports_json(reports: List[BotReport]) -> str:
    """Serialize bot reports to a structured JSON string."""
    data = []
    for r in reports:
        data.append({
            "bot": r.bot,
            "total_checks": r.total,
            "passed": r.passed,
            "failed": r.failed,
            "all_passed": r.all_passed,
            "stats": r.stats,
            "checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail}
                for c in r.checks
            ],
            "failures": r.failures,
        })
    return json.dumps({"timestamp": time.time(), "reports": data}, indent=2)


def export_reports_markdown(reports: List[BotReport]) -> str:
    """Format bot reports into a markdown string."""
    lines = ["# 🤖 CPU PIPELINE STUDIO Intelligent Bots Test Report", ""]
    for r in reports:
        status_icon = "✅" if r.all_passed else "❌"
        lines.append(f"## {status_icon} {r.bot} ({r.passed}/{r.total} Passed)")
        lines.append(f"**Verdict**: {'ALL PASSED' if r.all_passed else 'FAILURES DETECTED'}")
        if r.stats:
            stats_str = ", ".join(f"`{k}`: {v}" for k, v in r.stats.items())
            lines.append(f"**Metrics**: {stats_str}")
        lines.append("")
        lines.append("| Status | Check | Details |")
        lines.append("|:---:|:---|:---|")
        for c in r.checks:
            icon = "✅ PASS" if c.passed else "❌ FAIL"
            lines.append(f"| {icon} | {c.name} | {c.detail or '—'} |")
        lines.append("")
    return "\n".join(lines)
