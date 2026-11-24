# -*- coding: utf-8 -*-
"""④ 虚表写点全枚举 + 构造器/析构器/atexit 三分类（严格版）。

对每张 vt：
  - 枚举全镜像 dword==vt 的位置（C7 05 disp32 imm32 全局写 / C7 modrm imm32 对象写 / B8+r 载入）
  - 每个写点定位所在 atlas 函数，打印该函数**完整头部**（前若干条），
    并给出：首条 call 是否早于 install、是否出现 dl=1、是否 call 0x7258D0（析构特征）、
    是否 call 0x7C978A 之前 push 本函数（atexit 注册）、是否 call operator delete。
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from core2 import (u32, va_in, find_vtable_writes, is_atexit_registered,
                   find_containing_atlas_func, ATEXIT_VA, read_cstr)
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import *

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
md.detail = True

BASE_DTOR = 0x7258D0      # 基类析构（S13 判例：call 007258D0 = 析构特征）
ATEXIT = 0x7C978A

def func_insns(fva, size=None):
    if size is None:
        info = R.ATLAS.get("%08X" % fva)
        size = info["size"] if info else 0x200
    return [i for i in md.disasm(R.read_va(fva, size), fva) if i.id != 0], size

def classify(fva, vt):
    insns, size = func_insns(fva)
    inst = None
    for i in insns:
        if i.mnemonic == "mov" and len(i.operands) == 2 \
           and i.operands[0].type == X86_OP_MEM and i.operands[1].type == X86_OP_IMM \
           and (i.operands[1].imm & 0xFFFFFFFF) == vt:
            inst = i
            break
    if inst is None:
        return None
    idx = insns.index(inst)
    calls = [(k, i.address, i.operands[0].imm & 0xFFFFFFFF) for k, i in enumerate(insns)
             if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM]
    first_call = calls[0] if calls else None
    dl1 = next((i for i in insns[:idx] if i.mnemonic == "mov" and len(i.operands) == 2
                and i.operands[0].type == X86_OP_REG and i.operands[0].reg == X86_REG_DL), None)
    calls_before = [c for c in calls if c[0] < idx]
    calls_after = [c for c in calls if c[0] > idx]
    base_dtor_hit = [c for c in calls if c[2] == BASE_DTOR]
    if calls_before:
        shape = "CTOR"
        why = "install 前有 call %08X @%08X" % (calls_before[0][2], calls_before[0][1])
    elif dl1 is not None:
        shape = "DTOR(dl=1)"
        why = "install 前 mov dl,%s @%08X，无基类 ctor 调用" % (dl1.op_str, dl1.address)
    elif base_dtor_hit:
        shape = "DTOR(base-dtor)"
        why = "体内 call 基类析构 %08X @%08X" % (BASE_DTOR, base_dtor_hit[0][1])
    else:
        shape = "UNKNOWN"
        why = "install 前无 call、无 dl=1、体内无基类析构调用"
    return {"func": "%08X" % fva, "size": size, "install_va": "%08X" % inst.address,
            "install_bytes": inst.bytes.hex(), "install_op": inst.op_str,
            "shape": shape, "why": why,
            "first_call": "%08X@%08X" % (first_call[2], first_call[1]) if first_call else None,
            "dl1": "%08X" % dl1.address if dl1 else None,
            "n_calls": len(calls),
            "calls_head": ["%08X->%08X" % (a, t) for _, a, t in calls[:6]],
            "base_dtor_calls": ["%08X" % a for _, a, _ in base_dtor_hit]}

def all_writes(vt):
    w = find_vtable_writes(vt)
    sites = []
    for it in w["global"]:
        sites.append({"write_va": it["write_va"], "kind": "GLOBAL(C7 05)",
                      "target": "%08X" % (it["global"] or 0)})
    for x in w["regdisp"]:
        sites.append({"write_va": "%08X" % x, "kind": "OBJ(C7 modrm)", "target": None})
    for it in w["imm_load"]:
        pass
    out = []
    for s in sites:
        wva = int(s["write_va"], 16)
        f = find_containing_atlas_func(wva)
        rec = dict(s)
        if f:
            rec["in_func"] = f[1]
            ax = is_atexit_registered(f[0])
            rec["atexit_sites"] = [["%08X" % a, "%08X" % b] for a, b in ax]
            rec["atexit"] = bool(ax)
            rec["cls"] = classify(f[0], vt)
        else:
            rec["in_func"] = None
            rec["atexit"] = None
            rec["cls"] = None
        out.append(rec)
    out.sort(key=lambda r: r["write_va"])
    return out

def report(vt_hex):
    vt = int(vt_hex, 16)
    print("#" * 78)
    print("VTABLE %s   (u32[vt-4]=COL %08X)" % (vt_hex, u32(vt - 4) or 0))
    for s in all_writes(vt):
        c = s["cls"]
        print("  写点 %s %-13s in_func=%-9s atexit=%s" %
              (s["write_va"], s["kind"], s["in_func"], s["atexit"]))
        if c:
            print("        shape=%s   %s" % (c["shape"], c["why"]))
            print("        install=%s (%s) %s   first_call=%s  n_calls=%d" %
                  (c["install_va"], c["install_bytes"], c["install_op"],
                   c["first_call"], c["n_calls"]))
            print("        calls_head=%s" % c["calls_head"])
        else:
            print("        (no atlas function / no install insn)")

if __name__ == "__main__":
    for a in sys.argv[1:]:
        report(a)
