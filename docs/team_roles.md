# Developer Team Roles & Architecture Ownership

This platform is structured across five distinct engineering responsibilities, each tied to concrete codebase modules and automated verification suites:

---

### Role 1: Instruction Parser Developer
- **Lead**: **REHMAN** (`RH`)
- **Assigned Module**: `simulator/parser.py`
- **Verification Suite**: `tests/test_parser.py` (13 tests passed)
- **Responsibilities**:
  - Tokenization and MIPS instruction validation.
  - Register operand validation (`$1–$31`, `R0–R31`) and `R0` zero-register invariant enforcement.
  - Signed 32-bit immediate boundary validation.
  - Branch and jump label resolution and symbol table indexing.
  - Clear line-numbered syntax error diagnostics and spelling suggestions.
  - Parser regression tests and negative syntax edge-case coverage.

---

### Role 2: Pipeline Simulation Developer
- **Lead**: **Likhith** (`LK`)
- **Assigned Modules**: `simulator/pipeline.py`, `simulator/models.py`
- **Verification Suite**: `tests/test_pipeline.py`, `tests/test_reference.py` (17 tests passed)
- **Responsibilities**:
  - Five-stage cycle-by-cycle synchronous pipeline engine ($IF \to ID \to EX \to MEM \to WB$).
  - Instruction lifecycle management, dynamic history tracking, and retired count.
  - Cycle management and pipeline state transitions.
  - Split-phase register file timing (first-half write, second-half read).
  - Register and memory execution correctness.
  - Architectural parity verification against the unpipelined reference CPU.
  - Safe cycle cutoff bounds for infinite loop termination.

---

### Role 3: Hazard Detection Developer
- **Lead**: **MANIKANTH** (`MK`)
- **Assigned Modules**: `simulator/hazards.py`, `simulator/analytics/`
- **Verification Suite**: `tests/test_hazards.py`, `tests/test_analytics.py`, `bots/hazard_bot.py` (76 invariant checks passed)
- **Responsibilities**:
  - Dynamic RAW data hazard detection in the `ID` stage.
  - Load-use hazard detection inserting stall bubbles into the `EX` stage.
  - Fine-grained stall cycle vs discrete stall event accounting.
  - Zero double-counting verification across pipeline stages and execution cycles.
  - Slot conservation law auditing ($\text{Total Slots} = \text{Useful Slots} + \text{Bubble Slots}$).
  - Hazard Analytics workspace telemetric data provider and event tracking.

---

### Role 4: Forwarding & Control Hazard Developer
- **Lead**: **LATHISH** (`LT`)
- **Assigned Modules**: `simulator/forwarding.py`, control-flow branches/jumps
- **Verification Suite**: `tests/test_forwarding.py`, `tests/test_audit_and_regressions.py` (13 tests passed)
- **Responsibilities**:
  - Hardware forwarding paths (`EX/MEM \to EX` and `MEM/WB \to EX`) with newest-producer priority.
  - Dynamic operand selection and forwarded value computation.
  - Branch handling and prediction policies (`predict_not_taken`, `stall`).
  - Jump instruction decode-stage redirection (1 wasted fetch slot).
  - Pipeline flushing and 2-slot speculative instruction squashing.
  - Control hazard management and forwarding regression tests.

---

### Role 5: UI & Visualization Developer
- **Lead**: **MADHAN** (`MD`)
- **Assigned Modules**: `app.py`, `ui/`
- **Verification Suite**: `tests/test_engine_and_explainer.py` (14 tests passed)
- **Responsibilities**:
  - **CPU PIPELINE STUDIO** design system and unified Midnight Engineering tokens.
  - Instant cycle navigation (0.015ms stepping) decoupled from simulation execution.
  - Dual-mode Plotly pipeline timing diagrams (Windowed Fast View + Full Program).
  - Independent side-by-side Forwarding ON vs OFF comparison workspace.
  - Microarchitectural Cycle Explainer pedagogical glass cards.
  - Intelligent Multi-Bot Hub and Full Stack Engineering Agent workspace integration.
  - Responsive layouts, table styling, and browser-level stability.
