# -*- coding: utf-8 -*-
"""S02-K2 / T4: dump handler install site, except.txt fopen site, and crash handler entry."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import s02_common as C

REGIONS = [
    (0x006BE040, 0x006BE090, "SetUnhandledExceptionFilter install @0x6BE084"),
    (0x004C8FA0, 0x004C9130, "except.txt fopen/write region @0x4C901C"),
    (0x004C85E0, 0x004C8720, "crash handler entry 0x4C85E0"),
    (0x004C8940, 0x004C89A0, "Exception occurred at string use"),
    (0x004B9890, 0x004B99F0, "Access address handler 0x4B9890"),
]
out=[]
for va0,va1,title in REGIONS:
    out.append("=== %s ==="%title)
    for (ad,b,m,o) in C.disasm(va0, va1-va0):
        out.append("  0x%08X  %-20s %s %s"%(ad,b,m,o))
    out.append("")
msg="\n".join(out)
print(msg)
with open(os.path.join(C.CARD,"EVIDENCE","T4_chain_disasm.txt"),"w",encoding="utf-8") as f:
    f.write(msg+"\n")
