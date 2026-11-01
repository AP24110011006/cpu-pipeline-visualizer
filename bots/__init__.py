"""Intelligent Multi-Bot Engineering Suite for CPU PIPELINE STUDIO.

Bot 1 - TestBot: Scenario regression testing against textbook hand-verified programs.
Bot 2 - VerifierBot: Differential testing against reference CPU and structural invariants.
Bot 3 - Assembly Optimization Bot: DAG topological scheduling, hazard optimization, and workload synthesis.
Bot 4 - StressBot: Large-scale workload generation (100–5,000 instructions) and memory profiling.
Bot 5 - HazardBot: Microarchitectural conservation law and zero double-counting audits.
"""

from __future__ import annotations

from bots.bot_runner import (
    BOT_REGISTRY,
    export_reports_json,
    export_reports_markdown,
    run_all_bots,
    run_single_bot,
)
from bots.dev_bot import (
    DevBot,
    analyze_code,
    optimize_schedule,
    run_dev_bot,
    synthesize_program,
)
from bots.hazard_bot import run_hazard_bot
from bots.report import BotReport, CheckResult
from bots.stress_bot import run_stress_bot
from bots.test_bot import run_test_bot
from bots.verifier_bot import run_verifier_bot, verify_program

__all__ = [
    "BOT_REGISTRY",
    "BotReport",
    "CheckResult",
    "DevBot",
    "analyze_code",
    "export_reports_json",
    "export_reports_markdown",
    "optimize_schedule",
    "run_all_bots",
    "run_dev_bot",
    "run_hazard_bot",
    "run_single_bot",
    "run_stress_bot",
    "run_test_bot",
    "run_verifier_bot",
    "synthesize_program",
    "verify_program",
]
