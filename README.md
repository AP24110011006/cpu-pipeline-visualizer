# CPU PIPELINE STUDIO

**Advanced CPU Pipeline Simulation, Hazard Analysis and Performance Engineering Platform**

A commercial-grade Computer Organization and Architecture (COA) simulation, hazard analytics, and hardware verification studio built with Python, Streamlit, Plotly, and Pytest.

Implements a cycle-by-cycle **5-stage MIPS pipeline** (**IF · ID · EX · MEM · WB**), instruments hardware forwarding bypass paths, models load-use and speculative branch execution, audits mathematical slot conservation without double counting, provides 5 automated verification bots, and features a dedicated **Full Stack Engineering Agent**.

---

## 🎨 Design System: Midnight Engineering

CPU PIPELINE STUDIO features a bespoke, accessible **Midnight Engineering** theme:
- **Background**: `#0B1220` · **Main Surface**: `#111C2E` · **Secondary Surface**: `#162338` · **Borders**: `#27364B`
- **Primary Accent**: `#22D3EE` · **Secondary Accent**: `#A78BFA`
- **Status Accents**: Success `#10B981` · Warning `#F59E0B` · Error `#F43F5E`
- **Typography & Labels**: Primary `#F1F5F9` · Secondary `#94A3B8` · Muted `#64748B`

### Unified Pipeline Stage Colors
- **IF (Instruction Fetch)**: `#3B82F6` (Core Blue)
- **ID (Instruction Decode)**: `#8B5CF6` (Deep Violet)
- **EX (Execute / ALU)**: `#F59E0B` (Warm Amber)
- **MEM (Memory Access)**: `#06B6D4` (Cyan Blue)
- **WB (Write Back)**: `#10B981` (Emerald Green)
- **STALL**: `#EF4444` · **BUBBLE**: `#64748B` · **FORWARDING**: `#22D3EE` · **FLUSH**: `#F43F5E`

*An optional Clean Engineering Light Theme is available via the sidebar toggle.*

---

## 🏛️ The 11 Dedicated Workspaces

1. 📊 **Overview Dashboard**: High-level execution telemetry, CPI/IPC, dynamic hazard counters, stall cycles, avoided stalls, and engineering status.
2. 💻 **Assembly Simulator**: Interactive assembly editor, line numbers, error diagnostics, presets, register/memory initializers, and compilation controls.
3. ⏱️ **Pipeline Visualization**: Cycle-by-cycle stage cards (`IF`, `ID`, `EX`, `MEM`, `WB`), pedagogical explainer glass cards, and Plotly timing diagrams.
4. ⚡ **Forwarding Comparison**: Side-by-side Forwarding ON vs. OFF comparison with independent Diagram View Modes (`Window around cycle (Fast)` vs. `Full program`) and cycle synchronization.
5. ⚠️ **Hazard & Stall Analytics**: Detailed static vs. dynamic RAW counters, load-use events, stall events vs. stall clock cycles, stalls avoided, and complete searchable Event History.
6. 🧮 **Registers & Memory**: Live cycle-by-cycle inspection of registers (`R0`–`R31`) and data RAM with formal unpipelined Reference CPU differential check.
7. 📈 **Performance Analysis**: Quantitative metrics (CPI, IPC, Speedup vs. Unpipelined, Pipeline Efficiency) and hardware stage utilization bar charts.
8. 👥 **Developer Team & Progress**: 5-role architecture ownership tracking with evidence-based task tracking and verified test suites.
9. 🤖 **Intelligent Testing Bots & Engineering Agent**: Suite of 5 automated invariant bots, topological scheduler, and the autonomous Full Stack Engineering Agent.
10. 📚 **COA Learning Center**: Comprehensive educational guide, quantitative COA equations, and microarchitectural glossary.
11. ⚙️ **Settings & Configuration**: Safety bounds, execution limits, session cache clearing, and environment diagnostics.

---

## 👥 Authoritative Developer Team Architecture

| Role | Lead | Assigned Module | Verified Test Suite | Status |
|:---|:---|:---|:---|:---:|
| **Instruction Parser Developer** | **REHMAN** (`RH`) | `simulator/parser.py` | `tests/test_parser.py` (13 tests) | Verified Core • Active |
| **Pipeline Simulation Developer** | **Likhith** (`LK`) | `simulator/pipeline.py`, `simulator/models.py` | `tests/test_pipeline.py`, `tests/test_reference.py` (17 tests) | Verified Core • Active |
| **Hazard Detection Developer** | **MANIKANTH** (`MK`) | `simulator/hazards.py`, `simulator/analytics/` | `tests/test_hazards.py`, `tests/test_analytics.py` (12 tests) | Verified Core • Active |
| **Forwarding & Control Hazard Developer** | **LATHISH** (`LT`) | `simulator/forwarding.py`, control logic | `tests/test_forwarding.py` (13 tests) | Verified Core • Active |
| **UI & Visualization Developer** | **MADHAN** (`MD`) | `app.py`, `ui/` | `tests/test_engine_and_explainer.py` (14 tests) | Verified Core • Active |

*Progress is strictly evidence-based and calculated directly from completed vs. total task backlog.*

---

## 🤖 Intelligent Multi-Bot Suite & Engineering Agent

### 1. Invariant Verification Bots
- **Bot 1 — Testing Bot** (`bots/test_bot.py`): 27 textbook regression scenarios and 10 negative syntax edge-case rejections.
- **Bot 2 — Verification Bot** (`bots/verifier_bot.py`): Differential validation against unpipelined Reference CPU across 800 pipeline runs and structural invariants.
- **Bot 3 — Assembly Optimization Bot** (`bots/dev_bot.py`): DAG topological dependency scheduling, RAW/WAR/WAW ordering preservation, and assembly workload synthesis.
- **Bot 4 — Stress Testing Bot** (`bots/stress_bot.py`): Scalability benchmarking from 100 to 5,000 instructions, memory allocation tracking, and safe cycle cutoff.
- **Bot 5 — Hazard Analysis Bot** (`bots/hazard_bot.py`): Microarchitectural conservation law verification ($\text{Total Slots} = 5 \times \text{Cycles} = \text{Useful} + \text{Bubbles}$) and zero double-counting audits.

### 2. Autonomous Full Stack Engineering Agent (`agents/`)
- **Repository Intelligence**: Structural directory inspection, module responsibility mapping, and AST import dependency analysis.
- **Risk-Aware Task Planning**: Generates step-by-step implementation plans outlining targeted files and risk mitigations.
- **Controlled File Modification**: Workspace sandbox isolation, path traversal prevention, unified git diff generation, and safe rollback.
- **Diagnostic Engine & Bounded Repair**: Automatically captures test failure tracebacks, isolates root causes, synthesizes targeted repairs, and verifies completion.
- **Approval Controls**: Human-in-the-loop review before staging and applying modifications to disk.

---

## 🚀 Setup & Execution (Windows)

1. Open PowerShell or Command Prompt:
   ```powershell
   cd pipeline-execution-visualizer
   ```

2. Run the application:
   ```powershell
   py -3.12 -m streamlit run app.py
   ```
   Or double-click `run_windows.bat`.

3. Access the web application at **`http://localhost:8501`**.

---

## 🧪 Automated Testing & Verification Baseline

Run the complete pytest regression suite:
```powershell
py -3.12 -m pytest -v             # 155 unit & regression tests (100% pass)
```

Run all 5 autonomous verification bots:
```powershell
py -3.12 -m bots                  # 128 / 128 invariant checks (100% pass)
```

Run performance benchmark:
```powershell
py -3.12 -m tests.benchmark
```
