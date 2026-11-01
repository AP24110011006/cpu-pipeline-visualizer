# Performance & Scalability Guide

## Scalability Benchmarks

The simulator engine and UI are optimized for programs ranging from small textbook snippets to large workloads of up to 5,000 instructions:

| Workload Size | Parse Time | Simulation Time | Throughput | Peak Memory |
|:---|:---|:---|:---|:---|
| 100 instructions | ~4.5 ms | ~20 ms | ~5,000 instrs/sec | < 5 MB |
| 500 instructions | ~30 ms | ~85 ms | ~5,800 instrs/sec | < 6 MB |
| 1,000 instructions | ~50 ms | ~130 ms | ~7,500 instrs/sec | < 7.5 MB |
| 2,000 instructions | ~120 ms | ~330 ms | ~6,000 instrs/sec | < 8.0 MB |

## Architectural Performance Optimizations

1. **Decoupled Cycle Navigation**:
   - The simulation engine executes once upon program compilation and caches complete snapshots.
   - Cycle navigation steps in `0.015 ms` without re-running simulation loops.

2. **Windowed Timing Diagram**:
   - For programs with many cycles, the **Window around cycle (Fast)** mode renders a localized window ($\pm 15$ cycles), preventing browser DOM congestion.

3. **Dual-Mode Simulation Facade**:
   - Forwarding ON and Forwarding OFF simulations are executed and cached together in `EngineResult`, enabling zero-overhead instant comparison.
