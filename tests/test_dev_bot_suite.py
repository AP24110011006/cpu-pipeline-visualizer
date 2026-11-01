"""Comprehensive test suite for the Full Stack Development Bot (DevBot).

Verifies:
1. analyze_code edge cases:
   - Empty input, whitespace only
   - Comments-only and labels-only programs
   - Syntax errors (bad opcodes, bad registers, missing operands, overflow imm, duplicate labels, undefined labels)
   - Hazard detection accuracy (RAW, load-use, control hazard flushes)
   - Schema validation of returned metrics and bottlenecks

2. optimize_schedule edge cases:
   - Memory alias safety (SW vs LW, LW vs SW, SW vs SW)
   - Register dependency preservation (RAW, WAR, WAW, diamond DAGs)
   - Jump and branch target safety (no movement across jumps, branches, or label entry points)
   - Preservation of single and multiple label definitions
   - Semantic equivalence verification against Reference CPU
   - Safety rollback when semantics could diverge or code is already optimal

3. Differential Collaboration Fuzzing:
   - 20 randomized programs generated via VerifierBot's generator
   - Optimized via DevBot scheduler
   - Validated on Reference CPU for exact bit-level register and memory equivalence

4. Synthesizer verification:
   - All 4 core templates ('fibonacci', 'array_sum', 'hazard_stress', 'independent_burst')
   - Aliases and fuzzy name mapping
   - Error handling for invalid template requests
   - Execution correctness on PipelineSimulator and Reference CPU
"""

from __future__ import annotations

import random
from typing import Dict, List

import pytest

from bots.dev_bot import DevBot, analyze_code, optimize_schedule, run_dev_bot, synthesize_program
from bots.verifier_bot import generate_random_program, random_initial_state
from simulator.metrics import compute_metrics
from simulator.models import PipelineConfig
from simulator.parser import parse_program
from simulator.pipeline import PipelineSimulator
from simulator.reference import run_reference


# ==============================================================================
# 1. analyze_code Edge Cases
# ==============================================================================


class TestAnalyzeCodeEdgeCases:
    """Edge cases and boundary tests for DevBot's code analyzer."""

    def test_empty_string(self) -> None:
        result = analyze_code("")
        assert result["ok"] is False
        assert len(result["errors"]) > 0
        assert result["instruction_count"] == 0
        assert result["raw_hazards"] == []
        assert result["load_use_hazards"] == []
        assert any("syntax errors" in b.lower() or "no instructions" in str(result["errors"]).lower()
                   for b in result["bottlenecks"])

    def test_whitespace_and_newlines_only(self) -> None:
        result = analyze_code("   \n\n\t  \r\n   ")
        assert result["ok"] is False
        assert len(result["errors"]) > 0
        assert result["instruction_count"] == 0

    def test_pure_comments(self) -> None:
        code = (
            "# First comment line\n"
            "; Second comment line with semicolon\n"
            "// Third comment line with double slash\n"
        )
        result = analyze_code(code)
        assert result["ok"] is False
        assert len(result["errors"]) > 0
        assert result["instruction_count"] == 0

    def test_labels_only(self) -> None:
        code = "start:\nloop:\nskip:\nexit:\n"
        result = analyze_code(code)
        assert result["ok"] is False
        assert len(result["errors"]) > 0
        assert result["instruction_count"] == 0

    def test_labels_and_comments_only(self) -> None:
        code = (
            "# Program header\n"
            "start:\n"
            "   # Nested comment\n"
            "done:\n"
        )
        result = analyze_code(code)
        assert result["ok"] is False
        assert result["instruction_count"] == 0

    @pytest.mark.parametrize(
        "invalid_code,expected_error_substr",
        [
            ("FOOBAR R1, R2, R3", "unknown instruction"),
            ("ADD R1, R2", "needs 3 operand"),
            ("ADD R35, R1, R2", "does not exist"),
            ("ADDI R1, R2, 9999999", "does not fit in 16 bits"),
            ("LW R1, R2", "not a memory operand"),
            ("BEQ R1, R2, missing_label", "never defined"),
            ("label1:\nADD R1, R0, 1\nlabel1:\nADD R2, R0, 2", "defined more than once"),
        ],
    )
    def test_syntax_errors_reported_gracefully(self, invalid_code: str, expected_error_substr: str) -> None:
        result = analyze_code(invalid_code)
        assert result["ok"] is False
        assert result["instruction_count"] == 0
        assert any(expected_error_substr.lower() in err.lower() for err in result["errors"])
        assert "Program contains syntax errors preventing analysis." in result["bottlenecks"]

    def test_single_nop(self) -> None:
        result = analyze_code("NOP")
        assert result["ok"] is True
        assert result["instruction_count"] == 1
        assert result["raw_hazards"] == []
        assert result["load_use_hazards"] == []
        assert result["stats"]["raw_count"] == 0
        assert result["stats"]["load_use_count"] == 0
        assert result["stats"]["control_count"] == 0

    def test_independent_instructions_report_no_bottlenecks(self) -> None:
        code = (
            "ADDI R1, R0, 1\n"
            "ADDI R2, R0, 2\n"
            "ADDI R3, R0, 3\n"
        )
        result = analyze_code(code)
        assert result["ok"] is True
        assert result["instruction_count"] == 3
        assert len(result["raw_hazards"]) == 0
        assert len(result["load_use_hazards"]) == 0
        assert any("no critical hazard bottlenecks" in b.lower() for b in result["bottlenecks"])

    def test_raw_hazard_detection(self) -> None:
        code = "ADD R1, R2, R3\nSUB R4, R1, R5"
        result = analyze_code(code)
        assert result["ok"] is True
        assert len(result["raw_hazards"]) == 1
        h = result["raw_hazards"][0]
        assert h["register"] == "R1"
        assert h["distance"] == 1
        assert h["is_load_use"] is False
        assert h["stalls_without_forwarding"] == 2
        assert h["stalls_with_forwarding"] == 0
        assert any("tight raw dependency" in b.lower() for b in result["bottlenecks"])

    def test_load_use_hazard_detection(self) -> None:
        code = "LW R1, 0(R2)\nADD R3, R1, R4"
        result = analyze_code(code)
        assert result["ok"] is True
        assert len(result["load_use_hazards"]) == 1
        lu = result["load_use_hazards"][0]
        assert lu["register"] == "R1"
        assert lu["distance"] == 1
        assert lu["is_load_use"] is True
        assert lu["stalls_with_forwarding"] == 1
        assert any("load-use hazard" in b.lower() for b in result["bottlenecks"])
        assert any("hide the load-use delay" in opp.lower() for opp in result["optimization_opportunities"])

    def test_analyzer_stats_schema(self) -> None:
        code = "ADDI R1, R0, 10\nADD R2, R1, R1"
        result = analyze_code(code)
        assert result["ok"] is True
        stats = result["stats"]
        expected_keys = {
            "raw_count",
            "load_use_count",
            "control_count",
            "simulated_cycles_fwd",
            "simulated_cycles_no_fwd",
            "stalls_fwd",
            "stalls_no_fwd",
            "cpi_fwd",
            "cpi_no_fwd",
            "forwarding_events",
            "cycles_saved_by_forwarding",
        }
        assert expected_keys.issubset(stats.keys())
        assert stats["simulated_cycles_fwd"] <= stats["simulated_cycles_no_fwd"]


# ==============================================================================
# 2. optimize_schedule Edge Cases
# ==============================================================================


class TestOptimizeScheduleEdgeCases:
    """Safety invariants and edge case validation for the instruction scheduler."""

    def test_optimize_empty_and_syntax_error_programs(self) -> None:
        for bad_code in ["", "   ", "# Only comments", "INVALID_INSTR R1, R2"]:
            code_out, info = optimize_schedule(bad_code)
            assert code_out == bad_code
            assert info["ok"] is False
            assert info["verified"] is False
            assert "error" in info

    def test_memory_alias_safety_store_before_load(self) -> None:
        """Store followed by Load must NEVER allow the load to be reordered before the store."""
        code = (
            "SW R1, 0(R2)\n"
            "LW R3, 0(R2)\n"
            "ADD R4, R5, R6\n"
        )
        regs = {1: 42, 2: 100, 5: 1, 6: 2}
        mem = {100: 999}
        opt_code, info = optimize_schedule(code, regs, mem)
        p_opt = parse_program(opt_code)
        assert p_opt.ok

        sw_idx = next(i for i, inst in enumerate(p_opt.instructions) if inst.is_store)
        lw_idx = next(i for i, inst in enumerate(p_opt.instructions) if inst.is_load)
        assert sw_idx < lw_idx, "Store Word must precede Load Word to prevent memory read hazards"
        assert info["verified"] is True

        ref_orig = run_reference(parse_program(code).instructions, regs, mem)
        ref_opt = run_reference(p_opt.instructions, regs, mem)
        assert ref_opt.registers == ref_orig.registers
        assert ref_opt.memory == ref_orig.memory
        assert ref_opt.registers[3] == 42

    def test_memory_alias_safety_load_before_store(self) -> None:
        """Load followed by Store must NEVER allow the store to move before the load."""
        code = (
            "LW R1, 0(R2)\n"
            "SW R3, 0(R2)\n"
            "ADD R4, R5, R6\n"
        )
        regs = {2: 100, 3: 777, 5: 10, 6: 20}
        mem = {100: 123}
        opt_code, info = optimize_schedule(code, regs, mem)
        p_opt = parse_program(opt_code)
        assert p_opt.ok

        lw_idx = next(i for i, inst in enumerate(p_opt.instructions) if inst.is_load)
        sw_idx = next(i for i, inst in enumerate(p_opt.instructions) if inst.is_store)
        assert lw_idx < sw_idx, "Load Word must precede Store Word to preserve memory read value"
        assert info["verified"] is True

        ref_opt = run_reference(p_opt.instructions, regs, mem)
        assert ref_opt.registers[1] == 123
        assert ref_opt.memory[100] == 777

    def test_memory_alias_safety_store_before_store(self) -> None:
        """Store followed by Store must preserve sequential store order."""
        code = (
            "SW R1, 0(R2)\n"
            "SW R3, 0(R2)\n"
            "ADD R4, R5, R6\n"
        )
        regs = {1: 111, 2: 100, 3: 222, 5: 1, 6: 2}
        opt_code, info = optimize_schedule(code, regs)
        p_opt = parse_program(opt_code)
        assert p_opt.ok

        stores = [inst for inst in p_opt.instructions if inst.is_store]
        assert len(stores) == 2
        # First store must be R1, second store must be R3
        assert stores[0].sources[1] == 1
        assert stores[1].sources[1] == 3
        assert info["verified"] is True

        ref_opt = run_reference(p_opt.instructions, regs)
        assert ref_opt.memory[100] == 222

    def test_register_waw_preservation(self) -> None:
        """WAW (Write After Write): overwriting the same register must retain output order."""
        code = (
            "ADDI R1, R0, 10\n"
            "ADDI R1, R0, 20\n"
            "ADD R2, R3, R4\n"
        )
        opt_code, info = optimize_schedule(code, {3: 1, 4: 2})
        p_opt = parse_program(opt_code)
        assert p_opt.ok

        waw_writes = [inst for inst in p_opt.instructions if inst.dest == 1]
        assert len(waw_writes) == 2
        assert waw_writes[0].imm == 10
        assert waw_writes[1].imm == 20
        assert info["verified"] is True

        ref_opt = run_reference(p_opt.instructions)
        assert ref_opt.registers[1] == 20

    def test_register_war_preservation(self) -> None:
        """WAR (Write After Read / Anti-dependency): reader must execute before overwriter."""
        code = (
            "ADD R1, R2, R3\n"
            "ADDI R2, R0, 99\n"
            "ADD R4, R5, R6\n"
        )
        regs = {2: 5, 3: 10, 5: 1, 6: 2}
        opt_code, info = optimize_schedule(code, regs)
        p_opt = parse_program(opt_code)
        assert p_opt.ok

        read_idx = next(i for i, inst in enumerate(p_opt.instructions) if inst.opcode == "ADD" and inst.dest == 1)
        write_idx = next(i for i, inst in enumerate(p_opt.instructions) if inst.opcode == "ADDI" and inst.dest == 2)
        assert read_idx < write_idx, "ADD R1, R2, R3 must execute before ADDI R2 overwrites R2"
        assert info["verified"] is True

        ref_opt = run_reference(p_opt.instructions, regs)
        assert ref_opt.registers[1] == 15  # 5 + 10, not 99 + 10
        assert ref_opt.registers[2] == 99

    def test_register_raw_preservation(self) -> None:
        """RAW (Read After Write / True dependency): producer must precede consumer."""
        code = (
            "ADDI R1, R0, 5\n"
            "ADD R2, R1, R3\n"
            "ADD R4, R5, R6\n"
        )
        regs = {3: 10, 5: 1, 6: 2}
        opt_code, info = optimize_schedule(code, regs)
        p_opt = parse_program(opt_code)
        assert p_opt.ok

        prod_idx = next(i for i, inst in enumerate(p_opt.instructions) if inst.dest == 1)
        cons_idx = next(i for i, inst in enumerate(p_opt.instructions) if inst.dest == 2)
        assert prod_idx < cons_idx, "ADDI R1 must precede ADD R2 which consumes R1"
        assert info["verified"] is True

        ref_opt = run_reference(p_opt.instructions, regs)
        assert ref_opt.registers[2] == 15

    def test_diamond_dag_dependency_preservation(self) -> None:
        """Diamond DAG: R1 -> (R4, R6) -> R8."""
        code = (
            "ADD R1, R2, R3\n"
            "ADD R4, R1, R5\n"
            "ADD R6, R1, R7\n"
            "ADD R8, R4, R6\n"
        )
        regs = {2: 1, 3: 2, 5: 3, 7: 4}
        opt_code, info = optimize_schedule(code, regs)
        p_opt = parse_program(opt_code)
        assert p_opt.ok
        assert info["verified"] is True

        ref_orig = run_reference(parse_program(code).instructions, regs)
        ref_opt = run_reference(p_opt.instructions, regs)
        assert ref_opt.registers == ref_orig.registers
        assert ref_opt.registers[8] == (1 + 2 + 3) + (1 + 2 + 4)  # 6 + 7 = 13

    def test_jump_boundary_safety(self) -> None:
        """Instructions must never cross unconditional jump boundaries."""
        code = (
            "ADDI R1, R0, 10\n"
            "J skip\n"
            "ADDI R2, R0, 20\n"
            "skip:\n"
            "ADDI R3, R0, 30\n"
        )
        opt_code, info = optimize_schedule(code)
        p_opt = parse_program(opt_code)
        assert p_opt.ok
        assert "skip" in p_opt.labels
        assert info["verified"] is True

        ref_opt = run_reference(p_opt.instructions)
        assert ref_opt.registers[1] == 10
        assert ref_opt.registers[2] == 0   # R2 was skipped
        assert ref_opt.registers[3] == 30

    def test_branch_target_and_loop_boundary_safety(self) -> None:
        """Backward branch in loop must preserve basic block partitions and target labels."""
        code = (
            "ADDI R1, R0, 4\n"
            "ADDI R2, R0, 0\n"
            "loop:\n"
            "LW R3, 0(R4)\n"
            "ADD R2, R2, R3\n"
            "ADDI R4, R4, 4\n"
            "ADDI R1, R1, -1\n"
            "BNE R1, R0, loop\n"
            "SW R2, 0(R4)\n"
        )
        regs = {4: 100}
        mem = {100: 5, 104: 10, 108: 15, 112: 20}
        opt_code, info = optimize_schedule(code, regs, mem)
        p_opt = parse_program(opt_code)
        assert p_opt.ok
        assert "loop" in p_opt.labels
        assert info["verified"] is True

        ref_orig = run_reference(parse_program(code).instructions, regs, mem)
        ref_opt = run_reference(p_opt.instructions, regs, mem)
        assert ref_opt.registers == ref_orig.registers
        assert ref_opt.memory == ref_orig.memory
        assert ref_opt.registers[2] == 50
        assert ref_opt.memory[116] == 50

    def test_multiple_labels_and_end_labels(self) -> None:
        """Multiple labels at the same address and a label at the end of code must be preserved."""
        code = (
            "entry:\n"
            "start:\n"
            "ADDI R1, R0, 1\n"
            "middle:\n"
            "ADDI R2, R0, 2\n"
            "finish:\n"
        )
        opt_code, info = optimize_schedule(code)
        p_opt = parse_program(opt_code)
        assert p_opt.ok
        for lbl in ["entry", "start", "middle", "finish"]:
            assert lbl in p_opt.labels, f"Expected label '{lbl}' to be preserved"
        assert info["verified"] is True

    def test_r0_never_creates_false_dependency(self) -> None:
        """Instructions targeting R0 (discarded writes) must not constrain other instructions."""
        code = (
            "ADD R0, R1, R2\n"
            "ADD R3, R4, R5\n"
            "ADD R0, R6, R7\n"
        )
        opt_code, info = optimize_schedule(code)
        p_opt = parse_program(opt_code)
        assert p_opt.ok
        assert info["verified"] is True


# ==============================================================================
# 3. Differential Collaboration Fuzzing
# ==============================================================================


class TestDifferentialCollaborationFuzzing:
    """Differential testing: random programs generated via VerifierBot fuzzing."""

    @pytest.mark.parametrize("seed", list(range(100, 120)))
    def test_fuzzed_random_program_equivalence(self, seed: int) -> None:
        """Generate 20 distinct random programs and verify 100% semantic equivalence."""
        rng = random.Random(seed)
        code = generate_random_program(rng, units=6, allow_branches=True, allow_memory=True)
        regs, mem = random_initial_state(rng)

        p_orig = parse_program(code)
        assert p_orig.ok, f"Generated program with seed {seed} should parse cleanly"

        opt_code, info = optimize_schedule(code, regs, mem)
        assert info["ok"] is True
        assert info["verified"] is True, f"DevBot optimizer marked seed {seed} unverified"

        p_opt = parse_program(opt_code)
        assert p_opt.ok, f"Optimized code for seed {seed} failed parsing"

        ref_orig = run_reference(p_orig.instructions, regs, mem)
        ref_opt = run_reference(p_opt.instructions, regs, mem)

        assert not ref_orig.truncated, f"Original program truncated on seed {seed}"
        assert not ref_opt.truncated, f"Optimized program truncated on seed {seed}"
        assert ref_opt.registers == ref_orig.registers, (
            f"Seed {seed}: Register discrepancy between original and optimized on Reference CPU!"
        )
        assert ref_opt.memory == ref_orig.memory, (
            f"Seed {seed}: Memory discrepancy between original and optimized on Reference CPU!"
        )

    def test_fuzzed_straight_line_programs(self) -> None:
        """Straight-line code with dense memory and arithmetic operations."""
        rng = random.Random(999)
        for _ in range(5):
            code = generate_random_program(rng, units=5, allow_branches=False, allow_memory=True)
            regs, mem = random_initial_state(rng)
            opt_code, info = optimize_schedule(code, regs, mem)
            assert info["verified"] is True
            p_orig = parse_program(code)
            p_opt = parse_program(opt_code)
            ref_orig = run_reference(p_orig.instructions, regs, mem)
            ref_opt = run_reference(p_opt.instructions, regs, mem)
            assert ref_opt.registers == ref_orig.registers
            assert ref_opt.memory == ref_orig.memory


# ==============================================================================
# 4. Synthesizer Testing
# ==============================================================================


class TestSynthesizerTemplates:
    """Verification of program templates synthesized by DevBot."""

    TEMPLATES = ["fibonacci", "array_sum", "hazard_stress", "independent_burst"]

    @pytest.mark.parametrize("template", TEMPLATES)
    def test_template_parseability(self, template: str) -> None:
        code = synthesize_program(template)
        parsed = parse_program(code)
        assert parsed.ok, f"Template '{template}' generated syntax errors: {parsed.errors}"
        assert len(parsed.instructions) >= 5

    @pytest.mark.parametrize(
        "alias,canonical",
        [
            ("fib", "fibonacci"),
            ("Fibonacci", "fibonacci"),
            ("array", "array_sum"),
            ("array_sum", "array_sum"),
            ("ArraySum", "array_sum"),
            ("hazard", "hazard_stress"),
            ("stress", "hazard_stress"),
            ("hazard_stress", "hazard_stress"),
            ("burst", "independent_burst"),
            ("independent", "independent_burst"),
            ("INDEPENDENT_BURST", "independent_burst"),
        ],
    )
    def test_template_aliases(self, alias: str, canonical: str) -> None:
        code_alias = synthesize_program(alias)
        code_canon = synthesize_program(canonical)
        assert code_alias == code_canon

    def test_unknown_template_raises_value_error(self) -> None:
        with pytest.raises(ValueError) as excinfo:
            synthesize_program("non_existent_workload")
        assert "unknown template" in str(excinfo.value).lower()
        for t in self.TEMPLATES:
            assert t in str(excinfo.value)

    def test_fibonacci_workload_execution_and_values(self) -> None:
        code = synthesize_program("fibonacci")
        parsed = parse_program(code)
        assert parsed.ok

        # Execute on PipelineSimulator with forwarding
        sim_res = PipelineSimulator(PipelineConfig(forwarding=True)).run(parsed.instructions)
        assert not sim_res.truncated

        # Reference CPU check
        ref_res = run_reference(parsed.instructions)
        assert not ref_res.truncated
        assert sim_res.registers == ref_res.registers
        assert sim_res.memory == ref_res.memory

        # Sequence of 7 Fibonacci numbers at addresses 0, 4, 8, 12, 16, 20, 24
        expected = [0, 1, 1, 2, 3, 5, 8]
        actual = [sim_res.memory.get(addr, -1) for addr in range(0, 28, 4)]
        assert actual == expected

    def test_array_sum_workload_execution_and_values(self) -> None:
        code = synthesize_program("array_sum")
        parsed = parse_program(code)
        assert parsed.ok

        initial_mem = {0: 10, 4: 20, 8: 30, 12: 40}
        sim_res = PipelineSimulator(PipelineConfig(forwarding=True)).run(
            parsed.instructions, initial_memory=initial_mem
        )
        assert not sim_res.truncated

        ref_res = run_reference(parsed.instructions, initial_memory=initial_mem)
        assert sim_res.registers == ref_res.registers
        assert sim_res.memory == ref_res.memory

        # Expected sum = 10 + 20 + 30 + 40 = 100 stored at memory[16]
        assert sim_res.memory.get(16) == 100

    def test_hazard_stress_workload_execution_and_hazards(self) -> None:
        code = synthesize_program("hazard_stress")
        parsed = parse_program(code)
        assert parsed.ok

        # Analyzer confirms presence of RAW and load-use hazards
        analysis = analyze_code(code)
        assert analysis["ok"] is True
        assert len(analysis["raw_hazards"]) >= 3
        assert len(analysis["load_use_hazards"]) >= 1

        # Execution without infinite loops
        sim_res = PipelineSimulator(PipelineConfig(forwarding=True)).run(parsed.instructions)
        ref_res = run_reference(parsed.instructions)
        assert not sim_res.truncated
        assert not ref_res.truncated
        assert sim_res.registers == ref_res.registers
        assert sim_res.memory == ref_res.memory
        assert sim_res.memory.get(4) == 60

    def test_independent_burst_workload_zero_stalls(self) -> None:
        code = synthesize_program("independent_burst")
        parsed = parse_program(code)
        assert parsed.ok

        analysis = analyze_code(code)
        assert analysis["ok"] is True
        assert len(analysis["raw_hazards"]) == 0
        assert len(analysis["load_use_hazards"]) == 0

        # Must achieve 0 data stall cycles even with forwarding disabled
        sim_no_fwd = PipelineSimulator(PipelineConfig(forwarding=False)).run(parsed.instructions)
        metrics = compute_metrics(sim_no_fwd)
        assert metrics.data_stall_cycles == 0
        # Straight-line: total cycles = N + 4
        assert metrics.total_cycles == len(parsed.instructions) + 4


# ==============================================================================
# 5. DevBot Class Wrapper & Bot Self-Verification
# ==============================================================================


class TestDevBotInterface:
    """Verify DevBot object-oriented API and self-test report generation."""

    def test_devbot_class_methods(self) -> None:
        bot = DevBot()
        analysis = bot.analyze_code("ADD R1, R2, R3")
        assert analysis["ok"] is True

        code_synth = bot.synthesize_program("burst")
        assert parse_program(code_synth).ok

        opt_code, info = bot.optimize_schedule("ADD R1, R2, R3")
        assert info["ok"] is True
        assert info["verified"] is True

    def test_devbot_run_dev_bot_all_passed(self) -> None:
        report = run_dev_bot()
        assert report.all_passed, f"DevBot self-verification failed: {report.failures}"
        assert report.total >= 17
        assert report.stats.get("templates synthesized") == 4
        assert report.stats.get("semantic equivalence rate") == "100%"
