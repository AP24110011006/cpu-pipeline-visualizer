"""Intelligent Testing Bots & Full Stack Engineering Agent Workspace."""

from __future__ import annotations

import json
from typing import Dict, List, Optional
import streamlit as st

from agents import FullStackEngineeringAgent, Task, TaskState
from bots.bot_runner import (
    BOT_REGISTRY,
    export_reports_json,
    export_reports_markdown,
    run_all_bots,
    run_single_bot,
)
from bots.dev_bot import DevBot, analyze_code, optimize_schedule, synthesize_program
from bots.report import BotReport
from simulator.engine import EngineResult


def render_testing_bots(engine: Optional[EngineResult]) -> None:
    """Render the intelligent multi-bot testing, verification, and autonomous agent workspace."""
    st.markdown("## 🤖 Intelligent Bots & Full Stack Engineering Agent")
    st.caption("Automated regression testing, invariant verification, instruction scheduling, and autonomous repository engineering.")

    tab_runner, tab_optbot, tab_agent = st.tabs([
        "🚀 Bot Test Runner & Reports",
        "⚡ Assembly Optimization Bot",
        "🛠️ Full Stack Engineering Agent",
    ])

    # ---------------- TAB 1: Bot Test Runner
    with tab_runner:
        st.markdown("### Run Automated Invariant Verification Bots")
        st.caption("Executes 5 specialized bots validating pipeline physics, differential CPU parity, resource bounds, and hazard conservation.")

        b_col1, b_col2 = st.columns([2, 1])
        with b_col1:
            selected_bot = st.selectbox(
                "Select Bot to Execute",
                ["all"] + list(BOT_REGISTRY.keys()),
                format_func=lambda k: "Run All 5 Bots in Sequence" if k == "all" else BOT_REGISTRY[k]["name"],
            )
        with b_col2:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            run_btn = st.button("▶ Execute Selected Bot(s)", type="primary", use_container_width=True)

        # Execution logic
        if run_btn:
            with st.spinner("Executing verification bots..."):
                if selected_bot == "all":
                    reports = run_all_bots()
                else:
                    reports = [run_single_bot(selected_bot)]
                st.session_state["cached_bot_reports"] = reports

        reports: Optional[List[BotReport]] = st.session_state.get("cached_bot_reports")

        if reports:
            total_checks = sum(r.total for r in reports)
            passed_checks = sum(r.passed for r in reports)
            all_ok = all(r.all_passed for r in reports)

            # Header status
            if all_ok:
                st.success(f"✅ **All Bot Invariants Satisfied**: {passed_checks} / {total_checks} checks passed (100%).")
            else:
                st.error(f"❌ **Failures Detected**: {passed_checks} / {total_checks} checks passed.")

            # Individual bot report accordions
            for r in reports:
                status_icon = "✅" if r.all_passed else "❌"
                with st.expander(f"{status_icon} {r.bot} ({r.passed}/{r.total} Passed)", expanded=not r.all_passed):
                    if r.stats:
                        st.caption("Telemetry: " + " · ".join(f"**{k}**: {v}" for k, v in r.stats.items()))

                    # Display check results
                    for check in r.checks:
                        c_icon = "🟢" if check.passed else "🔴"
                        detail_str = f" — *{check.detail}*" if check.detail else ""
                        st.markdown(f"{c_icon} **{check.name}**{detail_str}")

                    if r.failures:
                        st.error("Failure logs:")
                        for f in r.failures:
                            st.code(f)

            # Export reports buttons
            st.markdown("#### 📥 Export Test Reports")
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                json_data = export_reports_json(reports)
                st.download_button(
                    "Download Reports (JSON)",
                    data=json_data,
                    file_name="cpu_pipeline_bot_report.json",
                    mime="application/json",
                    use_container_width=True,
                )
            with col_exp2:
                md_data = export_reports_markdown(reports)
                st.download_button(
                    "Download Reports (Markdown)",
                    data=md_data,
                    file_name="cpu_pipeline_bot_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
        else:
            st.info("Select a bot above and click **Execute Selected Bot(s)** to run verification checks.")

    # ---------------- TAB 2: Assembly Optimization Bot
    with tab_optbot:
        st.markdown("### ⚡ Bot 3: Assembly Optimization Bot (Scheduler & Synthesizer)")
        st.caption("Performs DAG topological dependency analysis (RAW, WAR, WAW) and safely reorders instructions to eliminate load-use stalls while preserving program semantics.")

        cur_code = engine.code if engine and engine.ok else st.session_state.get("code_input", "")

        c_opt1, c_opt2 = st.columns([1, 1])
        with c_opt1:
            st.markdown("#### 📄 Original Assembly Program")
            st.code(cur_code, language="mips")

        with c_opt2:
            st.markdown("#### ⚡ Optimization Engine")
            if st.button("🚀 Run Assembly DAG Optimization", use_container_width=True):
                dev = DevBot()
                opt_res = dev.optimize(cur_code)
                st.session_state["devbot_opt_result"] = opt_res

            opt_res = st.session_state.get("devbot_opt_result")
            if opt_res:
                if opt_res.success:
                    st.success(
                        f"✅ **Optimization Complete**: Eliminated {opt_res.stalls_eliminated} stall(s) "
                        f"({opt_res.cycles_before} ➔ {opt_res.cycles_after} cycles)."
                    )
                    st.code(opt_res.optimized_code, language="mips")
                    if st.button("Apply Optimized Code to Simulator", type="primary"):
                        st.session_state["code_input"] = opt_res.optimized_code
                        st.session_state["engine_result"] = None
                        st.session_state["nav_section"] = "simulator"
                        st.rerun()
                else:
                    st.warning(f"Could not optimize further: {opt_res.error_message}")
            else:
                st.info("Click **Run Assembly DAG Optimization** to inspect dependency graph and schedule instructions.")

        # Workload Synthesis
        st.markdown("---")
        st.markdown("#### 🧪 Workload Synthesis")
        st.caption("Generate verified synthetic assembly benchmark patterns directly from the Assembly Optimization Bot.")
        syn_col1, syn_col2 = st.columns([2, 1])
        with syn_col1:
            template_name = st.selectbox(
                "Select Synthesis Template",
                ["fibonacci", "array_sum", "hazard_stress", "independent_burst"],
            )
        with syn_col2:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            if st.button("Synthesize Program", use_container_width=True):
                dev = DevBot()
                syn_prog = dev.synthesize(template_name)
                st.session_state["code_input"] = syn_prog.code
                st.session_state["init_regs"] = syn_prog.suggested_regs
                st.session_state["init_mem"] = syn_prog.suggested_mem
                st.session_state["engine_result"] = None
                st.session_state["nav_section"] = "simulator"
                st.success(f"Synthesized '{template_name}'. Applied to simulator!")
                st.rerun()

    # ---------------- TAB 3: Full Stack Engineering Agent
    with tab_agent:
        st.markdown("### 🛠️ Autonomous Full Stack Engineering Agent")
        st.caption("Autonomous repository development tool with directory intelligence, risk-aware task planning, unified diff review, safe test execution, and rollback capability.")

        # Agent state in session
        if "fs_agent" not in st.session_state:
            st.session_state["fs_agent"] = FullStackEngineeringAgent()
        agent: FullStackEngineeringAgent = st.session_state["fs_agent"]

        # Provider banner
        st.markdown(
            f"""
            <div style="background: rgba(17, 28, 46, 0.7); border: 1px solid #27364B; border-radius: 8px; padding: 0.65rem 0.95rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-weight: 700; color: #F1F5F9;">AI Provider:</span>
                    <span style="color: #22D3EE; font-family: 'JetBrains Mono';"> {agent.provider_name}</span>
                </div>
                <div style="font-size: 0.78rem; color: #10B981; font-weight: 600;">
                    ● Sandbox Isolation Active
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Natural language task input
        task_prompt = st.text_area(
            "Natural-Language Development Task / Feature Request",
            value=st.session_state.get("agent_prompt_val", "Verify full codebase integrity, analyze import dependencies, and execute regression test suite"),
            height=80,
        )

        col_act1, col_act2, col_act3 = st.columns([1, 1, 1])
        with col_act1:
            plan_btn = st.button("📋 Analyze Repository & Plan Task", use_container_width=True)
        with col_act2:
            test_btn = st.button("🧪 Execute Local Pytest Suite", use_container_width=True)
        with col_act3:
            rollback_btn = st.button("⏪ Rollback Staged Changes", use_container_width=True)

        # Handle Plan generation
        if plan_btn:
            with st.spinner("Analyzing repository structure and dependencies..."):
                task = agent.create_task(task_prompt)
                agent.analyze(task)
                agent.plan(task)
                st.session_state["agent_current_task"] = task

        # Handle Test execution
        if test_btn:
            task = st.session_state.get("agent_current_task")
            if not task:
                task = agent.create_task("Run pytest verification suite")
                st.session_state["agent_current_task"] = task
            with st.spinner("Executing pytest in sandboxed workspace..."):
                agent.run_tests(task)

        # Handle Rollback
        if rollback_btn:
            task = st.session_state.get("agent_current_task")
            if task and task.changes:
                agent.rollback_task(task)
                st.success("Successfully rolled back all staged file changes.")
            else:
                st.info("No active changes to roll back.")

        # Display active task lifecycle
        active_task: Optional[Task] = st.session_state.get("agent_current_task")
        if active_task:
            st.markdown("---")
            # Lifecycle Status Bar
            state_color = {
                TaskState.PENDING: "#94A3B8",
                TaskState.ANALYZING: "#22D3EE",
                TaskState.PLANNING: "#A78BFA",
                TaskState.AWAITING_APPROVAL: "#F59E0B",
                TaskState.IMPLEMENTING: "#22D3EE",
                TaskState.TESTING: "#F59E0B",
                TaskState.FIXING: "#F43F5E",
                TaskState.VERIFIED: "#10B981",
                TaskState.FAILED: "#F43F5E",
            }.get(active_task.state, "#94A3B8")

            st.markdown(
                f"""
                <div style="background: #111C2E; border: 1px solid #27364B; border-radius: 8px; padding: 0.8rem 1rem; margin-bottom: 1rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-weight:700; color:#94A3B8;">Task ID:</span>
                            <code>{active_task.task_id}</code>
                        </div>
                        <div>
                            <span style="font-weight:700; color:#94A3B8;">Lifecycle State:</span>
                            <span style="color: {state_color}; font-weight:800; text-transform:uppercase;"> {active_task.state.value}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Display plan
            if active_task.plan:
                with st.expander("📋 Architecture Implementation Plan", expanded=True):
                    for step in active_task.plan.steps:
                        st.markdown(f"**Step {step.step_num}**: {step.description}")
                        st.caption(f"Target Files: `{', '.join(step.target_files)}` · Risks: *{step.risks}*")
                    if active_task.plan.potential_risks:
                        st.warning("⚠️ **Risk Assessment**:\n" + "\n".join(f"- {r}" for r in active_task.plan.potential_risks))

            # Approval Controls if awaiting approval
            if active_task.state == TaskState.AWAITING_APPROVAL:
                st.info("✋ **Approval Control**: Plan generated. Review target files above before granting approval.")
                if st.button("✅ Approve Plan & Proceed", type="primary"):
                    active_task.state = TaskState.IMPLEMENTING
                    st.rerun()

            # Display test results
            if active_task.test_results:
                last_test = active_task.test_results[-1]
                with st.expander("🧪 Test Runner Execution Telemetry", expanded=True):
                    if last_test.passed:
                        st.success(f"✅ Pytest PASSED in {last_test.duration_sec:.2f}s (Exit code 0)")
                    else:
                        st.error(f"❌ Pytest FAILED with exit code {last_test.returncode} in {last_test.duration_sec:.2f}s")
                    st.code(last_test.stdout or last_test.stderr)

            # Display logs
            with st.expander("📜 Agent Execution Audit Logs", expanded=False):
                for l in active_task.execution_logs:
                    st.text(l)

            # Download implementation report
            if active_task.final_report:
                st.download_button(
                    "📥 Download Implementation Report (Markdown)",
                    data=active_task.final_report,
                    file_name=f"agent_task_{active_task.task_id}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
