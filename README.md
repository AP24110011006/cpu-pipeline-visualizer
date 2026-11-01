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

## 🧠 Algorithms Implemented & Complexity Analysis

Likhith engineered three foundational microarchitectural algorithms governing synchronous cycle execution:

### Algorithm 1: Synchronous Reverse-Stage Pipeline Progression (`step`)
- **Purpose**: Advances the physical pipeline by exactly one clock cycle. Updates are executed in **reverse stage order** ($WB \to MEM \to EX \to ID \to IF$) to prevent output-input overwrite hazards within the same cycle.
- **Pseudocode**:
  ```python
  def step(self):
      cycle = self.current_cycle + 1
      
      # 1. WB Stage: Commit instruction and write back to register file
      wb_inst = self.latch_MEM_WB
      if wb_inst and is_real(wb_inst):
          if wb_inst.writes_reg and wb_inst.dest != 0:
              self.registers[wb_inst.dest] = wb_inst.computed_result
          self.retired_instructions += 1
      
      # 2. MEM Stage: Read/Write RAM and latch into MEM/WB
      mem_inst = self.latch_EX_MEM
      if mem_inst and is_real(mem_inst):
          if mem_inst.opcode == 'LW':
              mem_inst.computed_result = self.memory.read(mem_inst.memory_address)
          elif mem_inst.opcode == 'SW':
              self.memory.write(mem_inst.memory_address, mem_inst.store_value)
      self.latch_MEM_WB = mem_inst
      
      # 3. EX Stage: Compute ALU operation or address and latch into EX/MEM
      ex_inst = self.latch_ID_EX
      if ex_inst and is_real(ex_inst):
          op1, op2 = self.forwarding_unit.resolve_operands(ex_inst, self.latch_EX_MEM, self.latch_MEM_WB)
          ex_inst.computed_result = execute_alu(ex_inst.opcode, op1, op2)
      self.latch_EX_MEM = ex_inst
      
      # 4. ID Stage: Hazard Check & Latch to ID/EX
      stall = self.hazard_unit.detect_data_stall(self.latch_IF_ID, ex_inst, mem_inst, wb_inst)
      if stall:
          # FREEZE IF and ID stages; inject bubble into ID/EX
          self.latch_ID_EX = create_bubble(cycle, reason=stall.reason)
          # IF/ID remains unchanged; PC remains unchanged
      else:
          id_inst = self.latch_IF_ID
          if id_inst and is_real(id_inst):
              id_inst.val_rs = self.registers[id_inst.rs]
              id_inst.val_rt = self.registers[id_inst.rt]
          self.latch_ID_EX = id_inst
          
          # 5. IF Stage: Fetch next instruction from PC and increment PC
          if self.pc < len(self.instructions):
              self.latch_IF_ID = create_dynamic(self.instructions[self.pc], cycle)
              self.pc += 1
          else:
              self.latch_IF_ID = None
  ```
- **Complexity**:
  - **Time Complexity**: $\mathcal{O}(1)$ per clock cycle. Bounded strictly by 5 stage updates and a fixed 32-register register file. Total time: $\mathcal{O}(C)$ for $C$ cycles.
  - **Space Complexity**: $\mathcal{O}(1)$ active state; $\mathcal{O}(C)$ history recording for interactive GUI scrubbing.

---

### Algorithm 2: Gold-Standard Reference CPU Sequential Emulation (`run_reference`)
- **Purpose**: Executes the program sequentially without pipelining (1 instruction completes before the next begins), providing the formal baseline for differential verification.
- **Logic**:
  $$\text{State}_{t+1} = \text{Execute}(\text{Decode}(\text{Fetch}(PC_t)), \text{State}_t)$$
  - Each instruction runs through Fetch $\to$ Decode $\to$ Execute $\to$ Memory $\to$ WriteBack atomically.
  - Compares final register array $R_{\text{pipe}}[0..31] == R_{\text{ref}}[0..31]$ and memory array $M_{\text{pipe}} == M_{\text{ref}}$.
- **Complexity**:
  - **Time Complexity**: $\mathcal{O}(N)$ dynamic instruction executions.
  - **Space Complexity**: $\mathcal{O}(R + M)$ where $R=32$ registers and $M$ is active memory words.

---

### Algorithm 3: Pedagogical Stage State Introspection (`explain_stage`)
- **Purpose**: Dynamic narrative generation inspecting active stage latches, operand values, and control flags to generate crystal-clear educational explanations of stage actions.
- **Complexity**: $\mathcal{O}(1)$ per stage evaluation.

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
