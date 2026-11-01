"""Development task planning engine for the Full Stack Engineering Agent."""

from __future__ import annotations

import re
import uuid
from typing import List, Optional

from agents.models import PlanStep, TaskPlan
from agents.repo_intelligence import RepoInspector


class Planner:
    """Produces structured engineering implementation plans with dependency and risk analysis."""

    def __init__(self, inspector: RepoInspector) -> None:
        self.inspector = inspector

    def generate_plan(self, requirement: str) -> TaskPlan:
        """Analyze a requirement against the codebase and build a step-by-step plan."""
        task_id = str(uuid.uuid4())[:8]
        low_req = requirement.lower()

        target_files: List[str] = []
        steps: List[PlanStep] = []
        risks: List[str] = []

        # Heuristic dependency and target detection
        if any(w in low_req for w in ["parser", "syntax", "token", "opcode", "operand"]):
            target_files.extend(["simulator/parser.py", "tests/test_parser.py"])
            risks.append("Modifying parser token regex might break backward-compatibility with existing labels.")

        if any(w in low_req for w in ["pipeline", "stage", "cycle", "clock", "latch", "register write"]):
            target_files.extend(["simulator/pipeline.py", "simulator/models.py", "tests/test_pipeline.py"])
            risks.append("Altering stage latency or latch timing may invalidate reference CPU verification.")

        if any(w in low_req for w in ["hazard", "stall", "bubble", "raw", "load-use"]):
            target_files.extend(["simulator/hazards.py", "simulator/analytics/hazard_analytics.py", "tests/test_hazards.py"])
            risks.append("Hazard detector changes must preserve slot conservation law (Useful + Stalls = Total).")

        if any(w in low_req for w in ["forward", "bypass", "branch", "jump", "flush", "squash"]):
            target_files.extend(["simulator/forwarding.py", "tests/test_forwarding.py"])
            risks.append("Forwarding priorities (EX/MEM vs MEM/WB) must strictly favor the newest producer.")

        if any(w in low_req for w in ["ui", "theme", "color", "dashboard", "diagram", "chart", "button", "slider"]):
            target_files.extend(["ui/theme.py", "ui/charts.py", "ui/pages/pipeline_view.py"])
            risks.append("UI changes must ensure theme consistency and avoid unnecessary Streamlit rerun stutter.")

        if any(w in low_req for w in ["bot", "verifier", "scheduler", "stress"]):
            target_files.extend(["bots/bot_runner.py", "bots/dev_bot.py", "tests/test_bots.py"])
            risks.append("Multi-bot changes must ensure exception isolation between individual bot runners.")

        # Default fallback if no specific keywords hit
        if not target_files:
            all_py = self.inspector.list_files()
            # Try keyword search in files
            words = [w for w in re.findall(r"\w+", low_req) if len(w) > 3]
            for w in words[:3]:
                matches = self.inspector.search_code(w)
                for m in matches[:2]:
                    if m["file"] not in target_files:
                        target_files.append(m["file"])

        if not target_files:
            target_files = ["app.py", "tests/test_audit_and_regressions.py"]

        target_files = sorted(list(set(target_files)))

        # Build systematic steps
        steps.append(
            PlanStep(
                step_num=1,
                description=f"Inspect target files ({', '.join(target_files[:3])}) and review baseline test coverage.",
                target_files=target_files,
                risks="None (read-only inspection).",
            )
        )
        steps.append(
            PlanStep(
                step_num=2,
                description="Draft targeted code modifications, respecting module ownership and boundary invariants.",
                target_files=target_files,
                risks="Possible syntax errors or unintended regression side-effects.",
            )
        )
        steps.append(
            PlanStep(
                step_num=3,
                description="Execute local verification suite via pytest and verify zero regressions.",
                target_files=target_files,
                risks="Test assertion failures require automated diagnostic parsing and bounded correction.",
            )
        )
        steps.append(
            PlanStep(
                step_num=4,
                description="Produce final execution audit, unified git diff summary, and verification report.",
                target_files=target_files,
                risks="None.",
            )
        )

        if not risks:
            risks.append("Code changes must pass 100% of existing regression assertions.")

        return TaskPlan(
            task_id=task_id,
            requirement=requirement,
            steps=steps,
            files_to_modify=target_files,
            potential_risks=risks,
        )
