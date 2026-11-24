# -*- coding: utf-8 -*-
"""最终复核：
(1) direct caller 用 capstone 全 .text 反汇编在指令边界复核 E8 rel32 site+5+rel==entry，剔除 raw 伪命中。
(2) 0051FB00 的 0x87F7E8 引用细节 + 该全局所有 C7 05 构造写（确认多态歧义）。
(3) 输出边界核实后的 caller 集，供 EVIDENCE 用。只读。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_INS_CALL, X86_OP_IMM, X86_OP_IMM

WORK=os.path.dirname(os.path.abspath(__file__))
j=json.load(open(os.path.join(WORK,"analysis.json"),encoding="utf-8"))
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True

# 一次性全 .text 反汇编建 E8 目标 -> site 列表（指令边界）
boundary_calls={}
for ins in MD.disasm(R.TEXT_DATA,R.TEXT_VA):
    if ins.id==X86_INS_CALL and ins.operands and ins.operands[0].type==X86_OP_IMM:
        tgt=ins.operands[0].imm&0xFFFFFFFF
        boundary_calls.setdefault(tgt,[]).append(ins.address)

out={}
for r in j:
    e=r["entry"];ea=int(e,16)
    raw=r["direct_callers"]
    bc=boundary_calls.get(ea,[])
    out[e]={"raw_count":len(raw),"raw":[x for x in raw],
            "boundary_count":len(bc),"boundary":["%08X"%x for x in bc]}
    print("%s raw=%d boundary=%d"%(e,len(raw),len(bc)),flush=True)

# 0051FB00 全局 0x87F7E8 细节
g=0x87F7E8
detail={"global":"%08X"%g,"refs":[],"ctor_writes":[]}
for r in j:
    if r["entry"]=="0051FB00":
        ea=int(r["entry"],16);sz=r["atlas"].get("size",0)
        for ins in MD.disasm(R.read_va(ea,sz),ea):
            for op in ins.operands:
                if op.type==X86_OP_IMM and (op.imm&0xFFFFFFFF)==g:
                    detail["refs"].append("%08X: %s %s | %s"%(ins.address,ins.mnemonic,ins.op_str,ins.bytes.hex()))
# 全 .text C7 05 <g> <vt>
TD=R.TEXT_DATA;TV=R.TEXT_VA
for off in range(0,len(TD)-10):
    if TD[off]==0xC7 and TD[off+1]==0x05:
        gg=struct.unpack_from("<I",TD,off+2)[0]
        if gg==g:
            vt=struct.unpack_from("<I",TD,off+6)[0]
            nm=None
            c=W.u32(vt-4)
            if c:
                ci=W.parse_col(c)
                if ci and ci["sig"]==0:
                    tdi=W.parse_td(ci["td"])
                    if tdi: nm=tdi["name"]
            detail["ctor_writes"].append("%08X: C7 05 -> vt %08X (%s)"%(TV+off,vt,nm))
out["_GLOBAL_87F7E8"]=detail
json.dump(out,open(os.path.join(WORK,"verify7.json"),"w",encoding="utf-8"),
          ensure_ascii=False,indent=1)
print("global 87F7E8 refs:",detail["refs"])
print("global 87F7E8 ctor_writes:",detail["ctor_writes"])
print("wrote verify7.json")
