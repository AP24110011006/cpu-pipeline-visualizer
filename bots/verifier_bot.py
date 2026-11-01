"""Bot 2 - VerifierBot: differential testing + invariant checking.

How it works
    1. Generate random (but always terminating) assembly programs, or take the user's program.
    2. Run each one on a simple NON-pipelined reference CPU (the answer key).
    3. Run it on the pipeline in 8 configurations
       (forwarding on/off  x  branch policy  x  register-write timing).
    4. Compare final registers, memory and instruction count with the answer key.
    5. Check structural rules that must hold for ANY correct pipeline
       (stage order, one instruction per stage, in-order retirement, ...).

If forwarding or stall logic ever lets a wrong value through, step 4 catches it.

Run:  python -m bots.verifier_bot --programs 200 --seed 1
"""

from __future__ import annotations

import argparse
import itertools
import random
from typing import Dict, List, Optional, Tuple

from bots.report import BotReport
from simulator.models import (
    BRANCH_PREDICT_NOT_TAKEN,
    BRANCH_STALL,
    STAGES,
    PipelineConfig,
    SimulationResult,
)
from simulator.parser import parse_program
from simulator.pipeline import PipelineSimulator
from simulator.reference import run_reference

CONFIGURATIONS: List[PipelineConfig] = [
    PipelineConfig(forwarding=fwd, reg_write_first_half=half, branch_policy=policy, max_cycles=3000)
    for fwd, half, policy in itertools.product((True, False), (True, False), (BRANCH_PREDICT_NOT_TAKEN, BRANCH_STALL))
]

CHECK_NAMES = [
    "Runs without crashing",
    "Finishes (no endless loop)",
    "Final registers match reference CPU",
    "Final memory matches reference CPU",
    "Instruction count matches reference CPU",
    "Stage order IF>ID>EX>MEM>WB for every instruction",
    "At most one instruction per stage per cycle",
    "Instructions retire in program order",
    "Cycle count >= instructions + 4",
    "Forwarding never slower than no forwarding (straight-line code)",
]


def config_name(config: PipelineConfig) -> str:
    return (f"fwd={'ON' if config.forwarding else 'OFF'}, "
            f"regwrite={'1st-half' if config.reg_write_first_half else 'end-of-cycle'}, "
            f"branch={config.branch_policy}")


# --------------------------------------------------------------------------- random programs
def generate_random_program(rng: random.Random, units: int = 8, allow_branches: bool = True,
                            allow_memory: bool = True) -> str:
    """Create a random program that always terminates.

    Branches and jumps only go FORWARD, to the start of a later "unit", and loops use a
    dedicated counter register (R8), so the program cannot run forever.
    R7 is a fixed memory base register that is never written. Few registers are used on
    purpose, so that hazards happen all the time.
    """
    pool = [0, 1, 2, 3, 4, 5, 6]
    reg = lambda: f"R{rng.choice(pool)}"            # noqa: E731
    dest = lambda: f"R{rng.choice(pool[1:])}"        # noqa: E731 (R0 sometimes allowed below)

    def simple_statement() -> str:
        roll = rng.random()
        if allow_memory and roll < 0.22:
            return f"LW {dest()}, {rng.choice(range(0, 32, 4))}(R7)"
        if allow_memory and roll < 0.34:
            return f"SW {reg()}, {rng.choice(range(0, 32, 4))}(R7)"
        if roll < 0.50:
            return f"{rng.choice(['ADDI', 'ANDI', 'ORI', 'XORI', 'SLTI'])} {dest()}, {reg()}, {rng.randint(-8, 8)}"
        if roll < 0.53:
            return "NOP"
        target = f"R{rng.choice(pool)}"             # R0 is allowed as a destination (must stay 0)
        return f"{rng.choice(['ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLT'])} {target}, {reg()}, {reg()}"

    unit_lines: List[List[str]] = []
    for _ in range(units):
        roll = rng.random()
        if allow_branches and roll < 0.18:
            unit_lines.append(["BRANCH"])
        elif allow_branches and roll < 0.24:
            unit_lines.append(["JUMP"])
        elif allow_branches and roll < 0.34:
            body = [simple_statement() for _ in range(rng.randint(1, 3))]
            unit_lines.append(["LOOPSTART", *body, "LOOPEND"])
        else:
            unit_lines.append([simple_statement() for _ in range(rng.randint(1, 3))])

    lines: List[str] = []
    for index, unit in enumerate(unit_lines):
        lines.append(f"U{index}:")
        later = lambda: f"U{rng.randint(index + 1, units)}"   # noqa: E731  (U<units> = end of program)
        for statement in unit:
            if statement == "BRANCH":
                lines.append(f"{rng.choice(['BEQ', 'BNE'])} {reg()}, {reg()}, {later()}")
            elif statement == "JUMP":
                lines.append(f"J {later()}")
            elif statement == "LOOPSTART":
                lines.append(f"ADDI R8, R0, {rng.randint(1, 3)}")
                lines.append(f"L{index}:")
            elif statement == "LOOPEND":
                lines += ["ADDI R8, R8, -1", f"BNE R8, R0, L{index}"]
            else:
                lines.append(statement)
    lines.append(f"U{units}:")
    return "\n".join(lines)


def random_initial_state(rng: random.Random) -> Tuple[Dict[int, int], Dict[int, int]]:
    registers = {number: rng.randint(-20, 20) for number in range(1, 7)}
    registers[7] = 0                                 # memory base
    memory = {address: rng.randint(-50, 50) for address in range(0, 32, 4)}
    return registers, memory


# --------------------------------------------------------------------------- invariant checks
def check_invariants(result: SimulationResult) -> List[Tuple[str, str]]:
    """Return (check name, problem) pairs for every broken structural rule."""
    problems: List[Tuple[str, str]] = []
    order = {stage: position for position, stage in enumerate(STAGES)}
    occupied: Dict[Tuple[int, str], int] = {}

    for dyn in result.instructions:
        real = [(cycle, stage) for cycle, stage, state in dyn.history if state != "flushed"]
        for cycle, stage in real:
            key = (cycle, stage)
            if key in occupied and occupied[key] != dyn.seq:
                problems.append((CHECK_NAMES[6], f"I{occupied[key]} and I{dyn.seq} both in {stage} at cycle {cycle}"))
            occupied[key] = dyn.seq
        # stage order: collapse repeated stages (stalls) and compare with IF..WB prefix
        collapsed: List[str] = []
        for _cycle, stage in real:
            if not collapsed or collapsed[-1] != stage:
                collapsed.append(stage)
        if collapsed != STAGES[:len(collapsed)] or (dyn.retired and collapsed != STAGES):
            problems.append((CHECK_NAMES[5], f"I{dyn.seq} visited {collapsed}"))
        cycles_seen = [cycle for cycle, _stage in real]
        if cycles_seen != sorted(cycles_seen) or len(set(cycles_seen)) != len(cycles_seen):
            problems.append((CHECK_NAMES[5], f"I{dyn.seq} has non-increasing cycle numbers"))

    retire_cycles = [max(c for c, _s, st in dyn.history if st != "flushed") for dyn in result.instructions if dyn.retired]
    if retire_cycles != sorted(retire_cycles) or len(set(retire_cycles)) != len(retire_cycles):
        problems.append((CHECK_NAMES[7], "instructions finished out of order"))

    retired = sum(1 for dyn in result.instructions if dyn.retired)
    if retired and result.total_cycles < retired + 4:
        problems.append((CHECK_NAMES[8], f"{result.total_cycles} cycles for {retired} instructions"))
    return problems


# --------------------------------------------------------------------------- verification
def verify_program(
    code: str,
    registers: Optional[Dict[int, int]] = None,
    memory: Optional[Dict[int, int]] = None,
    report: Optional[BotReport] = None,
    label: str = "program",
) -> BotReport:
    """Verify one program in all configurations. Failures are appended to `report`."""
    own_report = report is None
    report = report or BotReport("Verifier Bot")
    tally: Dict[str, List[int]] = report.stats.setdefault("_tally", {name: [0, 0] for name in CHECK_NAMES})  # type: ignore

    def record(name: str, ok: bool, detail: str = "") -> None:
        tally[name][0 if ok else 1] += 1
        if not ok and len(report.failures) < 12:
            report.failures.append(f"[{name}] {label}\n  {detail}\n  program:\n    " + code.replace("\n", "\n    "))

    parsed = parse_program(code)
    if not parsed.ok:
        record(CHECK_NAMES[0], False, "program did not parse: " + "; ".join(map(str, parsed.errors)))
        return _finish(report, own_report)

    program = parsed.instructions
    reference = run_reference(program, registers, memory)
    has_control = any(instr.is_control for instr in program)
    cycles_by_config: Dict[Tuple[bool, bool, str], int] = {}

    for config in CONFIGURATIONS:
        where = config_name(config)
        try:
            result = PipelineSimulator(config).run(program, registers, memory)
        except Exception as problem:                  # noqa: BLE001 - the bot must report any crash
            record(CHECK_NAMES[0], False, f"{where}: {type(problem).__name__}: {problem}")
            continue
        record(CHECK_NAMES[0], True)
        if reference.truncated:
            continue                                  # reference never finished: nothing to compare with
        record(CHECK_NAMES[1], not result.truncated, f"{where}: hit the cycle limit")
        if result.truncated:
            continue
        record(CHECK_NAMES[2], result.registers == reference.registers,
               f"{where}: pipeline regs {_nonzero(result.registers)} vs reference {_nonzero(reference.registers)}")
        record(CHECK_NAMES[3], result.memory == reference.memory,
               f"{where}: pipeline memory {result.memory} vs reference {reference.memory}")
        retired = sum(1 for dyn in result.instructions if dyn.retired)
        record(CHECK_NAMES[4], retired == reference.executed,
               f"{where}: pipeline retired {retired}, reference executed {reference.executed}")
        broken = check_invariants(result)
        for name in (CHECK_NAMES[5], CHECK_NAMES[6], CHECK_NAMES[7], CHECK_NAMES[8]):
            messages = [text for check, text in broken if check == name]
            record(name, not messages, f"{where}: {messages[0] if messages else ''}")
        cycles_by_config[(config.forwarding, config.reg_write_first_half, config.branch_policy)] = result.total_cycles

    if not has_control and not reference.truncated:
        for half, policy in itertools.product((True, False), (BRANCH_PREDICT_NOT_TAKEN, BRANCH_STALL)):
            with_fwd = cycles_by_config.get((True, half, policy))
            without = cycles_by_config.get((False, half, policy))
            if with_fwd is not None and without is not None:
                record(CHECK_NAMES[9], with_fwd <= without, f"forwarding took {with_fwd} cycles, no forwarding {without}")
    return _finish(report, own_report)


def _nonzero(registers: List[int]) -> Dict[str, int]:
    return {f"R{number}": value for number, value in enumerate(registers) if value}


def _finish(report: BotReport, finalize: bool) -> BotReport:
    if finalize:
        _finalize(report)
    return report


def _finalize(report: BotReport) -> None:
    """Turn the running tally into CheckResult rows (called once at the end)."""
    tally = report.stats.pop("_tally", {})
    report.checks.clear()
    for name in CHECK_NAMES:
        passed, failed = tally.get(name, [0, 0])
        if passed + failed:
            report.add(name, failed == 0, f"{passed} passed, {failed} failed")


def run_verifier_bot(programs: int = 60, seed: int = 1, allow_branches: bool = True,
                     allow_memory: bool = True, units: int = 8) -> BotReport:
    """Fuzz-test the pipeline with `programs` random programs (8 configurations each)."""
    rng = random.Random(seed)
    report = BotReport("Verifier Bot")
    with_stalls = with_forwarding = with_flushes = 0
    for number in range(1, programs + 1):
        # every 4th program is straight-line code, so the "forwarding is never slower" rule gets tested too
        code = generate_random_program(rng, units, allow_branches and number % 4 != 0, allow_memory)
        registers, memory = random_initial_state(rng)
        verify_program(code, registers, memory, report, label=f"random program #{number} (seed {seed})")
        # coverage: did this program actually exercise hazards? (best effort - a crash here is
        # already reported by verify_program, so it must never stop the bot)
        parsed = parse_program(code)
        if parsed.ok:
            try:
                fast = PipelineSimulator(PipelineConfig(forwarding=True, max_cycles=3000)).run(parsed.instructions, registers, memory)
                slow = PipelineSimulator(PipelineConfig(forwarding=False, max_cycles=3000)).run(parsed.instructions, registers, memory)
            except Exception:                         # noqa: BLE001
                continue
            with_stalls += bool(slow.events_of("stall"))
            with_forwarding += bool(fast.events_of("forward"))
            with_flushes += bool(fast.events_of("flush"))
    _finalize(report)
    report.stats.update({
        "random programs": programs,
        "pipeline runs": programs * len(CONFIGURATIONS),
        "seed": seed,
        "programs with data stalls": with_stalls,
        "programs using forwarding": with_forwarding,
        "programs with branch flushes": with_flushes,
    })
    return report


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description="Differential-testing bot for the pipeline simulator")
    cli.add_argument("--programs", type=int, default=100, help="number of random programs")
    cli.add_argument("--seed", type=int, default=1)
    cli.add_argument("--no-branches", action="store_true")
    cli.add_argument("--no-memory", action="store_true")
    options = cli.parse_args()
    bot_report = run_verifier_bot(options.programs, options.seed, not options.no_branches, not options.no_memory)
    print(bot_report.to_text())
    raise SystemExit(0 if bot_report.all_passed else 1)
