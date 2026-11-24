# -*- coding: utf-8 -*-
"""B2 广义 ③b② 复扫：任何 call（直接/间接）后 <=4 条内对返回值寄存器做
test r,r / cmp r,imm / cmp r,<已知常量寄存器> ，再 <=3 条内有条件跳转。
同时报出 cmp 与 jcc 之间是否有该寄存器覆写。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, "rows_b2.json"), encoding="utf-8"))

R32 = {X86_REG_EAX: "eax", X86_REG_EBX: "ebx", X86_REG_ECX: "ecx", X86_REG_EDX: "edx",
       X86_REG_ESI: "esi", X86_REG_EDI: "edi", X86_REG_EBP: "ebp"}
JCC_ONLY = {X86_INS_JL, X86_INS_JLE, X86_INS_JG, X86_INS_JGE, X86_INS_JE, X86_INS_JNE,
            X86_INS_JB, X86_INS_JBE, X86_INS_JA, X86_INS_JAE, X86_INS_JS, X86_INS_JNS}


def wr(ins, reg):
    if ins.id == X86_INS_CALL:
        return True
    try:
        _, w = ins.regs_access()
        return reg in w
    except Exception:
        return False


def scan(entry):
    info = ATLAS.get(norm(entry))
    body = disasm(int(entry, 16), info["size"])
    calls = [(k, i) for k, i in enumerate(body) if i.id == X86_INS_CALL]
    out = []
    for k, ins in calls:
        kind = "direct"
        callee = None
        if ins.operands and ins.operands[0].type == X86_OP_IMM:
            callee = ins.operands[0].imm & 0xFFFFFFFF
        else:
            kind = "indirect"
        # 追返回值寄存器
        reg = X86_REG_EAX
        chk = None
        for a in range(k + 1, min(k + 5, len(body))):
            x = body[a]
            if x.id == X86_INS_MOV and len(x.operands) == 2 \
               and x.operands[0].type == X86_OP_REG and x.operands[0].reg in R32 \
               and x.operands[1].type == X86_OP_REG and x.operands[1].reg == reg:
                reg = x.operands[0].reg
                continue
            if x.id == X86_INS_TEST and len(x.operands) == 2 \
               and x.operands[0].type == X86_OP_REG and x.operands[0].reg == reg \
               and x.operands[1].type == X86_OP_REG and x.operands[1].reg == reg:
                chk = ("TEST", "0", a)
                break
            if x.id == X86_INS_CMP and len(x.operands) == 2 \
               and x.operands[0].type == X86_OP_REG and x.operands[0].reg == reg:
                o = x.operands[1]
                if o.type == X86_OP_IMM:
                    chk = ("CMP_IMM", hex(o.imm & 0xFFFFFFFF), a)
                elif o.type == X86_OP_REG:
                    chk = ("CMP_REG", R32.get(o.reg, "?"), a)
                break
            if wr(x, reg):
                break
        if not chk:
            continue
        # 找 jcc
        jc = None
        for b in range(chk[2] + 1, min(chk[2] + 4, len(body))):
            y = body[b]
            if y.id in JCC_ONLY:
                jc = y
                jb = b
                break
            if wr(y, reg):
                break
        if not jc:
            continue
        ovr = any(wr(body[x], reg) for x in range(chk[2] + 1, jb))
        tgt = jc.operands[0].imm & 0xFFFFFFFF if (jc.operands and jc.operands[0].type == X86_OP_IMM) else None
        out.append(dict(call=hx(ins.address), kind=kind, callee=hx(callee) if callee else None,
                        reg=R32.get(reg), chk=chk[0], val=chk[1], chk_va=hx(body[chk[2]].address),
                        jcc="%s %s" % (jc.mnemonic, hex(tgt) if tgt is not None else "?"),
                        jcc_va=hx(jc.address), tgt=hx(tgt) if tgt else None,
                        ft=hx(jc.address + jc.size), ovr=ovr))
    return out


print("=== 广义复扫 ===")
ALL = {}
for r in rows:
    s = scan(r["entry"])
    ALL[r["entry"]] = s
    print("\n## %s %s  sites=%d" % (r["entry"], r["name"], len(s)))
    for x in s:
        print("   %s %-8s -> %-8s  %s %s %s  %s %s (tgt %s ft %s) ovr=%s"
              % (x["call"], x["kind"], x["callee"], x["reg"], x["chk"], x["val"],
                 x["jcc"], x["jcc_va"], x["tgt"], x["ft"], x["ovr"]))
json.dump(ALL, open(os.path.join(HERE, "ring3_broad.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n-> ring3_broad.json")
