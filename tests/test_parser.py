"""Tests for simulator/parser.py (Member 2)."""

from simulator.parser import parse_memory_values, parse_program, parse_register_values


def test_parses_the_three_sample_instructions():
    result = parse_program("ADD R1, R2, R3\nSUB R4, R1, R5\nAND R6, R4, R7")
    assert result.ok
    assert [i.text for i in result.instructions] == ["ADD R1, R2, R3", "SUB R4, R1, R5", "AND R6, R4, R7"]
    assert result.instructions[0].dest == 1 and result.instructions[0].sources == (2, 3)


def test_is_case_insensitive_and_ignores_comments_and_blank_lines():
    result = parse_program("# start\n\nadd r1, r2, r3   ; sum\n  \nsub $R4,R1 , R5 // diff")
    assert result.ok and len(result.instructions) == 2
    assert result.instructions[1].text == "SUB R4, R1, R5"


def test_load_store_and_immediate_forms():
    result = parse_program("LW R1, 8(R2)\nSW R3, -4(R2)\nADDI R4, R0, 0x10\nLW R5, (R2)")
    assert result.ok
    load, store, addi, bare = result.instructions
    assert load.is_load and load.imm == 8 and load.sources == (2,) and load.dest == 1
    assert store.is_store and store.imm == -4 and store.sources == (2, 3) and store.dest is None
    assert addi.imm == 16
    assert bare.imm == 0


def test_labels_resolve_to_instruction_index():
    result = parse_program("start: ADD R1, R1, R1\nBEQ R1, R2, end\nJ start\nend:\n")
    assert result.ok
    assert result.instructions[1].target == 3      # label at end of program
    assert result.instructions[2].target == 0


def test_label_on_its_own_line_and_before_instruction():
    result = parse_program("a:\nb: ADD R1, R2, R3\nJ a")
    assert result.ok and result.instructions[1].target == 0


def test_reports_every_bad_line_with_line_number():
    result = parse_program("ADD R1, R2, R3\nFOO R1\nADD R1, R2\nLW R1, 4[R2]")
    assert not result.ok
    assert [error.line_no for error in result.errors] == [2, 3, 4]


def test_unknown_opcode_gets_a_suggestion():
    result = parse_program("ADDD R1, R2, R3")
    assert "Did you mean ADD" in result.errors[0].message


def test_register_and_immediate_ranges():
    assert "does not exist" in parse_program("ADD R1, R2, R32").errors[0].message
    assert "16 bits" in parse_program("ADDI R1, R2, 40000").errors[0].message
    assert "not a register" in parse_program("ADD R1, R2, 5").errors[0].message


def test_undefined_and_duplicate_labels():
    assert "never defined" in parse_program("J nowhere").errors[0].message
    assert "more than once" in parse_program("a: NOP\na: NOP").errors[0].message


def test_empty_input_is_an_error():
    assert not parse_program("").ok
    assert not parse_program("# just a comment").ok


def test_too_long_program_rejected():
    assert not parse_program("NOP\n" * 201).ok


def test_r0_is_not_a_hazard_source_or_destination():
    result = parse_program("ADD R0, R0, R1")
    instr = result.instructions[0]
    assert not instr.writes_register and instr.hazard_sources == (1,)


def test_initial_value_parsers():
    registers, errors = parse_register_values("R2=10, r3=-5\nR4=0x10")
    assert registers == {2: 10, 3: -5, 4: 16} and not errors
    memory, errors = parse_memory_values("100=7, 104=9")
    assert memory == {100: 7, 104: 9} and not errors
    _, errors = parse_register_values("R40=1, hello")
    assert len(errors) == 2
