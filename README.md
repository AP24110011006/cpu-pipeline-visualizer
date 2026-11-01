# ⏱️ Pipeline Simulation Engine — LIKHITH

**Lead Engineer**: **LIKHITH** (`LK`)  
**Role**: **Pipeline Simulation Developer**  
**Assigned Subsystem**: 5-Stage Classic RISC Pipeline Engine, Reference CPU, State Transitions & Lifecycle Management  
**Verification Suite**: `tests/test_pipeline.py`, `tests/test_reference.py`, `tests/test_engine_and_explainer.py` (800 Differential Runs Passed)

---

## 🎯 Architectural Mission & Role Overview

As the **Pipeline Simulation Developer**, Likhith is responsible for the core execution heart of CPU PIPELINE STUDIO: the cycle-by-cycle **5-stage synchronous MIPS pipeline engine**.

The pipeline executes instructions across five discrete physical stages:
1. **IF (Instruction Fetch)**: Fetches the instruction pointed to by Program Counter ($PC$) from instruction memory and increments $PC$.
2. **ID (Instruction Decode & Register Fetch)**: Decodes opcode, resolves register operands ($rs$, $rt$), reads values from the 32-register register file, and evaluates branch conditions.
3. **EX (Execute / Address Calculation)**: Computes ALU operations (arithmetic, logical, shifts) or calculates effective memory addresses ($rs + \text{imm}$).
4. **MEM (Memory Access)**: Reads from or writes to data memory for load (`LW`) and store (`SW`) instructions.
5. **WB (Write Back)**: Writes computation or load results back into the destination register ($rd$ or $rt$) in the register file.

Likhith's subsystem:
- Advances instructions synchronously cycle-by-cycle using strongly typed inter-stage latches (`IF/ID`, `ID/EX`, `EX/MEM`, `MEM/WB`).
- Implements stall freezing (holding $PC$ and `IF/ID` latches while injecting a bubble into `ID/EX`).
- Handles pipeline flushes (squashing instructions in `IF` and `ID` on taken branches).
- Integrates a gold-standard unpipelined **Reference CPU** to verify cycle-accurate semantic parity.
- Produces a step-by-step pedagogical explainer that details hardware operations in plain English.

---

## 📦 Delivered Modules & File Explanations

| Module / File | Component Responsibility & Implementation Details |
|:---|:---|
| [`simulator/pipeline.py`](simulator/pipeline.py) | **The Core 5-Stage Pipeline Simulation Engine**<br>• Implements `PipelineSimulator`: Cycle-by-cycle stepping, latch updating, stage transition management, and execution history recording.<br>• Supports dual-mode execution: Forwarding Enabled vs. Forwarding Disabled.<br>• Supports dual branch policies: `predict_not_taken` (speculative fetch with 2-slot flush) and `stall` (freeze until branch resolves in `EX`).<br>• Enforces safety cutoff thresholds to prevent infinite loops. |
| [`simulator/models.py`](simulator/models.py) | **Strongly Typed Architectural Data Models**<br>• `Instruction`: Static parsed instruction definition (opcode, $rd$, $rs$, $rt$, immediate, label, line number).<br>• `DynamicInstruction`: In-flight instruction tracking dynamic state, stage history, and forwarded operands.<br>• `Slot`: Represents a stage slot occupying an instruction, bubble, or stall in a specific cycle.<br>• `PipelineConfig`: Simulation configuration flags (forwarding, branch policy, register timing).<br>• `SimulationResult`: Complete execution artifact containing total cycles, instruction count, register file state, memory dumps, and stage execution grid. |
| [`simulator/reference.py`](simulator/reference.py) | **Gold-Standard Unpipelined Reference CPU**<br>Simple sequential architectural reference model. Executes instructions one by one to completion with zero pipelining, providing the exact ground-truth answer key for registers, memory, and instruction count. |
| [`simulator/engine.py`](simulator/engine.py) | **Simulation Engine Orchestrator**<br>Coordinates simulation runs, dual-engine comparison (Forwarding ON vs. OFF), and binds pipeline execution traces with analytics report builders. |
| [`simulator/execute.py`](simulator/execute.py) | **ALU & Execution Arithmetic**<br>Shared mathematical logic for signed/unsigned integer addition, subtraction, bitwise operations (`AND`, `OR`, `XOR`), comparisons (`SLT`), and branch condition testing. |
| [`simulator/explainer.py`](simulator/explainer.py) | **Pedagogical Natural-Language Stage Explainer**<br>Inspects the active instruction in each stage at any selected cycle and produces human-readable diagnostic explanations for educational walkthroughs. |
| [`simulator/samples.py`](simulator/samples.py) | **Pre-Packaged Educational Workloads**<br>Curated library of standard MIPS assembly programs (Arithmetic, RAW hazard demo, Load-use cascade, Loop countdown, Array processing, Fibonacci). |
| [`tests/test_pipeline.py`](tests/test_pipeline.py) | **Pipeline Execution Test Suite**<br>Verifies 5-stage synchronous progression, cycle counting, stall bubble propagation, and register write timing. |
| [`tests/test_reference.py`](tests/test_reference.py) | **Reference CPU & Parity Test Suite**<br>Verifies that pipeline execution produces bit-exact identical register and memory state to the unpipelined Reference CPU. |
| [`tests/test_engine_and_explainer.py`](tests/test_engine_and_explainer.py) | **Engine Orchestration & Explainer Test Suite**<br>Tests simulation orchestration, dual execution comparisons, and explainer card generation. |
| [`examples/stress/advanced_array_stress.s`](examples/stress/advanced_array_stress.s) | **Complex Array Processing Workload**<br>Array initialization, element accumulation, conditional even/odd check, and memory storage. |
| [`examples/memory/array_access.s`](examples/memory/array_access.s) | **Memory Subsystem Verification Workload**<br>Validates sequential load and store word operations across word-aligned data RAM offsets. |

---

## 🧪 Verification & How to Run Tests

Likhith's pipeline engine is validated against rigorous differential testing suites:

```bash
# 1. Run all pipeline simulation and reference CPU tests
pytest tests/test_pipeline.py tests/test_reference.py tests/test_engine_and_explainer.py -v

# 2. Run the Verification Bot (Differential testing across 800 pipeline runs)
python -m bots.verifier_bot --programs 100 --seed 1
```

### ✅ Verification Results
- **Differential Parity**: 800 random programs executed across all 8 pipeline configurations; **0 register discrepancies, 0 memory discrepancies** compared to Reference CPU.
- **Structural Invariants**: Stage order $IF \to ID \to EX \to MEM \to WB$ verified for every instruction.
- **In-Order Retirement**: Instructions retire in program order without hazard corruptions.
- **CI Status**: GitHub Actions Workflow **GREEN (Success ✅)**.
