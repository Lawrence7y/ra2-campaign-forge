# -*- coding: utf-8 -*-
"""宽扫描：所有直接调用 + 紧随其后的「返回值测试」（eax 或搬移到其它寄存器后再测），
不预设被调常量集，只把清单列出来供人工判断。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

here = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(here, "rows_b1.json"), encoding="utf-8"))

REGS = {}

def ret_consts(va):
    ai = C.atlas_covering(va)
    if not ai:
        return None, 0
    ins = C.disasm(va, ai[2])
    consts, nret = [], 0
    for k, i in enumerate(ins):
        if i.id != C.X86_INS_RET:
            continue
        nret += 1
        c = "unk"
        for j in range(max(0, k - 6), k):
            p = ins[j]
            if p.id == C.X86_INS_MOV and len(p.operands) == 2 and p.operands[0].type == C.X86_OP_REG \
               and p.operands[0].reg == C.X86_REG_EAX and p.operands[1].type == C.X86_OP_IMM:
                c = "0x%X" % (p.operands[1].imm & 0xFFFFFFFF)
            elif p.id in (C.X86_INS_XOR, C.X86_INS_SUB) and len(p.operands) == 2 \
                    and p.operands[0].type == C.X86_OP_REG and p.operands[0].reg == C.X86_REG_EAX \
                    and p.operands[1].type == C.X86_OP_REG and p.operands[1].reg == C.X86_REG_EAX:
                c = "0x0"
        consts.append(c)
    return consts, nret


def regname_from_mov(ins):
    if ins.id == C.X86_INS_MOV and len(ins.operands) == 2 \
       and ins.operands[0].type == C.X86_OP_REG and ins.operands[1].type == C.X86_OP_REG \
       and ins.operands[1].reg == C.X86_REG_EAX:
        return ins.operands[0].reg, ins.reg_name(ins.operands[0].reg)
    return None, None


for n, r in enumerate(rows, 1):
    e, insns = C.disasm_body(r["entry"])
    out = []
    for k, i in enumerate(insns):
        if i.id != C.X86_INS_CALL or not (i.operands and i.operands[0].type == C.X86_OP_IMM):
            continue
        callee = i.operands[0].imm & 0xFFFFFFFF
        if not C.in_text(callee):
            continue
        consts, nret = ret_consts(callee)
        if consts is None or nret < 2:
            continue
        # 候选测试寄存器：eax（就近）、或紧随的 mov reg,eax
        cands = [(C.X86_REG_EAX, "eax", k)]
        if k + 1 < len(insns):
            rr, rn = regname_from_mov(insns[k + 1])
            if rr is not None:
                cands.append((rr, rn, k + 1))
        for rid, rn, mvi in cands:
            hit = None
            for a in range(mvi + 1, min(mvi + 4, len(insns))):
                ins_a = insns[a]
                if ins_a.id in (C.X86_INS_TEST, C.X86_INS_OR) and len(ins_a.operands) == 2 \
                   and ins_a.operands[0].type == C.X86_OP_REG and ins_a.operands[0].reg == rid \
                   and ins_a.operands[1].type == C.X86_OP_REG and ins_a.operands[1].reg == rid:
                    hit = (a, "test")
                    break
                if ins_a.id == C.X86_INS_CMP and len(ins_a.operands) == 2 \
                   and ins_a.operands[0].type == C.X86_OP_REG and ins_a.operands[0].reg == rid \
                   and ins_a.operands[1].type == C.X86_OP_IMM:
                    hit = (a, "cmp %s" % hex(ins_a.operands[1].imm & 0xFFFFFFFF))
                    break
                if ins_a.id == C.X86_INS_CALL:
                    break
            if not hit:
                continue
            a, kind = hit
            for b in range(a + 1, min(a + 3, len(insns))):
                if insns[b].id in C.JCC:
                    ov = any(o.type == C.X86_OP_REG and o.reg == rid and (o.access & C.CS_AC_WRITE)
                             for x in range(a + 1, b) for o in insns[x].operands)
                    out.append((C.hx(i.address), C.hx(callee), rn, kind,
                                insns[b].mnemonic, C.hx(insns[b].address),
                                C.hx(insns[b].operands[0].imm & 0xFFFFFFFF),
                                sorted(set(consts))[:10], nret, ov))
                    break
            break
    if out:
        seen, uq = set(), []
        for o in out:
            key = (o[0], o[2], o[4], o[5])
            if key in seen:
                continue
            seen.add(key)
            uq.append(o)
        print("ROW %2d %s %-22s  返回值测试站点 %d" % (n, r["entry"], r["name"], len(uq)))
        for o in uq:
            print("    call %s ->%s reg=%-3s %-9s | %s@%s ->%s | callee consts=%s (n_ret=%d) | 覆写=%s" %
                  (o[0], o[1], o[2], o[3], o[4], o[5], o[6], o[7], o[8], o[9]))
    else:
        print("ROW %2d %s %-22s  返回值测试站点 0" % (n, r["entry"], r["name"]))
