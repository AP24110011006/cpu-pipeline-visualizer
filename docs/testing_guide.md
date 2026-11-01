# Testing & Quality Assurance Guide

## Automated Test Suites

The platform includes two layers of automated verification:

### 1. Pytest Test Suite (`tests/`)
Run with:
```bash
python -m pytest -v
```
Covers:
- `test_parser.py`: Syntax tokenization, immediate bounds, comment handling, register validation.
- `test_pipeline.py`: Step-by-step cycle advancement, bubble insertion, in-order retirement.
- `test_hazards.py`: Static and dynamic RAW detection, load-use recognition.
- `test_forwarding.py`: EX/MEM and MEM/WB forwarding decisions.
- `test_reference.py`: Parity against single-cycle unpipelined reference CPU.
- `test_metrics.py`: CPI, IPC, ideal cycles, and utilization calculations.
- `test_analytics.py`: Slot conservation, zero double-counting, event tracker queries.
- `test_bots_extended.py`: Verification of StressBot and HazardBot runners.

### 2. Intelligent Multi-Bot Engineering Suite (`bots/`)
Run with:
```bash
python -m bots
```
Or execute individual bots:
- `python -m bots.test_bot`: 27 textbook scenario regressions.
- `python -m bots.verifier_bot`: 10 structural invariant checks across 800 random program runs.
- `python -m bots.dev_bot`: 17 checks for DAG scheduling, RAW/WAR/WAW preservation.
- `python -m bots.stress_bot`: 10 scalability checks across 100 to 2,000 instructions.
- `python -m bots.hazard_bot`: 64 microarchitectural conservation audits.
