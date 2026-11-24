#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-J work: statically disassemble the two placement-path call sites of
0x47C620 and resolve the 2nd stack argument (arg2) semantics.

Read-only on ra2youli\gamemd.exe. Output to EVIDENCE/callsite_arg2.txt.
"""
import os
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
OUT = os.path.join(ROOT, "lead", "next_re_20261117_r14", "W177-J",
                   "EVIDENCE", "callsite_arg2.txt")

BASE = 0x400000
pe = pefile.PE(EXE)
image = pe.get_memory_mapped_image()

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

def rva(va):
    return va - BASE

def disasm_range(va_start, va_end):
    data = image[rva(va_start):rva(va_end)]
    lines = []
    for ins in md.disasm(data, va_start):
        lines.append("  %08X  %-24s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    return lines

out = []
out.append("SHA-matched gamemd.exe; ImageBase=0x%X" % BASE)
out.append("Resolving arg2 = 2nd stack arg of 0x47C620 (thiscall: ecx=this, ret 0xc => 3 stack args).")
out.append("At entry + prologue (sub esp,8; push ebx/ebp/esi/edi = 24 bytes), [esp+0x20] = arg2.")
out.append("")

for label, cs, ce, site in [
    ("CALL SITE 1 (placement main loop 0x43F180)", 0x43F180, 0x43F300, 0x43F2AE),
    ("CALL SITE 2 (can-place query 0x449440)",     0x449440, 0x4494C0, 0x449482),
]:
    out.append("=" * 78)
    out.append(label + "   call @ 0x%X" % site)
    out.append("=" * 78)
    out += disasm_range(cs, ce)
    out.append("")

# Also dump the function 0x449410..0x4494C0 (VERDICT D2 says esi=vptr at 0x43F1FD,
# and the query function 0x449440 is reached via vslot107).
out.append("=" * 78)
out.append("FUNC 0x449410..0x4494C0 (context around can-place query)")
out.append("=" * 78)
out += disasm_range(0x449410, 0x4494C0)

txt = "\n".join(out)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(txt + "\n")
print("wrote", OUT, len(out), "lines")
