# -*- coding: utf-8 -*-
"""逐行反汇编导出（带每条指令原始字节、call 形态标注、站点高亮）。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

here = os.path.dirname(os.path.abspath(__file__))


def rawbytes(va, n):
    return " ".join("%02x" % b for b in C.va_read(va, n))


def dump(entry, out=None, mark=()):
    e, insns = C.disasm_body(entry)
    lines = []
    for ins in insns:
        b = rawbytes(ins.address, ins.size)
        tag = ""
        if ins.address in mark:
            tag = "   <<<<"
        if ins.id == C.X86_INS_CALL:
            if ins.operands and ins.operands[0].type == C.X86_OP_IMM:
                tag += "  [direct->%08X]" % (ins.operands[0].imm & 0xFFFFFFFF)
            elif ins.operands and ins.operands[0].type == C.X86_OP_MEM:
                op = ins.operands[0].mem
                tag += "  [INDIRECT %s+%s*%d+0x%X]" % (
                    ins.reg_name(op.base) if op.base else "-",
                    ins.reg_name(op.index) if op.index else "-",
                    op.scale, op.disp & 0xFFFFFFFF)
        lines.append("%08X: %-24s %-34s ; %s%s" % (ins.address, b, ins.mnemonic + " " + ins.op_str, "", tag))
    txt = "\n".join(lines)
    if out:
        open(out, "w", encoding="utf-8").write(txt)
    return txt


if __name__ == "__main__":
    rows = json.load(open(os.path.join(here, "rows_b1.json"), encoding="utf-8"))
    for r in rows:
        p = os.path.join(here, "body_%s.txt" % r["entry"])
        dump(r["entry"], p)
        print("%s %s -> %d 行" % (r["entry"], r["name"], open(p, encoding="utf-8").read().count("\n") + 1))
