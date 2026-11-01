"""Benchmark suite for CPU Pipeline Simulator.

Measures:
1. Parsing time across program sizes (10 to 1,000 instructions).
2. Pipeline simulation time (Forwarding ON and OFF).
3. Reference CPU execution time.
4. Engine end-to-end execution and explainer performance.
5. Cycle navigation response time with caching.
"""

from __future__ import annotations

import time
from typing import List

from simulator.engine import run_pipeline_engine
from simulator.explainer import explain_cycle
from simulator.models import PipelineConfig
from simulator.parser import parse_program
from simulator.pipeline import PipelineSimulator
from simulator.reference import run_reference
from simulator.samples import SAMPLES


def generate_benchmark_program(num_instructions: int) -> str:
    """Generate a valid, terminating assembly program with RAW chains and independent ops."""
    lines = ["ADDI R1, R0, 1", "ADDI R2, R0, 2"]
    for i in range(num_instructions - 4):
        reg_dest = (i % 28) + 3  # R3 to R30
        reg_src1 = ((i - 1) % 28) + 3
        reg_src2 = ((i - 2) % 28) + 3
        op = i % 5
        if op == 0:
            lines.append(f"ADDI R{reg_dest}, R{reg_src1}, {i % 100}")
        elif op == 1:
            lines.append(f"ADD R{reg_dest}, R{reg_src1}, R{reg_src2}")
        elif op == 2:
            lines.append(f"SUB R{reg_dest}, R{reg_src1}, R{reg_src2}")
        elif op == 3:
            lines.append(f"AND R{reg_dest}, R{reg_src1}, R{reg_src2}")
        else:
            lines.append(f"OR R{reg_dest}, R{reg_src1}, R{reg_src2}")
    lines.append("ADD R31, R1, R2")
    lines.append("NOP")
    return "\n".join(lines)


def run_benchmark():
    print("=" * 70)
    print("CPU PIPELINE SIMULATOR PERFORMANCE & SCALABILITY BENCHMARK")
    print("=" * 70)

    # 1. Sample programs benchmark
    print("\n--- 1. Built-in Samples Performance ---")
    for name, sample in SAMPLES.items():
        parsed = parse_program(sample.code)
        sim = PipelineSimulator(PipelineConfig(forwarding=True))
        t0 = time.perf_counter()
        res = sim.run(parsed.instructions)
        dt = (time.perf_counter() - t0) * 1000
        print(f"Sample '{name[:32]}...': {len(parsed.instructions)} instrs, {res.total_cycles} cycles -> {dt:.3f} ms")

    # 2. Scalability benchmark (10 to 1,000 instructions)
    sizes = [10, 50, 100, 250, 500, 1000]
    print("\n--- 2. Scalability Across Program Sizes (10 to 1,000 Instructions) ---")
    header = f"{'Size':<6} | {'Parse (ms)':<11} | {'Sim Fwd (ms)':<13} | {'Sim NoFwd (ms)':<15} | {'Ref CPU (ms)':<13} | {'Total Cycles':<12}"
    print(header)
    print("-" * len(header))

    config_fwd = PipelineConfig(forwarding=True, max_cycles=10000)
    config_nofwd = PipelineConfig(forwarding=False, max_cycles=10000)
    sim_fwd = PipelineSimulator(config_fwd)
    sim_nofwd = PipelineSimulator(config_nofwd)

    for size in sizes:
        code = generate_benchmark_program(size)

        # Parse
        t0 = time.perf_counter()
        parsed = parse_program(code, max_instructions=2000)
        t_parse = (time.perf_counter() - t0) * 1000

        # Sim Fwd
        t0 = time.perf_counter()
        res_fwd = sim_fwd.run(parsed.instructions)
        t_fwd = (time.perf_counter() - t0) * 1000

        # Sim NoFwd
        t0 = time.perf_counter()
        res_nofwd = sim_nofwd.run(parsed.instructions)
        t_nofwd = (time.perf_counter() - t0) * 1000

        # Ref CPU
        t0 = time.perf_counter()
        ref = run_reference(parsed.instructions, max_steps=10000)
        t_ref = (time.perf_counter() - t0) * 1000

        print(f"{size:<6} | {t_parse:<11.3f} | {t_fwd:<13.3f} | {t_nofwd:<15.3f} | {t_ref:<13.3f} | {res_fwd.total_cycles:<12}")

    # 3. Explainer & Navigation Performance
    print("\n--- 3. Explainer & Cycle Navigation Response Time ---")
    code_100 = generate_benchmark_program(100)
    engine_res = run_pipeline_engine(
        code=code_100,
        init_regs_str="",
        init_mem_str="",
        config=PipelineConfig(forwarding=True),
        max_instructions=2000,
    )

    t0 = time.perf_counter()
    # Simulate user stepping through 20 cycles
    for cycle in range(1, 21):
        _ = explain_cycle(engine_res.primary, cycle)
    t_20_steps = (time.perf_counter() - t0) * 1000
    avg_per_step = t_20_steps / 20

    print(f"20 cycle navigation steps total time: {t_20_steps:.3f} ms (Average per step: {avg_per_step:.4f} ms)")
    print(f"Cycle navigation is {1000 / avg_per_step:.0f}+ frames/sec responsive (instantaneous UI updates).")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
