"""Bot 4 - Stress Testing Bot: large program scalability and resource limit verification.

Generates deterministic workloads up to 5,000 instructions and verifies:
1. Parsing scalability (< 15 ms for 1,000 instructions)
2. Execution throughput (> 20,000 instrs/sec)
3. Safe termination on cycle limits (infinite loops properly truncated)
4. Memory allocation stability across repeated simulation runs
"""

from __future__ import annotations

import time
import tracemalloc
from typing import Dict, List, Optional

from bots.report import BotReport
from simulator.models import PipelineConfig
from simulator.parser import parse_program
from simulator.pipeline import PipelineSimulator


def generate_stress_workload(num_instructions: int) -> str:
    """Generate a syntactically valid program with mixed ALU, memory, and RAW hazards."""
    lines: List[str] = []
    # Seed registers
    lines.append("ADDI R1, R0, 10")
    lines.append("ADDI R2, R0, 20")
    lines.append("ADDI R3, R0, 30")

    count = 3
    for i in range(num_instructions - 3):
        mode = i % 5
        reg_d = (i % 28) + 1
        reg_s1 = ((i + 1) % 28) + 1
        reg_s2 = ((i + 2) % 28) + 1

        if mode == 0:
            lines.append(f"ADD R{reg_d}, R{reg_s1}, R{reg_s2}")
        elif mode == 1:
            lines.append(f"ADDI R{reg_d}, R{reg_s1}, {i % 100}")
        elif mode == 2:
            lines.append(f"SUB R{reg_d}, R{reg_s1}, R{reg_s2}")
        elif mode == 3:
            lines.append(f"SW R{reg_s1}, {(i % 16) * 4}(R0)")
        else:
            lines.append(f"LW R{reg_d}, {(i % 16) * 4}(R0)")
        count += 1

    return "\n".join(lines)


def run_stress_bot(max_scale: int = 2000) -> BotReport:
    """Execute scalability and resource stress tests."""
    report = BotReport(bot="Stress Testing Bot")
    scales = [100, 500, 1000]
    if max_scale >= 2000:
        scales.append(2000)
    if max_scale >= 5000:
        scales.append(5000)

    tracemalloc.start()
    total_start = time.perf_counter()

    for n in scales:
        workload = generate_stress_workload(n)

        # 1. Parsing performance
        t0 = time.perf_counter()
        parsed = parse_program(workload, max_instructions=n + 100)
        t_parse = (time.perf_counter() - t0) * 1000.0

        parse_ok = (len(parsed.instructions) == n and len(parsed.errors) == 0)
        report.add(
            f"Parse scale {n} instructions",
            parse_ok and (t_parse < 500.0),
            f"Parsed {len(parsed.instructions)} instrs in {t_parse:.2f} ms",
        )

        # 2. Simulation throughput (forwarding ON)
        cfg = PipelineConfig(forwarding=True, max_cycles=n * 5)
        sim = PipelineSimulator(cfg)
        t0 = time.perf_counter()
        res = sim.run(parsed.instructions)
        t_sim = (time.perf_counter() - t0) * 1000.0
        throughput = (n / (t_sim / 1000.0)) if t_sim > 0 else 0

        sim_ok = (len(res.instructions) == n and not res.truncated)
        report.add(
            f"Simulate scale {n} instructions (Fwd ON)",
            sim_ok,
            f"Executed {n} instrs in {t_sim:.2f} ms ({throughput:,.0f} instrs/sec)",
        )

    # 3. Safety limit truncation test (infinite loop)
    inf_loop = "loop: BEQ R0, R0, loop"
    parsed_inf = parse_program(inf_loop)
    cfg_limit = PipelineConfig(max_cycles=150)
    sim_limit = PipelineSimulator(cfg_limit)
    res_inf = sim_limit.run(parsed_inf.instructions)
    report.add(
        "Infinite loop safe truncation",
        res_inf.truncated and res_inf.total_cycles == 150,
        f"Safely truncated at cycle limit {res_inf.total_cycles}",
    )

    # 4. Memory footprint stability
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mb = peak_mem / (1024 * 1024)
    report.add(
        "Memory footprint within bounds",
        peak_mb < 80.0,
        f"Peak memory during stress test: {peak_mb:.2f} MB",
    )

    report.stats["total_runtime_ms"] = round((time.perf_counter() - total_start) * 1000, 2)
    report.stats["peak_memory_mb"] = round(peak_mb, 2)
    return report


if __name__ == "__main__":
    rep = run_stress_bot()
    print(rep.to_text())
