"""The teammate bots (Testing Bot & Dev Bot) must pass on the real simulator AND catch injected bugs."""

import random
import simulator.pipeline as pipeline_module
from bots.dev_bot import DevBot, analyze_code, optimize_schedule, run_dev_bot, synthesize_program
from bots.test_bot import run_test_bot
from bots.verifier_bot import generate_random_program, run_verifier_bot, verify_program
from simulator.hazards import detect_data_stall
from simulator.parser import parse_program


def test_test_bot_passes():
    report = run_test_bot()
    assert report.all_passed, report.to_text()
    assert report.total >= 25


def test_verifier_bot_passes_on_random_programs():
    report = run_verifier_bot(programs=40, seed=11)
    assert report.all_passed, report.to_text()


def test_random_programs_always_parse():
    rng = random.Random(3)
    for _ in range(100):
        assert parse_program(generate_random_program(rng)).ok


def test_verify_program_on_user_code():
    report = verify_program("LW R1, 0(R2)\nADD R3, R1, R1\nSW R3, 4(R2)", {2: 8}, {8: 5})
    assert report.all_passed, report.to_text()


def test_bots_catch_a_broken_stall_unit():
    original = pipeline_module.detect_data_stall
    pipeline_module.detect_data_stall = lambda c, ex, mem, wb, fwd, half: (
        detect_data_stall(c, ex, mem, wb, fwd, half) if fwd else None)       # "forgets" to stall without forwarding
    try:
        assert not run_test_bot().all_passed
        assert not run_verifier_bot(programs=20, seed=2).all_passed
    finally:
        pipeline_module.detect_data_stall = original
    assert run_test_bot().all_passed


def test_dev_bot_passes():
    report = run_dev_bot()
    assert report.all_passed, report.to_text()
    assert report.total >= 15


def test_dev_bot_analyzer():
    res = analyze_code("LW R1, 0(R2)\nADD R3, R1, R4")
    assert res["ok"]
    assert len(res["load_use_hazards"]) == 1
    assert any("load-use" in b.lower() for b in res["bottlenecks"])


def test_dev_bot_scheduler_load_use_elimination():
    code = "LW R1, 0(R2)\nADD R3, R1, R4\nADD R5, R6, R7"
    opt_code, info = optimize_schedule(code, {2: 100, 4: 5, 6: 2, 7: 3}, {100: 42})
    assert info["ok"]
    assert info["verified"]
    assert info["stalls_eliminated"] >= 1
    assert info["cycles_saved_fwd"] >= 1


def test_dev_bot_synthesizer_templates():
    bot = DevBot()
    for name in ["fibonacci", "array_sum", "hazard_stress", "independent_burst"]:
        code = bot.synthesize_program(name)
        assert parse_program(code).ok
