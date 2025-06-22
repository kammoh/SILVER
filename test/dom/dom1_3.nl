in 0 0_0 # a[0]
in 1 0_1 # a[1]
in 2 1_0 # b[0]
in 3 1_1 # b[1]
in 4 2_0 # c[0]
in 5 2_1 # c[1]
ref 6
ref 7
ref 8
and 0 2
and 9 4  # a0 b0 c0
and 9 5  # a0 b0 c1
and 0 3
and 12 4 # a0 b1 c0
and 12 5 # a0 b1 c1
and 1 2 # a1b0
and 15 4 # a1 b0 c0
and 15 5 # a1 b0 c1
and 1 3 # a1b1
and 18 4 # a1 b1 c0
and 18 5 # a1 b1 c1
xor 11 6 # a0b0c1 + r1
xor 13 7 # a0b1c0 + r2
xor 14 8 # a0b1c1 + r3
xor 16 6 # a1b0c0 + r1
xor 17 7 # a1b0c1 + r2
xor 19 8 # a1b1c0 + r3
reg 10 # a0 b0 c0
reg 20 # a1 b1 c1
reg 21
reg 22
reg 23
reg 24
reg 25
reg 26
xor 27 29
xor 35 30
xor 36 31
xor 28 32
xor 38 33
xor 39 34
reg 37
reg 40
out 41 0_0 # d[0]
out 42 0_1 # d[1]