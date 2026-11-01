"""Fine-grained event tracking for pipeline hazard, stall, and forwarding history.

Records microarchitectural events cycle-by-cycle without duplication,
allowing filtering, searching, sorting, and export.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DetailedPipelineEvent:
    """An exact, traceable microarchitectural event during pipeline execution."""

    event_id: str                      # Unique ID, e.g. "EV-001"
    cycle: int                         # Clock cycle when event occurred
    instruction_seq: int               # Primary instruction sequence number
    instruction_text: str              # Assembly text, e.g. "SUB R4, R1, R5"
    hazard_type: str                   # "RAW", "Load-Use", "Control (Branch)", "Control (Jump)", "Structural"
    stage: str                         # Stage where detected/resolved: "ID", "EX", "MEM", "WB"
    producer_seq: Optional[int] = None # Sequence number of producer instruction
    producer_text: str = ""            # Assembly text of producer
    consumer_seq: Optional[int] = None # Sequence number of consumer instruction
    consumer_text: str = ""            # Assembly text of consumer
    register_dependency: Optional[str] = None  # e.g. "R1"
    resolution_method: str = "Normal"  # "Forwarding (EX/MEM)", "Stall (Bubble)", "Pipeline Flush", etc.
    stall_cycles: int = 0              # Stalls caused by this specific event occurrence
    forwarding_path: Optional[str] = None  # "EX/MEM -> EX", "MEM/WB -> EX", or None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EventTracker:
    """Collects and organizes DetailedPipelineEvent records."""

    def __init__(self) -> None:
        self.events: List[DetailedPipelineEvent] = []
        self._counter: int = 0

    def record(
        self,
        cycle: int,
        instruction_seq: int,
        instruction_text: str,
        hazard_type: str,
        stage: str,
        producer_seq: Optional[int] = None,
        producer_text: str = "",
        consumer_seq: Optional[int] = None,
        consumer_text: str = "",
        register_dependency: Optional[str] = None,
        resolution_method: str = "Normal",
        stall_cycles: int = 0,
        forwarding_path: Optional[str] = None,
        notes: str = "",
    ) -> DetailedPipelineEvent:
        self._counter += 1
        event = DetailedPipelineEvent(
            event_id=f"EV-{self._counter:03d}",
            cycle=cycle,
            instruction_seq=instruction_seq,
            instruction_text=instruction_text,
            hazard_type=hazard_type,
            stage=stage,
            producer_seq=producer_seq,
            producer_text=producer_text,
            consumer_seq=consumer_seq,
            consumer_text=consumer_text,
            register_dependency=register_dependency,
            resolution_method=resolution_method,
            stall_cycles=stall_cycles,
            forwarding_path=forwarding_path,
            notes=notes,
        )
        self.events.append(event)
        return event

    def filter(
        self,
        hazard_type: Optional[str] = None,
        stage: Optional[str] = None,
        cycle: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> List[DetailedPipelineEvent]:
        """Filter events with optional criteria."""
        results = self.events
        if hazard_type and hazard_type != "All":
            results = [e for e in results if e.hazard_type == hazard_type]
        if stage and stage != "All":
            results = [e for e in results if e.stage == stage]
        if cycle is not None:
            results = [e for e in results if e.cycle == cycle]
        if search_query:
            q = search_query.lower()
            results = [
                e for e in results
                if q in e.event_id.lower()
                or q in e.instruction_text.lower()
                or q in (e.register_dependency or "").lower()
                or q in e.resolution_method.lower()
                or q in e.notes.lower()
            ]
        return results

    def to_table_data(self) -> List[Dict[str, Any]]:
        return [
            {
                "Event ID": e.event_id,
                "Cycle": e.cycle,
                "Stage": e.stage,
                "Instruction": f"I{e.instruction_seq}: {e.instruction_text}",
                "Hazard Type": e.hazard_type,
                "Register": e.register_dependency or "—",
                "Resolution": e.resolution_method,
                "Forwarding Path": e.forwarding_path or "—",
                "Stall Cycles": e.stall_cycles,
                "Producer": f"I{e.producer_seq}" if e.producer_seq else "—",
                "Notes": e.notes,
            }
            for e in self.events
        ]
