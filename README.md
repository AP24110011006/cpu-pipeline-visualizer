# ⚠️ Hazard Detection Subsystem — MANIKANTH

**Lead Engineer**: **MANIKANTH** (`MK`)  
**Role**: **Hazard Detection Developer**  
**Assigned Subsystem**: Data Hazard Detection, Stall Accounting, Pipeline Analytics & Conservation Auditing  
**Verification Suite**: `tests/test_hazards.py`, `tests/test_analytics.py`, `tests/test_metrics.py`, `bots/hazard_bot.py` (76/76 Checks Passed)

---

## 🎯 Architectural Mission & Role Overview

As the **Hazard Detection Developer**, Manikanth is responsible for the microarchitectural safety, mathematical conservation, and hazard detection logic of the 5-stage CPU pipeline. 

In a pipelined CPU, instructions execute concurrently across five stages: **IF (Fetch) · ID (Decode) · EX (Execute) · MEM (Memory) · WB (Write Back)**. When instructions depend on data produced by prior uncompleted instructions, **Read-After-Write (RAW) data hazards** arise. If unmanaged, the pipeline would read stale register values, producing incorrect execution results.

Manikanth's subsystem:
1. **Detects RAW Hazards Dynamically**: Evaluates register dependencies between the instruction in the `ID` stage and in-flight instructions in `EX`, `MEM`, and `WB`.
2. **Inserts Stall Bubbles**: Freezes `IF` and `ID` stages while latching bubble instructions into `EX` when data cannot be bypassed.
3. **Implements Split-Phase Register Timing**: Accurately models the physical hardware invariant where the register file is written in the first half of the clock cycle (during `WB`) and read in the second half of the cycle (during `ID`). This eliminates stalls for distance-3 dependencies.
4. **Disambiguates Stalls vs. Events**: Strictly differentiates between *discrete stall events* and *stall clock cycles* (e.g., a load-use stall without forwarding causes 1 stall event spanning 2 clock cycles).
5. **Enforces Mathematical Conservation**: Validates that every execution run strictly obeys microarchitectural conservation laws without double-counting.

$$\text{Total Slots} = 5 \times \text{Cycles} = \text{Useful Instruction Slots} + \text{Bubble Slots}$$

---

## 🧠 Algorithms Implemented & Complexity Analysis

Manikanth designed and implemented three core microarchitectural algorithms to ensure hazard detection is both mathematically rigorous and optimal in performance:

### Algorithm 1: Dynamic RAW Hazard & Stall Detection (`detect_data_stall`)
- **Purpose**: Evaluates cycle-by-cycle whether the consumer instruction currently in `ID` must be stalled due to uncompleted producers in `EX`, `MEM`, or `WB`.
- **Pseudocode**:
  ```python
  def detect_data_stall(id_inst, ex_inst, mem_inst, wb_inst, forwarding_enabled, first_half_write):
      if id_inst is None or is_bubble(id_inst):
          return None  # No consumer, no hazard
      
      consumer_sources = get_read_registers(id_inst)  # e.g., (rs, rt) excluding R0
      
      # 1. Check EX Stage Producer (Distance 1)
      if ex_inst and writes_register(ex_inst) and ex_inst.dest in consumer_sources:
          if is_load(ex_inst):
              # Load-Use Hazard: value not ready until end of MEM
              return StallInfo(consumer=id_inst, producer=ex_inst, reg=ex_inst.dest, stage="EX", reason="Load-Use Hazard")
          elif not forwarding_enabled:
              # ALU-ALU Hazard without forwarding requires 2 stalls
              return StallInfo(consumer=id_inst, producer=ex_inst, reg=ex_inst.dest, stage="EX", reason="RAW Hazard (No Forwarding)")
      
      # 2. Check MEM Stage Producer (Distance 2)
      if mem_inst and writes_register(mem_inst) and mem_inst.dest in consumer_sources:
          if not forwarding_enabled:
              return StallInfo(consumer=id_inst, producer=mem_inst, reg=mem_inst.dest, stage="MEM", reason="RAW Hazard (No Forwarding)")
          # If forwarding is ON, MEM/WB -> EX bypasses the value with 0 stalls!
      
      # 3. Check WB Stage Producer (Distance 3)
      if wb_inst and writes_register(wb_inst) and wb_inst.dest in consumer_sources:
          if not first_half_write:
              # If split-phase timing is disabled, 1 stall needed to wait for register write
              return StallInfo(consumer=id_inst, producer=wb_inst, reg=wb_inst.dest, stage="WB", reason="RAW Hazard (WB Latch Delay)")
          # First-half write allows ID to read the newly written value in the second half (0 stalls)!
      
      return None  # All operands ready
  ```
- **Complexity**:
  - **Time Complexity**: $\mathcal{O}(1)$ per cycle. The algorithm checks at most 3 in-flight pipeline stages against at most 2 source registers.
  - **Space Complexity**: $\mathcal{O}(1)$ auxiliary working memory.

---

### Algorithm 2: Static Topological RAW Dependency & Distance Analyzer (`find_raw_hazards`)
- **Purpose**: Performs a static pass over the complete instruction sequence to detect all potential RAW hazards, compute dependency distances, and classify hazard types for UI visualization and pedagogical teaching.
- **Logic**:
  $$\text{Distance} = \text{Index}(\text{Consumer}) - \text{Index}(\text{Producer})$$
  - $\text{Distance} = 1$: Back-to-back dependency (stalls 2 cycles without forwarding; 0 stalls with forwarding for ALU; 1 stall for load-use).
  - $\text{Distance} = 2$: Separated by 1 instruction (stalls 1 cycle without forwarding; 0 stalls with forwarding).
  - $\text{Distance} \ge 3$: Separated by $\ge 2$ instructions (0 stalls under split-phase register file timing).
- **Complexity**:
  - **Time Complexity**: $\mathcal{O}(N)$ where $N$ is the number of instructions in the program.
  - **Space Complexity**: $\mathcal{O}(H)$ where $H$ is the number of detected hazard pairs ($H \le 2N$).

---

### Algorithm 3: Microarchitectural Conservation & Zero Double-Counting Audit
- **Purpose**: Mathematical validation algorithm executed by `HazardBot` to audit execution traces and verify that dynamic events obey physical hardware conservation laws.
- **Formulas**:
  1. **Cycle Conservation**:
     $$\text{Total Cycles} = (N + 4) + \text{Data Stall Cycles} + \text{Control Flush Cycles}$$
  2. **Slot Conservation**:
     $$\text{Total Stage Slots} = 5 \times \text{Total Cycles} = \text{Useful Instruction Slots} + \text{Bubble Slots}$$
  3. **Zero Double-Counting Invariant**:
     $$\sum \text{Discrete Stall Events} \le \sum \text{Stall Clock Cycles}$$
     $$\text{Reported Stalls} \equiv \text{Physical Hardware Bubbles Injected}$$
- **Complexity**:
  - **Time Complexity**: $\mathcal{O}(C)$ where $C$ is the total number of execution cycles.
  - **Space Complexity**: $\mathcal{O}(1)$ incremental accumulator state.

---

## 📦 Delivered Modules & File Explanations

| Module / File | Component Responsibility & Implementation Details |
|:---|:---|
| [`simulator/hazards.py`](simulator/hazards.py) | **Core Hazard Detection Engine**<br>• Implements `detect_data_stall()`: Dynamic hazard detection inspecting consumer operands in `ID` against active producers in `EX`, `MEM`, and `WB`.<br>• Implements `find_raw_hazards()`: Static dependency analyzer mapping all RAW hazards, producer-consumer pairs, and distance metrics.<br>• Implements `find_control_instructions()`: Static scanner detecting branches and jumps.<br>• Defines `StallInfo`: Structured diagnostic record detailing consumer, producer, register index, stage, and explanation. |
| [`simulator/analytics/__init__.py`](simulator/analytics/__init__.py) | **Analytics Package Interface**<br>Exposes high-level analytics builders, event trackers, and diagnostic report generators. |
| [`simulator/analytics/event_tracker.py`](simulator/analytics/event_tracker.py) | **Real-Time Event Tracking Framework**<br>Structured event bus recording cycle-by-cycle microarchitectural occurrences: hazard detections, stall insertions, bypass forwarding transfers, and branch flushes. |
| [`simulator/analytics/hazard_analytics.py`](simulator/analytics/hazard_analytics.py) | **Hazard Classification & Telemetry**<br>Aggregates dynamic hazard metrics, categorizes dependencies (ALU-to-ALU vs. Load-Use), calculates distance distributions, and maps producer-consumer hazard chains. |
| [`simulator/analytics/stall_analytics.py`](simulator/analytics/stall_analytics.py) | **Stall Cycle & Bubble Accounting**<br>Quantifies stall cycles vs. discrete events, measures wasted stage slots, accounts for stalls avoided by hardware forwarding, and computes pipeline stall penalty rates. |
| [`simulator/analytics/report_builder.py`](simulator/analytics/report_builder.py) | **Executive Diagnostic Report Builder**<br>Compiles complete simulation statistics into structured diagnostic reports (`PipelineAnalyticsReport`) for visualization in the UI. |
| [`simulator/metrics.py`](simulator/metrics.py) | **Performance Metrics Engine**<br>Computes quantitative architectural metrics: Cycles Per Instruction (CPI), Instructions Per Cycle (IPC), Speedup vs. Unpipelined Reference CPU, and Stage Utilization. |
| [`bots/hazard_bot.py`](bots/hazard_bot.py) | **Bot 5: Hazard Analysis Bot (Invariant Auditor)**<br>Autonomous verification bot running 76 microarchitectural invariant audits: verifies mathematical slot conservation, zero double-counting across stages, and forwarding causality. |
| [`tests/test_hazards.py`](tests/test_hazards.py) | **Hazard Unit Test Suite**<br>Verifies RAW detection across distance 1, 2, and 3 dependencies, load-use delays, $R0$ hazard immunity, and stall insertion. |
| [`tests/test_analytics.py`](tests/test_analytics.py) | **Analytics & Event Tracker Test Suite**<br>Verifies event recording fidelity, hazard breakdown aggregation, and report generation accuracy. |
| [`tests/test_metrics.py`](tests/test_metrics.py) | **Metrics Calculation Test Suite**<br>Validates mathematical accuracy of CPI, IPC, speedup formulas, and edge cases. |
| [`examples/hazards/load_use.s`](examples/hazards/load_use.s) | **Load-Use Benchmark Workload**<br>Curated assembly program demonstrating load-use data stalls under both Forwarding ON (1 stall) and Forwarding OFF (2 stalls). |
| [`examples/hazards/raw_hazard.s`](examples/hazards/raw_hazard.s) | **RAW Cascade Benchmark Workload**<br>Intensive register dependency chain stressing multi-stage RAW hazard detection. |

---

## 🧪 Verification & How to Run Tests

Manikanth's subsystem is backed by 100% passing automated test suites:

```bash
# 1. Run all Hazard Detection and Analytics unit tests
pytest tests/test_hazards.py tests/test_analytics.py tests/test_metrics.py -v

# 2. Run the Autonomous Hazard Analysis Bot (Conservation Law Audits)
python -m bots.hazard_bot
```

### ✅ Verification Results
- **Unit Tests**: `test_hazards.py`, `test_analytics.py`, `test_metrics.py` all **PASSED** (0 failures).
- **HazardBot Invariants**: **76 / 76 checks PASSED** (0 double counting, 100% slot conservation verified).
- **CI Status**: GitHub Actions Workflow **GREEN (Success ✅)**.
