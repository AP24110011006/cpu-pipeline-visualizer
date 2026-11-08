"""Pandas tables shown in the dashboard.  (Member 6 / Member 7)"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pandas as pd

from simulator.hazards import RawHazard
from simulator.metrics import PerformanceMetrics
from simulator.models import STAGES, Instruction, PipelineEvent, SimulationResult

_EVENT_LABELS = {
    "stall": "🛑 Stall",
    "forward": "➡️ Forward",
    "flush": "💥 Flush",
    "control_stall": "⏳ Fetch wait",
}


def instruction_type(instr: Instruction) -> str:
    if instr.is_load:
        return "Load"
    if instr.is_store:
        return "Store"
    if instr.is_branch:
        return "Branch"
    if instr.is_jump:
        return "Jump"
    if instr.opcode == "NOP":
        return "No-op"
    return "ALU"


def program_table(program: List[Instruction]) -> pd.DataFrame:
    rows = []
    for instr in program:
        rows.append({
            "#": instr.index + 1,
            "Instruction": instr.text,
            "Type": instruction_type(instr),
            "Writes": f"R{instr.dest}" if instr.writes_register else "—",
            "Reads": ", ".join(f"R{number}" for number in instr.hazard_sources) or "—",
        })
    return pd.DataFrame(rows)


def cycle_table(result: SimulationResult, cycle_range: Optional[Tuple[int, int]] = None) -> pd.DataFrame:
    rows = []
    cycles = result.cycles
    if cycle_range is not None:
        c_min, c_max = cycle_range
        cycles = [s for s in cycles if c_min <= s.cycle <= c_max]

    for snapshot in cycles:
        row: Dict[str, object] = {"Cycle": snapshot.cycle}
        row.update({stage: snapshot.stages[stage] for stage in STAGES})
        row["What happened"] = " | ".join(snapshot.notes)
        rows.append(row)
    return pd.DataFrame(rows)


def raw_hazard_table(hazards: List[RawHazard], program: List[Instruction]) -> pd.DataFrame:
    rows = []
    for hazard in hazards:
        rows.append({
            "Producer": f"{hazard.producer_index + 1}: {program[hazard.producer_index].text}",
            "Consumer": f"{hazard.consumer_index + 1}: {program[hazard.consumer_index].text}",
            "Register": f"R{hazard.register}",
            "Distance": hazard.distance,
            "Kind": hazard.kind,
            "Stalls without forwarding": hazard.stalls_without_forwarding,
            "Stalls with forwarding": hazard.stalls_with_forwarding,
        })
    return pd.DataFrame(rows)


def events_table(events: List[PipelineEvent], kinds: List[str]) -> pd.DataFrame:
    rows = [{"Cycle": event.cycle, "Type": _EVENT_LABELS.get(event.kind, event.kind), "Explanation": event.message}
            for event in events if event.kind in kinds]
    return pd.DataFrame(rows, columns=["Cycle", "Type", "Explanation"])


def metrics_table(
    metrics_by_name: Union[Dict[str, PerformanceMetrics], PerformanceMetrics, Any],
) -> pd.DataFrame:
    """One row per metric, one column per configuration. Accepts either a dict or a single PerformanceMetrics."""
    if metrics_by_name is None:
        return pd.DataFrame()

    if isinstance(metrics_by_name, dict):
        mapping = metrics_by_name
    elif hasattr(metrics_by_name, "as_rows"):
        mapping = {"Metric Value": metrics_by_name}
    else:
        return pd.DataFrame()

    def _format_cell(v: Any) -> str:
        if v is None:
            return "n/a"
        if isinstance(v, float):
            return f"{v:.3f}"
        if isinstance(v, int):
            return f"{v}"
        return str(v)

    columns = {}
    for name, m in mapping.items():
        if hasattr(m, "as_rows"):
            raw = m.as_rows()
            columns[name] = {k: _format_cell(v) for k, v in raw.items()}
        elif isinstance(m, dict):
            columns[name] = {k: _format_cell(v) for k, v in m.items()}

    if not columns:
        return pd.DataFrame()

    frame = pd.DataFrame(columns)
    frame.insert(0, "Metric", list(frame.index))
    return frame.reset_index(drop=True)


def registers_table(registers: List[int], only_nonzero: bool) -> pd.DataFrame:
    rows = [{"Register": f"R{number}", "Value": value} for number, value in enumerate(registers)
            if value != 0 or not only_nonzero]
    return pd.DataFrame(rows, columns=["Register", "Value"])


def memory_table(memory: Dict[int, int]) -> pd.DataFrame:
    rows = [{"Address": address, "Value": value} for address, value in sorted(memory.items())]
    return pd.DataFrame(rows, columns=["Address", "Value"])
