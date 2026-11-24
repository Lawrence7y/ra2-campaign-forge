#!/usr/bin/env python3
"""S01-K2: RTTI via file-offset scan (correct mapping) + GetSize chain + allocation points."""
import os, struct, re
import pefile

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
EV = os.path.join(ROOT, r"lead\next_re_20261117_r14\S01-K2\EVIDENCE")
IB = 0x400000
blob = open(EXE, "rb").read()
pe = pefile.PE(EXE, fast_load=True)

def off2va(off):
    try: return pe.get_rva_from_offset(off) + IB
    except: return None

def va2off(va):
    try: return pe.get_offset_from_rva(va - IB)
    except: return None

def read(va, n):
    o = va2off(va); return blob[o:o+n] if o is not None else b""

def dword(va):
    b = read(va, 4); return struct.unpack("<I", b)[0] if len(b) == 4 else 0

def secname(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.Name.rstrip(b"\0").decode(errors="replace")
    return None

def in_sec(va, name): return secname(va) == name

KEYS = ["logicclass", "conquer", "mainloop", "layerclass"]
found = []
p = 0
while True:
    p = blob.find(b".?AV", p)
    if p < 0: break
    e = blob.find(b"@@", p)
    if e > p and e - p < 120:
        try: nm = blob[p:e+2].decode("ascii")
        except: nm = ""
        if any(k in nm.lower() for k in KEYS):
            name_va = off2va(p)
            if name_va:
                found.append((name_va - 8, nm, p))
    p += 4
seen=set(); found=[x for x in found if not (x[0] in seen or seen.add(x[0]))]
print("=== RTTI TDs (name at TD+8), via file-offset scan ===")
for td, nm, off in found:
    print(f"  TD {td:#x}  vptr={dword(td):#x}  fileoff={off:#x}  {nm}")

# rdata VA range
rd = [s for s in pe.sections if s.Name.rstrip(b"\0")==b".rdata"][0]
rv = IB + rd.VirtualAddress; re_ = rv + max(rd.Misc_VirtualSize, rd.SizeOfRawData)

print("\n=== COL + vtable + GetSize (B8 imm32 C3) ===")
out=[]
for td, nm, off in found:
    cols=[q for q in range(rv, re_-0x10, 4) if dword(q+0xC)==td]
    seg=f"TD {td:#x} {nm}\n  COLs(COL+0xC==TD): {[hex(c) for c in cols]}"
    print(seg); out.append(seg)
    for col in cols:
        vts=[q+4 for q in range(rv, re_-8, 4) if dword(q)==col and in_sec(q+4,".rdata")]
        for vt in vts:
            slots=[dword(vt+4*i) for i in range(30)]
            gs=[]
            for i,sv in enumerate(slots):
                if in_sec(sv,".text") and read(sv,1)==b"\xb8" and read(sv+5,1)==b"\xc3":
                    imm=struct.unpack("<I",read(sv+1,4))[0]
                    gs.append((i,sv,imm))
            line=f"  COL {col:#x} vtable {vt:#x}\n    slots: "+" ".join(f"{x:08X}" for x in slots)
            line+="\n    B8-imm32-C3: "+((", ".join(f"v[{i}]={sv:#x} imm={imm}(0x{imm:x})" for i,sv,imm in gs)) if gs else "none")
            print(line); out.append(line)
open(os.path.join(EV,"getsize_candidates_v2.txt"),"w",encoding="utf-8").write("\n".join(out)+"\n")

# ---- allocation-point double check: push <imm> before operator new, for candidate sizes ----
print("\n=== allocation points (push <size>; call operator new 0x7CA650) near LogicClass ctor refs ===")
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
tv=[s for s in pe.sections if s.Name.rstrip(b"\0")==b".text"][0]
tva=IB+tv.VirtualAddress; tsz=min(tv.Misc_VirtualSize,tv.SizeOfRawData)
# collect all 'push imm8/imm32' immediately followed by call 0x7CA650 (operator new)
alloc=[]
ins_list=list(md.disasm(read(tva,tsz),tva))
for i,ins in enumerate(ins_list):
    if ins.mnemonic=="call" and ins.operands and ins.operands[0].type==CS_OP_IMM and ins.operands[0].imm==0x7CA650:
        if i>0 and ins_list[i-1].mnemonic=="push" and ins_list[i-1].operands:
            op=ins_list[i-1].operands[0]
            if op.type==CS_OP_IMM: alloc.append((ins_list[i-1].address, op.imm))
print(f"  push-imm -> call operator new(0x7CA650): count={len(alloc)}")
from collections import Counter
print("  size histogram (top 20):", Counter(v for _,v in alloc).most_common(20))
with open(os.path.join(EV,"alloc_points.txt"),"w",encoding="utf-8") as f:
    for a,v in alloc: f.write(f"{a:08X}\tpush {v:#x}({v})\n")
print("DONE")
