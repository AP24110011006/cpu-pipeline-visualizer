"""Small helpers shared by the tests."""

from simulator.metrics import compute_metrics
from simulator.models import PipelineConfig
from simulator.parser import parse_program, parse_register_values
from simulator.pipeline import PipelineSimulator

SAMPLE = "ADD R1, R2, R3\nSUB R4, R1, R5\nAND R6, R4, R7"


def run(code, forwarding=True, registers="", **config):
    """Parse `code`, simulate it and return (result, metrics)."""
    parsed = parse_program(code)
    assert parsed.ok, [str(error) for error in parsed.errors]
    values, _ = parse_register_values(registers)
    result = PipelineSimulator(PipelineConfig(forwarding=forwarding, **config)).run(parsed.instructions, values)
    return result, compute_metrics(result)


def stage_of(result, seq, cycle):
    """Which stage instruction I<seq> was in during `cycle` (None if not in the pipeline)."""
    for c, stage, state in result.instructions[seq - 1].history:
        if c == cycle and state != "flushed":
            return stage
    return None
