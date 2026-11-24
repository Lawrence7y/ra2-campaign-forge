import sys
from core import *

E = 0x00748190
print("=== bytes at entry ===")
print(read(E, 32).hex(" ").upper())
print()
print("=== disasm 00748160 .. 00748230 ===")
for l in dis_lines(0x00748160, 0x00748230):
    print(l)
