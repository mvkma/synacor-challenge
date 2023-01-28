"""
885 CALL 1723 [843, 1, 30000, 0, 0, 0, 0, 0] [887]

1723 PUSH 32768
1725 PUSH 32769
1727  SET 32769  6068

1730 RMEM 32768 32769          (memory[6068] is 6095 initially)
1733 PUSH 32769
1735 MULT 32769 32769 32769
1739 CALL  2125
1741  SET 32769 16724
1744 CALL  2125                (looks like register 0 has ascii characters)
1746  POP 32769
1748 WMEM 32769 32768
1751  ADD 32769 32769     1
1755   EQ 32768 30050 32769
1759   JF 32768 1730
1762  POP 32769
1764  POP 32768
1766  RET

2125 PUSH 32769
2127 PUSH 32770
2129  AND 32770 32768 32769
2133  NOT 32770 32770
2136   OR 32768 32768 32769
2140  AND 32768 32768 32770
2144  POP 32770
2146  POP 32769
2148  RET

- From 6068 to 26850 we have mostly ascii characters
- From 26851 to the end something else happens

"""

def decode(vm):
    r1, r2 = 0, 6068

    while r2 < 30050:
        r1 = vm.program[r2]

        r1 = r1 ^ (r2**2 % 2**15)
        r1 = r1 ^ 16724

        vm.program[r2] = r1

        r2 += 1

