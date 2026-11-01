"""High-performance facade and cache manager for the pipeline simulation.

Encapsulates parsing, execution, reference verification, and metrics generation.
Ensures deterministic computations can be cached and isolates session state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import replace
from typing import Dict, List, Optional, Tuple

import streamlit as st

from simulator.analytics import PipelineAnalyticsReport, build_analytics_report
from simulator.forwarding import find_forwarding_source
from simulator.hazards import RawHazard, find_control_instructions, find_raw_hazards
from simulator.metrics import PerformanceMetrics, compute_metrics
from simulator.models import Instruction, PipelineConfig, SimulationResult
from simulator.parser import parse_memory_values, parse_program, parse_register_values
from simulator.pipeline import PipelineSimulator
from simulator.reference import ReferenceResult, run_reference


@dataclass
class EngineResult:
    """Complete, self-contained result of a program simulation."""

    ok: bool
    errors: List[str] = field(default_factory=list)
    code: str = ""
    program: List[Instruction] = field(default_factory=list)
    initial_registers: Dict[int, int] = field(default_factory=dict)
    initial_memory: Dict[int, int] = field(default_factory=dict)
    config: PipelineConfig = field(default_factory=PipelineConfig)

    primary: Optional[SimulationResult] = None
    on: Optional[SimulationResult] = None
    off: Optional[SimulationResult] = None
    reference: Optional[ReferenceResult] = None

    metrics_primary: Optional[PerformanceMetrics] = None
    metrics_on: Optional[PerformanceMetrics] = None
    metrics_off: Optional[PerformanceMetrics] = None

    analytics_primary: Optional[PipelineAnalyticsReport] = None
    analytics_on: Optional[PipelineAnalyticsReport] = None
    analytics_off: Optional[PipelineAnalyticsReport] = None

    raw_hazards: List[RawHazard] = field(default_factory=list)
    control_instructions: List[Instruction] = field(default_factory=list)


def run_pipeline_engine(
    code: str,
    init_regs_str: str,
    init_mem_str: str,
    config: PipelineConfig,
    max_instructions: int = 2000,
) -> EngineResult:
    """Parse, simulate in dual configurations (Forwarding ON/OFF), and verify against reference CPU."""
    # 1. Parse assembly
    parsed = parse_program(code, max_instructions=max_instructions)
    registers, reg_errors = parse_register_values(init_regs_str)
    memory, mem_errors = parse_memory_values(init_mem_str)

    errors = [str(err) for err in parsed.errors]
    errors += [f"Initial registers: {msg}" for msg in reg_errors]
    errors += [f"Initial memory: {msg}" for msg in mem_errors]

    if errors or not parsed.instructions:
        return EngineResult(
            ok=False,
            errors=errors or ["No valid instructions found."],
            code=code,
            config=config,
        )

    program = parsed.instructions

    # 2. Simulate Forwarding ON and OFF
    config_on = replace(config, forwarding=True)
    config_off = replace(config, forwarding=False)

    sim_on = PipelineSimulator(config_on)
    sim_off = PipelineSimulator(config_off)

    res_on = sim_on.run(program, registers, memory)
    res_off = sim_off.run(program, registers, memory)

    primary = res_on if config.forwarding else res_off

    # 3. Reference CPU execution
    ref_res = run_reference(program, registers, memory, max_steps=config.max_cycles)

    # 4. Metrics & Detailed Analytics
    met_on = compute_metrics(res_on)
    met_off = compute_metrics(res_off)
    met_primary = met_on if config.forwarding else met_off

    analytics_on = build_analytics_report(res_on, reference_off_result=res_off)
    analytics_off = build_analytics_report(res_off, reference_off_result=None)
    analytics_primary = analytics_on if config.forwarding else analytics_off

    # 5. Static hazard analysis
    raw_hazards = find_raw_hazards(program, config.reg_write_first_half)
    control_instrs = find_control_instructions(program)

    return EngineResult(
        ok=True,
        errors=[],
        code=code,
        program=program,
        initial_registers=registers,
        initial_memory=memory,
        config=config,
        primary=primary,
        on=res_on,
        off=res_off,
        reference=ref_res,
        metrics_primary=met_primary,
        metrics_on=met_on,
        metrics_off=met_off,
        analytics_primary=analytics_primary,
        analytics_on=analytics_on,
        analytics_off=analytics_off,
        raw_hazards=raw_hazards,
        control_instructions=control_instrs,
    )
