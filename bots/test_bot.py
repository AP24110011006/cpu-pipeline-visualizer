"""Bot 1 - TestBot: scenario regression testing.

Every scenario below was worked out by hand on paper (textbook pipeline diagrams).
The bot runs each one and compares the simulator's output with the expected numbers.
It also feeds the parser a list of invalid programs and checks that each is rejected
with a helpful message.

Run:  python -m bots.test_bot
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from bots.report import BotReport
from simulator.metrics import compute_metrics
from simulator.models import BRANCH_PREDICT_NOT_TAKEN, BRANCH_STALL, PipelineConfig
from simulator.parser import parse_program, parse_register_values
from simulator.pipeline import PipelineSimulator


@dataclass
class Scenario:
    name: str
    code: str
    forwarding: bool = True
    first_half: bool = True
    policy: str = BRANCH_PREDICT_NOT_TAKEN
    registers: str = ""
    # expected values (None = do not check)
    cycles: Optional[int] = None
    retired: Optional[int] = None
    data_stalls: Optional[int] = None
    forwards: Optional[int] = None
    control_penalty: Optional[int] = None
    final_registers: Optional[Dict[int, int]] = None


SAMPLE = "ADD R1, R2, R3\nSUB R4, R1, R5\nAND R6, R4, R7"

SCENARIOS: List[Scenario] = [
    Scenario("RAW chain, forwarding OFF (11 cycles, 4 stalls)", SAMPLE, forwarding=False,
             cycles=11, retired=3, data_stalls=4, forwards=0),
    Scenario("RAW chain, forwarding ON (7 cycles, no stalls)", SAMPLE, forwarding=True,
             cycles=7, retired=3, data_stalls=0, forwards=2),
    Scenario("RAW chain computes correct values", SAMPLE, forwarding=True,
             registers="R2=10, R3=5, R5=2, R7=12",
             final_registers={1: 15, 4: 13, 6: 12}),   # 10+5=15 ; 15-2=13 ; 13&12=12
    Scenario("Load-use, forwarding ON (1 stall)", "LW R1, 0(R2)\nADD R3, R1, R4", forwarding=True,
             cycles=7, data_stalls=1, forwards=1),
    Scenario("Load-use, forwarding OFF (2 stalls)", "LW R1, 0(R2)\nADD R3, R1, R4", forwarding=False,
             cycles=8, data_stalls=2, forwards=0),
    Scenario("Independent instructions (no hazards)",
             "ADD R1, R2, R3\nADD R4, R5, R6\nADD R7, R2, R3", cycles=7, data_stalls=0, forwards=0),
    Scenario("Distance-2 dependency, forwarding OFF (1 stall)",
             "ADD R1, R2, R3\nADD R8, R5, R6\nSUB R4, R1, R5", forwarding=False, cycles=8, data_stalls=1),
    Scenario("Distance-2 dependency, forwarding ON (0 stalls)",
             "ADD R1, R2, R3\nADD R8, R5, R6\nSUB R4, R1, R5", forwarding=True, cycles=7, data_stalls=0, forwards=1),
    Scenario("Distance-3 dependency, register file written in first half (0 stalls)",
             "ADD R1, R2, R3\nADD R8, R5, R6\nADD R9, R5, R6\nSUB R4, R1, R5",
             forwarding=False, first_half=True, cycles=8, data_stalls=0),
    Scenario("Distance-3 dependency, NO first-half write (1 stall)",
             "ADD R1, R2, R3\nADD R8, R5, R6\nADD R9, R5, R6\nSUB R4, R1, R5",
             forwarding=False, first_half=False, cycles=9, data_stalls=1),
    Scenario("R0 is never a hazard and never changes",
             "ADD R0, R1, R2\nADD R3, R0, R0", registers="R1=4, R2=6", cycles=6, data_stalls=0,
             final_registers={0: 0, 3: 0}),
    Scenario("Store then load returns the stored value",
             "SW R5, 0(R2)\nLW R6, 0(R2)", registers="R2=100, R5=42", cycles=6, data_stalls=0,
             final_registers={6: 42}),
    Scenario("Taken branch, predict-not-taken (2 flushed slots)",
             "BEQ R0, R0, skip\nADD R1, R1, R1\nADD R2, R2, R2\nskip: ADD R3, R3, R3",
             registers="R1=1, R2=1, R3=1", cycles=8, retired=2, control_penalty=2,
             final_registers={1: 1, 2: 1, 3: 2}),
    Scenario("Not-taken branch, predict-not-taken (no penalty)",
             "BNE R0, R0, skip\nADD R1, R1, R1\nADD R2, R2, R2\nskip: ADD R3, R3, R3",
             cycles=8, retired=4, control_penalty=0),
    Scenario("Not-taken branch, stall policy (2 wasted slots)",
             "BNE R0, R0, skip\nADD R1, R1, R1\nADD R2, R2, R2\nskip: ADD R3, R3, R3",
             policy=BRANCH_STALL, cycles=10, retired=4, control_penalty=2),
    Scenario("Jump loses exactly one fetch slot",
             "J end\nADD R1, R1, R1\nend: ADD R2, R2, R2", cycles=7, retired=2, control_penalty=1),
    Scenario("Countdown loop ends with R1 = 0",
             "ADDI R1, R0, 3\nloop: ADDI R1, R1, -1\nBNE R1, R0, loop\nADD R2, R0, R0",
             retired=8, final_registers={1: 0}),
]

# (program text, a phrase the error message must contain)
INVALID_PROGRAMS = [
    ("ADD R1, R2", "needs 3 operand"),
    ("ADD R1, R2, R32", "does not exist"),
    ("MUL R1, R2, R3", "unknown instruction"),
    ("ADD R1, R2, X3", "not a register"),
    ("LW R1, 8[R2]", "not a memory operand"),
    ("BEQ R1, R2, nowhere", "never defined"),
    ("a: ADD R1, R2, R3\na: SUB R1, R2, R3", "more than once"),
    ("ADDI R1, R2, 99999", "16 bits"),
    ("ADDI R1, R2, abc", "not a valid number"),
    ("   \n# only a comment", "no instructions"),
]


def _run_scenario(scenario: Scenario, report: BotReport) -> None:
    parsed = parse_program(scenario.code)
    if not parsed.ok:
        report.add(scenario.name, False, "scenario program failed to parse: " + "; ".join(map(str, parsed.errors)))
        return
    registers, _ = parse_register_values(scenario.registers)
    config = PipelineConfig(forwarding=scenario.forwarding, reg_write_first_half=scenario.first_half,
                            branch_policy=scenario.policy)
    try:
        result = PipelineSimulator(config).run(parsed.instructions, registers)
    except Exception as problem:                      # noqa: BLE001 - a crash is a test failure, not a bot failure
        report.add(scenario.name, False, f"simulator crashed: {type(problem).__name__}: {problem}")
        return
    metrics = compute_metrics(result)

    problems: List[str] = []

    def expect(label: str, expected, actual) -> None:
        if expected is not None and expected != actual:
            problems.append(f"{label}: expected {expected}, got {actual}")

    expect("cycles", scenario.cycles, metrics.total_cycles)
    expect("instructions completed", scenario.retired, metrics.instructions_retired)
    expect("data stalls", scenario.data_stalls, metrics.data_stall_cycles)
    expect("forwarding events", scenario.forwards, metrics.forwarding_events)
    expect("control penalty", scenario.control_penalty, metrics.control_penalty_cycles)
    for number, value in (scenario.final_registers or {}).items():
        expect(f"R{number}", value, result.registers[number])
    if result.truncated:
        problems.append("simulation hit the cycle limit")
    report.add(scenario.name, not problems, "; ".join(problems) if problems else
               f"{metrics.total_cycles} cycles, {metrics.data_stall_cycles} stalls")


def run_test_bot() -> BotReport:
    """Run every hand-verified scenario and every invalid-input check."""
    report = BotReport("Test Bot")
    for scenario in SCENARIOS:
        _run_scenario(scenario, report)
    for code, phrase in INVALID_PROGRAMS:
        parsed = parse_program(code)
        messages = " | ".join(str(error) for error in parsed.errors)
        report.add(f"Parser rejects: {code.splitlines()[0][:28]!r}", (not parsed.ok) and phrase in messages,
                   f"expected message containing '{phrase}'" if phrase not in messages else "rejected with a clear message")
    report.stats = {"scenarios": len(SCENARIOS), "invalid-input checks": len(INVALID_PROGRAMS)}
    report.failures = [f"{check.name}: {check.detail}" for check in report.checks if not check.passed]
    return report


if __name__ == "__main__":
    bot_report = run_test_bot()
    print(bot_report.to_text())
    raise SystemExit(0 if bot_report.all_passed else 1)
