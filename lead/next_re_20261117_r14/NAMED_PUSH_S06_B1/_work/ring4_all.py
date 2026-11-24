# -*- coding: utf-8 -*-
"""For each row: find vtable install points matching its (class,slot) RTTI slot,
classify constructor vs destructor via byte signatures, and decide ring4.
Destructor signature: `push 1/0; call dword ptr [reg]` (virtual dtor of members) after vptr install,
or atexit-registered. Constructor: base-ctor call + field init + vptr install, no dtor signature.
"""
import os, sys, io, json, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import recore as R
import core2 as C2
from capstone import *
from capstone.x86 import *

AN = json.load(open(os.path.join(WORK,"analysis.json"),encoding="utf-8"))
ROWS = json.load(open(os.path.join(WORK,"b1_rows.json"),encoding="utf-8"))

def resolve_slot_ext(refva, maxk=130):
    for k in range(0,maxk):
        vb=refva-4*k; c=C2.u32(vb-4)
        if not c: continue
        ci=C2.parse_col(c)
        if not ci or ci["sig"]!=0: continue
        tdi=C2.parse_td(ci["td"])
        if tdi and tdi["name"] and ".?AV" in tdi["name"]:
            return vb,4*k,tdi["name"]
    return None

def classify_func(va, vtable):
    """Return (kind, evidence). kind in ctor/dtor/unknown."""
    cap=R.ATLAS.get(R.hx(va),{}).get("size") or 96
    cap=min(cap, 0x400)
    insns=R.disasm(va, R.read_va(va,cap))
    ax=C2.is_atexit_registered(va)
    dtor_sig=[]; ctor_sig=[]; vptr_writes=[]
    for i,ins in enumerate(insns):
        # atexit push 1 then call [reg] (virtual destructor call) near vptr write
        if ins.id==X86_INS_PUSH and ins.operands and ins.operands[0].type==X86_OP_IMM and ins.operands[0].imm in (0,1):
            for k in range(i+1,min(i+3,len(insns))):
                nx=insns[k]
                if nx.id==X86_INS_CALL and nx.operands and nx.operands[0].type==X86_OP_MEM:
                    dtor_sig.append((ins.address,nx.address))
        if ins.id==X86_INS_CALL and ins.operands and ins.operands[0].type==X86_OP_IMM:
            ctor_sig.append((ins.address, ins.operands[0].imm&0xffffffff))
    if ax:
        return "dtor", "atexit_registered=%s"%ax
    # Strong destructor signature: push 0/1; call [reg] (member virtual dtor) present
    if dtor_sig:
        return "dtor", "member_virtual_dtor_calls=%s"%[(hex(a),hex(b)) for a,b in dtor_sig[:4]]
    if ctor_sig:
        return "ctor", "base/helper calls=%s"%[hex(x[1]) for x in ctor_sig[:6]]
    return "unknown","no signature"

for i,(rec,row) in enumerate(zip(AN,ROWS),1):
    e=rec["entry"]; ea=int(e,16); sn=int(row["name"].rsplit("slot",1)[1])
    cls=row["name"].rsplit("::",1)[0]
    refs=C2.find_dword_refs(ea)
    best=None
    for refva,sec in refs:
        r=resolve_slot_ext(refva)
        if r and r[1]//4==sn:
            best=(refva,r[0],r[1],r[2]); break
    if not best:
        print("%2d %s %-40s ②slot MISSING (no matching class/slot)"%(i,e,row["name"])); continue
    refva,vb,off,nm=best
    w=C2.find_vtable_writes(vb)
    sites=[]
    for g in w["global"]:
        wva=g["write_va"]; inf=g.get("in_func")
        infva=inf[0] if inf else None
        if infva is None: continue
        kind,ev=classify_func(infva,vb)
        sites.append((wva,infva,kind,ev,g.get("atexit")))
    for rw in w["regdisp"]:
        # regdisp writes handled inside core2 as global entries already
        pass
    # determine if any live ctor write OUTSIDE row body
    rowend=ea+(R.ATLAS.get(e,{}).get("size") or 256)
    live=[s for s in sites if s[2]=="ctor" and not (ea<=int(s[0],16)<rowend)]
    print("%2d %s %-40s slot=%08X vt=%08X #%d %s"%(i,e,row["name"],refva,vb,sn,nm))
    for wva,infva,kind,ev,ax in sites:
        inrow="INROW" if ea<=int(wva,16)<rowend else "OUT"
        print("     write=%s func=%s kind=%-7s %s atexit=%s"%(wva,("%08X"%infva) if isinstance(infva,int) else infva,kind,inrow,ax))
        print("        %s"%ev)
    print("     => live ctor OUT-of-row sites: %d"%len(live))
