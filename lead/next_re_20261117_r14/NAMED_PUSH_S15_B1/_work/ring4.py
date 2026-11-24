# -*- coding: utf-8 -*-
"""④ 使用见证：枚举某虚表在 .text 的**全部**写点，并逐个分类
   CTOR（先调基类构造器再装 vptr）/ DTOR（先装 vptr 后干活、dl=1、注册表摘除）
   / ATEXIT（该函数被 push 到 atexit）/ UNKNOWN。
遵守 ㉓：析构器不算 ④ 见证；必须找到至少一个非析构、非 atexit 的构造安装点。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from core2 import (u32, find_vtable_writes, is_atexit_registered,
                   find_containing_atlas_func, ATEXIT_VA)
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_INS_CALL, X86_INS_RET, X86_INS_JMP,
                          X86_OP_REG, X86_OP_IMM, X86_OP_MEM,
                          X86_REG_DL, X86_REG_EDX)

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
md.detail = True


def classify_func(func_va, size, vt):
    """分析装 vt 的函数体，返回形状判定与关键指令地址。"""
    code = R.read_va(func_va, size)
    insns = [i for i in md.disasm(code, func_va) if i.id != 0]
    install_idx = None
    for k, i in enumerate(insns):
        if i.id == 0x8A:  # mov
            continue
    # 找装 vt 的那条指令
    for k, i in enumerate(insns):
        if i.mnemonic == "mov" and len(i.operands) == 2 and i.operands[0].type == X86_OP_MEM \
           and i.operands[1].type == X86_OP_IMM and (i.operands[1].imm & 0xFFFFFFFF) == vt:
            install_idx = k
            break
    if install_idx is None:
        return None
    first_call_idx = next((k for k, i in enumerate(insns) if i.id == X86_INS_CALL), None)
    dl1_idx = next((k for k, i in enumerate(insns)
                    if i.mnemonic == "mov" and len(i.operands) == 2
                    and i.operands[0].type == X86_OP_REG and i.operands[0].reg == X86_REG_DL
                    and i.operands[1].type == X86_OP_IMM), None)
    # 是否引用全局注册表：存在 mov ecx/edx, imm32 指向 .data 的 0x00B0xxxx 且随后有 push
    regs = set()
    for i in insns:
        if i.mnemonic == "mov" and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG \
           and i.operands[1].type == X86_OP_IMM:
            v = i.operands[1].imm & 0xFFFFFFFF
            if 0x00A00000 <= v < 0x00C00000:
                regs.add(i.operands[0].reg)
    calls = []
    for i in insns:
        if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM:
            calls.append((i.address, i.operands[0].imm & 0xFFFFFFFF))

    if first_call_idx is not None and first_call_idx < install_idx:
        shape = "CTOR"
        why = "install 之前有 call（基类构造器）@%08X" % insns[first_call_idx].address
    elif dl1_idx is not None and dl1_idx < install_idx:
        shape = "DTOR"
        why = "install 之前先 mov dl,<imm> @%08X，无基类 ctor 调用（析构器形状）" % insns[dl1_idx].address
    else:
        shape = "UNKNOWN"
        why = "install 之前既无 call 也无 dl=1"
    return {
        "func": "%08X" % func_va, "size": size,
        "install_va": "%08X" % insns[install_idx].address,
        "install_idx": install_idx,
        "first_call": "%08X" % insns[first_call_idx].address if first_call_idx is not None else None,
        "dl1_va": "%08X" % insns[dl1_idx].address if dl1_idx is not None else None,
        "shape": shape, "why": why,
        "n_calls": len(calls),
        "calls": [["%08X" % a, "%08X" % t] for a, t in calls[:8]],
        "globals_touched": len(regs),
    }


def all_writes(vt):
    w = find_vtable_writes(vt)
    sites = []
    for it in w["global"]:
        sites.append({"write_va": it["write_va"], "global": it["global"]})
    for x in w["regdisp"]:
        sites.append({"write_va": "%08X" % x, "global": None})
    out = []
    for s in sites:
        wva = int(s["write_va"], 16)
        f = find_containing_atlas_func(wva)
        rec = dict(s)
        if f:
            rec["in_func"] = f[1]
            rec["atexit"] = bool(is_atexit_registered(f[0]))
            rec["cls"] = classify_func(f[0], f[2], vt)
        else:
            rec["in_func"] = None
            rec["atexit"] = None
            rec["cls"] = None
        out.append(rec)
    out.sort(key=lambda r: r["write_va"])
    return out


def report(vt, verbose=True):
    sites = all_writes(vt)
    ctor = [s for s in sites if s["cls"] and s["cls"]["shape"] == "CTOR" and not s["atexit"]]
    dtor = [s for s in sites if s["cls"] and s["cls"]["shape"] == "DTOR"]
    ate = [s for s in sites if s["atexit"]]
    if verbose:
        print("vt %08X  写点共 %d   CTOR=%d DTOR=%d ATEXIT=%d" %
              (vt, len(sites), len(ctor), len(dtor), len(ate)))
        for s in sites:
            c = s["cls"]
            print("   %s in=%-9s atexit=%-5s %s %s" % (
                s["write_va"], s["in_func"], s["atexit"],
                (c["shape"] if c else "NO-INSTALL"),
                ("install@" + c["install_va"] + " first_call=" + str(c["first_call"])) if c else ""))
    return {"vt": "%08X" % vt, "sites": sites,
            "ctor_ok": [s["write_va"] for s in ctor],
            "dtor": [s["write_va"] for s in dtor],
            "atexit": [s["write_va"] for s in ate]}


if __name__ == "__main__":
    for a in sys.argv[1:]:
        report(int(a, 16))
        print()
