# 🎨 UI & Visualization Studio — MADHAN

**Lead Engineer**: **MADHAN** (`MD`)  
**Role**: **UI & Visualization Developer**  
**Assigned Subsystem**: Professional Engineering Interface, Midnight Engineering Design System, Interactive Visualizers & Dashboard Workspaces  
**Verification Suite**: `tests/test_team_and_theme.py`, Live Streamlit Verification (11 Dedicated Workspaces)

---

## 🎯 Architectural Mission & Role Overview

As the **UI & Visualization Developer**, Madhan is responsible for the user-facing product experience of CPU PIPELINE STUDIO. 

Madhan's mission is to elevate the platform from a routine academic script into a **commercial-grade, visually stunning, high-performance CPU engineering studio**. Through the bespoke **Midnight Engineering** dark design system, responsive Plotly timing diagrams, live register/memory tables, and step-by-step cycle execution steppers, Madhan transforms abstract microarchitectural concepts into intuitive, interactive visual reality.

Madhan's subsystem:
1. **Midnight Engineering Design System**: Bespoke, accessible dark theme (`#0B1220`) featuring unified pipeline stage colors, cyan/violet accents, glowing status badges, and polished card surfaces.
2. **Interactive Timing Diagrams (Gantt Charts)**: Responsive Plotly visualizations illustrating the cycle-by-cycle journey of every instruction across `IF`, `ID`, `EX`, `MEM`, `WB`, `STALL`, and `FLUSH`.
3. **Synchronized Forwarding Comparison**: Side-by-side Forwarding Enabled vs. Forwarding Disabled comparison view with synchronized multi-step cycle steppers (`⏮️ -5`, `◀ Prev`, `Next ▶`, `+5 ⏭️`, `Reset`).
4. **11 Dedicated Engineering Workspaces**: Comprehensive tabbed navigation separating simulation, pipeline views, hazard analytics, memory inspection, performance metrics, testing bots, educational guide, and developer team architecture.
5. **Real-Time Telemetry & Metric Cards**: High-impact metrics displaying CPI, IPC, Total Cycles, Avoided Stalls, and Stage Utilization.

---

## 📦 Delivered Modules & File Explanations

| Module / File | Component Responsibility & Implementation Details |
|:---|:---|
| [`app.py`](app.py) | **Application Entrypoint**<br>Initializes the Streamlit application, configures wide layout, injects Midnight Engineering global styling, and mounts the workspace router. |
| [`ui/__init__.py`](ui/__init__.py) | **UI Package Initializer**<br>Exposes high-level dashboard and rendering entrypoints. |
| [`ui/theme.py`](ui/theme.py) | **Midnight Engineering Design System**<br>Defines color palettes, typography, CSS styling rules, and authoritative pipeline stage colors (`IF` Blue, `ID` Violet, `EX` Amber, `MEM` Cyan, `WB` Emerald). |
| [`ui/dashboard.py`](ui/dashboard.py) | **Main Dashboard Layout & Navigation Router**<br>Manages state persistence, sidebar configuration, sample loader, and routes active tab views. |
| [`ui/charts.py`](ui/charts.py) | **Interactive Visualization & Timing Diagrams**<br>Builds responsive Plotly Gantt charts, pipeline execution grids, and stage utilization bar graphs with custom tooltips and legend controls. |
| [`ui/tables.py`](ui/tables.py) | **Data Grid & Inspection Tables**<br>Renders formatted Pandas dataframes for live register files (`R0`–`R31`), memory addresses, and comparative performance metrics. |
| [`ui/helpers.py`](ui/helpers.py) | **Interactive Controls & Cycle Steppers**<br>Implements step-by-step cycle controller buttons (`⏮️ -5`, `◀ Prev`, `Next ▶`, `+5 ⏭️`, `Reset`) and simulation execution bridges. |
| [`ui/styles.py`](ui/styles.py) | **Custom CSS Injection Engine**<br>Injects card styling, glassmorphism borders, glowing status indicators, and custom button hover effects. |
| [`ui/guide.py`](ui/guide.py) | **Interactive Educational Documentation**<br>Interactive walkthrough explaining the 5-stage pipeline, hazards, forwarding, and quantitative performance formulas. |
| [`ui/bots_panel.py`](ui/bots_panel.py) | **Automated Multi-Bot Control Center**<br>UI dashboard for triggering and viewing reports from TestBot, VerifierBot, DevBot, StressBot, and HazardBot. |
| [`ui/pages/overview.py`](ui/pages/overview.py) | **Overview Workspace**: Executive execution telemetry, CPI/IPC cards, dynamic hazard counters, and pipeline highlights. |
| [`ui/pages/simulator.py`](ui/pages/simulator.py) | **Assembly Simulator Workspace**: Interactive code editor, line numbers, error diagnostics, and register/RAM initializers. |
| [`ui/pages/pipeline_view.py`](ui/pages/pipeline_view.py) | **Pipeline Visualization Workspace**: Cycle-by-cycle stage cards, natural-language explainer cards, and timing charts. |
| [`ui/pages/forwarding_comparison.py`](ui/pages/forwarding_comparison.py) | **Forwarding Comparison Workspace**: Side-by-side Forwarding ON vs. OFF execution comparison with synchronized cycle controls. |
| [`ui/pages/hazard_analytics.py`](ui/pages/hazard_analytics.py) | **Hazard & Stall Analytics Workspace**: Static vs. dynamic RAW counters, load-use events, and searchable event histories. |
| [`ui/pages/registers_memory.py`](ui/pages/registers_memory.py) | **Registers & Memory Workspace**: Live cycle-by-cycle register inspector (`R0`–`R31`) and RAM viewer with Reference CPU check. |
| [`ui/pages/performance.py`](ui/pages/performance.py) | **Performance Workspace**: Quantitative metric tables (CPI, IPC, Speedup, Efficiency) and stage utilization charts. |
| [`ui/pages/developer_team.py`](ui/pages/developer_team.py) | **Developer Team Workspace**: Dedicated architectural team showcase mapping all 5 engineering roles and verified modules. |
| [`ui/pages/testing_bots.py`](ui/pages/testing_bots.py) | **Testing Bots Workspace**: Interactive runner for all 5 automated bots and the Assembly Optimization Bot. |
| [`ui/pages/learning_center.py`](ui/pages/learning_center.py) | **Learning Center Workspace**: Comprehensive COA textbook guide, quantitative equations, and hardware glossary. |
| [`ui/pages/settings.py`](ui/pages/settings.py) | **Settings Workspace**: Safety bounds, execution limits, cache management, and environment diagnostics. |

---

## 🎨 Unified Pipeline Color Palette

| Stage | Name | Color Code | Visual Swatch |
|:---:|:---|:---:|:---:|
| **IF** | Instruction Fetch | `#3B82F6` | Core Blue |
| **ID** | Instruction Decode | `#8B5CF6` | Deep Violet |
| **EX** | Execute / ALU | `#F59E0B` | Warm Amber |
| **MEM** | Memory Access | `#06B6D4` | Cyan Blue |
| **WB** | Write Back | `#10B981` | Emerald Green |
| **STALL** | Data Stall | `#EF4444` | Crimson Red |
| **BUBBLE** | Pipeline Bubble | `#64748B` | Slate Gray |
| **FWD** | Bypass Forwarding | `#22D3EE` | Bright Cyan |
| **FLUSH** | Branch Flush | `#F43F5E` | Rose Coral |

---

## 🧪 How to Launch the Application & Run Tests

```bash
# 1. Run the Streamlit engineering studio
streamlit run app.py

# 2. Run the UI & theme validation test suite
pytest tests/test_team_and_theme.py -v
```

### ✅ Verification Results
- **Theme Tokens**: All Midnight Engineering colors, surface tokens, and stage badges verified.
- **Interface Workspaces**: All 11 dedicated workspaces load smoothly with zero exceptions.
- **CI Status**: GitHub Actions Workflow **GREEN (Success ✅)**.
