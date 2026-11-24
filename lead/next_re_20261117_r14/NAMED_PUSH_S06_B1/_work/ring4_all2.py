# -*- coding: utf-8 -*-
import os, sys, io, json
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

def classify_func(va):
    cap=min(R.ATLAS.get(R.hx(va),{}).get("size") or 96, 0x500)
    insns=R.disasm(va, R.read_va(va,cap))
    ax=C2.is_atexit_registered(va)
    # destructor signature: `push 0/1` immediately followed by `call dword ptr [reg]`
    dtor=[]
    for i,ins in enumerate(insns):
        if ins.id==X86_INS_PUSH and ins.operands and ins.operands[0].type==X86_OP_IMM and ins.operands[0].imm in (0,1):
            for k in range(i+1,min(i+3,len(insns))):
                nx=insns[k]
                if nx.id==X86_INS_CALL and nx.operands and nx.operands[0].type==X86_OP_MEM:
                    dtor.append((ins.address,nx.address))
    # near entry: call to another func (base ctor) before any dtor sig
    pre=[]
    for ins in insns[:12]:
        if ins.id==X86_INS_CALL and ins.operands and ins.operands[0].type==X86_OP_IMM:
            pre.append(ins.operands[0].imm&0xffffffff)
    kind = "dtor" if (ax or dtor) else ("ctor" if pre else "unknown")
    ev = "atexit=%s dtorcalls=%s preCalls=%s"%(ax,[hex(x[0]) for x in dtor[:3]],[hex(x) for x in pre[:4]])
    return kind,ev

def all_writes(vb):
    w=C2.find_vtable_writes(vb)
    out=[]
    for g in w["global"]:
        out.append((g["write_va"],"global"))
    for rw in w["regdisp"]:
        out.append((rw,"regdisp"))
    return out

for i,(rec,row) in enumerate(zip(AN,ROWS),1):
    e=rec["entry"]; ea=int(e,16); sn=int(row["name"].rsplit("slot",1)[1])
    refs=C2.find_dword_refs(ea)
    best=None
    for refva,sec in refs:
        r=resolve_slot_ext(refva)
        if r and r[1]//4==sn:
            best=(refva,r[0],r[1],r[2]); break
    if not best: continue
    refva,vb,off,nm=best
    writes=all_writes(vb)
    rowend=ea+R.ATLAS.get(e,{}).get("size",256)
    info=[]
    for wva,wt in writes:
        wv = int(wva,16) if isinstance(wva,str) else wva
        inf=C2.find_containing_atlas_func(wv)
        if not inf: continue
        infva=inf[0]
        kind,ev=classify_func(infva)
        inrow = ea<=wv<rowend
        info.append((wva,infva,kind,inrow,ev))
    live=[x for x in info if x[2]=="ctor" and not x[3]]
    dtors=[x for x in info if x[2]=="dtor"]
    print("%2d %s %-42s vt=%08X #%d writes=%d ctorOUT=%d dtor=%d  R4=%s"%(
        i,e,row["name"],vb,sn,len(info),len(live),len(dtors),"PASS" if live else "FAIL"))
    for wva,infva,kind,inrow,ev in info:
        print("      %s func=%08X %-7s %s  %s"%(wva,infva,kind,"INROW" if inrow else "OUT",ev))
