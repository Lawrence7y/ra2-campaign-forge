# -*- coding: utf-8 -*-
"""S02-K2 / T3: dump heap init + sbh allocator regions and find writes to heap globals."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import s02_common as C

REGIONS=[
 (0x007CF680,0x007CF720,"heap init (HeapCreate@0x7CF6C2)"),
 (0x007CF720,0x007CF7C0,"sbh alloc A (HeapAlloc@0x7CF78C)"),
 (0x007CF7E0,0x007CF870,"free A (HeapFree@0x7CFAAC region)"),
 (0x007CFAE0,0x007CFB10,"heap alloc/free detail"),
 (0x007D0F40,0x007D0F70,"heap_handle check @0x7D1059"),
]
out=[]
for va0,va1,title in REGIONS:
    out.append("=== %s ==="%title)
    for ad,b,m,o in C.disasm(va0,va1-va0):
        out.append("  0x%08X  %-20s %s %s"%(ad,b,m,o))
    out.append("")
# find all writes to 0xb782c4 / 0xb782c0..0xb782d0 via any addressing form (full disasm)
out.append("=== writes/refs to 0xB782C0..0xB782D0 (all operand forms) ===")
pe=C.pe_obj; TEXT=pe.sections[0]
tva=C.rva2va(TEXT.VirtualAddress); tb=pe.__data__[TEXT.PointerToRawData:TEXT.PointerToRawData+TEXT.SizeOfRawData]
for ins in C.md.disasm(tb,tva):
    ops=ins.op_str.lower()
    for g in [0xB782C0,0xB782C4,0xB782C8,0xB782CC,0xB782D0]:
        if ("0x%x"%g) in ops:
            out.append("  0x%08X %-8s %s"%(ins.address,ins.mnemonic,ins.op_str))
            break
msg="\n".join(out)
print(msg[:12000])
with open(os.path.join(C.CARD,"EVIDENCE","T3_sbh_dump.txt"),"w",encoding="utf-8") as f:
    f.write(msg+"\n")
