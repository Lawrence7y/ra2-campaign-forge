#!/usr/bin/env python3
# Independent cross-checks: where exactly does the differing byte sit inside body A,
# and what imm32 does it belong to?
import struct
PATH = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
data = open(PATH, "rb").read()
def rd(off, n): return data[off:off+n]

A = rd(0x2bedb0, 106)
B = rd(0x1c250, 106)
pat = struct.pack("<I", 0x817bc0)
patB = struct.pack("<I", 0x817bb0)
print("imm32 0x817bc0 inside bodyA at offset", A.find(pat))
print("imm32 0x817bb0 inside bodyB at offset", B.find(patB))
print("diff offset 0x4e =", 0x4e, "-> A[0x4e]=", hex(A[0x4e]), "B[0x4e]=", hex(B[0x4e]))
print("surrounding A 0x48..0x53:", A[0x48:0x54].hex())
print("surrounding B 0x48..0x53:", B[0x48:0x54].hex())
# 0x817bc0 little-endian inside A: confirm which of the 4 bytes is at 0x4e
loc = A.find(pat)
print(f"imm32 spans bodyA offsets {loc:#x}..{loc+3:#x}; differing byte 0x4e is byte index {0x4e-loc} of the imm32")
