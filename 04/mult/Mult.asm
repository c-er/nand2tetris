// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// R2 = 0
@R2 // 3
M=0

(LOOP)
// if R0 <= 0, jmp end
@R0
D=M
@END
D;JLE

// R2 += R1
@R1
D=M
@R2
M=M+D

// R0--
@R0
M=M-1

// goto LOOP
@LOOP
0;JMP

(END)
@END
0;JMP
