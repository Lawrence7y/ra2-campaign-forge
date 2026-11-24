# -*- coding: utf-8 -*-
"""补充扫描 2：捕获「call → mov <reg>,eax → test/cmp <reg>,… → jcc」的搬移形态，
以及「cmp eax,-N / 大负常量」的 HRESULT 形态，避免漏判。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

here = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(here, "rows_b1.json"), encoding="utf-8"))

REGS = {"eax": C.X86_REG_EAX, "ebx": C.X86_REG_EBX, "ecx": C.X86_REG_ECX,
        "edx": C.X86_REG_EDX, "esi": C.X86_REG_ESI, "edi": C.X86_REG_EDI, "ebp": C.X86_REG_EBP}


def ret_info(va):
    ai = C.atlas_covering(va)
    if not ai:
        return None
    ins = C.disasm(va, ai[2])
    consts, nret = set(), 0
    for k, i in enumerate(ins):
        if i.id != C.X86_INS_RET:
            continue
        nret += 1
        for j in range(max(0, k - 6), k):
            p = ins[j]
            if p.id == C.X86_INS_MOV and len(p.operands) == 2 and p.operands[0].type == C.X86_OP_REG \
               and p.operands[0].reg == C.X86_REG_EAX and p.operands[1].type == C.X86_OP_IMM:
                consts.add(p.operands[1].imm & 0xFFFFFFFF)
            elif p.id in (C.X86_INS_XOR, C.X86_INS_SUB) and len(p.operands) == 2 \
                    and p.operands[0].type == C.X86_OP_REG and p.operands[0].reg == C.X86_REG_EAX \
                    and p.operands[1].type == C.X86_OP_REG and p.operands[1].reg == C.X86_REG_EAX:
                consts.add(0)
    return consts, nret


def errlike(cs):
    if not cs or 0 not in cs:
        return False
    return any(1 <= c <= 0x40 for c in cs) and len(cs) >= 2


for n, r in enumerate(rows, 1):
    e, insns = C.disasm_body(r["entry"])
    idx = {i.address: k for k, i in enumerate(insns)}
    hits = []
    for k, i in enumerate(insns):
        # 形态 A: call direct ; mov reg,eax ; test/cmp reg ; jcc
        if i.id != C.X86_INS_CALL or not (i.operands and i.operands[0].type == C.X86_OP_IMM):
            continue
        callee = i.operands[0].imm & 0xFFFFFFFF
        if not C.in_text(callee):
            continue
        ri = ret_info(callee)
        if not ri or not errlike(ri[0]):
            continue
        # 前一跳（含 0 跳）是否有 mov reg,eax
        for mv in range(k, min(k + 2, len(insns))):
            ins_mv = insns[mv]
            reg = None
            if mv == k:
                reg = "eax"
            elif ins_mv.id == C.X86_INS_MOV and len(ins_mv.operands) == 2 \
                    and ins_mv.operands[0].type == C.X86_OP_REG and ins_mv.operands[1].type == C.X86_OP_REG \
                    and ins_mv.operands[1].reg == C.X86_REG_EAX:
                reg = ins_mv.reg_name(ins_mv.operands[0].reg)
            if reg is None:
                continue
            rid = REGS.get(reg)
            if rid is None:
                continue
            for a in range(mv + 1, min(mv + 4, len(insns))):
                ins_a = insns[a]
                ok = False
                if ins_a.id in (C.X86_INS_TEST, C.X86_INS_OR) and len(ins_a.operands) == 2 \
                        and ins_a.operands[0].type == C.X86_OP_REG and ins_a.operands[0].reg == rid \
                        and ins_a.operands[1].type == C.X86_OP_REG and ins_a.operands[1].reg == rid:
                    ok = True
                if ins_a.id == C.X86_INS_CMP and len(ins_a.operands) == 2 \
                        and ins_a.operands[0].type == C.X86_OP_REG and ins_a.operands[0].reg == rid \
                        and ins_a.operands[1].type == C.X86_OP_IMM:
                    ok = True
                if not ok:
                    if ins_a.id == C.X86_INS_CALL:
                        break
                    continue
                for b in range(a + 1, min(a + 3, len(insns))):
                    if insns[b].id in C.JCC:
                        # 该寄存器在 a+1..b-1 被覆写？
                        ov = False
                        for x in range(a + 1, b):
                            ins_x = insns[x]
                            for o in ins_x.operands:
                                if o.type == C.X86_OP_REG and o.reg == rid and (o.access & C.CS_AC_WRITE):
                                    ov = True
                        hits.append((C.hx(i.address), C.hx(callee), reg, sorted(ri[0])[:6],
                                     C.hx(insns[b].address), insns[b].mnemonic, ov))
                        break
                break
    seen = set()
    uniq = []
    for h in hits:
        key = (h[0], h[1], h[2], tuple(h[3]), h[4])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(h)
    if uniq:
        print("ROW %2d %s %-22s 搬移形态错误码站点 %d:" % (n, r["entry"], r["name"], len(uniq)))
        for h in uniq:
            print("     call %s -> %s | reg=%s consts=%s | %s@%s | 覆写=%s" %
                  (h[0], h[1], h[2], [hex(c) for c in h[3]], h[5], h[4], h[6]))
    else:
        print("ROW %2d %s %-22s 搬移形态错误码站点 0" % (n, r["entry"], r["name"]))
