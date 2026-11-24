# -*- coding: utf-8 -*-
"""B2 ③b② 站点扫描：机械口径（test/cmp eax）+ 返回值搬移形态（mov r,eax 后 test/cmp r）。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, "rows_b2.json"), encoding="utf-8"))

R32 = {X86_REG_EAX: "eax", X86_REG_EBX: "ebx", X86_REG_ECX: "ecx",
       X86_REG_EDX: "edx", X86_REG_ESI: "esi", X86_REG_EDI: "edi",
       X86_REG_EBP: "ebp"}


def reg_written(ins, reg):
    if ins.id == X86_INS_CALL:
        return True
    for o in ins.operands:
        if o.type == X86_OP_REG and o.reg == reg and o.access & CS_AC_WRITE:
            return True
    try:
        _, wr = ins.regs_access()
        if reg in wr:
            return True
    except Exception:
        pass
    return False


def calls_in(insns):
    out = []
    for k, i in enumerate(insns):
        if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM:
            out.append((k, i, i.operands[0].imm & 0xFFFFFFFF))
    return out


def ret_consts(fn_va, maxn=None):
    """被调返回常量集合：线性扫描函数体，收集 ret 前的 eax 常量。"""
    info = ATLAS.get(hx(fn_va))
    if not info:
        return None
    body = disasm(fn_va, info["size"])
    eax = None
    rets = []
    noret = 0
    for ins in body:
        if not ins.id:
            continue
        if ins.id == X86_INS_CALL:
            eax = None
        elif ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands) == 2 \
                and ins.operands[0].type == X86_OP_REG and ins.operands[0].reg == X86_REG_EAX \
                and ins.operands[1].type == X86_OP_REG and ins.operands[1].reg == X86_REG_EAX:
            eax = 0
        elif ins.id == X86_INS_OR and len(ins.operands) == 2 \
                and ins.operands[0].type == X86_OP_REG and ins.operands[0].reg == X86_REG_EAX \
                and ins.operands[1].type == X86_OP_IMM and ins.operands[1].imm == -1:
            eax = -1
        elif ins.id == X86_INS_MOV and len(ins.operands) == 2 \
                and ins.operands[0].type == X86_OP_REG and ins.operands[0].reg == X86_REG_EAX:
            b = ins.operands[1]
            eax = (b.imm & 0xFFFFFFFF) if b.type == X86_OP_IMM else None
        elif ins.id == X86_INS_RET:
            rets.append((ins.address, eax))
            eax = None
    return dict(size=info["size"], nret=len(rets),
                rets=[(hx(a), ("%X" % v) if v is not None else "?") for a, v in rets])


def find_sites(insns):
    """返回所有 (call, chk_reg, kind, imm, jcc) 站点：机械 eax 形态 + 搬移形态。"""
    out = []
    for k, ins, callee in calls_in(insns):
        # 形态 A：紧随 <=3 条内 test/cmp eax
        reg, kind, imm = X86_REG_EAX, None, None
        ci = k
        moved = None
        for a in range(k + 1, min(k + 4, len(insns))):
            x = insns[a]
            # 搬移形态
            if x.id == X86_INS_MOV and len(x.operands) == 2 \
                    and x.operands[0].type == X86_OP_REG and x.operands[0].reg in R32 \
                    and x.operands[1].type == X86_OP_REG and x.operands[1].reg == X86_REG_EAX:
                moved = x.operands[0].reg
                ci = a
                reg = moved
                continue
            r = moved if moved else X86_REG_EAX
            if x.id == X86_INS_TEST and len(x.operands) == 2 \
                    and x.operands[0].type == X86_OP_REG and x.operands[0].reg == r \
                    and x.operands[1].type == X86_OP_REG and x.operands[1].reg == r:
                kind, imm = ("TEST", 0)
                ci = a
                break
            if x.id == X86_INS_CMP and len(x.operands) == 2 \
                    and x.operands[0].type == X86_OP_REG and x.operands[0].reg == r \
                    and x.operands[1].type == X86_OP_IMM:
                kind, imm = ("CMP", x.operands[1].imm & 0xFFFFFFFF)
                ci = a
                break
            if reg_written(x, r) and x.id != X86_INS_MOV:
                break
        if kind is None:
            continue
        # 找 jcc
        for b in range(ci + 1, min(ci + 3, len(insns))):
            jc = insns[b]
            if jc.id in JCC:
                tgt = jc.operands[0].imm & 0xFFFFFFFF if (jc.operands and jc.operands[0].type == X86_OP_IMM) else None
                # 检查 ci..b 之间 reg 是否被覆写
                overwritten = any(reg_written(insns[x], reg) for x in range(ci + 1, b))
                out.append(dict(call_va=hx(ins.address), callee=hx(callee),
                                moved=(R32.get(moved) if moved else None),
                                chk_va=hx(insns[ci].address), chk_kind=kind,
                                chk_imm=("%X" % imm) if imm is not None else None,
                                jcc_va=hx(jc.address), jcc_mn=jc.mnemonic,
                                jcc_tgt=hx(tgt) if tgt else None,
                                ft=hx(jc.address + jc.size),
                                reg_overwritten_between=overwritten))
                break
    return out


print("=== ③b② 站点扫描 ===")
ALL = []
for r in rows:
    e = r["entry"]
    ev, body = disasm_body(e)
    sites = find_sites(body)
    print("\n## %s %s  size=%d insns=%d sites=%d" % (e, r["name"], len(va_read(ev, 0)) or 0, len(body), len(sites)))
    recs = []
    for s in sites:
        rc = ret_consts(int(s["callee"], 16))
        s["callee_ret"] = rc
        recs.append(s)
        print("   call %s -> %s   %s %s %s%s  jcc %s %s (tgt %s ft %s)  reg_ovr=%s"
              % (s["call_va"], s["callee"],
                 ("mov %s,eax;" % s["moved"]) if s["moved"] else "",
                 s["chk_kind"], s["chk_imm"] or "", s["chk_va"],
                 s["jcc_mn"], s["jcc_va"], s["jcc_tgt"], s["ft"], s["reg_overwritten_between"]))
        if rc:
            print("        callee size=%d nret=%d retconsts=%s" % (rc["size"], rc["nret"], rc["rets"]))
        else:
            print("        callee: no atlas boundary")
    ALL.append(dict(entry=e, name=r["name"], n_sites=len(sites), sites=recs))

json.dump(ALL, open(os.path.join(HERE, "ring3_sites.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n-> ring3_sites.json")
