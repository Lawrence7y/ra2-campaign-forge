# -*- coding: utf-8 -*-
"""环② 构造链细查：
(A) 每个函数：序言是否用 ecx(thiscall)；体内是否 mov [this+off], vt（构造器特征）。
(B) 每个 direct call site：call 前 24 条内是否有 mov [obj],vt 且 obj 指针随后进 ecx 传给 call。
输出逐行 JSON + 文本，供 EVIDENCE 引用。只读。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_INS_MOV,
                          X86_REG_ECX, X86_INS_CALL)

WORK = os.path.dirname(os.path.abspath(__file__))
j = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True

def resolve_vt(imm):
    c = W.u32(imm-4)
    if not c: return None
    ci = W.parse_col(c)
    if not ci or ci["sig"]!=0: return None
    tdi = W.parse_td(ci["td"])
    if tdi and tdi["name"] and ".?AV" in tdi["name"]: return tdi["name"]
    return None

def func_prologue_and_this(ea, size, n=14):
    insns = list(MD.disasm(R.read_va(ea, size if size else 512), ea))
    head = insns[:n]
    uses_ecx = any(op.type==X86_OP_REG and op.reg==X86_REG_ECX
                   for i in head for op in i.operands)
    lines = ["%08X: %s %s"%(i.address,i.mnemonic,i.op_str) for i in head]
    return uses_ecx, lines

def ctor_write_to_ecx(ea, size):
    """体内是否存在 mov [ecx+off], imm(vt) 或把 ecx 保存到 reg 后 mov [reg+0],vt。"""
    insns = list(MD.disasm(R.read_va(ea, size if size else 512), ea))
    # 简化：只认 [ecx] / [reg where reg 来自 mov reg,ecx]
    this_regs = {X86_REG_ECX}
    hits=[]
    for i in insns:
        if i.id==X86_INS_MOV and len(i.operands)==2 and i.operands[0].type==X86_OP_REG \
           and i.operands[1].type==X86_OP_REG and i.operands[1].reg==X86_REG_ECX:
            this_regs.add(i.operands[0].reg)
        if i.id==X86_INS_MOV and len(i.operands)==2:
            dst,src=i.operands
            if dst.type==X86_OP_MEM and dst.mem.base in this_regs and src.type==X86_OP_IMM:
                name=resolve_vt(src.imm & 0xFFFFFFFF)
                if name:
                    hits.append({"ins":"%08X: %s %s"%(i.address,i.mnemonic,i.op_str),
                                 "vt":"%08X"%(src.imm&0xFFFFFFFF),"name":name})
    return hits

def caller_context(site_ea, back=22):
    """以 call site 结束向前取 back 条（用 atlas 包含函数起点），找 vtable 构造写入的对象是否进 ecx。"""
    f=W.find_containing_atlas_func(site_ea)
    if not f: return {"site":"%08X"%site_ea,"func":None,"lines":[],"ctor_to_ecx":[]}
    fe,fs,size=f[0],f[1],f[2]
    insns=list(MD.disasm(R.read_va(fe,size if size else 512),fe))
    idx=None
    for k,i in enumerate(insns):
        if i.address==site_ea: idx=k;break
    if idx is None: return {"site":"%08X"%site_ea,"func":"%08X"%fe,"lines":[],"ctor_to_ecx":[]}
    window=insns[max(0,idx-back):idx+1]
    lines=["%08X: %s %s"%(i.address,i.mnemonic,i.op_str) for i in window]
    # 找窗口内 mov [reg+..],vt（构造），之后 mov ecx,reg / lea ecx,[reg..]
    ctor=[]
    for a,i in enumerate(window):
        if i.id==X86_INS_MOV and len(i.operands)==2:
            dst,src=i.operands
            if dst.type==X86_OP_MEM and src.type==X86_OP_IMM:
                nm=resolve_vt(src.imm&0xFFFFFFFF)
                if nm:
                    base=dst.mem.base
                    # 之后是否 ecx<=base 或直接 push 该对象
                    handed=[]
                    for j in window[a+1:]:
                        if j.id==X86_INS_MOV and len(j.operands)==2 \
                           and j.operands[0].type==X86_OP_REG and j.operands[0].reg==X86_REG_ECX \
                           and j.operands[1].type==X86_OP_REG and j.operands[1].reg==base:
                            handed.append("%08X: mov ecx,%s"%(j.address,MD.reg_name(base)))
                        if j.address>=site_ea: break
                    ctor.append({"write":"%08X: %s %s"%(i.address,i.mnemonic,i.op_str),
                                 "name":nm,"to_ecx":handed})
    return {"site":"%08X"%site_ea,"func":"%08X"%fe,"lines":lines,"ctor_to_ecx":ctor}

out={}
for r in j:
    e=r["entry"];ea=int(e,16);sz=r["atlas"].get("size",0)
    uses_ecx,pro=func_prologue_and_this(ea,sz)
    cw=ctor_write_to_ecx(ea,sz)
    ctx=[caller_context(int(c,16)) for c in r["direct_callers"]]
    out[e]={"entry":e,"prologue_uses_ecx":uses_ecx,"prologue":pro,
            "ctor_write_to_this":cw,"callers":ctx}
    nhand=sum(len(x["ctor_to_ecx"]) for x in ctx)
    print("%s prologue_ecx=%s ctor_this=%d callers=%d ctor_handoff=%d"%(
        e,uses_ecx,len(cw),len(ctx),nhand),flush=True)

json.dump(out,open(os.path.join(WORK,"verify5.json"),"w",encoding="utf-8"),
          ensure_ascii=False,indent=1)
print("wrote verify5.json")
