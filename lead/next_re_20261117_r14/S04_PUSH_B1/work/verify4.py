# -*- coding: utf-8 -*-
"""环② 构造链通道：检查 18 个函数自身体内是否写 vtable（作为立即数出现可解析 RTTI 的 vt base）。
若函数体把某 vtable base 写入 [ecx+0]/全局，则它可能是该类的构造器 => ② 可由构造链建立。
同时列出函数体内所有能解析到 .?AV 类名的立即数（vtable 或 COL 或 TD）。
只读。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM

WORK = os.path.dirname(os.path.abspath(__file__))
j = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True

def resolve_vtable_rtti(vt_va):
    c = W.u32(vt_va - 4)
    if not c: return None
    ci = W.parse_col(c)
    if not ci or ci["sig"] != 0: return None
    tdi = W.parse_td(ci["td"])
    if tdi and tdi["name"] and ".?AV" in tdi["name"]:
        return {"col":"%08X"%c,"name":tdi["name"]}
    return None

def scan_body_imms(ea, size):
    code = R.read_va(ea, size if size else 512)
    insns = list(MD.disasm(code, ea))
    vt = []
    for ins in insns:
        for op in ins.operands:
            if op.type == X86_OP_IMM:
                imm = op.imm & 0xFFFFFFFF
                r = resolve_vtable_rtti(imm)
                if r:
                    vt.append({"ins":"%08X: %s %s"%(ins.address,ins.mnemonic,ins.op_str),
                               "imm":"%08X"%imm, "rtti":r})
    return vt

out={}
for r in j:
    e=r["entry"]; ea=int(e,16); sz=r["atlas"].get("size",0)
    vt=scan_body_imms(ea,sz)
    out[e]=vt
    names=sorted(set(x["rtti"]["name"] for x in vt))
    print("%s body-vtable-imms=%d names=%s" % (e,len(vt),names), flush=True)

json.dump(out, open(os.path.join(WORK,"verify4.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("wrote verify4.json")
