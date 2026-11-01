# Loop countdown demonstration
ADDI R1, R0, 5
loop:
SUBI R1, R1, 1
BNE R1, R0, loop
ADDI R2, R0, 100
