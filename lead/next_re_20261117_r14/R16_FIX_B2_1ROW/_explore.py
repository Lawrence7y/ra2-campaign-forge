# -*- coding: utf-8 -*-
"""R16-FIX-B2-1ROW read-only exploration of vt 0x7E16B0 install sites."""
import os, sys, io
sys.dont_write_bytecode = True
import capstone, pefile
IB = 0x400000
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
print("EXE", EXE, os.path.getsize(EXE))
pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    secs.append((IB + s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData,
                 s.get_data(), s.Name.rstrip(b"\x00").decode("latin-1")))
end = max(va + max(vs, rs) for va, vs, rs, _d, _n in secs)
buf = bytearray(end - IB + 16)
for va, vs, rs, d, nm in secs:
    buf[va - IB:va - IB + len(d)] = d
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
VTF = 0x7E16B0
pat = VTF.to_bytes(4, "little")
occ = [o for o in range(len(buf) - 4) if buf[o:o+4] == pat]
print("raw occurrences of b0 16 7e 00:", len(occ))
stores = []   # (site, ins, base, disp)
regloads = []
for o in occ:
    vend = IB + o + 4
    dec = None
    for back in range(0, 17):
        s = IB + o - back
        if s < IB: continue
        r = list(md.disasm(bytes(buf[s-IB:s-IB+24]), s, count=1))
        if not r: continue
        ins = r[0]
        if ins.address + ins.size != vend or ins.mnemonic != "mov" or len(ins.operands) != 2: continue
        a, b = ins.operands
        if a.type == capstone.x86.X86_OP_MEM and b.type == capstone.x86.X86_OP_IMM and (b.imm & 0xffffffff) == VTF:
            mo = a.mem
            base = md.reg_name(mo.base) if mo.base else ""
            dec = (s, ins, base, mo.disp & 0xffffffff)
            break
    if dec:
        stores.append(dec)
    else:
        prev = buf[o-1] if o else None
        regloads.append((IB + o - 1, "mov reg,imm" if prev in (0xb8,0xb9,0xba,0xbb,0xbc,0xbd,0xbe,0xbf) else "other"))
stores.sort()
print("mov [mem],vt stores:", len(stores), " regloads:", len(regloads))
from collections import Counter
kinds = Counter()
for s, ins, base, disp in stores:
    if base in ("esp","ebp"): k = "stack"
    elif base == "": k = "static"
    elif disp == 0 and base in ("eax","ebx","ecx","edx","esi","edi"): k = "this(reg+0)"
    else: k = "other"
    kinds[k] += 1
print("kind counts:", dict(kinds))
print("--- all non-stack stores ---")
for s, ins, base, disp in stores:
    if base in ("esp","ebp"): continue
    print("%08X  %-20s  %s" % (s, ins.bytes.hex(), ins.op_str))
print("--- host candidates disassembly ---")
for h, n in [(0x401980,0x80),(0x4739F0,0x80),(0x473A30,0x90),(0x473A80,0x40),(0x535A70,0x20),(0x47AA30,0x20)]:
    print("== host %08X ==" % h)
    for x in md.disasm(bytes(buf[h-IB:h-IB+n]), h):
        print("  %08X  %-20s %s %s" % (x.address, x.bytes.hex(), x.mnemonic, x.op_str))
