"""Simulation engine for the CPU Pipeline Execution Visualizer.

The engine is pure Python (no Streamlit, no Plotly) so it can be tested on its own.

Module map (who owns what):
    models.py      - shared data classes (Instruction, DynamicInstruction, results)   [Member 1]
    parser.py      - assembly text -> Instruction objects, input validation          [Member 2]
    pipeline.py    - cycle-by-cycle five-stage pipeline engine                       [Member 3]
    hazards.py     - RAW data hazard + stall detection, control hazard helpers      [Member 4]
    forwarding.py  - forwarding (bypass) logic                                       [Member 5]
    metrics.py     - CPI, total cycles, speedup, utilization                         [Member 7]
    execute.py     - ALU / branch arithmetic shared by pipeline and reference model
    reference.py   - simple sequential CPU used to double-check the pipeline
    samples.py     - ready-made example programs
"""

from simulator.metrics import PerformanceMetrics, compute_metrics
from simulator.models import PipelineConfig, SimulationResult
from simulator.parser import parse_program
from simulator.pipeline import PipelineSimulator

__all__ = [
    "PerformanceMetrics",
    "PipelineConfig",
    "PipelineSimulator",
    "SimulationResult",
    "compute_metrics",
    "parse_program",
]
