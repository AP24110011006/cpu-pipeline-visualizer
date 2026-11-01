# Developer Guide

## Development Environment Setup

1. **Python Runtime**: Python 3.12 (Recommended).
2. **Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Running the Application**:
   ```bash
   streamlit run app.py
   ```
   Or on Windows:
   ```cmd
   run_windows.bat
   ```

## Running Automated Verification

- Run full pytest suite:
  ```bash
  python -m pytest -v
  ```
- Run the 5 Intelligent Engineering Bots:
  ```bash
  python -m bots
  ```
- Run performance benchmarks:
  ```bash
  python -m tests.benchmark
  ```

## Architecture Directory Structure
- `simulator/`: Core 5-stage MIPS pipeline simulation engine.
- `simulator/analytics/`: Fine-grained hazard, stall, and forwarding telemetry.
- `ui/`: Modern 11-workspace Streamlit dashboard and Plotly timing diagrams.
- `bots/`: 5 autonomous verification and optimization bots.
- `tests/`: Unit, integration, and regression tests.
- `examples/`: Categorized assembly code examples.
- `docs/`: Technical specifications and architecture guides.
