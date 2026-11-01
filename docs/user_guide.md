# User Guide: CPU Pipeline Visualizer

## Overview
The **CPU Pipeline Visualizer** is an interactive, cycle-accurate simulation platform designed to illustrate five-stage MIPS pipeline dynamics, data hazard handling, hardware bypassing, and branch prediction policies.

---

## Workflow: From Code to Analysis

1. **Assembly Simulator Workspace**:
   - Write or load an assembly program (e.g. from the textbook examples dropdown).
   - Configure architectural switches: Forwarding ON/OFF, Register File split-phase, and Branch Prediction Policy.
   - Click **Run Simulation**.

2. **Pipeline Visualization**:
   - Use the slider or step buttons to navigate clock cycles ($C = 1, 2, \dots$).
   - Inspect the live contents of the five stages: `IF`, `ID`, `EX`, `MEM`, `WB`.
   - Toggle the Diagram View Mode between **Window around cycle (Fast)** and **Full program**.

3. **Forwarding Comparison**:
   - Compare execution of the identical program under Forwarding ON vs Forwarding OFF side-by-side.
   - Inspect cycle savings, eliminated data stalls, and CPI differences.

4. **Dedicated Hazard & Stall Analytics**:
   - View dynamic RAW events, load-use hazards, static dependencies, and forwarding breakdowns.
   - Filter and search the complete Microarchitectural Event History.

5. **Intelligent Testing Bots**:
   - Run the 5 automated verification bots to validate pipeline correctness or use the Dev Bot DAG optimizer to reschedule instructions and eliminate load-use stalls.
