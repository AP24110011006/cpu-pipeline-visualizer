# Array storage and retrieval
ADDI R1, R0, 100
ADDI R2, R0, 42
SW R2, 0(R1)
ADDI R3, R0, 99
SW R3, 4(R1)
LW R4, 0(R1)
LW R5, 4(R1)
ADD R6, R4, R5
