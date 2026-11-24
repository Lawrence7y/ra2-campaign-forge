# -*- coding: utf-8 -*-
"""S02-K2 / T2: byte-level verification of candidate CRT names."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import s02_common as C

CANDS = [
    (0x007C8B48, "qsort",        "YRpp CRT.h:88"),
    (0x007C8E25, "bsearch",      "YRpp CRT.h:91"),
    (0x007CB302, "vfprintf",     "YRpp CRT.h:108"),
    (0x007C5F00, "_ftol",        "YRpp Unsorted.h:29 + 台账§4"),
    (0x007C9442, "_nh_malloc",   "call-graph: 0x7C8E17(_new)+0x7C9430(malloc)"),
]
out=[]
for va, name, ev in CANDS:
    out.append("=== 0x%08X  candidate=%s  evidence=%s ===" % (va,name,ev))
    for (ad,b,m,o) in C.disasm(va,48):
        out.append("  0x%08X  %-18s %s %s" % (ad,b,m,o))
    out.append("")
msg="\n".join(out)
print(msg)
with open(os.path.join(C.CARD,"EVIDENCE","T2_byte_verify.txt"),"w",encoding="utf-8") as f:
    f.write(msg+"\n")
