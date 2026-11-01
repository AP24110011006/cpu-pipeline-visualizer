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

## 📦 Delivered Modules & File Explanations

| Module / File | Component Responsibility & Implementation Details |
|:---|:---|
| [`simulator/hazards.py`](simulator/hazards.py) | **Core Hazard Detection Engine**<br>• Implements `detect_data_stall()`: Cycle-by-cycle dynamic hazard detection inspecting consumer operands in `ID` against active producers in `EX`, `MEM`, and `WB`.<br>• Implements `find_raw_hazards()`: Static dependency analyzer mapping all RAW hazards, producer-consumer pairs, and distance metrics.<br>• Implements `find_control_instructions()`: Static scanner detecting branches and jumps.<br>• Defines `StallInfo`: Structured diagnostic record detailing consumer, producer, register index, stage, and explanation. |
| [`simulator/analytics/__init__.py`](simulator/analytics/__init__.py) | **Analytics Package Interface**<br>Exposes high-level analytics builders, event trackers, and diagnostic report generators. |
| [`simulator/analytics/event_tracker.py`](simulator/analytics/event_tracker.py) | **Real-Time Event Tracking Framework**<br>Structured event bus recording cycle-by-cycle microarchitectural occurrences: hazard detections, stall insertions, bypass forwarding transfers, and branch flushes. |
| [`simulator/analytics/hazard_analytics.py`](simulator/analytics/hazard_analytics.py) | **Hazard Classification & Telemetry**<br>Aggregates dynamic hazard metrics, categorizes dependencies (ALU-to-ALU vs. Load-Use), calculates distance distributions, and maps producer-consumer hazard chains. |
| [`simulator/analytics/stall_analytics.py`](simulator/analytics/stall_analytics.py) | **Stall Cycle & Bubble Accounting**<br>Quantifies stall cycles vs. discrete events, measures wasted stage slots, accounts for stalls avoided by hardware forwarding, and computes pipeline stall penalty rates. |
| [`simulator/analytics/report_builder.py`](simulator/analytics/report_builder.py) | **Executive Diagnostic Report Builder**<br>Compiles complete simulation statistics into structured diagnostic reports (`PipelineAnalyticsReport`) for visualization in the UI. |
| [`simulator/metrics.py`](simulator/metrics.py) | **Performance Metrics Engine**<br>Computes quantitative architectural metrics: Cycles Per Instruction (CPI), Instructions Per Cycle (IPC), Speedup vs. Unpipelined Reference CPU, and Stage Utilization. |
| [`bots/hazard_bot.py`](bots/hazard_bot.py) | **Bot 5: Hazard Analysis Bot (Invariant Auditor)**<br>Autonomous verification bot running 76 microarchitectural invariant audits: verifies mathematical slot conservation, zero double-counting across stages, and forwarding causality. |
| [`tests/test_hazards.py`](tests/test_hazards.py) | **Hazard Unit Test Suite**<br>Verifies RAW detection across distance 1, 2, and 3 dependencies, load-use delays, $R0$ hazard immunity, and stall insertion. |
| [`tests/test_analytics.py`](tests/test_analytics.py) | **Analytics & Event Tracker Test Suite**<br>Verifies event recording fidelity, hazard breakdown aggregation, and report generation accuracy. |
| [`tests/test_metrics.py`](tests/test_metrics.py) | **Metrics Calculation Test Suite**<br>Validates mathematical accuracy of CPI, IPC, speedup formulas, and edge cases (e.g. empty programs, single-instruction programs). |
| [`examples/hazards/load_use.s`](examples/hazards/load_use.s) | **Load-Use Benchmark Workload**<br>Curated assembly program demonstrating load-use data stalls under both Forwarding ON (1 stall) and Forwarding OFF (2 stalls). |
| [`examples/hazards/raw_hazard.s`](examples/hazards/raw_hazard.s) | **RAW Cascade Benchmark Workload**<br>Intensive register dependency chain stressing multi-stage RAW hazard detection. |

---

## 🔬 Mathematical Conservation Laws Verified

Manikanth's subsystem proves and audits two fundamental microarchitectural conservation laws:

### 1. Cycle Conservation Law
$$\text{Total Execution Cycles} = \text{Ideal Cycles} + \text{Data Stall Cycles} + \text{Control Penalty Cycles}$$
Where $\text{Ideal Cycles} = N + 4$ (for $N$ instructions in a 5-stage pipeline).

### 2. Slot Conservation Law
Every clock cycle advances 5 physical hardware stage slots:
$$\text{Total Stage Slots} = 5 \times \text{Total Cycles} = \text{Useful Instruction Slots} + \text{Bubble Slots}$$

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
