# -*- coding: utf-8 -*-
"""④ final classifier: for each vtable, enumerate ALL write sites, find containing function
(scan back to ret/int3 padding), classify ctor / dtor(operator delete or atexit handler) /
global-init, and check liveness (callers). Anchor in dtor => FAIL (㉓)."""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE,"b5_rows.json"),encoding="utf-8") as f: rows=json.load(f)
with open(os.path.join(HERE,"ring_analysis.json"),encoding="utf-8") as f: RA=json.load(f)

TEXT=R.TEXT_DATA; TVA=R.TEXT_VA
DEL={0x7C8B3D,0x7C93E8}; ATEXIT=0x7C978A

def func_start(va):
    """scan backward from va to nearest function start: after a `ret`/`ret imm` followed by padding or int3,
    or after atlas entry. Simpler: use atlas entry if va inside an atlas func; else scan back to C3/C2 followed by 90/CC."""
    # atlas first
    best=None
    for e,info in R.ATLAS.items():
        ea=int(e,16)
        if ea<=va<ea+info["size"]:
            if best is None or ea>best: best=ea
    if best is not None: return best,"atlas"
    # scan back in bytes
    off=va-TVA
    for k in range(off-1, max(0,off-0x400), -1):
        b=TEXT[k]
        # potential end of previous func: C3 or C2 xx xx, then 00/90/CC padding
        if b in (0xC3,0xC2):
            j=k+1
            pad=0
            while j<len(TEXT) and TEXT[j] in (0x90,0xCC,0x00) and pad<16:
                pad+=1; j+=1
            if pad>=2 and TVA+j<=va:
                return TVA+j,"scan"
    return None,"none"

def func_calls(ea, cap):
    out=[]
    if cap is None or cap<=0 or cap>0x2000: cap=0x200
    for i in R.disasm_body(ea,cap):
        if i.id==X86_INS_CALL and i.operands and i.operands[0].type==X86_OP_IMM:
            out.append(i.operands[0].imm & 0xFFFFFFFF)
    return out

def classify_write(wa):
    fs,how=func_start(wa)
    if fs is None:
        return {"write":"%08X"%wa,"func":None,"kind":"unknown"}
    info=R.ATLAS.get("%08X"%fs)
    cap=info["size"] if info else None
    cs=func_calls(fs,cap)
    is_dtor_delete = any(c in DEL for c in cs)
    # atexit handler? check if func_start itself is pushed before call atexit
    atexit_reg=False
    needle=b"\x68"+struct.pack("<I",fs)
    off=0
    while True:
        i=TEXT.find(needle,off)
        if i<0: break
        for j in range(i+5,min(i+5+0x40,len(TEXT)-5)):
            if TEXT[j]==0xE8:
                rel=struct.unpack_from("<i",TEXT,j+1)[0]
                if (TVA+j+5+rel)&0xFFFFFFFF==ATEXIT:
                    atexit_reg=True; break
        off=i+1
    # writes to absolute global (C7 05 disp32 imm32) => global init
    is_global = (TEXT[wa-TVA-6]==0xC7 and TEXT[wa-TVA-5]==0x05)
    kind=[]
    if is_dtor_delete: kind.append("DTOR(operator delete)")
    if atexit_reg: kind.append("ATEXIT-handler")
    if is_global: kind.append("GLOBAL-init")
    if not kind: kind.append("CTOR/non-dtor")
    callers=C.find_direct_calls(fs)
    return {"write":"%08X"%wa,"func":"%08X"%fs,"how":how,"cap":cap,
            "kind":"+".join(kind),"delete_calls":[hex(c) for c in cs if c in DEL],
            "atexit_reg":atexit_reg,"callers":["%08X"%x for x in callers[:8]]}

for r in rows:
    entry=r["entry"]; d=RA[entry]; s=d["slot2"]
    vt=int(s["vtable_base"],16)
    print("="*105)
    print(entry, d["name"], "vt=%08X"%vt)
    # find all write sites of this vtable (imm in .text)
    needle=struct.pack("<I",vt)
    writes=[]
    off=0
    while True:
        i=TEXT.find(needle,off)
        if i<0: break
        # imm at TEXT_VA+i; check instruction forms
        o=TVA+i
        # form C7 r/m32 imm32 -> imm at i, opcode C7 at i-2 (regdisp) or i-6 (global)
        if i>=6 and TEXT[i-6]==0xC7 and TEXT[i-5]==0x05:
            writes.append(o)  # global; imm begins at i
        elif i>=2 and TEXT[i-2]==0xC7:
            writes.append(o)
        off=i+1
    print("  write sites (%d):"%len(writes))
    verdicts=[]
    for w in writes:
        c=classify_write(w)
        verdicts.append(c)
        print("    ",c)
    # overall ④: PASS if any non-dtor/ctor/global-init live anchor exists
    good=[c for c in verdicts if ("CTOR" in c["kind"] or "GLOBAL-init" in c["kind"]) and "DTOR" not in c["kind"] and "ATEXIT" not in c["kind"]]
    print("  => ④ anchor non-dtor:", "PASS (%d)"%len(good) if good else "FAIL(All dtor/atexit)")
