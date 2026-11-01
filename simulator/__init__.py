"""Simulation engine for the CPU Pipeline Execution Visualizer.

The engine is pure Python (no Streamlit, no Plotly) so it can be tested on its own.
"""

__all__ = []

try:
    from simulator.metrics import PerformanceMetrics, compute_metrics
    __all__.extend(["PerformanceMetrics", "compute_metrics"])
except ImportError:
    PerformanceMetrics = None
    compute_metrics = None

try:
    from simulator.models import PipelineConfig, SimulationResult
    __all__.extend(["PipelineConfig", "SimulationResult"])
except ImportError:
    PipelineConfig = None
    SimulationResult = None

try:
    from simulator.parser import parse_program
    __all__.extend(["parse_program"])
except ImportError:
    parse_program = None

try:
    from simulator.pipeline import PipelineSimulator
    __all__.extend(["PipelineSimulator"])
except ImportError:
    PipelineSimulator = None
