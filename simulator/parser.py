"""Assembly parser and input validation.   (Member 2)

Turns the text typed by the student into a list of ``Instruction`` objects and
produces friendly, line-numbered error messages for anything it cannot understand.

Supported syntax (case-insensitive, one instruction per line):
    ADD  R1, R2, R3        R-type : ADD SUB AND OR XOR SLT   (rd, rs, rt)
    ADDI R1, R2, 5         I-type : ADDI ANDI ORI XORI SLTI  (rt, rs, imm)
    LW   R1, 8(R2)         load word
    SW   R1, 8(R2)         store word
    BEQ  R1, R2, label     branch if equal      (BNE: branch if not equal)
    J    label             unconditional jump
    NOP
    label:                 labels may sit on their own line or before an instruction
Comments start with '#', ';' or '//'.  Registers are R0..R31 (R0 is always 0).
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from simulator.models import (
    ALL_OPCODES,
    BRANCH_OPCODES,
    I_TYPE_OPCODES,
    Instruction,
    R_TYPE_OPCODES,
)

MAX_SOURCE_LENGTH = 500_000
DEFAULT_MAX_INSTRUCTIONS = 200
MAX_INSTRUCTIONS = DEFAULT_MAX_INSTRUCTIONS
IMM_MIN, IMM_MAX = -32768, 32767

_REGISTER_RE = re.compile(r"^\$?[rR](\d{1,2})$")
_MEMORY_RE = re.compile(r"^([+-]?(?:0[xX][0-9a-fA-F]+|\d+))?\(\s*(\$?[rR]\d{1,2})\s*\)$")
_LABEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class ParseError:
    line_no: int
    line: str
    message: str

    def __str__(self) -> str:
        return f"Line {self.line_no}: {self.message}   →   {self.line.strip()}"


@dataclass
class ParseResult:
    instructions: List[Instruction] = field(default_factory=list)
    errors: List[ParseError] = field(default_factory=list)
    labels: Dict[str, int] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors and bool(self.instructions)


# --------------------------------------------------------------------------- helpers
def _strip_comment(line: str) -> str:
    for marker in ("#", ";", "//"):
        position = line.find(marker)
        if position != -1:
            line = line[:position]
    return line.strip()


def _parse_register(token: str) -> int:
    match = _REGISTER_RE.match(token.strip())
    if not match:
        raise ValueError(f"'{token.strip()}' is not a register (use R0 to R31)")
    number = int(match.group(1))
    if number > 31:
        raise ValueError(f"register '{token.strip()}' does not exist (R0 to R31 only)")
    return number


def _parse_immediate(token: str) -> int:
    token = token.strip()
    try:
        value = int(token, 0)
    except ValueError:
        try:
            value = int(token, 10)
        except ValueError:
            raise ValueError(f"'{token}' is not a valid number") from None
    if not IMM_MIN <= value <= IMM_MAX:
        raise ValueError(f"immediate {value} does not fit in 16 bits ({IMM_MIN} to {IMM_MAX})")
    return value


def _parse_memory_operand(token: str) -> Tuple[int, int]:
    """Parse 'offset(Rn)' and return (offset, base_register)."""
    match = _MEMORY_RE.match(token.strip())
    if not match:
        raise ValueError(f"'{token.strip()}' is not a memory operand (use offset(Rn), e.g. 8(R2))")
    offset = _parse_immediate(match.group(1)) if match.group(1) else 0
    return offset, _parse_register(match.group(2))


def _expect_operands(opcode: str, operands: List[str], count: int, usage: str) -> None:
    if len(operands) != count:
        raise ValueError(f"{opcode} needs {count} operand(s), found {len(operands)}. Example: {usage}")


# --------------------------------------------------------------------------- main parser
def parse_program(text: str, max_instructions: int = DEFAULT_MAX_INSTRUCTIONS) -> ParseResult:
    """Parse assembly text. Never raises: problems are collected in ``result.errors``."""
    result = ParseResult()
    if len(text) > MAX_SOURCE_LENGTH:
        result.errors.append(
            ParseError(0, "", f"source file too large ({len(text):,} characters, limit is {MAX_SOURCE_LENGTH:,})")
        )
        return result

    statements: List[Tuple[int, str, str, List[str]]] = []   # (line_no, raw, opcode, operands)

    # ---- pass 1: strip comments, collect labels and raw statements
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = _strip_comment(raw)
        if not line:
            continue
        while ":" in line:                                    # one or more "label:" prefixes
            label_part, _, rest = line.partition(":")
            label = label_part.strip()
            if not _LABEL_RE.match(label):
                result.errors.append(ParseError(line_no, raw, f"'{label}' is not a valid label name"))
                line = rest.strip()
                continue
            if label in result.labels:
                result.errors.append(ParseError(line_no, raw, f"label '{label}' is defined more than once"))
            else:
                result.labels[label] = len(statements)
            line = rest.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        opcode = parts[0].upper()
        operand_text = parts[1] if len(parts) > 1 else ""
        operands = [piece.strip() for piece in operand_text.split(",")] if operand_text.strip() else []
        statements.append((line_no, raw, opcode, operands))

    if len(statements) > max_instructions:
        result.errors.append(ParseError(0, "", f"program is too long (has {len(statements)} instructions, limit is {max_instructions})"))
        return result

    # ---- pass 2: build Instruction objects
    for index, (line_no, raw, opcode, operands) in enumerate(statements):
        try:
            instruction = _build_instruction(index, line_no, opcode, operands, result.labels)
        except ValueError as problem:
            result.errors.append(ParseError(line_no, raw, str(problem)))
            continue
        result.instructions.append(instruction)

    if not statements and not result.errors:
        result.errors.append(ParseError(0, "", "no instructions found - type at least one instruction"))
    return result


def _build_instruction(index: int, line_no: int, opcode: str, operands: List[str], labels: Dict[str, int]) -> Instruction:
    if opcode not in ALL_OPCODES:
        hint = difflib.get_close_matches(opcode, ALL_OPCODES, n=1)
        suggestion = f" Did you mean {hint[0]}?" if hint else ""
        raise ValueError(f"unknown instruction '{opcode}'.{suggestion} Supported: {', '.join(ALL_OPCODES)}")

    if opcode in R_TYPE_OPCODES:
        _expect_operands(opcode, operands, 3, f"{opcode} R1, R2, R3")
        rd, rs, rt = (_parse_register(token) for token in operands)
        return Instruction(index, opcode, f"{opcode} R{rd}, R{rs}, R{rt}", dest=rd, sources=(rs, rt), line_no=line_no)

    if opcode in I_TYPE_OPCODES:
        _expect_operands(opcode, operands, 3, f"{opcode} R1, R2, 5")
        rd, rs = _parse_register(operands[0]), _parse_register(operands[1])
        imm = _parse_immediate(operands[2])
        return Instruction(index, opcode, f"{opcode} R{rd}, R{rs}, {imm}", dest=rd, sources=(rs,), imm=imm, line_no=line_no)

    if opcode == "LW":
        _expect_operands(opcode, operands, 2, "LW R1, 8(R2)")
        rt = _parse_register(operands[0])
        offset, base = _parse_memory_operand(operands[1])
        return Instruction(index, opcode, f"LW R{rt}, {offset}(R{base})", dest=rt, sources=(base,), imm=offset, line_no=line_no)

    if opcode == "SW":
        _expect_operands(opcode, operands, 2, "SW R1, 8(R2)")
        rt = _parse_register(operands[0])
        offset, base = _parse_memory_operand(operands[1])
        return Instruction(index, opcode, f"SW R{rt}, {offset}(R{base})", sources=(base, rt), imm=offset, line_no=line_no)

    if opcode in BRANCH_OPCODES:
        _expect_operands(opcode, operands, 3, f"{opcode} R1, R2, label")
        rs, rt = _parse_register(operands[0]), _parse_register(operands[1])
        label = operands[2]
        if label not in labels:
            raise ValueError(f"label '{label}' is never defined")
        return Instruction(index, opcode, f"{opcode} R{rs}, R{rt}, {label}", sources=(rs, rt), target=labels[label], line_no=line_no)

    if opcode == "J":
        _expect_operands(opcode, operands, 1, "J label")
        label = operands[0]
        if label not in labels:
            raise ValueError(f"label '{label}' is never defined")
        return Instruction(index, opcode, f"J {label}", target=labels[label], line_no=line_no)

    _expect_operands(opcode, operands, 0, "NOP")           # NOP
    return Instruction(index, "NOP", "NOP", line_no=line_no)


# --------------------------------------------------------------------------- initial values
def _parse_assignments(text: str, kind: str) -> Tuple[Dict[int, int], List[str]]:
    values: Dict[int, int] = {}
    errors: List[str] = []
    for chunk in re.split(r"[,\n;]+", text or ""):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            errors.append(f"'{chunk}': write it as {'R2=10' if kind == 'register' else '100=7'}")
            continue
        left, _, right = chunk.partition("=")
        try:
            key = _parse_register(left) if kind == "register" else int(left.strip(), 0)
            value = int(right.strip(), 0)
        except ValueError as problem:
            errors.append(f"'{chunk}': {problem}")
            continue
        values[key] = value
    return values, errors


def parse_register_values(text: str) -> Tuple[Dict[int, int], List[str]]:
    """Parse 'R2=10, R3=5' into ({2: 10, 3: 5}, errors)."""
    return _parse_assignments(text, "register")


def parse_memory_values(text: str) -> Tuple[Dict[int, int], List[str]]:
    """Parse '100=7, 104=9' into ({100: 7, 104: 9}, errors)."""
    return _parse_assignments(text, "memory")
