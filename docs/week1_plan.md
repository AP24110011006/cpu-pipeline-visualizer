# Project Plan and Roadmap

> The original brief asked for a week-by-week build (Week 1 foundation ... Week 8 documentation).
> The team decided to deliver the **complete project at once**, so every phase below is already implemented.
> This file is kept as the plan, the ownership map and the checklist for the final review.

| Phase | Goal | Where it lives | Owner | Status |
|---|---|---|---|---|
| Week 1 | Folder structure, Streamlit shell, stage cards, input area, samples, README, requirements, .gitignore, architecture diagram | `app.py`, `ui/`, `docs/`, root files | Members 1 and 6 | Done |
| Week 2 | Instruction parsing and cycle-by-cycle five-stage simulation | `simulator/parser.py`, `simulator/pipeline.py` | Members 2 and 3 | Done |
| Week 3 | RAW hazard detection, stalls and bubbles | `simulator/hazards.py` | Member 4 | Done |
| Week 4 | Forwarding and ON/OFF comparison | `simulator/forwarding.py`, Performance tab | Member 5 | Done |
| Week 5 | Interactive timing diagram and execution controls | `ui/charts.py`, step controls | Member 6 | Done |
| Week 6 | CPI, total cycles, speedup, utilization | `simulator/metrics.py` | Member 7 | Done |
| Week 7 | Testing, branch handling, bug fixes | `tests/`, `bots/`, control hazards in `pipeline.py` | Members 5 and 7 | Done |
| Week 8 | Final documentation, presentation, demo | `README.md`, `docs/` | Members 1 and 7 | Docs done - presentation and demo are for the team |

Faculty requirement: **two testing bots** - see `docs/testing_bots.md`.

## Final review checklist
- [ ] Every member can run `streamlit run app.py` and `python -m pytest`
- [ ] Every member can explain their own module in 2 minutes
- [ ] Demo script: sample chain (forwarding OFF then ON) -> load-use -> taken branch -> run both bots
- [ ] Each member has commits in GitHub under their own name
