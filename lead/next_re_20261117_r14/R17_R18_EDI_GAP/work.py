# -*- coding: utf-8 -*-
# work.py - reproducible, bounded static analysis for R17-R18-EDI-GAP
import hashlib, struct
from capstone import *
from capstone.x86 import *

IMG = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_PREFIX = "73201CC0"
data = open(IMG,"rb").read()
sha = hashlib.sha256(data).hexdigest().upper()
assert sha.startswith(EXPECT_PREFIX), ("SHA MISMATCH", sha)
BASE = 0x400000
def off(va): return va - BASE   # valid for .text (RVA==RAW==0x1000)

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True

def disas(start, end, annotate=True):
    out=[]
    for ins in md.disasm(data[off(start):off(end)], start):
        line = f"{ins.address:08X}  " + " ".join(f"{b:02X}" for b in ins.bytes).ljust(20) + f"  {ins.mnemonic} {ins.op_str}".rstrip()
        out.append((ins, line))
    return out

if __name__ == "__main__":
    print("PATH:", IMG)
    print("SHA256:", sha)
    print("=== MAIN 0x43F180..0x43F5E0 ===")
    for ins,line in disas(0x43F180,0x43F5E0): print(line)
