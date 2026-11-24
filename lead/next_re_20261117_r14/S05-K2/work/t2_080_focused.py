#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S05-K2 T2 +0x80 focused counter:
 (a) vcall breakdown call vs jmp at disp 0x80
 (b) byte-sized writes byte[reg+0x80] count + distinct enclosing functions
     (compare S07-K2 181 writes/81 funcs vs R14_COMMON 179/83)
 (c) same for other 4 fields' vcalls
"""
import pefile, os, json, bisect, collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM

ROOT = r"D:\Project\ra2-campaign-forge"
P = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUTDIR = os.path.join(ROOT, "lead", "next_re_20261117_r14", "S05-K2")
EVID = os.path.join(OUTDIR, "EVIDENCE")

pe = pefile.PE(P); IB = pe.OPTIONAL_HEADER.ImageBase
SECS = []
for s in pe.sections:
    SECS.append((s.Name.rstrip(b"\0").decode(), s.VirtualAddress + IB, s.Misc_VirtualSize,
                 s.PointerToRawData, s.SizeOfRawData))
SM = {s[0]: s for s in SECS}
TEXT = SM[".text"]
DATA = open(P, "rb").read()
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.skipdata = True; MD.detail = True

funcs = []
with open(ATLAS, encoding="utf-8") as f:
    f.readline()
    for line in f:
        p = line.rstrip("\n").split("\t")
        try: funcs.append((int(p[0], 16), int(p[1])))
        except Exception: pass
funcs.sort(); starts = [e for e, _ in funcs]
def enclosing(va):
    i = bisect.bisect_right(starts, va) - 1
    if i >= 0:
        e, sz = funcs[i]
        if e <= va < e + max(sz, 1): return e
    return None

WRITE_MN = {'mov','movzx','movsx','add','sub','inc','dec','or','and','xor','adc','sbb',
            'neg','not','shl','shr','sar','imul','sete','setne','setz','setnz','seta','setb','setg','setl'}

TARGET = [0x10, 0x20, 0x74, 0x80, 0x94]
recs = {d: [] for d in TARGET}
base = DATA[TEXT[3]:TEXT[3]+TEXT[4]]
for ins in MD.disasm(base, TEXT[1]):
    try: ops = ins.operands
    except Exception: continue
    if not ops: continue
    mn = ins.mnemonic
    for oi, op in enumerate(ops):
        if op.type != X86_OP_MEM: continue
        disp = int(op.mem.disp)
        if disp not in recs: continue
        if op.mem.index != 0: continue   # noidx caliber
        base_reg = ins.reg_name(op.mem.base) if op.mem.base else None
        rec = {"va": ins.address, "mn": mn, "op": ins.op_str, "bytes": ins.bytes.hex(),
               "size": op.size, "base": base_reg, "func": enclosing(ins.address), "oi": oi}
        recs[disp].append(rec)

out = {"method": "capstone skipdata=True detail=True; noidx; op.size=operand width",
       "sha256": "73201CC0...F67476", "fields": {}}
for d in TARGET:
    R = recs[d]
    vcalls = [r for r in R if r["mn"] in ("call","jmp") and r["oi"]==0]
    calls = [r for r in vcalls if r["mn"]=="call"]
    jmps  = [r for r in vcalls if r["mn"]=="jmp"]
    writes = [r for r in R if r["oi"]==0 and r["mn"] in WRITE_MN]
    byte_writes = [r for r in writes if r["size"]==1]  # byte ptr writes
    dword_writes = [r for r in writes if r["size"]==4]
    def fset(rows): return sorted(set(r["func"] for r in rows if r["func"]))
    out["fields"]["0x%X"%d] = {
        "vcall_total": len(vcalls), "call": len(calls), "jmp": len(jmps),
        "writes_all": len(writes),
        "writes_byte": len(byte_writes), "funcs_byte": len(fset(byte_writes)),
        "writes_dword": len(dword_writes), "funcs_dword": len(fset(dword_writes)),
        "byte_write_addrs": [("%08X"%r["va"], "%08X"%r["func"] if r["func"] else None, r["bytes"], r["op"]) for r in byte_writes],
    }
    print("+0x%-3X vcall=%d (call=%d jmp=%d) writes_all=%d byte_w=%d/%d funcs dword_w=%d/%d funcs"%(
        d, len(vcalls), len(calls), len(jmps), len(writes), len(byte_writes),
        len(fset(byte_writes)), len(dword_writes), len(fset(dword_writes))))

with open(os.path.join(EVID, "t2_080_focused.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print("WROTE", os.path.join(EVID, "t2_080_focused.json"))
