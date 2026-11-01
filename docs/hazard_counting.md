# Microarchitectural Hazard & Stall Counting Specification

## 1. Core Principle: Zero Double-Counting

In an in-order five-stage pipelined processor ($IF \to ID \to EX \to MEM \to WB$), an instruction advances through stages cycle by cycle. When a dependency occurs, it is evaluated strictly at the hazard boundary. To prevent inaccurate metrics, the counting definitions are defined as follows:

---

## 2. Counting Definitions

### A. Static RAW Dependency
- **Definition**: A pair of instructions $(P, C)$ in the source assembly text where producer $P$ writes register $R$ ($R \neq 0$), consumer $C$ reads register $R$, and the static distance $(index_C - index_P) \le 3$.
- **Scope**: Program text inspection (teaching aid). Loops and branching are not considered.

### B. Dynamic RAW Hazard Event
- **Definition**: A cycle in which an active dynamic instruction in the **ID** stage attempts to read register $R$, while an older in-flight instruction (in **EX**, **MEM**, or **WB**) writes to $R$.
- **Resolution**:
  - With Forwarding: Resolved dynamically via ALU bypass latches (0 stall cycles, unless producer is a `LW` in EX).
  - Without Forwarding: Results in 1 or more stall cycles.

### C. Stall Event vs. Stall Clock Cycles
- **Stall Event**: A single distinct microarchitectural hazard encounter that forces the pipeline to insert bubbles.
- **Stall Clock Cycles**: The exact number of clock cycles during which the `IF` and `ID` pipeline stages were held stationary while bubbles were injected into `EX`.
- **Note**: A single stall event may produce multiple stall cycles (e.g., distance-1 RAW without forwarding produces 2 stall cycles for 1 dependency event).

### D. Stalls Avoided through Forwarding
- **Definition**: The difference between the data stall cycles required without forwarding and the data stall cycles required with forwarding for the exact same instruction sequence:
  \[
  \text{Stalls}_{\text{avoided}} = \text{Stalls}_{\text{off}} - \text{Stalls}_{\text{on}}
  \]

### E. Control Hazards & Flushes
- **Pipeline Flush Event**: An occurrence where a branch evaluated in `EX` or jump evaluated in `ID` redirects the Program Counter (`PC`).
- **Flushed Instructions**: The count of wrong-path instructions fetched speculatively that are converted into bubbles (`squashed = True`). In predict-not-taken, a taken branch flushes 2 instructions (`IF` and `ID`).

---

## 3. Mathematical Conservation Laws

For any valid execution of length $C$ cycles:
1. **Total Pipeline Slots**:
   \[
   \text{Slots}_{\text{total}} = 5 \times C = \text{Slots}_{\text{useful}} + \text{Slots}_{\text{bubble}}
   \]
2. **Cycle Accounting**:
   \[
   C = \text{Ideal Cycles} + \text{Stall Cycles}_{\text{data}} + \text{Penalty}_{\text{control}}
   \]
   where $\text{Ideal Cycles} = \text{Retired Instructions} + 4$.
