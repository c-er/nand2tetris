// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

(KEYCHECK)
// if key pressed, blacken, else whiten
@24576
D=M+D;
@BLACKEN
D;JNE

// set color to white
@color
M=0
@INIT
0;JMP

(BLACKEN)
// set color to black
D=0
@color
M=!D

(INIT)
// set ptr to 0x4000 (base of screen mmap)
@16384
D=A
@ptr
M=D

// set ctr to 0x2000 (number of bytes)
@8192
D=A
@ctr
M=D

(LOOP)
// if ctr <= 0, jmp to keycheck
@ctr
D=M
@KEYCHECK
D;JLE

// write color to ptr
@color
D=M
@ptr
A=M
M=D

// increment ptr
@ptr
M=M+1

// decrement ctr
@ctr
M=M-1

// jump back to loop
@LOOP
0;JMP
