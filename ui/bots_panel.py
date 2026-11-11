"""Teammate Bots Panel: Interactive interface for Testing Bot and Full Stack Dev Bot.

Teammate 1 - Testing Bot: Regression and Differential Verifier.
Teammate 2 - Full Stack Dev Bot: Hazard Analyzer, Instruction Scheduler, Program Synthesizer.
Collaboration: Optimize with Dev Bot & Verify with Testing Bot.
"""

from __future__ import annotations

from typing import Dict, Optional

import pandas as pd
import streamlit as st

from bots.dev_bot import (
    SYNTHESIZED_PROGRAMS,
    analyze_code,
    optimize_schedule,
    run_dev_bot,
    synthesize_program,
)
from bots.report import BotReport
from bots.test_bot import run_test_bot
from bots.verifier_bot import CONFIGURATIONS, run_verifier_bot, verify_program
from ui.helpers import show_df


def _show_report(report: Optional[BotReport]) -> None:
    if report is None:
        return
    left, middle, right = st.columns(3)
    left.metric("Checks passed", report.passed)
    middle.metric("Checks failed", report.failed)
    right.metric("Total checks", report.total)
    if report.all_passed:
        st.success(report.summary())
    else:
        st.error(report.summary())
    rows = [
        {"Result": "✅ Pass" if check.passed else "❌ FAIL", "Check": check.name, "Details": check.detail}
        for check in report.checks
    ]
    show_df(pd.DataFrame(rows, columns=["Result", "Check", "Details"]))
    stats = {key: value for key, value in report.stats.items() if not key.startswith("_")}
    if stats:
        st.caption("  ·  ".join(f"{key}: {value}" for key, value in stats.items()))
    for number, failure in enumerate(report.failures[:5], start=1):
        with st.expander(f"Failure details #{number}"):
            st.code(failure)


def render_bots_panel(loaded: Optional[dict]) -> None:
    st.markdown(
        "Two automated bots collaborate as development teammates: **Teammate 1 (Testing Bot)** ensures regression "
        "and differential correctness, while **Teammate 2 (Full Stack Dev Bot)** provides hazard analysis, "
        "instruction scheduling, and workload synthesis."
    )

    tab_dev, tab_test, tab_collab = st.tabs([
        "⚡ Teammate 2: Full Stack Dev Bot",
        "🧪 Teammate 1: Testing Bot",
        "🤝 Teammate Collaboration",
    ])

    # =========================================================================
    # TAB 1: FULL STACK DEV BOT
    # =========================================================================
    with tab_dev:
        st.subheader("⚡ Teammate 2 — Full Stack Dev Bot")
        st.caption(
            "Responsible for full-stack pipeline development: pipeline bottleneck detection, "
            "instruction scheduling (reordering independent instructions to fill delay slots), "
            "and workload program synthesis."
        )

        # 1. Dev Bot Self Verification
        with st.expander("🛠️ Dev Bot Self-Verification Report", expanded=False):
            st.markdown("Run the Dev Bot's built-in self-tests verifying instruction reordering and code synthesizers.")
            if st.button("Run Full Stack Dev Bot Self-Test", key="run_dev_bot_btn", type="secondary"):
                with st.spinner("Dev Bot running self-verification suite..."):
                    st.session_state["dev_bot_report"] = run_dev_bot()
            _show_report(st.session_state.get("dev_bot_report"))

        st.divider()

        # 2. Hazard Analyzer
        st.markdown("### 🔍 Pipeline Hazard & Bottleneck Analyzer")
        st.caption("Inspects assembly instructions for RAW dependencies, load-use delays, and stall risks.")

        current_code = loaded["code"] if loaded else st.session_state.get("code_input", "")
        code_to_analyze = st.text_area(
            "Assembly program to analyze:",
            value=current_code,
            height=130,
            key="analyzer_code_input",
            help="Type or paste assembly code to analyze hazard bottlenecks.",
        )

        if st.button("Analyze Code with Dev Bot", key="analyze_btn", type="primary"):
            with st.spinner("Analyzing pipeline dependencies..."):
                st.session_state["analysis_results"] = analyze_code(code_to_analyze)

        analysis = st.session_state.get("analysis_results")
        if analysis:
            if not analysis["ok"]:
                st.error("Analysis Failed: " + "; ".join(analysis["errors"]))
            else:
                stats = analysis["stats"]
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Instructions", analysis["instruction_count"])
                m2.metric("RAW Hazards", stats["raw_count"])
                m3.metric("Load-Use Delays", stats["load_use_count"])
                m4.metric("Forwarding Cycles", stats["simulated_cycles_fwd"])

                st.markdown("#### Bottleneck Assessment")
                for bn in analysis["bottlenecks"]:
                    if "load-use" in bn.lower() or "wasted" in bn.lower() or "lost" in bn.lower():
                        st.warning(f"⚠️ {bn}")
                    else:
                        st.info(f"ℹ️ {bn}")

                st.markdown("#### Optimization Opportunities")
                for opp in analysis["optimization_opportunities"]:
                    st.success(f"💡 {opp}")

                if analysis["raw_hazards"]:
                    st.markdown("#### Static RAW Dependency Breakdown")
                    raw_df = pd.DataFrame([
                        {
                            "Producer": f"I{h['producer_index'] + 1}: {h['producer_text']}",
                            "Consumer": f"I{h['consumer_index'] + 1}: {h['consumer_text']}",
                            "Register": h["register"],
                            "Distance": h["distance"],
                            "Kind": h["kind"],
                            "Stalls (Fwd ON)": h["stalls_with_forwarding"],
                            "Stalls (Fwd OFF)": h["stalls_without_forwarding"],
                        }
                        for h in analysis["raw_hazards"]
                    ])
                    show_df(raw_df)

        st.divider()

        # 3. Instruction Scheduler & Optimizer
        st.markdown("### 🚀 Instruction Scheduler & Delay Slot Optimizer")
        st.caption(
            "Reorders independent instructions to fill delay slots (e.g. between LW and its consumer) "
            "while strictly preserving RAW, WAR, WAW dependencies and branch labels."
        )

        regs_dict = loaded["regs"] if loaded else {}
        mem_dict = loaded["mem"] if loaded else {}

        if st.button("🚀 Optimize Schedule with Dev Bot", key="optimize_btn", type="primary"):
            with st.spinner("Dev Bot scheduling instructions..."):
                opt_code, opt_info = optimize_schedule(code_to_analyze, regs_dict, mem_dict)
                st.session_state["optimizer_result"] = (opt_code, opt_info)

        opt_data = st.session_state.get("optimizer_result")
        if opt_data:
            opt_code, opt_info = opt_data
            if not opt_info.get("ok", True):
                st.error(opt_info.get("error", "Optimization error"))
            else:
                saved = opt_info.get("cycles_saved_fwd", 0)
                stalls_elim = opt_info.get("stalls_eliminated", 0)

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Original Cycles (Fwd ON)", opt_info.get("original_cycles_fwd", 0))
                col2.metric("Optimized Cycles (Fwd ON)", opt_info.get("optimized_cycles_fwd", 0), delta=-saved if saved else None)
                col3.metric("Stalls Eliminated", stalls_elim)
                col4.metric("Verification Status", "✅ Verified" if opt_info.get("verified") else "⚠️ Warning")

                if saved > 0:
                    st.success(f"🎉 Optimization Success: Dev Bot eliminated {stalls_elim} stall(s) and saved {saved} execution cycle(s)!")
                else:
                    st.info("Instruction sequence was already optimal or strictly constrained by dependencies.")

                st.markdown("#### Transformations Applied")
                for tf in opt_info.get("transformations", []):
                    st.markdown(f"- {tf}")

                st.markdown("#### Side-by-Side Code Comparison")
                c_left, c_right = st.columns(2)
                with c_left:
                    st.markdown("**Original Assembly:**")
                    st.code(code_to_analyze, language="asm")
                with c_right:
                    st.markdown("**Dev-Bot Optimized Assembly:**")
                    st.code(opt_code, language="asm")

                if st.button("📥 Apply Optimized Code to Visualizer", key="apply_opt_code"):
                    st.session_state["code_input"] = opt_code
                    st.session_state["engine_result"] = None
                    st.session_state["loaded"] = None
                    st.success("Optimized code applied to visualizer! Switch to the 🚀 Simulator tab to inspect or run it.")
                    st.rerun()

        st.divider()

        # 4. Workload Program Synthesizer
        st.markdown("### ✨ Workload Program Synthesizer")
        st.caption("Synthesizes verified assembly programs for representative processor workloads.")

        template_options = {
            "Fibonacci Sequence (Loop & Data Flow)": "fibonacci",
            "Array Sum (Memory Access & Delay Slot Scheduling)": "array_sum",
            "Hazard Stress Benchmark (Tight RAW Chains & Load-Use)": "hazard_stress",
            "Independent Burst (Ideal IPC & Zero Stalls)": "independent_burst",
        }
        selected_label = st.selectbox("Select workload template:", list(template_options.keys()), key="synth_select")
        selected_key = template_options[selected_label]

        if st.button("✨ Synthesize Workload", key="synth_btn"):
            synth_text = synthesize_program(selected_key)
            st.session_state["synth_output"] = synth_text
            st.session_state["synth_template_key"] = selected_key

        synth_result = st.session_state.get("synth_output")
        if synth_result:
            st.markdown(f"**Synthesized `{selected_label}` Assembly:**")
            st.code(synth_result, language="asm")
            if st.button("📥 Load Synthesized Code into Visualizer", key="load_synth_btn"):
                st.session_state["code_input"] = synth_result
                # Configure initial memory/regs for templates that need them
                if st.session_state.get("synth_template_key") == "array_sum":
                    st.session_state["init_mem"] = "0=10, 4=20, 8=30, 12=40"
                    st.session_state["init_regs"] = ""
                else:
                    st.session_state["init_mem"] = ""
                    st.session_state["init_regs"] = ""
                st.session_state["engine_result"] = None
                st.session_state["loaded"] = None
                st.success(f"Synthesized '{selected_label}' copied to visualizer input! Switch to 🚀 Simulator tab to inspect or run it.")
                st.rerun()

    # =========================================================================
    # TAB 2: TESTING BOT
    # =========================================================================
    with tab_test:
        st.subheader("🤖 Teammate 1 — Testing Bot")
        st.caption("Comprehensive automated test bot: scenario regression and 8-configuration differential testing.")

        st.markdown("#### Scenario Regression (Test Bot)")
        st.caption("Runs textbook programs and validates cycle counts, data stalls, forwarding events, and register states.")
        if st.button("Run Test Bot", key="run_test_bot_tab", type="primary"):
            with st.spinner("Test Bot is running regression scenarios..."):
                st.session_state["test_bot_report"] = run_test_bot()
        _show_report(st.session_state.get("test_bot_report"))

        st.divider()

        st.markdown("#### Differential Testing (Verifier Bot)")
        st.caption(
            f"Fuzz-tests the pipeline across {len(CONFIGURATIONS)} hardware configurations against a simple "
            "non-pipelined reference CPU and verifies structural pipeline invariants."
        )
        col_a, col_b = st.columns(2)
        programs = col_a.slider("Random programs", 10, 300, 60, step=10, key="bot_programs_tab")
        seed = col_b.number_input("Random seed", min_value=0, max_value=10_000, value=1, step=1, key="bot_seed_tab")
        col_c, col_d = st.columns(2)
        with_branches = col_c.checkbox("Include branches, jumps and loops", value=True, key="bot_branches_tab")
        with_memory = col_d.checkbox("Include loads and stores", value=True, key="bot_memory_tab")

        if st.button("Run Verifier Bot on random programs", key="run_verifier_bot_tab"):
            with st.spinner("Verifier Bot is generating and differentially testing programs..."):
                st.session_state["verifier_report"] = run_verifier_bot(
                    programs=int(programs), seed=int(seed),
                    allow_branches=bool(with_branches), allow_memory=bool(with_memory))
        _show_report(st.session_state.get("verifier_report"))

        st.divider()

        st.markdown("#### Verify Loaded Program")
        if loaded is None:
            st.info("Load instructions first (top of the page) to verify your own program.")
        elif st.button("Verify my loaded program in all configurations", key="verify_loaded_tab"):
            st.session_state["verify_loaded_report"] = verify_program(
                loaded["code"], loaded["regs"], loaded["mem"], label="your loaded program")
        if loaded is not None:
            _show_report(st.session_state.get("verify_loaded_report"))

    # =========================================================================
    # TAB 3: TEAMMATE COLLABORATION
    # =========================================================================
    with tab_collab:
        st.subheader("🤝 Teammate Collaboration: Dev Bot + Testing Bot")
        st.markdown(
            "Experience both teammate bots working as a collaborative unit: **Full Stack Dev Bot** optimizes the "
            "instruction schedule to eliminate data stalls, and **Testing Bot** immediately performs differential "
            "verification across all 8 pipeline configurations against the reference CPU."
        )

        collab_code = loaded["code"] if loaded else st.session_state.get("code_input", "")
        st.text_area("Program for Teammate Collaboration:", value=collab_code, height=120, key="collab_code_input", disabled=True)

        regs_collab = loaded["regs"] if loaded else {}
        mem_collab = loaded["mem"] if loaded else {}

        if st.button("🚀 Optimize with Dev Bot & Verify with Testing Bot", key="run_collab_btn", type="primary"):
            with st.spinner("Dev Bot optimizing schedule and Testing Bot verifying equivalence..."):
                opt_code, opt_info = optimize_schedule(collab_code, regs_collab, mem_collab)
                verif_report = verify_program(opt_code, regs_collab, mem_collab, label="Dev-Bot Optimized Program")
                st.session_state["collab_result"] = {
                    "opt_code": opt_code,
                    "opt_info": opt_info,
                    "verif_report": verif_report,
                }

        collab = st.session_state.get("collab_result")
        if collab:
            opt_info = collab["opt_info"]
            verif_report = collab["verif_report"]
            saved = opt_info.get("cycles_saved_fwd", 0)

            if verif_report.all_passed:
                if saved > 0:
                    st.success(
                        f"🎉 **Teammate Collaboration Succeeded!** Full Stack Dev Bot optimized the schedule and "
                        f"saved **{saved} cycle(s)** ({opt_info.get('stalls_eliminated', 0)} data stall eliminated), "
                        f"and Testing Bot confirmed **100% differential equivalence** across all 8 configurations!"
                    )
                else:
                    st.success(
                        "✅ **Teammate Collaboration Verified!** Program is already optimal, and Testing Bot "
                        "verified 100% equivalence across all 8 configurations."
                    )
            else:
                st.error("❌ Collaboration check flagged a verification issue.")

            c1, c2, c3 = st.columns(3)
            c1.metric("Original Cycles", opt_info.get("original_cycles_fwd", 0))
            c2.metric("Optimized Cycles", opt_info.get("optimized_cycles_fwd", 0), delta=-saved if saved else None)
            c3.metric("Testing Bot Invariants", f"{verif_report.passed}/{verif_report.total} Passed")

            st.markdown("#### Testing Bot Differential Report on Optimized Code")
            _show_report(verif_report)

            st.markdown("#### Dev-Bot Optimized Assembly")
            st.code(collab["opt_code"], language="asm")
            if st.button("📥 Apply Collaborative Optimization to Visualizer", key="collab_apply_btn"):
                st.session_state["code_input"] = collab["opt_code"]
                st.session_state["engine_result"] = None
                st.session_state["loaded"] = None
                st.success("Optimized code applied! Switch to the 🚀 Simulator tab to inspect or run it.")
                st.rerun()
