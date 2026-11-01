# ==========================================
# ADVANCED CPU PIPELINE STRESS TEST
# Array Processing and Conditional Loop
# ==========================================

# Initialize registers
ADDI R1, R0, 100       # Array base address
ADDI R2, R0, 5         # Number of elements
ADDI R3, R0, 0         # Index
ADDI R4, R0, 0         # Sum
ADDI R5, R0, 1         # Increment value
ADDI R6, R0, 0         # Even count

# Initialize array in memory
ADDI R10, R0, 10
SW R10, 0(R1)

ADDI R10, R0, 20
SW R10, 4(R1)

ADDI R10, R0, 30
SW R10, 8(R1)

ADDI R10, R0, 40
SW R10, 12(R1)

ADDI R10, R0, 50
SW R10, 16(R1)

# ==========================================
# MAIN ARRAY PROCESSING LOOP
# ==========================================

loop:
BEQ R3, R2, finish

# Calculate current array address
ADD R7, R1, R3
ADD R7, R7, R3
ADD R7, R7, R3
ADD R7, R7, R3

# Load array element
LW R8, 0(R7)

# Accumulate sum
ADD R4, R4, R8

# Create dependency chain
ADD R9, R8, R5
ADD R11, R9, R4
SUB R12, R11, R8

# Check whether element is even
ANDI R13, R8, 1
BNE R13, R0, odd

# Count even elements
ADD R6, R6, R5
J continue

odd:
ADDI R14, R0, 1

continue:
# Increment index
ADD R3, R3, R5
J loop

# ==========================================
# FINAL CALCULATIONS
# ==========================================

finish:
ADD R15, R4, R6
SUB R16, R15, R3
AND R17, R4, R2
OR R18, R4, R6
XOR R19, R15, R16
SLT R20, R6, R2

# Store final results
SW R4, 20(R1)
SW R6, 24(R1)
SW R15, 28(R1)

# Load stored values
LW R21, 20(R1)
LW R22, 24(R1)
LW R23, 28(R1)

# Final dependency chain
ADD R24, R21, R22
ADD R25, R24, R23
SUB R26, R25, R4
ADD R27, R26, R6

NOP
