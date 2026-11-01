"""Pedagogical explainer for pipeline cycles.

Produces simple, student-friendly explanations of:
- What each pipeline stage is doing in the selected cycle
- Why stalls, bubbles, or flushes occurred
- Active data forwarding paths
- State changes (register/memory writes)
- What will happen in the subsequent cycle
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from simulator.models import STAGES, STAGE_INFO, CycleSnapshot, SimulationResult


@dataclass
class StageDetail:
    stage: str
    stage_name: str
    instruction: str
    status: str           # "active", "stalled", "bubble", "flushed", "empty"
    badge_color: str
    explanation: str


@dataclass
class CycleExplanation:
    cycle: int
    total_cycles: int
    stages: Dict[str, StageDetail]
    hazard_summary: Optional[str] = None
    forwarding_summary: Optional[str] = None
    state_changes: List[str] = field(default_factory=list)
    next_cycle_preview: Optional[str] = None
    simple_summary: str = ""


_STAGE_COLORS = {
    "IF": "#4F8EF7",
    "ID": "#9B6BDF",
    "EX": "#2FB67C",
    "MEM": "#E9A23B",
    "WB": "#E8678A",
}


def explain_cycle(result: SimulationResult, cycle_num: int) -> CycleExplanation:
    """Generate a student-friendly explanation for cycle `cycle_num` (1-based)."""
    if not result.cycles or cycle_num < 1 or cycle_num > len(result.cycles):
        return CycleExplanation(
            cycle=cycle_num,
            total_cycles=result.total_cycles,
            stages={},
            simple_summary="No simulation data available for this cycle.",
        )

    idx = cycle_num - 1
    snapshot = result.cycles[idx]
    next_snap = result.cycles[idx + 1] if idx + 1 < len(result.cycles) else None

    # Find events occurring in this cycle
    cycle_events = [e for e in result.events if e.cycle == cycle_num]
    stall_events = [e for e in cycle_events if e.kind == "stall"]
    fwd_events = [e for e in cycle_events if e.kind == "forward"]
    flush_events = [e for e in cycle_events if e.kind == "flush"]
    ctrl_stall_events = [e for e in cycle_events if e.kind == "control_stall"]

    # 1. Stage by stage inspection
    stage_details: Dict[str, StageDetail] = {}
    for stage in STAGES:
        text = snapshot.stages[stage]
        stage_name = STAGE_INFO[stage][0]

        if text == "—" or text.startswith("bubble (empty)"):
            status = "empty"
            badge_color = "#9CA3AF"
            explanation = f"{stage} is idle (no instruction in this stage yet)."
        elif "stall" in text:
            status = "stalled"
            badge_color = "#EF4444"
            explanation = f"{stage} holds a stall bubble because an earlier instruction was waiting for data."
        elif "flushed" in text or "flush" in text:
            status = "flushed"
            badge_color = "#6B7280"
            explanation = f"{stage} holds a flushed bubble from a taken branch or jump redirection."
        elif "control" in text or "waiting" in text:
            status = "stalled"
            badge_color = "#F59E0B"
            explanation = f"{stage} is paused while waiting for a branch decision to be calculated in EX."
        else:
            # Active instruction
            is_stalled = snapshot.stalled and stage in ("IF", "ID")
            if is_stalled:
                status = "stalled"
                badge_color = "#EF4444"
                explanation = f"Instruction '{text}' is held in {stage} because required source data is not ready."
            else:
                status = "active"
                badge_color = _STAGE_COLORS.get(stage, "#3B82F6")
                if stage == "IF":
                    explanation = f"Fetched '{text}' into the pipeline."
                elif stage == "ID":
                    explanation = f"Decoded '{text}' and read operands from the register file."
                elif stage == "EX":
                    explanation = f"Executing '{text}' in the ALU."
                elif stage == "MEM":
                    explanation = f"Processing memory access or passing result through for '{text}'."
                elif stage == "WB":
                    explanation = f"Writing final result back to the register file for '{text}'."
                else:
                    explanation = f"Processing '{text}'."

        stage_details[stage] = StageDetail(
            stage=stage,
            stage_name=stage_name,
            instruction=text,
            status=status,
            badge_color=badge_color,
            explanation=explanation,
        )

    # 2. Hazard explanation
    hazard_summary = None
    if stall_events:
        st = stall_events[0]
        hazard_summary = (
            f"⚠️ **Data Hazard (RAW)**: A dependent instruction had to wait. "
            f"The needed value for R{st.register} was still in the pipeline and not yet written to registers."
        )
    elif ctrl_stall_events:
        hazard_summary = (
            "⏳ **Control Hazard Wait**: Fetch is paused until the branch condition is evaluated in EX."
        )
    elif flush_events:
        hazard_summary = (
            "💥 **Control Hazard (Pipeline Flush)**: A branch was taken or a jump was taken. "
            "Wrong-path instructions fetched in the shadow were flushed from the pipeline."
        )

    # 3. Forwarding explanation
    forwarding_summary = None
    if fwd_events:
        descriptions = [
            f"R{e.register} forwarded from cycle {e.cycle} producer to consumer in EX"
            for e in fwd_events
        ]
        forwarding_summary = (
            f"⚡ **Data Forwarding Active**: {'; '.join(descriptions)}. "
            "Data was bypassed directly to EX, avoiding stall bubbles!"
        )

    # 4. State changes extracted from snapshot notes
    state_changes: List[str] = []
    for note in snapshot.notes:
        if note.startswith("WB:") and "writes R" in note:
            state_changes.append(note.replace("WB: ", "✏️ Register Write: "))
        elif note.startswith("MEM:") and ("stores" in note or "loads" in note):
            state_changes.append(note.replace("MEM: ", "💾 Memory: "))

    # 5. Next cycle preview
    next_preview = None
    if next_snap is not None:
        advancing = []
        for stage_idx, stage in enumerate(STAGES[:-1]):
            next_stage = STAGES[stage_idx + 1]
            curr_instr = snapshot.stages[stage]
            next_instr = next_snap.stages[next_stage]
            if not curr_instr.startswith("bubble") and curr_instr != "—" and curr_instr == next_instr:
                advancing.append(f"'{curr_instr}' advances to {next_stage}")
        if advancing:
            next_preview = "In Cycle " + str(cycle_num + 1) + ": " + ", ".join(advancing[:3])
            if len(advancing) > 3:
                next_preview += f", and {len(advancing) - 3} more."
        elif next_snap.stalled:
            next_preview = f"In Cycle {cycle_num + 1}: The pipeline will stall on a data dependency."
        else:
            next_preview = f"In Cycle {cycle_num + 1}: Pipeline advances with new fetch."
    else:
        next_preview = "Program execution completes after this cycle. All instructions have retired."

    # 6. Overall simple summary
    if snapshot.stalled:
        simple_summary = "Pipeline Stalled: Instructions in IF and ID are held for 1 cycle while waiting for operands."
    elif flush_events:
        simple_summary = "Branch/Jump Redirection: Target address resolved; wrong-path instructions squashed."
    elif fwd_events:
        simple_summary = "Smooth Execution with Forwarding: Operands bypassed directly between stages without stalling."
    elif any(s.status == "active" for s in stage_details.values()):
        simple_summary = "Normal Flow: Instructions advance one stage forward in program order."
    else:
        simple_summary = "Pipeline idle or completing execution."

    return CycleExplanation(
        cycle=cycle_num,
        total_cycles=result.total_cycles,
        stages=stage_details,
        hazard_summary=hazard_summary,
        forwarding_summary=forwarding_summary,
        state_changes=state_changes,
        next_cycle_preview=next_preview,
        simple_summary=simple_summary,
    )
