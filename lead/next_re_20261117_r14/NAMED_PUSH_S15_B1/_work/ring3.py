# -*- coding: utf-8 -*-
"""③b② 严格判据（R14_COMMON:611 + MEASURE_F3A/CONTROLS.md 修正）：
   (A) `cmp <op>,-1` 哨兵驱动 jcc/setcc，或
   (B) 字面 -1 紧邻 ret 返回。
   同时报告 test eax,eax + jcc 的弱形态（归 ③a，不计 ③b②）。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_OP_IMM, X86_OP_REG, X86_REG_EAX, X86_INS_RET,
                          X86_INS_CMP, X86_INS_TEST, X86_INS_MOV, X86_INS_JMP)

ENTRIES = ["006E3E30", "006E57A0", "006E6470", "0071F930", "0071FA80",
           "00726860", "007268D0", "00726950", "00727BF0", "00727C80"]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
md.detail = True

JCC = set()
import capstone.x86 as cx
for n in dir(cx):
    if n.startswith("X86_INS_J") and n != "X86_INS_JMP":
        v = getattr(cx, n)
        if isinstance(v, int):
            JCC.add(v)
SETCC = {v for n, v in ((n, getattr(cx, n)) for n in dir(cx) if n.startswith("X86_INS_SET"))
         if isinstance(v, int)}


def scan(entry):
    ea = int(entry, 16)
    size = R.ATLAS.get(entry, {}).get("size") or 0x80
    insns = [i for i in md.disasm(R.read_va(ea, size), ea) if i.id != 0]
    cmp_m1, neg_ret, weak = [], [], []
    for k, i in enumerate(insns):
        if i.id == X86_INS_CMP and len(i.operands) == 2 \
           and i.operands[1].type == X86_OP_IMM and (i.operands[1].imm & 0xFFFFFFFF) == 0xFFFFFFFF:
            # 其后 1..2 条内是否 jcc/setcc（中间不得覆写标志）
            for m in range(k + 1, min(k + 3, len(insns))):
                j = insns[m]
                if j.id in JCC or j.id in SETCC:
                    cmp_m1.append({"cmp": "%08X" % i.address, "cmp_str": "%s %s" % (i.mnemonic, i.op_str),
                                   "br": "%08X" % j.address, "br_str": "%s %s" % (j.mnemonic, j.op_str),
                                   "br_target": "%08X" % (j.operands[0].imm & 0xFFFFFFFF)
                                   if j.operands and j.operands[0].type == X86_OP_IMM else None})
                    break
        if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG \
           and i.operands[0].reg == X86_REG_EAX and i.operands[1].type == X86_OP_IMM \
           and (i.operands[1].imm & 0xFFFFFFFF) == 0xFFFFFFFF:
            nxt = insns[k + 1] if k + 1 < len(insns) else None
            if nxt is not None and (nxt.id == X86_INS_RET or nxt.mnemonic.startswith("pop")):
                neg_ret.append({"mov": "%08X" % i.address, "next": "%s %s" % (nxt.mnemonic, nxt.op_str)})
        if i.id == X86_INS_TEST and len(i.operands) == 2 \
           and all(o.type == X86_OP_REG and o.reg == X86_REG_EAX for o in i.operands):
            for m in range(k + 1, min(k + 3, len(insns))):
                j = insns[m]
                if j.id in JCC:
                    weak.append({"test": "%08X" % i.address, "br": "%08X" % j.address,
                                 "br_str": "%s %s" % (j.mnemonic, j.op_str)})
                    break
    return {"entry": entry, "cmp_m1": cmp_m1, "neg_ret": neg_ret, "weak_test_jcc": weak,
            "b3b2_ok": bool(cmp_m1 or neg_ret)}


if __name__ == "__main__":
    for e in (sys.argv[1:] or ENTRIES):
        r = scan(e)
        print("%s  ③b②=%s  cmp-1:%d  lit-1-return:%d  weak(test/jcc):%d" %
              (e, "PASS" if r["b3b2_ok"] else "FAIL", len(r["cmp_m1"]), len(r["neg_ret"]),
               len(r["weak_test_jcc"])))
        for c in r["cmp_m1"]:
            print("     cmp@%s (%s) -> %s %s" % (c["cmp"], c["cmp_str"], c["br"], c["br_str"]))
        for n in r["neg_ret"]:
            print("     mov eax,-1 @%s  next=%s" % (n["mov"], n["next"]))
        for w in r["weak_test_jcc"]:
            print("     [weak] test eax,eax@%s -> %s %s" % (w["test"], w["br"], w["br_str"]))
