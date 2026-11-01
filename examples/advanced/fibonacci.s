# Fibonacci sequence calculation stored to memory
ADDI R1, R0, 0
ADDI R2, R0, 1
ADDI R3, R0, 10
ADDI R4, R0, 0
loop:
BEQ R3, R0, done
SW R1, 0(R4)
ADD R5, R1, R2
ADD R1, R0, R2
ADD R2, R0, R5
ADDI R4, R4, 4
SUBI R3, R3, 1
J loop
done:
ADDI R31, R0, 1
