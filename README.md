# ⚡ Forwarding & Control Hazard Subsystem — LATHISH

**Lead Engineer**: **LATHISH** (`LT`)  
**Role**: **Forwarding & Control Hazard Developer**  
**Assigned Subsystem**: Hardware Bypass Forwarding Unit, Priority Multiplexing, Branch Penalty Modeling & Pipeline Flushing  
**Verification Suite**: `tests/test_forwarding.py`, `tests/test_audit_and_regressions.py` (13/13 Tests Passed)

---

## 🎯 Architectural Mission & Role Overview

As the **Forwarding & Control Hazard Developer**, Lathish is responsible for mitigating pipeline stalls through hardware data bypassing and managing control-flow pipeline disruptions (branches and jumps).

In an unforwarded pipeline, an instruction producing a register in `EX` does not write it back to the register file until `WB`. Any dependent instruction entering `ID` would be forced to stall for 2 clock cycles. Lathish's subsystem implements hardware bypass forwarding paths, routing computed results directly from intermediate pipeline stage latches into the ALU inputs of subsequent instructions.

Lathish's subsystem:
1. **EX/MEM $\to$ EX Forwarding (Distance 1)**: Forwards the computation result of the instruction currently in `MEM` to the ALU input of the instruction currently in `EX`. Eliminates stalls for back-to-back ALU instructions!
2. **MEM/WB $\to$ EX Forwarding (Distance 2)**: Forwards the computation or load result of the instruction currently in `WB` to the ALU input of the instruction in `EX`.
3. **Resolves Priority Hazards**: When both `EX/MEM` and `MEM/WB` stages target the same destination register, Lathish's unit enforces **newest-producer priority**, routing the most recent `EX/MEM` value.
4. **Zero-Register Safety**: Ensures `R0` is never forwarded, preserving the architectural invariant that register 0 is immutable.
5. **Models Branch Penalties**: Implements branch resolution in `EX` with configurable prediction policies:
   - `predict_not_taken`: Optimistically fetches sequential instructions; if the branch evaluates to taken, 2 speculative instructions in `IF` and `ID` are flushed (`FLUSH`).
   - `stall`: Stalls the fetch unit until the branch resolves, incurring a deterministic 2-cycle penalty.

---

## 🧠 Algorithms Implemented & Complexity Analysis

Lathish engineered three microarchitectural control algorithms governing hardware multiplexer routing and speculative branch recovery:

### Algorithm 1: Hardware Bypass Forwarding Multiplexer Routing (`resolve_forwarding`)
- **Purpose**: Evaluates bypass conditions for ALU inputs $A$ and $B$ in the `EX` stage, enforcing newest-producer priority and $R0$ exclusion.
- **Multiplexer Truth Table**:
  | Control Code | Forward Path | Source Stage | Description |
  |:---:|:---:|:---:|:---|
  | `00` | No Forwarding | Register File | Operand read directly from register file during `ID` |
  | `10` | `EX/MEM -> EX` | `MEM` Stage | Distance-1 bypass: newest result forwarded from `EX/MEM` latch |
  | `01` | `MEM/WB -> EX` | `WB` Stage | Distance-2 bypass: result forwarded from `MEM/WB` latch |

- **Pseudocode**:
  ```python
  def resolve_forwarding(id_ex, ex_mem, mem_wb):
      forward_a = "00"  # Default: register file
      forward_b = "00"
      
      # 1. Forward to Operand A (rs)
      if ex_mem and ex_mem.reg_write and ex_mem.rd != 0 and ex_mem.rd == id_ex.rs:
          forward_a = "10"  # EX/MEM -> EX has newest priority!
      elif mem_wb and mem_wb.reg_write and mem_wb.rd != 0 and mem_wb.rd == id_ex.rs:
          forward_a = "01"  # MEM/WB -> EX
          
      # 2. Forward to Operand B (rt)
      if ex_mem and ex_mem.reg_write and ex_mem.rd != 0 and ex_mem.rd == id_ex.rt:
          forward_b = "10"  # EX/MEM -> EX has newest priority!
      elif mem_wb and mem_wb.reg_write and mem_wb.rd != 0 and mem_wb.rd == id_ex.rt:
          forward_b = "01"  # MEM/WB -> EX
          
      return forward_a, forward_b
  ```
- **Complexity**:
  - **Time Complexity**: $\mathcal{O}(1)$ execution per cycle. Checks 4 conditional clauses over fixed-size integer registers.
  - **Space Complexity**: $\mathcal{O}(1)$ auxiliary storage.

---

### Algorithm 2: Speculative Branch Recovery & Squashing Algorithm
- **Purpose**: Controls branch resolution in the `EX` stage and squashes speculatively fetched wrong-path instructions.
- **Logic**:
  $$\text{Condition} = \begin{cases} 
  (rs == rt) & \text{for } \text{BEQ} \\ 
  (rs \ne rt) & \text{for } \text{BNE} 
  \end{cases}$$
  - **Policy `predict_not_taken`**:
    - If $\text{Condition} == \text{False}$: Branch was correctly predicted not taken. Penalty = $0$ cycles!
    - If $\text{Condition} == \text{True}$ (Misprediction):
      1. Flush `IF` stage: overwrite `IF/ID` latch with `BUBBLE(FLUSH)`.
      2. Flush `ID` stage: overwrite `ID/EX` latch with `BUBBLE(FLUSH)`.
      3. Redirect Program Counter: $PC \leftarrow \text{BranchTarget}$.
      4. Incur exact 2-cycle penalty.
- **Complexity**: $\mathcal{O}(1)$ per branch resolution.

---

### Algorithm 3: Forwarding Telemetry & Stall Avoidance Accounting
- **Purpose**: Calculates cumulative stall cycles avoided by hardware forwarding:
  $$\text{Avoided Stalls} = \sum_{t=1}^{C} \left( \text{Stalls}_{\text{NoFwd}}(t) - \text{Stalls}_{\text{Fwd}}(t) \right)$$
  Computes hardware bypass path efficiency:
  $$\text{Bypass Efficiency} = \frac{\text{Avoided Stalls}}{\text{Ideal Cycles} + \text{Avoided Stalls}} \times 100\%$$
- **Complexity**: $\mathcal{O}(1)$ cycle update.

---

## 📦 Delivered Modules & File Explanations

| Module / File | Component Responsibility & Implementation Details |
|:---|:---|
| [`simulator/forwarding.py`](simulator/forwarding.py) | **Hardware Bypass Forwarding Unit**<br>• Implements `ForwardingUnit`: Evaluates bypass availability for both ALU operands (`ForwardA` and `ForwardB`).<br>• Implements Distance-1 (`EX/MEM -> EX`) and Distance-2 (`MEM/WB -> EX`) multiplexer routing.<br>• Enforces newest-producer priority when multiple stages write the same register.<br>• Implements `R0` forwarding suppression. |
| [`simulator/analytics/forwarding_analytics.py`](simulator/analytics/forwarding_analytics.py) | **Forwarding Path Telemetry & Analytics**<br>Tracks forwarding path utilization rates (`EX/MEM` vs `MEM/WB`), quantifies total stall clock cycles saved by forwarding, and analyzes operand bypass efficiency. |
| [`simulator/analytics/control_analytics.py`](simulator/analytics/control_analytics.py) | **Control Hazard & Branch Penalty Analytics**<br>Monitors branch execution outcomes (taken vs. not-taken), measures branch misprediction penalties, tracks squashed instruction counts, and audits flush penalties. |
| [`tests/test_forwarding.py`](tests/test_forwarding.py) | **Forwarding Unit Test Suite**<br>Verifies Distance-1 and Distance-2 forwarding, priority resolution between overlapping producers, load-use stall insertion despite forwarding, and $R0$ bypass suppression. |
| [`tests/test_audit_and_regressions.py`](tests/test_audit_and_regressions.py) | **Control Hazard & Flush Regression Test Suite**<br>Verifies pipeline flush consistency, speculative slot squashing, and branch penalty calculations. |
| [`examples/control_flow/loop_countdown.s`](examples/control_flow/loop_countdown.s) | **Tight Loop Control Flow Benchmark**<br>Iterative countdown loop testing branch condition evaluation, branch flush squashing, and cyclic dependency forwarding. |

---

## 🧪 Verification & How to Run Tests

Lathish's subsystem is verified against comprehensive bypass and control-flow test suites:

```bash
# Run all forwarding and control hazard regression tests
pytest tests/test_forwarding.py tests/test_audit_and_regressions.py -v
```

### ✅ Verification Results
- **Bypass Verification**: All Distance-1 and Distance-2 forwarding paths verified with 0 data stalls for ALU chains.
- **Priority Handling**: Most recent producer correctly prioritized in multi-producer dependency chains.
- **Branch Flushes**: Exact 2-cycle penalty and 2-slot instruction squashing verified under `predict_not_taken`.
- **CI Status**: GitHub Actions Workflow **GREEN (Success ✅)**.
