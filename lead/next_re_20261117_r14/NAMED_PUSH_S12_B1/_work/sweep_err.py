# -*- coding: utf-8 -*-
"""补充扫描：直接调用 + 被调返回常量集合含 0 与至少一个非 0 小常量者，
再检查调用点之后 1..5 条内是否 test/cmp eax 并条件跳转（不看机械 p2 签名）。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

here = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(here, "rows_b1.json"), encoding="utf-8"))


def ret_consts(va):
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


def looks_errorcode(consts):
    if consts is None:
        return False
    if 0 not in consts:
        return False
    small = [c for c in consts if c not in (0,) and 1 <= c <= 0x40]
    return len(small) >= 1 and len(consts) >= 2


for n, r in enumerate(rows, 1):
    e, insns = C.disasm_body(r["entry"])
    idx = {i.address: k for k, i in enumerate(insns)}
    found = []
    for k, i in enumerate(insns):
        if i.id != C.X86_INS_CALL or not (i.operands and i.operands[0].type == C.X86_OP_IMM):
            continue
        callee = i.operands[0].imm & 0xFFFFFFFF
        if not C.in_text(callee):
            continue
        rc = ret_consts(callee)
        if not rc or not looks_errorcode(rc[0]):
            continue
        consts, nret = rc
        # 调用点后 1..6 条内 test/cmp eax + jcc
        for a in range(k + 1, min(k + 6, len(insns))):
            tk = C.test_kind(insns[a])
            if not tk:
                if C.writes_eax(insns[a]):
                    break
                continue
            for b in range(a + 1, min(a + 3, len(insns))):
                if insns[b].id in C.JCC:
                    # eax 覆写检查
                    ov = any(C.writes_eax(insns[x]) for x in range(a + 1, b))
                    found.append(dict(call=C.hx(i.address), callee=C.hx(callee),
                                      nret=nret, consts=sorted(consts)[:8],
                                      test_kind=tk[0], test_imm=tk[1],
                                      jcc=insns[b].mnemonic, jcc_va=C.hx(insns[b].address),
                                      tgt=C.hx(insns[b].operands[0].imm & 0xFFFFFFFF),
                                      eax_overwrite=ov))
                    break
            break
    print("ROW %2d %s %-22s  错误码型直接调用站点=%d" % (n, r["entry"], r["name"], len(found)))
    for f in found:
        print("     call %s -> %s rets=%d consts=%s | %s imm=%s | %s@%s -> %s | eax覆写=%s" %
              (f["call"], f["callee"], f["nret"], [hex(c) for c in f["consts"]],
               f["test_kind"], ("0x%X" % f["test_imm"]) if f["test_imm"] is not None else "-",
               f["jcc"], f["jcc_va"], f["tgt"], f["eax_overwrite"]))
