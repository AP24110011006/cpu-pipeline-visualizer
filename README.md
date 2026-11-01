# 📝 Instruction Parser & ISA Subsystem — REHMAN

**Lead Engineer**: **REHMAN** (`RH`)  
**Role**: **Instruction Parser Developer**  
**Assigned Subsystem**: Lexical Tokenization, MIPS-32 ISA Syntax Validation, Symbol Table & Diagnostic Error Reporting  
**Verification Suite**: `tests/test_parser.py` (13/13 Tests Passed, 10/10 Negative Cases Handled)

---

## 🎯 Architectural Mission & Role Overview

As the **Instruction Parser Developer**, Rehman is responsible for the front-end compiler and validation pipeline of CPU PIPELINE STUDIO. 

Before any assembly code can enter the simulation pipeline, it must be tokenized, sanitized, validated, and translated into strongly typed instruction models. If an assembly programmer makes a syntax typo, uses an out-of-range immediate, or references an undefined label, Rehman's parser catches it immediately and generates helpful, line-numbered diagnostic error messages.

Rehman's subsystem:
1. **Parses MIPS-32 Assembly**: Full support for R-type, I-type, and J-type instructions with case-insensitive tokenization.
2. **Enforces Register Conventions**: Supports registers `R0` through `R31` (as well as `$0` through `$31`). Hardwires `R0` to strictly evaluate to 0.
3. **Validates Immediate Boundaries**: Validates 16-bit signed immediates ($-32,768$ to $32,767$) and unsigned immediates ($0$ to $65,535$), raising descriptive errors on overflow.
4. **Resolves Labels & Offsets**: Implements a two-pass symbol table indexing branch and jump targets, resolving forward and backward jumps.
5. **Generates User-Friendly Diagnostics**: Provides exact line numbers, syntax suggestions via string distance matching (e.g. suggests `ADD` when user types `AD`), and strips comments (`#`, `;`, `//`).

---

## 🧠 Algorithms Implemented & Complexity Analysis

Rehman engineered three compiler front-end algorithms providing high parsing speed, robust error containment, and intelligent diagnostics:

### Algorithm 1: Two-Pass Lexical Tokenization & Symbol Table Indexing (`parse_program`)
- **Purpose**: Translates multi-line assembly text into validated `Instruction` objects while correctly binding forward and backward branch/jump target labels.
- **Pseudocode**:
  ```python
  def parse_program(assembly_text):
      lines = assembly_text.splitlines()
      symbol_table = {}
      cleaned_lines = []
      
      # PASS 1: Sanitize, strip comments, and record label definitions
      instruction_index = 0
      for line_num, raw_line in enumerate(lines, start=1):
          # Strip comments (#, ;, //) and whitespace
          line = strip_comments_and_whitespace(raw_line)
          if not line:
              continue
          
          # Check for label definition (e.g., "loop:" or "loop: ADD R1, R2, R3")
          if ':' in line:
              label, remainder = line.split(':', 1)
              label = label.strip()
              validate_label_name(label, line_num)
              symbol_table[label] = instruction_index
              line = remainder.strip()
          
          if line:
              cleaned_lines.append((line_num, line))
              instruction_index += 1
      
      # PASS 2: Parse opcodes, validate registers, and resolve target labels
      instructions = []
      for line_num, line in cleaned_lines:
          tokens = tokenize_operands(line)
          opcode = tokens[0].upper()
          
          validate_opcode(opcode, line_num)
          operands = parse_and_validate_operands(opcode, tokens[1:], line_num)
          
          # Resolve branch/jump label targets
          if opcode in BRANCH_OPCODES or opcode in JUMP_OPCODES:
              target_label = operands.label
              if target_label not in symbol_table:
                  raise SyntaxError(f"Line {line_num}: Unresolved label '{target_label}'")
              operands.target_index = symbol_table[target_label]
          
          instructions.append(Instruction(opcode=opcode, operands=operands, line_number=line_num))
      
      return ParseResult(instructions=instructions, symbol_table=symbol_table)
  ```
- **Complexity**:
  - **Time Complexity**: $\mathcal{O}(L + N)$ where $L$ is total text lines and $N$ is instruction count. Guaranteed linear two-pass execution.
  - **Space Complexity**: $\mathcal{O}(N)$ for symbol table mapping and tokenized instruction sequence.

---

### Algorithm 2: Two's Complement Immediate Bound & Memory Operand Parsing
- **Purpose**: Validates memory offset syntax `offset(base)` and immediate integer limits according to MIPS architecture specifications.
- **Formulas & Invariants**:
  - Signed 16-bit Immediate Range:
    $$-2^{15} \le \text{imm} \le 2^{15} - 1 \implies [-32,768, \; 32,767]$$
  - Unsigned Immediate Range:
    $$0 \le \text{imm} \le 2^{16} - 1 \implies [0, \; 65,535]$$
  - Memory Offset Extraction:
    $$\text{Regex Pattern}: \quad \text{r}"\^\s\*([+-]?\d+)\s\*\(\s\*\$?([rR]?\d+)\s\*\)\s\*\$"$$
- **Complexity**: $\mathcal{O}(1)$ regex and arithmetic evaluation per instruction.

---

### Algorithm 3: Gestalt Pattern Typo Suggestion Algorithm (`suggest_opcode`)
- **Purpose**: When an unrecognized opcode is entered, computes similarity metric against known ISA opcodes using Ratcliff-Obershelp gestalt pattern matching (`difflib.get_close_matches`), producing helpful hints (e.g., *“Unknown opcode 'AD'. Did you mean 'ADD'?”*).
- **Complexity**: $\mathcal{O}(K \times M)$ where $K$ is total known opcodes ($K \approx 15$) and $M$ is string length ($M \le 5$), executing in sub-millisecond time.

---

## 📦 Delivered Modules & File Explanations

| Module / File | Component Responsibility & Implementation Details |
|:---|:---|
| [`simulator/parser.py`](simulator/parser.py) | **The Core Assembly Parser & ISA Validation Subsystem**<br>• Implements `parse_program()`: Tokenizes assembly text into a sequence of `Instruction` objects.<br>• Implements two-pass label resolution: Discovers labels (`loop:`, `target:`) and maps target instruction indices.<br>• Implements register parsing: Parses `$R1`, `R1`, `$1`, and validates register range $0–31$.<br>• Enforces $R0$ invariants: Prevents $R0$ from ever being treated as a hazard source or mutable register.<br>• Implements immediate bounds checking: Enforces signed 16-bit limits $[-32768, 32767]$.<br>• Implements memory operand parsing: Decodes `offset(base)` syntax (e.g. `8(R2)`).<br>• Implements `parse_register_values()` and `parse_memory_values()`: Parses user-specified initial register and memory states.<br>• Provides intelligent typo suggestions using `difflib.get_close_matches`. |
| [`tests/test_parser.py`](tests/test_parser.py) | **Instruction Parser Unit & Negative Test Suite**<br>• Verifies parsing of standard 3-register R-type, immediate I-type, load/store, and jump instructions.<br>• Verifies comment stripping and case insensitivity.<br>• Verifies label resolution for branch and jump targets.<br>• Negative testing: Verifies rejection of missing operands, invalid register indices (`R32`), unknown opcodes, malformed memory syntax (`8[R2]`), undefined labels, and immediate overflow. |
| [`examples/basic/arithmetic.s`](examples/basic/arithmetic.s) | **Baseline Verification Workload**<br>Clean, robust assembly workload exercising basic arithmetic, immediate loading, and register manipulation. |

---

## 📋 Supported Instruction Set Architecture (MIPS-32 Subset)

| Type | Syntax | Operation | Description |
|:---|:---|:---|:---|
| **R-Type** | `ADD R1, R2, R3` | $R1 \leftarrow R2 + R3$ | Signed integer addition |
| **R-Type** | `SUB R1, R2, R3` | $R1 \leftarrow R2 - R3$ | Signed integer subtraction |
| **R-Type** | `AND R1, R2, R3` | $R1 \leftarrow R2 \& R3$ | Bitwise logical AND |
| **R-Type** | `OR R1, R2, R3` | $R1 \leftarrow R2 \mid R3$ | Bitwise logical OR |
| **R-Type** | `XOR R1, R2, R3` | $R1 \leftarrow R2 \oplus R3$ | Bitwise logical XOR |
| **R-Type** | `SLT R1, R2, R3` | $R1 \leftarrow (R2 < R3 ? 1 : 0)$ | Set on less than (signed) |
| **I-Type** | `ADDI R1, R2, imm` | $R1 \leftarrow R2 + \text{imm}$ | Add immediate (signed 16-bit) |
| **I-Type** | `ANDI R1, R2, imm` | $R1 \leftarrow R2 \& \text{imm}$ | Bitwise AND immediate |
| **I-Type** | `ORI R1, R2, imm` | $R1 \leftarrow R2 \mid \text{imm}$ | Bitwise OR immediate |
| **I-Type** | `LW R1, offset(R2)` | $R1 \leftarrow \text{Mem}[R2 + \text{offset}]$ | Load word from data memory |
| **I-Type** | `SW R1, offset(R2)` | $\text{Mem}[R2 + \text{offset}] \leftarrow R1$ | Store word to data memory |
| **I-Type** | `BEQ R1, R2, label` | $\text{if } R1 == R2 \implies PC \leftarrow \text{label}$ | Branch if equal |
| **I-Type** | `BNE R1, R2, label` | $\text{if } R1 \ne R2 \implies PC \leftarrow \text{label}$ | Branch if not equal |
| **J-Type** | `J label` | $PC \leftarrow \text{label}$ | Unconditional jump |
| **Other** | `NOP` | — | No operation |

---

## 🧪 Verification & How to Run Tests

Rehman's parser is validated through extensive positive and negative test cases:

```bash
# Run the complete Instruction Parser test suite
pytest tests/test_parser.py -v
```

### ✅ Verification Results
- **Positive Scenarios**: 13/13 parser tests **PASSED** (100% syntax compliance).
- **Negative Scenarios**: 10/10 malformed inputs properly caught with line-numbered error diagnostics.
- **CI Status**: GitHub Actions Workflow **GREEN (Success ✅)**.
