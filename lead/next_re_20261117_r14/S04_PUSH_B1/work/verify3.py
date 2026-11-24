# -*- coding: utf-8 -*-
"""环② 构造链通道复核：对每个 direct caller 所在函数，检查是否写 vtable（C7 05 / C7 r/m /
mov reg,imm + mov [..],reg），并把写的立即数当 vtable base 反查 COL->TD->RTTI 名。
若 caller 是构造器且写入可解析 RTTI 的 vtable，则可用『构造链』建立②。
只读。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_INS_MOV, X86_OP_IMM, X86_OP_MEM, X86_OP_REG)

WORK = os.path.dirname(os.path.abspath(__file__))
v = json.load(open(os.path.join(WORK, "verify2.json"), encoding="utf-8"))
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True

def resolve_vtable_rtti(vt_va):
    """vt_va 作为 vtable base：读 [vt-4]=COL，COL.sig==0，COL+0xC=TD，TD+8 名为 .?AVxxx。"""
    c = W.u32(vt_va - 4)
    if not c: return None
    ci = W.parse_col(c)
    if not ci or ci["sig"] != 0: return None
    tdi = W.parse_td(ci["td"])
    if tdi and tdi["name"] and ".?AV" in tdi["name"]:
        return {"col": "%08X"%c, "td": "%08X"%ci["td"], "name": tdi["name"],
                "name_va": "%08X"%tdi["name_va"]}
    return None

def scan_func_vtable_writes(func_ea, size):
    code = R.read_va(func_ea, size if size else 512)
    insns = list(MD.disasm(code, func_ea))
    writes = []
    for ins in insns:
        if ins.id != X86_INS_MOV: continue
        for op in ins.operands:
            if op.type == X86_OP_IMM:
                imm = op.imm & 0xFFFFFFFF
                # 立即数指向可读数据且 [imm-4] 可解析 RTTI -> 可能 vtable base
                rtti = resolve_vtable_rtti(imm)
                if rtti:
                    writes.append({"ins": "%08X: %s %s" % (ins.address, ins.mnemonic, ins.op_str),
                                   "imm": "%08X"%imm, "rtti": rtti})
    return writes

out = {}
for e, d in v.items():
    fns = sorted(set(x["func"] for x in d["direct_callers_with_func"] if x["func"]))
    info = []
    for f in fns:
        fe = int(f, 16)
        fi = R.ATLAS.get(f, {})
        sz = fi.get("size", 0)
        wlist = scan_func_vtable_writes(fe, sz)
        info.append({"func": f, "func_size": sz, "vtable_writes": wlist})
    out[e] = info
    nw = sum(len(x["vtable_writes"]) for x in info)
    print("%s caller-funcs=%d vtable-writes=%d" % (e, len(fns), nw), flush=True)

json.dump(out, open(os.path.join(WORK, "verify3.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("wrote verify3.json")
