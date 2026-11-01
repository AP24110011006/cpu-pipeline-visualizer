"""Keeps the project root on sys.path and safely manages test collection across modular branches."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

collect_ignore = []

# Map of test files to the source files they require
MODULE_REQUIREMENTS = {
    "tests/test_parser.py": ["simulator/parser.py"],
    "tests/test_pipeline.py": ["simulator/pipeline.py"],
    "tests/test_reference.py": ["simulator/reference.py"],
    "tests/test_engine_and_explainer.py": ["simulator/engine.py", "simulator/explainer.py"],
    "tests/test_hazards.py": ["simulator/hazards.py"],
    "tests/test_analytics.py": ["simulator/hazards.py", "simulator/analytics/hazard_analytics.py"],
    "tests/test_metrics.py": ["simulator/metrics.py"],
    "tests/test_forwarding.py": ["simulator/forwarding.py"],
    "tests/test_audit_and_regressions.py": ["simulator/forwarding.py", "simulator/pipeline.py"],
    "tests/test_team_and_theme.py": ["ui/theme.py"],
    "tests/test_bots.py": ["simulator/pipeline.py", "simulator/parser.py", "simulator/hazards.py", "simulator/metrics.py"],
    "tests/test_bots_extended.py": ["simulator/pipeline.py", "simulator/parser.py", "simulator/hazards.py", "simulator/metrics.py"],
    "tests/test_dev_bot_suite.py": ["bots/dev_bot.py", "simulator/hazards.py", "simulator/metrics.py"],
    "tests/test_agents.py": ["agents/orchestrator.py"],
}

for test_rel, reqs in MODULE_REQUIREMENTS.items():
    if (ROOT / test_rel).exists():
        if any(not (ROOT / req).exists() for req in reqs):
            collect_ignore.append(test_rel)
