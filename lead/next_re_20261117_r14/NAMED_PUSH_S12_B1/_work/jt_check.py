# -*- coding: utf-8 -*-
"""③b① 跳转表核验：解析每行的间接跳转表，逐项读目标，判是否互异/在 .text/每路可单独验证。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

here = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(here, "rows_b1.json"), encoding="utf-8"))


def block_terminates(insns_by_addr, target, maxn=60):
    """从 target 起沿线性路径走到 ret/jmp/条件跳转，返回 (终止方式, 指令数, 是否含非栈写)。"""
    seq = []
    a = target
    for _ in range(maxn):
        if a not in insns_by_addr:
            return ("fall-out", len(seq), False)
        ins = insns_by_addr[a]
        seq.append(ins)
        if ins.id == C.X86_INS_RET:
            return ("ret", len(seq), any(is_nonstack_write(i) for i in seq))
        if ins.id == C.X86_INS_JMP:
            return ("jmp", len(seq), any(is_nonstack_write(i) for i in seq))
        if ins.id in C.JCC:
            return ("jcc", len(seq), any(is_nonstack_write(i) for i in seq))
        a = ins.address + ins.size
    return ("too-long", len(seq), False)


def is_nonstack_write(ins):
    if not ins.operands:
        return False
    d = ins.operands[0]
    if d.type != C.X86_OP_MEM:
        return False
    base = ins.reg_name(d.mem.base) if d.mem.base else ""
    if base in ("esp", "ebp"):
        return False
    return True


for n, r in enumerate(rows, 1):
    e, insns = C.disasm_body(r["entry"])
    by = {i.address: i for i in insns}
    jts = C.jumptables(insns)
    if not jts:
        continue
    print("ROW %2d %s %-22s" % (n, r["entry"], r["name"]))
    for jt in jts:
        tg = jt["targets"]
        print("   jmp@%08X  op=%s  table=%s bound=%s n=%s 目标数=%d" %
              (jt["jmp_va"], jt["op_str"],
               ("%08X" % jt["table_va"]) if jt["table_va"] else None,
               jt["bound"], jt["ncase"], len(tg)))
        if not tg:
            continue
        uniq = sorted({t for _, t in tg})
        print("      互异目标=%d  全部在.text=%s" % (len(uniq), all(C.in_text(t) for _, t in tg)))
        # 逐项块形态
        kinds = {}
        for c, t in tg:
            term, ln, nsw = block_terminates(by, t)
            kinds.setdefault((term, nsw), []).append(c)
        for k, v in kinds.items():
            print("      块形态 %s 非栈写=%s : %d 路 -> cases %s" % (k[0], k[1], len(v), v[:12]))
