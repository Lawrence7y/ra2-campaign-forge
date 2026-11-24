# -*- coding: utf-8 -*-
"""被调返回约定取证 + 站点上下文（判断两路动作是否真不同）。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C


def callee_profile(va):
    """反向：列出被调所有 ret 路径的 eax 来源（imm 常量 / 未知）。"""
    ai = C.atlas_covering(va)
    if not ai:
        return dict(ok=False, reason="not in atlas")
    size = ai[2]
    insns = C.disasm(va, size)
    prof = []
    eax = None
    for ins in insns:
        if ins.id == 0:
            continue
        if ins.id in (C.X86_INS_XOR, C.X86_INS_SUB) and len(ins.operands) == 2 \
                and ins.operands[0].type == C.X86_OP_REG and ins.operands[0].reg == C.X86_REG_EAX \
                and ins.operands[1].type == C.X86_OP_REG and ins.operands[1].reg == C.X86_REG_EAX:
            eax = 0
        elif ins.id == C.X86_INS_MOV and len(ins.operands) == 2 \
                and ins.operands[0].type == C.X86_OP_REG and ins.operands[0].reg == C.X86_REG_EAX:
            b = ins.operands[1]
            eax = ("imm", b.imm & 0xFFFFFFFF) if b.type == C.X86_OP_IMM else ("unk",)
        elif ins.id == C.X86_INS_CALL:
            eax = ("call",)
        elif ins.id == C.X86_INS_RET:
            prof.append((ins.address, eax))
            eax = None
    return dict(ok=True, entry=C.hx(va), size=size, n_insn=len(insns),
                rets=[(C.hx(a), (e if not isinstance(e, tuple) else list(e))) for a, e in prof])


def site_context(entry, call_va, before=10, after=26):
    e, insns = C.disasm_body(entry)
    idx = [k for k, i in enumerate(insns) if i.address == call_va]
    if not idx:
        return "(call 不在函数体内)"
    k = idx[0]
    out = []
    for j in range(max(0, k - before), min(len(insns), k + after)):
        ins = insns[j]
        tag = " <<<" if ins.address == call_va else ""
        out.append("%08X: %-22s %s%s" % (ins.address,
                                         ins.mnemonic + " " + ins.op_str,
                                         "", tag))
    return "\n".join(out)


if __name__ == "__main__":
    for c in (0x0065C7E0, 0x004F7870, 0x0065AD30, 0x0045EC90, 0x0047C520, 0x0049FAE0, 0x00500510, 0x0041C380):
        p = callee_profile(c)
        print("%08X -> %s" % (c, json.dumps(p, ensure_ascii=False)))
        print()
