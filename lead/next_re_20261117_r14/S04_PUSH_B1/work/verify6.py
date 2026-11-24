# -*- coding: utf-8 -*-
"""环② 构造链最后一通道（S17_ENGFAM 法）：
对每行函数体取所有落在 .data/.bss 的全局地址立即数；对每个全局地址，全 .text 扫
mov [global], vt imm32（C7 05 disp32 imm32）且 vt 可解 RTTI。
若函数操作某全局对象且该对象类经构造写定死 => ② 可由构造链建立。
只读。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM

WORK=os.path.dirname(os.path.abspath(__file__))
j=json.load(open(os.path.join(WORK,"analysis.json"),encoding="utf-8"))
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True

DATA_SECS=[]
for s in R._pe.sections:
    nm=s.Name.rstrip(b"\x00").decode("latin1")
    if nm==".text": continue
    va=R.IB+s.VirtualAddress
    sz=max(s.Misc_VirtualSize,s.SizeOfRawData)
    DATA_SECS.append((nm,va,sz))

def in_data(x):
    for nm,v0,sz in DATA_SECS:
        if v0<=x<v0+sz: return nm
    return None

def resolve_vt(imm):
    c=W.u32(imm-4)
    if not c: return None
    ci=W.parse_col(c)
    if not ci or ci["sig"]!=0: return None
    tdi=W.parse_td(ci["td"])
    if tdi and tdi["name"] and ".?AV" in tdi["name"]: return tdi["name"]
    return None

global_vt_writes={}
TD=R.TEXT_DATA; TV=R.TEXT_VA
for off in range(0,len(TD)-10):
    if TD[off]==0xC7 and TD[off+1]==0x05:
        g=struct.unpack_from("<I",TD,off+2)[0]
        vt=struct.unpack_from("<I",TD,off+6)[0]
        nm=resolve_vt(vt)
        if nm:
            global_vt_writes.setdefault(g,[]).append((TV+off,"%08X"%vt,nm))

out={}
for r in j:
    e=r["entry"];ea=int(e,16);sz=r["atlas"].get("size",0)
    insns=list(MD.disasm(R.read_va(ea,sz if sz else 512),ea))
    globs={}
    for ins in insns:
        for op in ins.operands:
            if op.type==X86_OP_IMM:
                imm=op.imm&0xFFFFFFFF
                sec=in_data(imm)
                if sec:
                    gw=global_vt_writes.get(imm,[])
                    if gw:
                        g="%08X"%imm
                        globs.setdefault(g,{"sec":sec,"writes":[]})
                        for wv,vt,nm in gw:
                            tup=("%08X"%wv,vt,nm)
                            if tup not in [tuple(x) for x in globs[g]["writes"]]:
                                globs[g]["writes"].append(list(tup))
    out[e]=globs
    summ={g:[w[2] for w in d["writes"]] for g,d in globs.items()}
    print("%s global-objs-with-known-class=%d %s"%(e,len(globs),summ),flush=True)

json.dump(out,open(os.path.join(WORK,"verify6.json"),"w",encoding="utf-8"),
          ensure_ascii=False,indent=1)
print("wrote verify6.json")
